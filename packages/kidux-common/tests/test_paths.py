"""Tests for the one place paths are spelled out.

Mostly about one thing: a username arrives from an adult typing into the panel
and from D-Bus calls, so it is input. The daemon runs as root, and it turns a
username straight into a filename.
"""

import importlib

import pytest

from kidux import paths


def test_child_files_live_under_the_children_directory():
    assert paths.child_profile("ana").parent == paths.child_dir("ana")
    assert paths.child_dir("ana").parent == paths.CHILDREN_DIR


def test_the_four_child_files_are_distinct():
    files = {
        paths.child_profile("ana"),
        paths.child_access("ana"),
        paths.child_usage("ana"),
        paths.child_modules("ana"),
    }
    assert len(files) == 4


@pytest.mark.parametrize(
    "username",
    [
        "../../../etc",
        "ana/../../root",
        "/etc/passwd",
        "..",
        ".",
        "",
        "back\\slash",
    ],
)
def test_a_username_cannot_escape_the_children_directory(username):
    # Without this, a D-Bus caller could aim a root-owned write at any path on
    # the machine by choosing the right name for a child.
    with pytest.raises(ValueError):
        paths.child_dir(username)


def test_ordinary_usernames_are_accepted():
    for username in ["ana", "luis2", "maria-jose", "a"]:
        assert paths.child_dir(username).name == username


def test_roots_come_from_the_environment(monkeypatch, tmp_path):
    # This is what lets the tests run at all without touching a real /home.
    monkeypatch.setenv("KIDUX_STATE_ROOT", str(tmp_path / "state"))
    monkeypatch.setenv("KIDUX_DATA_ROOT", str(tmp_path / "data"))

    reloaded = importlib.reload(paths)
    try:
        assert reloaded.STATE_ROOT == tmp_path / "state"
        assert reloaded.DATA_ROOT == tmp_path / "data"
        assert reloaded.CONFIG_FILE == tmp_path / "state" / "config.toml"
    finally:
        monkeypatch.undo()
        importlib.reload(paths)


def test_the_state_root_is_on_home_by_default(monkeypatch):
    # Reinstalling the system partition must not lose a family's settings or
    # the record of how much time a child has used.
    monkeypatch.delenv("KIDUX_STATE_ROOT", raising=False)

    reloaded = importlib.reload(paths)
    try:
        assert str(reloaded.STATE_ROOT).startswith("/home/")
    finally:
        importlib.reload(paths)
