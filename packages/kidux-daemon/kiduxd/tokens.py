"""Adult-panel tokens.

`Unlock(password)` hands the adult panel a token, and every configuration
change carries it. A token is bound to the D-Bus connection it was issued to
and to that connection's uid, so it is worthless anywhere else, and it dies
when any of these happens (D6, D26):

- the panel gives it back with `Lock(token)`;
- the connection it was issued to leaves the bus, because the panel closed,
  crashed or was killed;
- it has not been used for the configured number of minutes, because a panel
  left open in a living room is open to whoever walks past;
- the same connection unlocks again: one token per connection.
"""

import secrets
import time
from dataclasses import dataclass
from typing import Callable

from .errors import NotUnlocked


@dataclass
class _Token:
    value: str
    unique_name: str
    uid: int
    last_used: float


class Tokens:
    def __init__(
        self,
        timeout_seconds: float,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._timeout = timeout_seconds
        self._clock = clock
        self._by_name: dict[str, _Token] = {}

    def issue(self, unique_name: str, uid: int) -> str:
        value = secrets.token_urlsafe(32)
        self._by_name[unique_name] = _Token(value, unique_name, uid, self._clock())
        return value

    def check(self, value: str, unique_name: str, uid: int) -> None:
        """Accept the token for this caller, or raise NotUnlocked.

        Using a token counts as activity: the panel stays unlocked for as long
        as an adult is actually doing something in it.
        """
        token = self._by_name.get(unique_name)

        if (
            token is None
            or not value
            or not secrets.compare_digest(token.value, value)
            or token.uid != uid
        ):
            raise NotUnlocked("the adult panel is not unlocked")

        if self._clock() - token.last_used > self._timeout:
            del self._by_name[unique_name]
            raise NotUnlocked("the adult panel was left unlocked too long")

        token.last_used = self._clock()

    def revoke(self, value: str, unique_name: str) -> bool:
        token = self._by_name.get(unique_name)
        if token is not None and secrets.compare_digest(token.value, value):
            del self._by_name[unique_name]
            return True
        return False

    def set_timeout(self, timeout_seconds: float) -> None:
        """A new length for "too long", from the next check on."""
        self._timeout = timeout_seconds

    def revoke_name(self, unique_name: str) -> bool:
        """The connection left the bus. True if it held a token."""
        return self._by_name.pop(unique_name, None) is not None

    def expire(self) -> list[int]:
        """Drop every token idle for too long; return the uids they belonged to."""
        now = self._clock()
        expired = [
            name
            for name, token in self._by_name.items()
            if now - token.last_used > self._timeout
        ]
        return [self._by_name.pop(name).uid for name in expired]

    def __len__(self) -> int:
        return len(self._by_name)
