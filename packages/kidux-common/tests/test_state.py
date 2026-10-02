"""Tests for reading and writing the files under /home/.kidux.

The cases here are the ones that actually happen on a family's machine: a
child pulls the plug, an upgrade is interrupted halfway, a file gets truncated.
Each one has a right answer that is not the obvious one, which is why they are
written down.
"""

import os
import stat

import pytest

from kidux import paths, state


def test_round_trip(tmp_path):
    path = tmp_path / "profile.toml"
    state.write(path, {"display_name": "Ana", "language": "es_ES.UTF-8"}, "profile")

    document = state.read(path, "profile")

    assert document["display_name"] == "Ana"
    assert document["language"] == "es_ES.UTF-8"


def test_write_stamps_the_schema_version(tmp_path):
    path = tmp_path / "profile.toml"
    state.write(path, {"display_name": "Ana"}, "profile")

    assert state.read(path, "profile")["schema_version"] == (
        state.SCHEMA_VERSIONS["profile"]
    )


def test_write_creates_missing_directories(tmp_path):
    # A child is created before their directory exists, which is every time a
    # child is created.
    path = tmp_path / "children" / "ana" / "profile.toml"
    state.write(path, {"display_name": "Ana"}, "profile")

    assert path.is_file()


def test_written_files_are_closed_to_children(tmp_path):
    # The whole point of /home/.kidux is that a child cannot read it. A file
    # written world-readable would hand every child the adult password hash.
    path = tmp_path / "adults.toml"
    state.write(path, {"password_hash": "$argon2id$..."}, "adults")

    mode = stat.S_IMODE(path.stat().st_mode)

    assert not mode & stat.S_IROTH
    assert not mode & stat.S_IWOTH


def test_write_leaves_no_temporary_files_behind(tmp_path):
    path = tmp_path / "usage.toml"
    state.write(path, {"seconds_used_today": 120}, "usage")

    assert sorted(entry.name for entry in tmp_path.iterdir()) == ["usage.toml"]


def test_write_replaces_atomically(tmp_path):
    # The old contents have to survive intact until the new ones are complete,
    # because the alternative is a child's daily counter resetting on a crash.
    path = tmp_path / "usage.toml"
    state.write(path, {"seconds_used_today": 100}, "usage")
    first_inode = path.stat().st_ino

    state.write(path, {"seconds_used_today": 200}, "usage")

    assert state.read(path, "usage")["seconds_used_today"] == 200
    # A replace, not an in-place rewrite: a reader holding the old file keeps
    # reading a whole, valid document.
    assert path.stat().st_ino != first_inode


def test_missing_file_with_a_default(tmp_path):
    document = state.read(
        tmp_path / "modules.toml", "modules", default={"enabled": []}
    )

    assert document == {"enabled": []}


def test_missing_file_without_a_default_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        state.read(tmp_path / "modules.toml", "modules")


def test_corrupt_file_is_an_error_not_a_default(tmp_path):
    # The dangerous version of this bug: treating an unreadable access policy
    # as "no policy" would hand a child unlimited time.
    path = tmp_path / "access.toml"
    path.write_text("this is not toml = = =")

    with pytest.raises(state.CorruptStateError):
        state.read(path, "access", default={"mode": "manual"})


def test_truncated_file_is_an_error(tmp_path):
    path = tmp_path / "access.toml"
    state.write(path, {"mode": "daily", "daily_minutes": 45}, "access")

    with open(path, "r+b") as handle:
        handle.truncate(10)

    with pytest.raises(state.StateError):
        state.read(path, "access")


def test_file_without_a_schema_version_is_refused(tmp_path):
    path = tmp_path / "config.toml"
    path.write_text('default_language = "es_ES.UTF-8"\n')

    with pytest.raises(state.CorruptStateError):
        state.read(path, "config")


def test_newer_schema_is_refused_rather_than_guessed(tmp_path):
    # An interrupted upgrade, or a /home moved to a machine running an older
    # Kidux. Reading it as though we understood it would corrupt it.
    path = tmp_path / "config.toml"
    path.write_text(
        f"schema_version = {state.SCHEMA_VERSIONS['config'] + 1}\n"
        'something_we_do_not_know_about = true\n'
    )

    with pytest.raises(state.SchemaTooNewError):
        state.read(path, "config")


def test_older_schema_without_a_migration_is_refused(tmp_path):
    path = tmp_path / "config.toml"
    path.write_text("schema_version = 0\n")

    with pytest.raises(state.StateError):
        state.read(path, "config")


def test_older_schema_is_migrated_when_a_migration_exists(tmp_path, monkeypatch):
    def add_the_new_field(document):
        document["reset_hour"] = 4
        return document

    monkeypatch.setitem(state.SCHEMA_VERSIONS, "config", 2)
    monkeypatch.setitem(state._MIGRATIONS, ("config", 1), add_the_new_field)

    path = tmp_path / "config.toml"
    path.write_text('schema_version = 1\ndefault_language = "es_ES.UTF-8"\n')

    document = state.read(path, "config")

    assert document["reset_hour"] == 4
    assert document["schema_version"] == 2
    assert document["default_language"] == "es_ES.UTF-8"


def test_unknown_kind_is_a_programming_error(tmp_path):
    with pytest.raises(ValueError):
        state.read(tmp_path / "whatever.toml", "not-a-kind")

    with pytest.raises(ValueError):
        state.write(tmp_path / "whatever.toml", {}, "not-a-kind")


def test_failed_write_leaves_the_old_file_intact(tmp_path, monkeypatch):
    path = tmp_path / "usage.toml"
    state.write(path, {"seconds_used_today": 100}, "usage")

    def explode(*args, **kwargs):
        raise OSError("the disk is full")

    monkeypatch.setattr(os, "replace", explode)

    with pytest.raises(OSError):
        state.write(path, {"seconds_used_today": 200}, "usage")

    assert state.read(path, "usage")["seconds_used_today"] == 100
    assert sorted(entry.name for entry in tmp_path.iterdir()) == ["usage.toml"]


def test_root_gives_what_it_writes_to_the_administrators(tmp_path, monkeypatch):
    # Root writes every state file, and a file root makes belongs to group
    # root, which would close /home/.kidux to the administrators it is meant
    # to be readable by. So the daemon gives each file to kidux-admin.
    import grp

    given = []
    monkeypatch.setattr(os, "geteuid", lambda: 0)
    monkeypatch.setattr(grp, "getgrnam", lambda name: type("g", (), {"gr_gid": 1234})())
    monkeypatch.setattr(os, "chown", lambda path, uid, gid: given.append((uid, gid)))
    monkeypatch.setattr(paths, "STATE_ROOT", tmp_path)

    state.write(tmp_path / "children" / "ana" / "profile.toml", {"display_name": "Ana"}, "profile")

    assert (0, 1234) in given
    # The directories on the way too, whoever made them.
    assert given.count((0, 1234)) == 3


def test_anyone_else_writes_as_themselves(tmp_path, monkeypatch):
    # Under a test or a developer's account there is nothing to give away.
    monkeypatch.setattr(os, "geteuid", lambda: 1000)
    monkeypatch.setattr(os, "chown", lambda *args: pytest.fail("chown called"))

    state.write(tmp_path / "profile.toml", {"display_name": "Ana"}, "profile")
