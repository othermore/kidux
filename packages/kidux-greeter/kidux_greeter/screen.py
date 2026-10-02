"""What every state machine of the trusted screens answers with."""

from dataclasses import dataclass, field

#: What an adult may pick when giving time, in minutes.
GRANT_CHOICES = (15, 30, 60)


@dataclass(frozen=True)
class Screen:
    name: str
    language: str
    data: dict = field(default_factory=dict)
    #: A sentence to show on top of the screen: a wrong password, say. A
    #: vocabulary string, untranslated; the view translates it.
    notice: str | None = None
    #: Which state machine answers what is tapped on this screen: "" for the
    #: one the program started with (the sign-in or the lock screen),
    #: "wizard" or "panel" for the ones it hands over to.
    owner: str = ""
