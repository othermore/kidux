#!/usr/bin/python3
"""A package's upstream.toml, read for the shell scripts (D68).

    ci/upstream/upstream.py <package> <field>     print one field
    ci/upstream/upstream.py <package> tarball     the tarball's file name
    ci/upstream/upstream.py <package> source      its source tarball's
    ci/upstream/upstream.py <package> set-sha256 <sum>
    ci/upstream/upstream.py <package> set-source-sha256 <sum>

A package built from a program that is not in trixie says in
packages/<package>/upstream.toml where the program comes from and what it
was built into: the repository, the commit, the version, the Node.js
release its build needs, the build script, and the SHA-256 of the tarball
and of the source tarball published beside it, which holds everything the
build fetched (D71; docs/dev/packaging.md, "Programs built at development
time").
"""

import re
import sys
import tomllib
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
FIELDS = ("name", "repository", "commit", "version", "node", "build", "sha256",
          "source_sha256")


def path(package: str) -> Path:
    return REPO / "packages" / package / "upstream.toml"


def read(package: str) -> dict:
    with path(package).open("rb") as file:
        return tomllib.load(file)["upstream"]


def tarball(package: str) -> str:
    return f"{package}_{read(package)['version']}.orig.tar.xz"


def source(package: str) -> str:
    return f"{package}_{read(package)['version']}.source.tar.xz"


def set_sum(package: str, field: str, sum_: str) -> None:
    """Write a SHA-256 into its line, adding the line after sha256's when
    upstream.toml has none yet."""
    if not re.fullmatch(r"[0-9a-f]{64}", sum_):
        sys.exit(f"not a SHA-256: {sum_!r}")
    text = path(package).read_text()
    line = f'{field} = "{sum_}"'
    new, count = re.subn(rf'^{field} = ".*"$', line, text, flags=re.M)
    if count == 0 and field != "sha256":
        new, count = re.subn(r'^(sha256 = ".*")$', rf"\1\n{line}", text, flags=re.M)
    if count != 1:
        sys.exit(f"{path(package)} has no line for {field}")
    path(package).write_text(new)


def main(args: list[str]) -> int:
    if len(args) == 3 and args[1] in ("set-sha256", "set-source-sha256"):
        set_sum(args[0], args[1][4:].replace("-", "_"), args[2])
        return 0
    if len(args) != 2:
        print(__doc__.strip().splitlines()[2], file=sys.stderr)
        return 2
    package, field = args
    if field == "tarball":
        print(tarball(package))
    elif field == "source":
        print(source(package))
    elif field in FIELDS:
        print(read(package).get(field, ""))
    else:
        print(f"no field {field!r}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
