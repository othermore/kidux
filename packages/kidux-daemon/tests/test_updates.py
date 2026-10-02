"""Updates: the status file, the job, and the script that runs apt.

daemon.md section 13. The job runs in a unit of its own and says what it is
doing in a file; everything the daemon then says about it comes from that
file, so every line apt writes and every way a job can end has a test here,
and the script itself runs against a fake apt.
"""

import os
import subprocess
from pathlib import Path

import pytest

from kiduxd.errors import Busy
from kiduxd.updates import Updates, read


# --- the status file -----------------------------------------------------------


def test_a_check_that_finds_two_updates():
    reading = read("kidux:job:check\n"
                   "dlstatus:1:40.0:Retrieving file 1\n"
                   "kidux:checked:2:kidux-greeter,kidux-daemon\n")

    assert reading.job == "checking"
    assert reading.verdict == ("checked", "", ["kidux-greeter", "kidux-daemon"])


def test_a_check_that_finds_nothing():
    assert read("kidux:job:check\nkidux:checked:0:\n").verdict == ("checked", "", [])


def test_an_installation_moves_from_downloading_to_installing():
    reading = read("kidux:job:apply\ndlstatus:1:50.0:Retrieving\n")
    assert reading.fraction == pytest.approx(0.15)

    reading = read("pmstatus:kidux-greeter:50.0:Installing kidux-greeter\n", reading)
    assert reading.fraction == pytest.approx(0.65)
    assert reading.package == "kidux-greeter"


def test_the_bar_never_goes_backwards():
    reading = read("kidux:job:apply\npmstatus:a:80.0:x\npmstatus:b:10.0:y\n")

    assert reading.fraction == pytest.approx(0.86)


@pytest.mark.parametrize("line,verdict", [
    ("kidux:done:updated", ("updated", "", [])),
    ("kidux:done:up-to-date", ("up-to-date", "", [])),
    ("kidux:done:restart-needed", ("restart-needed", "", [])),
    ("kidux:failed:E: Unable to locate package", ("failed", "E: Unable to locate package", [])),
])
def test_every_way_an_installation_ends(line, verdict):
    assert read(f"kidux:job:apply\n{line}\n").verdict == verdict


def test_lines_it_does_not_know_are_ignored():
    reading = read("kidux:job:apply\nsomething else\npmstatus:broken\ndlstatus:x:notanumber:y\n")

    assert (reading.fraction, reading.verdict) == (0.0, None)


# --- the job -------------------------------------------------------------------


class FakeRunner:
    def __init__(self, status: Path) -> None:
        self.status = status
        self.started: list[str] = []
        self.active = False

    def start_update(self, kind: str, package: str = "") -> None:
        self.started.append(kind)
        self.active = True
        self.status.write_text(f"kidux:job:{kind}\n")

    def update_active(self) -> bool:
        return self.active

    def write(self, text: str) -> None:
        with open(self.status, "a") as handle:
            handle.write(text)


@pytest.fixture
def job(tmp_path):
    status = tmp_path / "update.status"
    runner = FakeRunner(status)
    signals, audit = [], []
    updates = Updates(runner, status=status,
                      emit=lambda *signal: signals.append(signal),
                      audit=lambda action, outcome, **fields: audit.append((action, outcome)))
    return updates, runner, signals, audit


def test_a_check_is_answered_by_a_signal_and_remembered(job):
    updates, runner, signals, audit = job
    updates.start("check")
    assert updates.state()[0] == "checking"

    runner.write("kidux:checked:1:kidux-greeter\n")
    runner.active = False

    assert updates.poll() is False
    assert ("System1", "UpdatesChecked", "(uass)", (1, ["kidux-greeter"], "")) in signals
    assert updates.state() == ("idle", 0.0, "", "checked", "", ["kidux-greeter"])
    assert ("update check", "ok") in audit
    assert not runner.status.exists()


def test_an_installation_says_how_far_it_has_got(job):
    updates, runner, signals, _ = job
    updates.start("apply")

    runner.write("pmstatus:kidux-greeter:50.0:Installing\n")
    assert updates.poll() is True
    assert ("System1", "UpdateProgress", "(ds)", (pytest.approx(0.65), "kidux-greeter")) in signals

    runner.write("kidux:done:updated\n")
    runner.active = False
    assert updates.poll() is False
    assert ("System1", "UpdateFinished", "(ss)", ("updated", "")) in signals


def test_half_a_line_waits_for_the_rest(job):
    updates, runner, signals, _ = job
    updates.start("apply")

    runner.write("kidux:done:upd")
    assert updates.poll() is True
    runner.write("ated\n")
    runner.active = False
    updates.poll()

    assert updates.state()[3] == "updated"


def test_a_job_that_stops_without_a_verdict_failed(job):
    updates, runner, signals, audit = job
    updates.start("apply")
    runner.active = False

    updates.poll()

    assert updates.state()[3] == "failed"
    assert ("update finished", "failed") in audit


def test_one_job_at_a_time(job):
    updates, runner, _, _ = job
    updates.start("check")

    with pytest.raises(Busy):
        updates.start("apply")


def test_a_job_started_elsewhere_is_busy_too(job):
    updates, runner, _, _ = job
    runner.active = True

    with pytest.raises(Busy):
        updates.start("check")


def test_after_a_restart_a_running_job_is_watched_again(job, tmp_path):
    _, runner, signals, _ = job
    runner.start_update("apply")
    runner.write("pmstatus:kidux-daemon:20.0:Installing\n")
    # The daemon was replaced by that very update and starts again.
    again = Updates(runner, status=runner.status, emit=lambda *s: signals.append(s))

    assert again.resume() is True
    assert again.state()[0] == "applying"
    runner.write("kidux:done:updated\n")
    runner.active = False
    again.poll()
    assert ("System1", "UpdateFinished", "(ss)", ("updated", "")) in signals


def test_after_a_restart_a_finished_job_is_reported_once(job):
    _, runner, signals, _ = job
    runner.start_update("apply")
    runner.write("kidux:done:restart-needed\n")
    runner.active = False
    again = Updates(runner, status=runner.status, emit=lambda *s: signals.append(s))

    assert again.resume() is False
    assert signals == [("System1", "UpdateFinished", "(ss)", ("restart-needed", ""))]
    assert again.resume() is False
    assert len(signals) == 1


# --- the script ----------------------------------------------------------------


def script() -> Path:
    root = Path(os.environ.get("KIDUX_DAEMON_SOURCE") or Path(__file__).resolve().parents[1])
    return root / "bin" / "kidux-update"


FAKE_APT = """#!/bin/sh
# A stand-in for apt-get: the status descriptor gets what apt would write.
case "$*" in
    *" update"*|update*)
        [ -n "${FAIL_UPDATE:-}" ] && { echo "E: The repository is not signed."; exit 100; }
        echo "dlstatus:1:100:Done" >&3 2>/dev/null
        exit 0 ;;
    *-s*dist-upgrade*)
        for p in $PENDING; do echo "Inst $p [1.0] (1.1 Kidux:testing [all])"; done
        exit 0 ;;
    *dist-upgrade*)
        for p in $PENDING; do echo "pmstatus:$p:50:Installing $p" >&3 2>/dev/null; done
        exit 0 ;;
esac
exit 0
"""


@pytest.fixture
def fake_apt(tmp_path):
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    for name, text in (("apt-get", FAKE_APT), ("dpkg", "#!/bin/sh\nexit 0\n")):
        (bin_dir / name).write_text(text)
        (bin_dir / name).chmod(0o755)

    def run(kind, pending="", **extra):
        status = tmp_path / "status"
        status.unlink(missing_ok=True)
        env = {"PATH": f"{bin_dir}:/usr/bin:/bin", "KIDUX_UPDATE_STATUS": str(status),
               "KIDUX_REBOOT_REQUIRED": str(tmp_path / "reboot-required"),
               "PENDING": pending, **extra}
        result = subprocess.run(["sh", str(script()), kind], env=env, capture_output=True,
                                text=True, timeout=30)
        assert result.returncode == 0, result.stderr
        return read(status.read_text())
    return run


def test_the_script_checks(fake_apt):
    reading = fake_apt("check", pending="kidux-greeter kidux-daemon")

    assert reading.job == "checking"
    assert reading.verdict == ("checked", "", ["kidux-greeter", "kidux-daemon"])


def test_the_script_finds_nothing_to_do(fake_apt):
    assert fake_apt("check").verdict == ("checked", "", [])


def test_the_script_installs(fake_apt):
    reading = fake_apt("apply", pending="kidux-greeter")

    assert reading.package == "kidux-greeter"
    assert reading.verdict == ("updated", "", [])


def test_the_script_says_when_there_was_nothing_to_install(fake_apt):
    assert fake_apt("apply").verdict == ("up-to-date", "", [])


def test_the_script_says_why_it_failed_and_still_exits_cleanly(fake_apt):
    reading = fake_apt("check", FAIL_UPDATE="1")

    assert reading.verdict == ("failed", "E: The repository is not signed.", [])


def test_the_script_says_when_the_computer_must_restart(fake_apt, tmp_path):
    (tmp_path / "reboot-required").touch()

    assert fake_apt("apply", pending="linux-image-amd64").verdict == ("restart-needed", "", [])
