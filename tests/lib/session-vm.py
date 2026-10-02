#!/usr/bin/python3
"""Every test in tests/session/, on a machine that has rebooted into Kidux.

    tests/run session

docs/dev/session.md, section 8. Unlike the acceptance run, this one is driven
from outside the machine, because what it tests only exists after a reboot
and can only be tried with keys pressed on the machine's own keyboard:
Ctrl+Alt+F2, Alt+SysRq, the power button, Esc at the boot menu.

So the machine gets a disk of its own for the length of the run (an overlay
on the base image, deleted afterwards), an SSH key for the administrator, and
a QEMU monitor through which the tests press keys and take pictures of the
screen. Every picture is left in build/vm/session-NN-<screen>.png.

    KIDUX_VM_LANGUAGE=en      set the machine up in English instead of
                              Spanish: its own disk, ports and pictures,
                              build/vm/session-en-NN-<screen>.png, so that
                              it can run beside a Spanish one
    KIDUX_VM_EVERY_TEST=1     in a language other than Spanish, run every
                              test, not only the pictures' (below)

In Spanish every test runs. In any other language only what that language
can show differently: the tests that set the machine up and the one that
says every screen fits, which say so with `EVERY_LANGUAGE = True`, and every
test that takes a picture the user guide shows (tests/lib/doc-screenshots.txt),
found in its source. What a test checks besides is the same in every
language, and the Spanish run has checked it.

The tests are the files in tests/session/, run in the order of their names,
each a module with `run(machine)`. They share one machine, so each starts
where the one before left it. A test that returns False says nothing after it
can mean anything, and the run stops there. A new test is a new file; nothing
here needs to know its name.

    KIDUX_VM_STOP_AFTER=04    stop after the test whose name starts 04, and
                              leave the machine running to look at
    KIDUX_VM_SNAPSHOT=1       with KIDUX_VM_STOP_AFTER (tests/run vm up does
                              both): keep the machine's disk as it is after
                              that test, and the next time start from it
                              instead of running the tests again (below)
    KIDUX_VM_LEAVE_RUNNING=1  the same, after 04-family
    KIDUX_VM_KEEP=1           keep the disk afterwards

    tests/run session --stop  power off a machine left running, and delete
                              its disk

A run refuses to start while a machine left running still answers: it would
delete the disk under it and start a second machine on the same ports.

A snapshot is the machine's disk, its firmware's variables, its SSH key and
its seed, kept in build/vm/snapshots/ after the tests up to NN, the machine
powered off. It stands for those tests' files, this file and sessionlib.py,
the seed's sources, the base image and the screen size: when any of them
changes, the tests run again and a new one is kept. A machine started from
one boots a fresh overlay on it, takes the Kidux packages the archive has now
(apt-get dist-upgrade), and restarts when that changed anything, so it holds
what a run of the tests would have installed. It is for the quick loop: the
battery never uses one.

Each check prints PASS or FAIL; the exit status is the number of failures.
"""

import fcntl
import hashlib
import importlib.util
import os
import re
import shutil
import signal
import socket
import subprocess
import sys
import time

import sessionlib
from sessionlib import (
    CONSOLE, DISK, KEY, MONITOR, REPO, RUN, SEED, SEED_PORT, SSH_PORT, VM,
    Machine, report, root, shlex_quote, ssh, up, wait, write_seed,
)

TESTS = REPO / "tests" / "session"
#: The seed server of a machine left running, for --stop to end with it.
SERVER_PID = VM / f"{RUN}-seed-server.pid"


SNAPSHOTS = VM / "snapshots"
OVMF_VARS = VM / f"OVMF_VARS_{RUN}.fd"


def snapshot_name(stop_after: str, base: str) -> str:
    """The snapshot a machine stopped after test `stop_after` is kept as:
    named for everything that made it (above)."""
    digest = hashlib.sha256()
    image = os.stat(base)
    digest.update(f"{base} {image.st_size} {image.st_mtime_ns}".encode())
    digest.update(os.environ.get("KIDUX_VM_SCREEN", "").encode())
    sources = [path for path in sorted(TESTS.glob("[0-9]*.py")) if path.name[:2] <= stop_after]
    sources += [REPO / "tests" / "lib" / "session-vm.py", REPO / "tests" / "lib" / "sessionlib.py"]
    sources += sorted(path for path in (REPO / "tests" / "lib" / "seed").rglob("*") if path.is_file())
    for path in sources:
        digest.update(str(path.relative_to(REPO)).encode())
        digest.update(path.read_bytes())
    return f"{RUN}-{stop_after}-{digest.hexdigest()[:16]}"


def keep_snapshot(machine: Machine, snapshot) -> None:
    """Power the machine off and keep its disk, firmware variables, key and
    seed as `snapshot`, the older snapshots of the same run and test gone."""
    root("systemctl poweroff", timeout=20)
    try:
        machine.process.wait(180)
    except subprocess.TimeoutExpired:
        machine.stop()
    prefix = snapshot.name.rsplit("-", 1)[0] + "-"
    for old in SNAPSHOTS.glob(prefix + "*"):
        shutil.rmtree(old, ignore_errors=True)
    partial = snapshot.with_name(snapshot.name + ".part")
    shutil.rmtree(partial, ignore_errors=True)
    partial.mkdir(parents=True)
    shutil.move(str(DISK), partial / "disk.qcow2")
    for source, name in ((OVMF_VARS, "ovmf_vars.fd"), (KEY, "key"),
                         (KEY.with_suffix(".pub"), "key.pub")):
        shutil.copy2(source, partial / name)
    shutil.copytree(SEED, partial / "seed")
    partial.rename(snapshot)
    print(f"==> Kept as the snapshot {snapshot.name}", flush=True)


def from_snapshot(snapshot) -> None:
    """The machine's disk, firmware variables, key and seed from `snapshot`,
    on a fresh overlay that leaves the snapshot as it is."""
    for stale in (DISK, KEY, KEY.with_suffix(".pub"), OVMF_VARS, CONSOLE):
        stale.unlink(missing_ok=True)
    subprocess.run(["qemu-img", "create", "-q", "-f", "qcow2", "-b",
                    str(snapshot / "disk.qcow2"), "-F", "qcow2", str(DISK)], check=True)
    shutil.copy2(snapshot / "ovmf_vars.fd", OVMF_VARS)
    shutil.copy2(snapshot / "key", KEY)
    shutil.copy2(snapshot / "key.pub", KEY.with_suffix(".pub"))
    KEY.chmod(0o600)
    shutil.rmtree(SEED, ignore_errors=True)
    shutil.copytree(snapshot / "seed", SEED)


def brought_up_to_date(machine: Machine) -> bool:
    """Take the packages the archive has now, and restart if any changed."""
    upgraded = root("DEBIAN_FRONTEND=noninteractive apt-get update -qq && "
                    "DEBIAN_FRONTEND=noninteractive apt-get dist-upgrade -y -qq "
                    "-o Dpkg::Options::=--force-confold -o DPkg::Lock::Timeout=600 "
                    "| grep -c '^Setting up' || true", timeout=1200).stdout.strip()
    print(f"    {upgraded or 0} packages taken from the archive", flush=True)
    if upgraded in ("", "0"):
        return True
    return sessionlib.reboot(machine)


def guide_pictures() -> set[str]:
    """The screens the user guide shows, by the name their picture is taken as."""
    names = set()
    for line in (REPO / "tests" / "lib" / "doc-screenshots.txt").read_text().splitlines():
        if line.strip() and not line.startswith("#"):
            names.add(line.split()[0])
    return names


def in_this_language(path, pictures: set[str]) -> bool:
    """Whether the test at `path` runs in this run's language (above)."""
    if sessionlib.LANGUAGE == "es" or os.environ.get("KIDUX_VM_EVERY_TEST") == "1":
        return True
    source = path.read_text()
    if re.search(r"^EVERY_LANGUAGE\s*=\s*True", source, re.MULTILINE):
        return True
    taken = set(re.findall(r"screenshot\(\s*[\"']([a-z0-9-]+)[\"']", source))
    if "catch_the_splash(" in source:
        taken.add("boot-splash")
    return bool(taken & pictures)


def load(path):
    spec = importlib.util.spec_from_file_location(f"session_{path.stem.replace('-', '_')}", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def left_running() -> bool:
    """Whether a machine an earlier run left running answers on its monitor."""
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as connection:
        connection.settimeout(2)
        try:
            connection.connect(str(MONITOR))
        except OSError:
            return False
    return True


def stop_left_running() -> int:
    """Power off a machine left running, its seed server with it, and delete
    its disk."""
    if left_running():
        Machine().monitor("quit")
        if not wait(lambda: not left_running(), 20, 0.5):
            print("the machine left running did not stop", file=sys.stderr)
            return 1
        print("stopped the machine left running")
    else:
        print("no machine was left running")
    try:
        os.kill(int(SERVER_PID.read_text()), signal.SIGTERM)
    except (OSError, ValueError):
        pass
    for leftover in (DISK, MONITOR, SERVER_PID):
        leftover.unlink(missing_ok=True)
    return 0


def leave_running(machine: Machine, server) -> None:
    """For looking into a failure by hand, or the quick loop: the machine
    stays up, reachable as below, until it is powered off."""
    print(f"==> Left running: ssh -i {KEY} -p {SSH_PORT} debian@127.0.0.1; "
          f"monitor at {MONITOR}", flush=True)
    machine.process = None
    SERVER_PID.write_text(str(server.pid))


def main(argv: list[str]) -> int:
    if argv[1:] == ["--stop"]:
        return stop_left_running()
    if argv[1:]:
        print(__doc__, file=sys.stderr)
        return 2
    if left_running():
        print(f"a machine left running still answers on {MONITOR}: look at it with "
              f"ssh -i {KEY} -p {SSH_PORT} debian@127.0.0.1, or stop it with "
              "tests/run session --stop", file=sys.stderr)
        return 1

    # One run at a time in each language: two would fight over the disk, the
    # ports and the monitor, and each would report the other's machine.
    VM.mkdir(parents=True, exist_ok=True)
    lock = open(VM / f"{RUN}.lock", "w")
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        print("another session run is going; not starting a second", file=sys.stderr)
        return 1

    # Debian with what Kidux needs from Debian already installed, or the
    # stock image when KIDUX_VM_COLD=1 (tests/lib/warm-image.sh).
    image = subprocess.run([str(REPO / "tests" / "lib" / "warm-image.sh")],
                           stdout=subprocess.PIPE, text=True)
    if image.returncode != 0:
        print("no image to start the machine from", file=sys.stderr)
        return 1
    base = image.stdout.strip()

    stop_after = os.environ.get("KIDUX_VM_STOP_AFTER") or (
        "04" if os.environ.get("KIDUX_VM_LEAVE_RUNNING") == "1" else "")
    tests = sorted(TESTS.glob("[0-9]*.py"))

    snapshot = None
    if stop_after and os.environ.get("KIDUX_VM_SNAPSHOT") == "1":
        snapshot = SNAPSHOTS / snapshot_name(stop_after, base)
    for old in VM.glob(f"{RUN}-[0-9]*.png"):
        old.unlink()
    restored = snapshot is not None and (snapshot / "disk.qcow2").exists()
    if restored:
        print(f"==> From the snapshot {snapshot.name}", flush=True)
        from_snapshot(snapshot)
    else:
        for stale in (DISK, KEY, KEY.with_suffix(".pub"), OVMF_VARS, CONSOLE):
            stale.unlink(missing_ok=True)
        subprocess.run(["qemu-img", "create", "-q", "-f", "qcow2", "-b", base, "-F", "qcow2",
                        str(DISK), "12G"], check=True)
        subprocess.run(["ssh-keygen", "-q", "-t", "ed25519", "-N", "", "-f", str(KEY)],
                       check=True)
        write_seed()

    server = subprocess.Popen(
        [sys.executable, "-m", "http.server", str(SEED_PORT), "--bind", "127.0.0.1",
         "--directory", str(SEED)],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    machine = Machine()
    try:
        started = time.monotonic()
        machine.boot()
        if not report("the machine comes up and takes the administrator's key", wait(up, 300, 3)):
            return sessionlib.failures
        wait(lambda: ssh("cloud-init status --wait", timeout=600).returncode in (0, 2), 600, 5)
        print(f"    the machine took {time.monotonic() - started:.0f} s to come up", flush=True)
        if restored:
            report("it takes the archive's packages", brought_up_to_date(machine))
            leave_running(machine, server)
            server = None
            return sessionlib.failures

        pictures = guide_pictures()
        for path in tests:
            if not in_this_language(path, pictures):
                print(f"--- {path.name}: Spanish only", flush=True)
                continue
            print(f"--- {path.name}", flush=True)
            started = time.monotonic()
            outcome = load(path).run(machine)
            print(f"    {path.name} took {time.monotonic() - started:.0f} s", flush=True)
            if outcome is False:
                print(f"==> {path.name} failed in a way nothing after it can survive", flush=True)
                break
            if stop_after and path.name.startswith(stop_after):
                if snapshot is not None and sessionlib.failures == 0:
                    keep_snapshot(machine, snapshot)
                    from_snapshot(snapshot)
                    machine.boot()
                    if not report("the machine comes up again from it", wait(up, 300, 3)):
                        return sessionlib.failures
                leave_running(machine, server)
                server = None
                return sessionlib.failures
    finally:
        machine.stop()
        if server is not None:
            server.send_signal(signal.SIGTERM)
        if os.environ.get("KIDUX_VM_KEEP") != "1" and machine.process is not None:
            DISK.unlink(missing_ok=True)

    print()
    failures = sessionlib.failures
    print("==> Session and hardening: " + ("PASS" if failures == 0 else f"FAIL ({failures})"))
    return failures


if __name__ == "__main__":
    if os.environ.get("KIDUX_VM_REEXEC") != "1" and not os.access("/dev/kvm", os.W_OK):
        # Being added to the kvm group does not reach a shell that was
        # already open; sg picks it up for this one run.
        os.environ["KIDUX_VM_REEXEC"] = "1"
        os.execvp("sg", ["sg", "kvm", "-c", " ".join([sys.executable, *map(shlex_quote, sys.argv)])])
    sys.exit(main(sys.argv))
