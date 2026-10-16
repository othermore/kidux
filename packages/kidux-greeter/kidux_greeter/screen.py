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


#: What moves on from one look at a running job to the next: a page drawn
#: again for it alone would only flicker over itself.
PROGRESS = ("fraction", "package", "packages")


def only_progress_differs(old: Screen, new: Screen) -> bool:
    """Whether `new` is `old` with a job's progress moved on, and nothing
    else: the same polled screen, so that the page on display keeps its
    place and only its bars and words follow."""
    if (old.name, old.owner, old.language, old.notice) != (new.name, new.owner, new.language,
                                                            new.notice):
        return False
    if not (old.data.get("polling") and new.data.get("polling")):
        return False

    def rest(data: dict) -> dict:
        return {key: value for key, value in data.items() if key != "update"}

    def still(data: dict) -> dict:
        return {key: value for key, value in (data.get("update") or {}).items()
                if key not in PROGRESS}

    return rest(old.data) == rest(new.data) and still(old.data) == still(new.data)
