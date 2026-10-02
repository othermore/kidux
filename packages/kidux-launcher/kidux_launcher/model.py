"""What the launcher shows, worked out without a screen (launcher.md section 3).

The daemon holds the clock; this only keeps the last figures it gave, counts
down between two answers so the number moves every minute, and remembers the
warning to show. It never decides that time is up: the daemon does, and
locks, and there is then nothing for the launcher to draw.
"""

import math
import time

UNLIMITED = -1


class Model:
    def __init__(self, clock=time.monotonic) -> None:
        self._clock = clock
        self.used = 0
        self._left = UNLIMITED
        self._fetched_at = clock()
        #: False while the daemon cannot be asked: the figures stay, and stop.
        self.daemon_there = False
        #: The warning to show, in seconds left when it was given, or None.
        self.warning: int | None = None

    def update(self, used: int, left: int) -> None:
        """What the daemon answered to Usage."""
        self.used, self._left = used, left
        self._fetched_at = self._clock()
        self.daemon_there = True

    def daemon_away(self) -> None:
        # Freeze where it was: counting down on its own would show a guess.
        self._left = self.left()
        self._fetched_at = self._clock()
        self.daemon_there = False

    @property
    def unlimited(self) -> bool:
        return self._left == UNLIMITED

    def left(self) -> int:
        """Seconds left now, or UNLIMITED."""
        if self._left == UNLIMITED:
            return UNLIMITED
        if not self.daemon_there:
            return self._left
        return max(0, self._left - int(self._clock() - self._fetched_at))

    def minutes_left(self) -> int | None:
        """Whole minutes left, rounded up so that zero only means none; None if unlimited."""
        left = self.left()
        return None if left == UNLIMITED else math.ceil(left / 60)

    def time_text(self, translations) -> str | None:
        """ "25 minutes left" in the child's language; None for a child with no limit."""
        minutes = self.minutes_left()
        if minutes is None:
            return None
        return translations.ngettext(
            "{count} minute left", "{count} minutes left", minutes).format(count=minutes)

    def time_clock(self) -> str | None:
        """The time left as a clock reads it, hours and minutes: "00:51",
        "01:30"; None for a child with no limit."""
        minutes = self.minutes_left()
        if minutes is None:
            return None
        return f"{minutes // 60:02d}:{minutes % 60:02d}"

    def warn(self, seconds_left: int) -> None:
        """TimeWarning from the daemon: ten, five or one minute."""
        self.warning = seconds_left

    def dismiss(self) -> None:
        self.warning = None

    def warning_text(self, translations) -> str | None:
        if self.warning is None:
            return None
        minutes = max(1, math.ceil(self.warning / 60))
        return translations.ngettext(
            "{count} minute left. Save your work.",
            "{count} minutes left. Save your work.", minutes).format(count=minutes)
