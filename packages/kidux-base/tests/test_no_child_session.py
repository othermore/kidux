"""The daily upgrade's condition (bin/kidux-no-child-session, D115).

It is run with stand-ins for loginctl and id first on its PATH, each a
small script that prints what the test gives it: what it says is all the
condition goes by.
"""

import json
import subprocess
from pathlib import Path

import pytest

PACKAGE = Path(__file__).resolve().parents[1]
SCRIPT = PACKAGE / "bin" / "kidux-no-child-session"


def run(tmp_path, sessions, groups: dict, loginctl_fails: bool = False) -> int:
    """The script's exit status, logind listing `sessions` and each user in
    the groups `groups` names."""
    stand_ins = tmp_path / "bin"
    stand_ins.mkdir(exist_ok=True)
    loginctl = stand_ins / "loginctl"
    if loginctl_fails:
        loginctl.write_text("#!/bin/sh\necho 'Failed to connect to bus' >&2\nexit 1\n")
    else:
        (tmp_path / "sessions.json").write_text(json.dumps(sessions))
        loginctl.write_text(f"#!/bin/sh\ncat {tmp_path / 'sessions.json'}\n")
    cases = "".join(f"    {user}) echo '{' '.join(names)}' ;;\n" for user, names in groups.items())
    (stand_ins / "id").write_text(
        "#!/bin/sh\n"
        'user="$3"\n'
        'case "$user" in\n'
        f"{cases}"
        "    *) echo \"id: '$user': no such user\" >&2; exit 1 ;;\n"
        "esac\n")
    for program in stand_ins.iterdir():
        program.chmod(0o755)
    return subprocess.run([str(SCRIPT)], capture_output=True, text=True,
                          env={"PATH": f"{stand_ins}:/usr/bin:/bin"}).returncode


def session(user: str, kind: str = "user") -> dict:
    return {"session": "3", "uid": 1001, "user": user, "seat": "seat0", "class": kind,
            "tty": "tty7", "idle": False}


GROUPS = {"leo": ["leo", "kidux-children", "video"], "debian": ["debian", "sudo"],
          "_greetd": ["_greetd", "video"]}


def test_with_nobody_signed_in_the_upgrade_runs(tmp_path):
    assert run(tmp_path, [], GROUPS) == 0


def test_an_adult_s_session_or_the_sign_in_screen_s_lets_it_run(tmp_path):
    assert run(tmp_path, [session("debian"), session("_greetd", "greeter")], GROUPS) == 0


def test_a_child_s_session_skips_it(tmp_path):
    assert run(tmp_path, [session("debian"), session("leo")], GROUPS) == 1


@pytest.mark.parametrize("kind", ["greeter", "lock-screen", "background"])
def test_only_a_user_session_of_a_child_counts(tmp_path, kind):
    assert run(tmp_path, [session("leo", kind)], GROUPS) == 0


def test_a_user_id_does_not_know_is_no_child(tmp_path):
    assert run(tmp_path, [session("gone")], GROUPS) == 0


def test_when_logind_cannot_be_asked_the_upgrade_runs(tmp_path):
    assert run(tmp_path, [], GROUPS, loginctl_fails=True) == 0


def test_the_drop_in_names_the_script_as_installed():
    drop_in = (PACKAGE / "systemd" / "apt-daily-upgrade.service.d" / "kidux.conf").read_text()
    install = (PACKAGE / "debian" / "install").read_text()

    assert "ExecCondition=/usr/libexec/kidux-no-child-session" in drop_in.splitlines()
    assert "bin/kidux-no-child-session      usr/libexec" in install.splitlines()
    assert "systemd/apt-daily-upgrade.service.d usr/lib/systemd/system" in install.splitlines()
