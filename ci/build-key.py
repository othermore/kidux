#!/usr/bin/python3
"""What a package's build is made from, as one SHA-256: its key in the build
cache (docs/dev/packaging.md, "The build cache").

    ci/build-key.py <package>

The key covers everything of this repository a build of the package reads:
every file of packages/<package>/ but the caches a local test run leaves
(an upstream package's upstream.toml names its tarball's SHA-256, so the
tarball is in it too), ci/build-package.sh and what it calls, the build
chroot's tarball, the distribution, and, for each package of ours its
Build-Depends name, that package's own key: a new kidux-common is a new key
for every package that builds against python3-kidux. It does not cover the
Debian packages the chroot installs while building, which the cache's age
limit covers instead.
"""

import hashlib
import os
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PACKAGES = REPO / "packages"
SKIPPED = {"__pycache__", ".pytest_cache", "upstream"}
#: What every build runs, besides the package's own files.
SCRIPTS = ("ci/build-package.sh", "ci/fetch-upstream.sh", "ci/upstream/upstream.py")


def binaries() -> dict[str, str]:
    """Each binary package this repository builds, and its source."""
    found = {}
    for control in PACKAGES.glob("*/debian/control"):
        for name in re.findall(r"^Package:\s*(\S+)", control.read_text(), re.MULTILINE):
            found[name] = control.parent.parent.name
    return found


def ours_built_against(package: str, made: dict[str, str]) -> list[str]:
    """The sources of ours whose binaries `package` names in Build-Depends."""
    control = (PACKAGES / package / "debian" / "control").read_text()
    field = re.search(r"^Build-Depends(?:-Indep|-Arch)?:(.*?)(?=^\S|\Z)", control,
                      re.MULTILINE | re.DOTALL)
    names = re.findall(r"([a-z0-9][a-z0-9.+-]+)", field.group(1)) if field else []
    return sorted({made[name] for name in names if name in made and made[name] != package})


def files_of(package: str) -> list[Path]:
    found = []
    for directory, subdirectories, names in os.walk(PACKAGES / package):
        subdirectories[:] = sorted(d for d in subdirectories if d not in SKIPPED)
        found += [Path(directory) / name for name in sorted(names)]
    return found


def key(package: str, made: dict[str, str] | None = None, seen: tuple = ()) -> str:
    made = binaries() if made is None else made
    if package in seen:
        raise SystemExit(f"a build-dependency loop through {package}")
    digest = hashlib.sha256()
    digest.update(os.environ.get("KIDUX_DIST", "trixie").encode())
    chroot = Path.home() / ".cache" / "sbuild" / f"{os.environ.get('KIDUX_DIST', 'trixie')}-amd64.tar"
    if chroot.exists():
        stat = chroot.stat()
        digest.update(f"chroot {stat.st_size} {stat.st_mtime_ns}".encode())
    for script in SCRIPTS:
        digest.update(script.encode())
        digest.update((REPO / script).read_bytes())
    for path in files_of(package):
        digest.update(str(path.relative_to(PACKAGES)).encode())
        digest.update(path.read_bytes())
    for other in ours_built_against(package, made):
        digest.update(f"built against {other} {key(other, made, seen + (package,))}".encode())
    return digest.hexdigest()


if __name__ == "__main__":
    if len(sys.argv) != 2 or not (PACKAGES / sys.argv[1] / "debian").is_dir():
        print(__doc__.strip().splitlines()[2], file=sys.stderr)
        sys.exit(2)
    print(key(sys.argv[1]))
