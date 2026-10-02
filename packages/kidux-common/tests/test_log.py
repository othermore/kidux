"""Tests for the audit trail.

One of these matters more than the rest: a password must never reach the file,
whatever a caller does. Kidux has no lock-out on the adult password by design,
so every attempt is recorded — and a recorded *wrong* password is often
somebody's real password somewhere else.
"""

import json

import pytest

from kidux import log, paths


@pytest.fixture
def audit_file(tmp_path, monkeypatch):
    path = tmp_path / "audit.log"
    monkeypatch.setattr(paths, "AUDIT_LOG", path)
    return path


def read_entries(path):
    return [json.loads(line) for line in path.read_text().splitlines()]


def test_an_entry_records_what_happened(audit_file):
    log.audit("unlock", "ok", caller="_greetd")

    entry = read_entries(audit_file)[0]

    assert entry["action"] == "unlock"
    assert entry["outcome"] == "ok"
    assert entry["caller"] == "_greetd"
    assert entry["time"]


def test_entries_accumulate_rather_than_replace(audit_file):
    log.audit("unlock", "denied")
    log.audit("unlock", "ok")
    log.audit("grant_time", "ok", username="ana", minutes=15)

    assert len(read_entries(audit_file)) == 3


@pytest.mark.parametrize(
    "field",
    ["password", "adult_password", "child_password", "new_password", "token"],
)
def test_secrets_never_reach_the_file(audit_file, field):
    log.audit("unlock", "denied", **{field: "hunter2"}, username="ana")

    raw = audit_file.read_text()

    assert "hunter2" not in raw
    assert field not in raw
    # The surrounding facts still have to be recorded, or the trail would be
    # useless for spotting someone guessing.
    assert json.loads(raw)["username"] == "ana"


def test_a_refused_attempt_is_recorded_as_such(audit_file):
    # The only protection an adult has against guessing is being able to see,
    # afterwards, that it happened.
    log.audit("unlock", "denied", source="lock-screen")

    assert read_entries(audit_file)[0]["outcome"] == "denied"


def test_an_unwritable_trail_does_not_take_the_daemon_down(monkeypatch, tmp_path):
    # A disk that fills up mid-session must not end a child's session.
    unwritable = tmp_path / "nowhere" / "audit.log"
    monkeypatch.setattr(paths, "AUDIT_LOG", unwritable)

    def refuse(*args, **kwargs):
        raise OSError("read-only file system")

    monkeypatch.setattr(log.Path, "mkdir", refuse)

    log.audit("unlock", "ok")


def test_the_file_is_closed_to_children(audit_file):
    import stat

    log.audit("unlock", "ok")
    mode = stat.S_IMODE(audit_file.stat().st_mode)

    assert not mode & stat.S_IROTH
    assert not mode & stat.S_IWOTH


def test_entries_are_one_json_object_per_line(audit_file):
    # So that the trail can be read with grep and tail on a machine with
    # nothing else installed.
    log.audit("unlock", "ok", note="a value with\na newline in it")

    lines = audit_file.read_text().splitlines()

    assert len(lines) == 1
    assert json.loads(lines[0])["note"] == "a value with\na newline in it"


def test_root_gives_the_trail_to_the_administrators(audit_file, monkeypatch):
    # The trail exists for the administrators to read (D15); a file root
    # makes belongs to group root unless it is given away.
    import grp
    import os

    given = []
    monkeypatch.setattr(os, "geteuid", lambda: 0)
    monkeypatch.setattr(grp, "getgrnam", lambda name: type("g", (), {"gr_gid": 1234})())
    monkeypatch.setattr(os, "chown", lambda path, uid, gid: given.append((str(path), uid, gid)))

    log.audit("unlock", "ok")

    assert (str(audit_file), 0, 1234) in given
