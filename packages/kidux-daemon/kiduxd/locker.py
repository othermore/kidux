"""Putting the lock screen up over a child's session, and taking it down.

daemon.md section 10. The lock screen is a separate compositor on its own
virtual terminal, running as _greetd. Locking switches the seat to it through
logind, which takes the display and the input devices away from the child's
compositor whether it likes it or not, and then freezes everything the child
was running. Nothing the child runs can stop any of it.

A lock has happened only when logind confirms the child's session is no
longer active (D28). If that confirmation does not come, the child still has
the screen, and a time limit that can be ignored is worse than losing unsaved
work, which the launcher warned about at ten, five and one minute: the
session is ended instead, and the reason is audited.
"""

import time
from typing import Callable, Protocol

from kidux.log import get_logger

from .errors import Failed
from .sessions import Tracked

_log = get_logger("locker")

#: The virtual terminal the lock screen runs on. The sign-in screen is on 7.
LOCK_VT = 8

LOCKER_READY_SECONDS = 5.0
SWITCH_SECONDS = 3.0
#: After the child's session has the screen back, how long before its
#: compositor has surely resumed its input devices (`Machine.wake_input`).
WAKE_INPUT_SECONDS = 0.5


def user_manager(tracked: Tracked) -> str:
    """The child's systemd user manager, under which their modules run in
    scopes of their own (D32), outside the session's scope: frozen and thawed
    with it, so that a module is stopped under the lock screen as the session
    is."""
    return f"user@{tracked.uid}.service"


class Machine(Protocol):
    """What the lock needs from systemd and logind."""

    def start_locker(self, username: str) -> None: ...
    def stop_locker(self, username: str) -> None: ...
    def locker_ready(self) -> bool: ...
    def switch_to(self, vt: int) -> None: ...
    def session_active(self, session_path: str) -> bool: ...
    def freeze(self, scope: str) -> None: ...
    def thaw(self, scope: str) -> None: ...
    def terminate(self, session_path: str) -> None: ...
    def session_closing(self, session_path: str) -> bool: ...
    def stop_scope(self, scope: str) -> None: ...
    def wake_input(self) -> None: ...


def wait_for(
    condition: Callable[[], bool],
    seconds: float,
    sleep: Callable[[float], None] = time.sleep,
    step: float = 0.1,
) -> bool:
    """Poll `condition` until it holds or `seconds` pass. True if it held."""
    waited = 0.0
    while True:
        try:
            if condition():
                return True
        except Exception:
            _log.debug("condition raised while waiting", exc_info=True)
        if waited >= seconds:
            return False
        sleep(step)
        waited += step


class Locker:
    def __init__(
        self,
        machine: Machine,
        audit: Callable[..., None],
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self._machine = machine
        self._audit = audit
        self._sleep = sleep

    def _wait(self, condition: Callable[[], bool], seconds: float) -> bool:
        return wait_for(condition, seconds, self._sleep)

    def lock(self, tracked: Tracked, reason: str) -> bool:
        """Lock the session. True if locked; False if it had to be ended instead."""
        machine = self._machine

        try:
            machine.start_locker(tracked.username)
        except Exception as error:  # noqa: BLE001 — systemd refused; the child still has the screen
            return self._give_up(tracked, reason, f"the lock screen could not be started: {error}")
        if not self._wait(machine.locker_ready, LOCKER_READY_SECONDS):
            return self._give_up(tracked, reason, "the lock screen did not start")

        machine.switch_to(LOCK_VT)
        if not self._wait(lambda: not machine.session_active(tracked.session_path), SWITCH_SECONDS):
            return self._give_up(tracked, reason, "logind did not switch away from the session")

        for unit in (tracked.scope, user_manager(tracked)):
            try:
                machine.freeze(unit)
            except Exception as error:
                # The session has already lost the screen and the input
                # devices; a unit that will not freeze keeps running out of
                # sight but cannot be used. Worth knowing, not worth ending
                # the session over.
                _log.warning("could not freeze %s: %s", unit, error)
                self._audit("freeze", "failed", child=tracked.username, unit=unit,
                            reason=str(error))

        self._audit("lock", "ok", child=tracked.username, reason=reason)
        return True

    def _give_up(self, tracked: Tracked, reason: str, why: str) -> bool:
        self._audit("lock", "failed", child=tracked.username, reason=reason, why=why)
        try:
            self._machine.terminate(tracked.session_path)
        finally:
            try:
                self._machine.stop_locker(tracked.username)
            except Exception:
                _log.debug("could not stop the locker", exc_info=True)
        self._audit("session ended", "ok", child=tracked.username, reason="lock failed")
        return False

    def unlock(self, tracked: Tracked) -> None:
        """Give the screen back. Raises Failed if logind does not switch back."""
        machine = self._machine

        # Thaw first, so the compositor and the module are running when the
        # display returns.
        for unit in (user_manager(tracked), tracked.scope):
            try:
                machine.thaw(unit)
            except Exception as error:
                _log.warning("could not thaw %s: %s", unit, error)

        machine.switch_to(tracked.vtnr)
        if not self._wait(lambda: machine.session_active(tracked.session_path), SWITCH_SECONDS):
            # The lock screen stays up: better a child who has to ask again
            # than one left looking at nothing.
            self._audit("unlock", "failed", child=tracked.username)
            raise Failed("could not switch back to the child's session")

        # A compositor that gets the screen back takes its input devices
        # back too, but does not look at them until the first event comes,
        # and that event, a key the child presses, is spent on setting the
        # keyboard up and never reaches the window (wlroots 0.18 resumes
        # libinput without reading its queue). A change event on the input
        # devices, from here, is what makes it look first.
        self._sleep(WAKE_INPUT_SECONDS)
        try:
            machine.wake_input()
        except Exception:
            _log.warning("could not wake the input devices", exc_info=True)

        machine.stop_locker(tracked.username)
        self._audit("unlock", "ok", child=tracked.username)

    def thaw(self, tracked: Tracked) -> None:
        """Thaw the session's units without unlocking: before ending the
        session, and before the machine powers off or the daemon stops,
        since systemd refuses to stop a frozen unit and a frozen process
        cannot act on the signal that asks it to save and go."""
        for unit in (user_manager(tracked), tracked.scope):
            try:
                self._machine.thaw(unit)
            except Exception:
                _log.debug("could not thaw %s", unit, exc_info=True)

    def abandoned(self, tracked: Tracked) -> bool:
        """Whether a locked session has lost its compositor while frozen.

        When greetd stops, it ends the process that is the session, and the
        kernel ends that process's group with it; but the compositor starts the
        launcher in a group of its own, which a frozen process cannot
        leave on its own. logind then tries to stop the session's scope,
        and systemd refuses to stop a frozen unit: the session is left
        closing, with the launcher frozen in it, for ever.
        """
        try:
            return self._machine.session_closing(tracked.session_path)
        except Exception:
            _log.debug("could not ask about session %s", tracked.session_id, exc_info=True)
            return False

    def end_abandoned(self, tracked: Tracked) -> None:
        """End a session `abandoned` says is left closing. logind has
        already tried to stop it and does not try again, so its scope is
        stopped here, once thawed; and its lock screen goes with it."""
        self.thaw(tracked)
        try:
            self._machine.stop_scope(tracked.scope)
        finally:
            self.release(tracked)

    def end(self, tracked: Tracked) -> None:
        self.thaw(tracked)
        try:
            self._machine.terminate(tracked.session_path)
        finally:
            self.release(tracked)

    def release(self, tracked: Tracked) -> None:
        """Take down the lock screen of a session that is gone or going.

        Never left up on its own: a lock screen with no session behind it
        guards nothing, and would be the one shown the next time this child
        is locked. The child's user manager outlives the session, and a lock
        froze it: it is thawed too, or the child's next session would start
        on a frozen manager and every module in it would hang.
        """
        self.thaw_user_manager(tracked)
        try:
            self._machine.stop_locker(tracked.username)
        except Exception:
            _log.warning("could not stop %s's lock screen", tracked.username, exc_info=True)

    def thaw_user_manager(self, tracked: Tracked) -> None:
        """Thaw the child's user manager, whatever froze it and whether or not
        it is frozen: for a session that has gone, and for one that starts."""
        try:
            self._machine.thaw(user_manager(tracked))
        except Exception:
            _log.debug("could not thaw %s", user_manager(tracked), exc_info=True)
