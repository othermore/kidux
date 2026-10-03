#!/usr/bin/python3
"""The quick loop's machine: a session machine left up, and changes taken to it.

    tests/run vm up [NN]          boot the session machine, run the session
                                  tests up to the one whose name starts NN
                                  (04 when none is given: Kidux set up, its
                                  three children made, nobody signed in),
                                  and leave it up, its screen over VNC; kept
                                  as a snapshot, so that the next time it
                                  starts from there in a minute, with the
                                  archive's packages (tests/lib/session-vm.py)
    tests/run vm push <package>…  build each package from the tree as a
                                  development version, publish it to the
                                  archive's testing suite, and install it on
                                  the machine left up, restarting what it runs
    tests/run vm test <NN>        run the session test whose name starts NN
                                  against the machine left up
    tests/run vm shot <name>      a picture of its screen, in build/vm/
    tests/run vm ssh [command]    a shell on it, or one command, as its
                                  administrator (sudo for root)
    tests/run vm down             power it off and delete its disk

tests/README.md, "The quick loop". A development version is the tree's
version with `~dev.<the time, to the second>` appended in a copy of the
source: Debian's `~` sorts before, so it is older than the tree's own
build of that version, which replaces it when the battery publishes it,
and never the same as an earlier try. So the tree's version has to be one
the archive has not published: a package is bumped in its changelog when
it is first changed, and a push of one the archive already holds at that
version, or above it, is refused (D77). The MacBook, which follows the
same suite, takes a pushed package with `sudo apt update && sudo apt
upgrade` (rollout.md, section 5).
"""

import datetime
import os
import re
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import sessionlib  # noqa: E402
from sessionlib import KEY, MONITOR, REPO, SSH_PORT, VM, Machine, root  # noqa: E402

DEV = REPO / "build" / "dev"
#: The VNC display the machine offers its screen on: 1 is port 5901, beside
#: ci/vm/try.sh's 5900.
VNC_DISPLAY = "1"
#: Sources a development build of makes no sense: the archive's key and
#: sources, which every machine trusts and follows.
NOT_PUSHED = {"kidux-archive-keyring"}


#: The archive the machines follow, asked what it holds before a push.
ARCHIVE = os.environ.get("KIDUX_ARCHIVE_URL", "http://kidux.local/apt")


def dev_version(version: str, now: datetime.datetime) -> str:
    """The development version of `version` built at `now`: before it."""
    return f"{version}~dev.{now:%Y%m%d%H%M%S}"


def tree_version(source: str) -> str:
    changelog = (REPO / "packages" / source / "debian" / "changelog").read_text()
    return re.match(r"\S+ \(([^)]+)\)", changelog).group(1)


def binaries_of(source: str) -> set[str]:
    control = (REPO / "packages" / source / "debian" / "control").read_text()
    return set(re.findall(r"^Package: (\S+)", control, re.MULTILINE))


def versions_in(packages: str, binaries: set[str]) -> list[str]:
    """Every version a suite's Packages index holds of these binaries."""
    found = []
    for stanza in packages.split("\n\n"):
        fields = dict(line.split(": ", 1) for line in stanza.splitlines() if ": " in line)
        if fields.get("Package") in binaries and fields.get("Version"):
            found.append(fields["Version"])
    return found


def published_versions(source: str) -> list[str]:
    """What the archive's testing suite holds of the source's binaries;
    nothing where the archive cannot be asked, as off the development host."""
    try:
        with urllib.request.urlopen(f"{ARCHIVE}/dists/testing/main/binary-amd64/Packages",
                                    timeout=5) as answer:
            packages = answer.read().decode()
    except (OSError, ValueError):
        return []
    return versions_in(packages, binaries_of(source))


def newer(first: str, second: str) -> bool:
    return subprocess.run(["dpkg", "--compare-versions", first, "gt", second]).returncode == 0


def held_at_or_above(source: str, version: str) -> list[str]:
    """The archive's versions of the source that a development build of
    `version` would sort below: the version itself, or a later one. A
    development build of the same version sorts below it and is not one."""
    return [held for held in published_versions(source) if not newer(version, held)]


def changelog_entry(source: str, version: str, trailer: str, date: str) -> str:
    """A changelog entry for a development build, above the tree's own:
    `trailer` is the maintainer as the newest entry names them, `date` the
    time from `date -R`."""
    return (f"{source} ({version}) trixie; urgency=medium\n\n"
            "  * Development build of the working tree, for trying a change; never\n"
            "    released.\n\n"
            f" -- {trailer}  {date}\n\n")


def restate(copy: Path, version: str, dev: str) -> None:
    """The development version wherever the package states its version
    besides its changelog, as tests/project/versions.sh holds it to: a
    module's manifest, pyproject.toml, a VERSION constant. pyproject.toml's
    is written as Python's versions are, `0.1.2.dev<time>`, which also sorts
    before `0.1.2`: Python's build refuses a `~`."""
    python = dev.replace("~dev.", ".dev")
    for path in [copy / "module.toml", copy / "pyproject.toml", *copy.glob("*/__init__.py")]:
        if path.is_file():
            text = path.read_text()
            stated = text.replace(f'version = "{version}"\n',
                                  f'version = "{python if path.name == "pyproject.toml" else dev}"\n')
            stated = stated.replace(f'VERSION = "{version}"\n', f'VERSION = "{dev}"\n')
            if stated != text:
                path.write_text(stated)


def after_install(sources: list[str], child_signed_in: bool) -> tuple[list[str], list[str]]:
    """What the machine runs again once `sources` are installed on it, as
    commands for root, and what waits, as notes to print."""
    commands: list[str] = []
    notes: list[str] = []
    if "kidux-daemon" in sources or "kidux-common" in sources:
        commands.append("systemctl restart kidux-daemon")
    if "kidux-greeter" in sources or "kidux-common" in sources:
        if child_signed_in:
            notes.append("the sign-in and lock screens take it when the child signed in "
                         "logs out")
        else:
            commands.append("systemctl restart greetd")
    if "kidux-launcher" in sources or "kidux-common" in sources:
        notes.append("the launcher takes it at the next sign-in")
    if "kidux-webapps" in sources:
        commands.append("systemctl try-restart kidux-webapps")
    if any(s.startswith("kidux-module-") for s in sources):
        notes.append("a module takes it the next time it is opened")
    if "kidux-session" in sources:
        notes.append("kidux-session takes a reboot: tests/run vm ssh sudo systemctl reboot")
    return commands, notes


def binaries(changes: Path) -> list[str]:
    """The binary packages a .changes file names."""
    for line in changes.read_text().splitlines():
        if line.startswith("Binary:"):
            return line.split(":", 1)[1].split()
    return []


def machine_up() -> bool:
    return MONITOR.exists() and sessionlib.up()


def up(argv: list[str]) -> int:
    if len(argv) > 1 or (argv and not re.fullmatch(r"\d\d", argv[0])):
        print("usage: tests/run vm up [NN]", file=sys.stderr)
        return 2
    env = {**os.environ, "KIDUX_VM_STOP_AFTER": argv[0] if argv else "04",
           "KIDUX_VM_VNC": VNC_DISPLAY, "KIDUX_VM_SNAPSHOT": "1"}
    outcome = subprocess.run([str(REPO / "tests" / "lib" / "session-vm.py")], env=env)
    if machine_up():
        print(f"\n==> Up. Its screen: VNC on 127.0.0.1:590{VNC_DISPLAY}, password kidux "
              f"(from another computer: ssh -N -L 590{VNC_DISPLAY}:127.0.0.1:590{VNC_DISPLAY} "
              "<you>@kidux.local). A shell: tests/run vm ssh.")
    return outcome.returncode


def push(sources: list[str]) -> int:
    if not sources:
        print("usage: tests/run vm push <package>…", file=sys.stderr)
        return 2
    for source in sources:
        if source in NOT_PUSHED or not (REPO / "packages" / source / "debian").is_dir():
            print(f"not a package to push: {source}", file=sys.stderr)
            return 2
    # kidux-common first: the others build against the python3-kidux it makes.
    sources = sorted(set(sources), key=lambda s: (s != "kidux-common", s))
    now = datetime.datetime.now()
    out = DEV / f"{now:%Y%m%d%H%M%S}"
    date = subprocess.run(["date", "-R"], capture_output=True, text=True, check=True).stdout.strip()
    # A development build sorts below the version it tries, so the version
    # must be one the archive has not published, or apt would keep the
    # archive's: the package's changelog is bumped first (D77).
    for source in sources:
        version = tree_version(source)
        held = held_at_or_above(source, version)
        if held:
            print(f"{source} {version}: the archive's testing suite already holds "
                  f"{', '.join(held)}, which apt would keep over a development build of "
                  f"{version}; bump {source}'s changelog first", file=sys.stderr)
            return 1
    built: dict[str, tuple[str, list[str]]] = {}
    for source in sources:
        tree = REPO / "packages" / source
        changelog = (tree / "debian" / "changelog").read_text()
        version = tree_version(source)
        trailer = re.search(r"^ -- (.+?)  ", changelog, re.MULTILINE).group(1)
        copy = out / "src" / source
        shutil.copytree(tree, copy, ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache"))
        dev = dev_version(version, now)
        (copy / "debian" / "changelog").write_text(
            changelog_entry(source, dev, trailer, date) + changelog)
        restate(copy, version, dev)
        print(f"==> Building {source} {dev}", flush=True)
        log = out / f"{source}.log"
        with log.open("w") as handle:
            result = subprocess.run(
                [str(REPO / "ci" / "build-package.sh"), source],
                env={**os.environ, "KIDUX_BUILD_DIR": str(out), "KIDUX_SOURCE_DIR": str(copy)},
                stdout=handle, stderr=subprocess.STDOUT)
        if result.returncode != 0:
            print(f"{source} did not build; the end of {log}:", file=sys.stderr)
            print("".join(log.read_text().splitlines(keepends=True)[-30:]), file=sys.stderr)
            return 1
        built[source] = (dev, binaries(out / f"{source}_{dev}_amd64.changes"))

    print("==> Publishing to testing", flush=True)
    result = subprocess.run([str(REPO / "ci" / "publish-local.sh"), "testing"],
                            env={**os.environ, "KIDUX_BUILD_DIR": str(out),
                                 "KIDUX_DEV_BUILD": "1"},
                            stdout=subprocess.DEVNULL)
    if result.returncode != 0:
        print("publishing failed: ci/publish-local.sh testing", file=sys.stderr)
        return 1
    for source, (dev, names) in built.items():
        print(f"    {source} {dev}: {' '.join(names)}")

    if not machine_up():
        print("==> No machine is up: published only. A machine following testing takes it "
              "with sudo apt update && sudo apt upgrade.")
        return 0
    installed = [name for _, names in built.values() for name in names
                 if root(f"dpkg-query -W -f '${{db:Status-Status}}' {name}").stdout == "installed"]
    if installed:
        print(f"==> Installing on the machine: {' '.join(installed)}", flush=True)
        result = root("DEBIAN_FRONTEND=noninteractive apt-get update -qq && "
                      "DEBIAN_FRONTEND=noninteractive apt-get install -y -qq "
                      "-o DPkg::Lock::Timeout=600 -o Dpkg::Options::=--force-confold "
                      + " ".join(installed), timeout=900)
        if result.returncode != 0:
            print(result.stdout[-2000:] + result.stderr[-2000:], file=sys.stderr)
            return 1
    else:
        print("==> None of it is installed on the machine: published only, for the panel "
              "or apt to install.")
    child = root("pgrep -x labwc").returncode == 0
    commands, notes = after_install(list(built), child)
    for command in commands:
        print(f"    {command}")
        root(command, timeout=120)
    for note in notes:
        print(f"    {note}")
    return 0


def test(argv: list[str]) -> int:
    found = sorted((REPO / "tests" / "session").glob(f"{argv[0]}*.py")) if len(argv) == 1 else []
    if len(found) != 1:
        print("usage: tests/run vm test <NN>, NN naming one file in tests/session/",
              file=sys.stderr)
        return 2
    return subprocess.run([str(REPO / "tests" / "lib" / "session-one.py"), str(found[0])]).returncode


def shot(argv: list[str]) -> int:
    if len(argv) != 1 or not re.fullmatch(r"[a-z0-9-]+", argv[0]):
        print("usage: tests/run vm shot <name>", file=sys.stderr)
        return 2
    machine = Machine()
    machine.pictures = 90
    print(machine.screenshot(argv[0]))
    return 0


def shell(argv: list[str]) -> int:
    os.execvp("ssh", ["ssh", "-i", str(KEY), "-p", str(SSH_PORT),
                      "-o", "StrictHostKeyChecking=no", "-o", "UserKnownHostsFile=/dev/null",
                      "-o", "LogLevel=ERROR", "debian@127.0.0.1", *argv])


def main(argv: list[str]) -> int:
    commands = {"up": up, "push": push, "test": test, "shot": shot, "ssh": shell}
    if argv[1:2] == ["down"] and len(argv) == 2:
        return subprocess.run([str(REPO / "tests" / "lib" / "session-vm.py"), "--stop"]).returncode
    if len(argv) < 2 or argv[1] not in commands:
        print(__doc__, file=sys.stderr)
        return 2
    if argv[1] in ("test", "shot", "ssh") and not machine_up():
        print(f"no machine is up ({MONITOR}): tests/run vm up", file=sys.stderr)
        return 1
    VM.mkdir(parents=True, exist_ok=True)
    return commands[argv[1]](argv[2:])


if __name__ == "__main__":
    sys.exit(main(sys.argv))
