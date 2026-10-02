"""The pictures children pick themselves.

A child who cannot yet read reliably still has to find their own row on the
sign-in screen, in front of a sibling who is waiting. The avatar is how they do
it, so it is not decoration: it is the only part of that screen a four-year-old
can use.

The set is shipped with Kidux rather than letting an adult supply a photograph.
A fixed set is always there, always legible at the size the screen shows it,
and never accidentally puts a photograph of a child on a screen that anyone
walking past can see.

Avatars are stored by name — "fox", "owl" — never by path. The name goes in the
child's profile and survives the file moving, being redrawn, or another format
replacing SVG.
"""

import re
from pathlib import Path

from . import paths

#: What a valid avatar name looks like. Deliberately narrow: the name comes out
#: of a state file and is turned straight into a filename.
_NAME = re.compile(r"\A[a-z][a-z0-9-]{0,31}\Z")

#: Shown when a child's avatar names a file that is not installed — an avatar
#: removed by a later version, or a profile restored from an older machine. A
#: missing picture must never be an empty space a child cannot identify.
FALLBACK = "star"


class UnknownAvatarError(Exception):
    """The name is not one of the avatars this installation ships."""


def is_valid_name(name: str) -> bool:
    """Whether a string could name an avatar at all.

    Separate from whether it exists: a name can be well-formed and simply not
    installed, and the two failures want different answers.
    """
    return bool(_NAME.match(name))


def path_for(name: str) -> Path:
    """Where the file for this avatar is, whether or not it exists."""
    if not is_valid_name(name):
        raise UnknownAvatarError(f"not a valid avatar name: {name!r}")
    return paths.AVATAR_DIR / f"{name}.svg"


def available() -> list[str]:
    """Every avatar installed, sorted, for the adult panel to offer.

    An empty list means the data package is missing or broken, which the caller
    has to handle: a first-run wizard with no avatars to choose from cannot
    create a child.
    """
    directory = paths.AVATAR_DIR
    if not directory.is_dir():
        return []

    return sorted(
        entry.stem
        for entry in directory.glob("*.svg")
        if is_valid_name(entry.stem)
    )


def exists(name: str) -> bool:
    return is_valid_name(name) and path_for(name).is_file()


def resolve(name: str | None) -> str:
    """The avatar to actually show for a stored name.

    Falls back rather than failing. This is called while drawing a screen a
    child is waiting in front of, and a missing picture is never worth an
    error there. If even the fallback is missing the first installed avatar is
    used, and only a completely empty set raises.
    """
    if name and exists(name):
        return name

    if exists(FALLBACK):
        return FALLBACK

    installed = available()
    if installed:
        return installed[0]

    raise UnknownAvatarError("no avatars are installed")
