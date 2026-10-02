"""Tests for the pictures children pick themselves.

Run against the avatars actually shipped in this package, not fixtures: what
matters is that the set a child will be offered is complete and legible, and a
test on invented files would not say that.
"""

import importlib
import xml.etree.ElementTree as ElementTree
import pytest

from kidux import avatars, paths


@pytest.fixture
def installed(monkeypatch, shipped_avatars):
    """Point the library at the avatars in this source tree."""
    monkeypatch.setattr(paths, "AVATAR_DIR", shipped_avatars)
    yield
    importlib.reload(paths)


def test_the_shipped_set_is_not_empty(installed):
    # A first-run wizard with no avatars cannot create a child at all.
    assert avatars.available()


def test_there_are_enough_for_the_children_of_one_family(installed):
    # Siblings picking from three pictures will end up arguing, and two
    # children with the same avatar defeats the whole point of having one.
    assert len(avatars.available()) >= 6


def test_the_fallback_is_one_of_them(installed):
    # resolve() leans on this whenever a profile names an avatar that a later
    # version removed.
    assert avatars.FALLBACK in avatars.available()


def test_every_shipped_file_is_valid_svg(shipped_avatars):
    for path in sorted(shipped_avatars.glob("*.svg")):
        ElementTree.parse(path)


def test_every_shipped_file_scales(shipped_avatars):
    # Without a viewBox an SVG has a fixed size, and the sign-in screen shows
    # these at whatever the display scale asks for.
    for path in sorted(shipped_avatars.glob("*.svg")):
        root = ElementTree.parse(path).getroot()
        assert root.get("viewBox"), f"{path.name} has no viewBox"


def test_every_shipped_file_says_what_it_is(shipped_avatars):
    # Read aloud by a screen reader, and by an adult helping a child choose.
    for path in sorted(shipped_avatars.glob("*.svg")):
        root = ElementTree.parse(path).getroot()
        label = root.get("{http://www.w3.org/XML/1998/namespace}label") or root.get(
            "aria-label"
        )
        assert label, f"{path.name} has no aria-label"


def test_resolve_keeps_a_valid_choice(installed):
    assert avatars.resolve("fox") == "fox"


def test_resolve_falls_back_rather_than_failing(installed):
    # Called while drawing a screen a child is waiting in front of. An error
    # there would be far worse than the wrong picture.
    assert avatars.resolve("a-removed-avatar") == avatars.FALLBACK
    assert avatars.resolve(None) == avatars.FALLBACK
    assert avatars.resolve("") == avatars.FALLBACK


@pytest.mark.parametrize(
    "name",
    ["../../etc/passwd", "fox/../../x", "Fox", "fox.svg", "", "-fox", "9lives"],
)
def test_invalid_names_are_refused(name):
    # The name comes out of a state file and is turned into a filename.
    assert not avatars.is_valid_name(name)
    with pytest.raises(avatars.UnknownAvatarError):
        avatars.path_for(name)


def test_an_empty_installation_raises(monkeypatch, tmp_path):
    monkeypatch.setattr(paths, "AVATAR_DIR", tmp_path)
    try:
        assert avatars.available() == []
        with pytest.raises(avatars.UnknownAvatarError):
            avatars.resolve("fox")
    finally:
        importlib.reload(paths)
