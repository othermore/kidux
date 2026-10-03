#!/usr/bin/python3
"""Development builds: a package tried as `<version>~dev.<stamp>` (D77, D93).

    ci/devbuild.py copy <package> <stamp> <destination>
    ci/devbuild.py unpublished <package>

A development version is the tree's version with `~dev.<stamp>` appended,
the stamp the time to the second, in a copy of the source: Debian's `~`
sorts before, so it is older than the version itself and never the same as
an earlier try. A package gets its version at its first change in a piece
of work, and every try of it is such a build, by `tests/run vm push` and by
the battery (ci/test-release.sh); the version itself is built for
publishing only once the owner has tried the work and said yes (D93).

`copy` writes the copy at <destination>, with a changelog entry for the
development version above the tree's own and that version wherever the
package states its own, and prints the development version. `unpublished`
exits 0 when the archive's testing suite holds neither the tree's version
of the package nor a later one, so that a development build of it would be
the newest there; a build that cannot ask the archive takes it as
unpublished.
"""

import datetime
import os
import re
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
#: The archive the machines follow, asked what it holds.
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


def copy(source: str, now: datetime.datetime, destination: Path) -> str:
    """The package's source at `destination` as a development build of its
    version made at `now`; returns that version."""
    tree = REPO / "packages" / source
    changelog = (tree / "debian" / "changelog").read_text()
    version = tree_version(source)
    trailer = re.search(r"^ -- (.+?)  ", changelog, re.MULTILINE).group(1)
    date = subprocess.run(["date", "-R"], capture_output=True, text=True, check=True).stdout.strip()
    shutil.copytree(tree, destination, ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache"))
    dev = dev_version(version, now)
    (destination / "debian" / "changelog").write_text(
        changelog_entry(source, dev, trailer, date) + changelog)
    restate(destination, version, dev)
    return dev


def main(argv: list[str]) -> int:
    if len(argv) == 5 and argv[1] == "copy" and re.fullmatch(r"\d{14}", argv[3]):
        now = datetime.datetime.strptime(argv[3], "%Y%m%d%H%M%S")
        print(copy(argv[2], now, Path(argv[4])))
        return 0
    if len(argv) == 3 and argv[1] == "unpublished":
        return 1 if held_at_or_above(argv[2], tree_version(argv[2])) else 0
    print(__doc__, file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
