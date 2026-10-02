#!/usr/bin/python3
"""A built web site served under a path of its own (D68).

    ci/upstream/check-site.py <directory> <prefix> [<reference>...]

kidux-webapps serves a module's site at /<id>/, not at the root. A site
built for the root refers to its files as /static/…, which the server has
not, and shows a blank page. This walks the site's .html, .css and .js
files and fails on every reference that starts at the root and not with
<prefix>: src="/…", href="/…", url(/…), and a quoted "/static/…". It fails
too on a webpack bundle whose public path starts at the root and not with
<prefix> (`__webpack_require__.p="/"`, minified `o.p="/"`), even one nested
in another bundle: what it loads by that path, such as a web worker's
script, is looked for at the server's root, and never found. A
reference to another server, //host/… or https://…, is not the site's and
is left alone, and so is each <reference> named after the prefix: one the
build script has found the editor never asks for here, such as a picture of
a website's own menu, and says why.
"""

import re
import sys
from pathlib import Path

#: webpack's runtime public path, set to a path from the root.
PUBLIC_PATH = re.compile(r"""\b[A-Za-z_$][\w$]*\.p\s*=\s*["'](/[^"']*)["']""")

PATTERNS = (
    re.compile(r"""(?:src|href)\s*=\s*["'](/[^/"'][^"']*)["']"""),
    re.compile(r"""url\(\s*["']?(/[^/)"'][^)"']*)["']?\s*\)"""),
    re.compile(r"""["'](/static/[^"']*)["']"""),
)


def wrong(directory: Path, prefix: str, allowed=()) -> list[str]:
    found = []
    for path in sorted(directory.rglob("*")):
        if path.suffix not in (".html", ".css", ".js") or not path.is_file():
            continue
        text = path.read_text(errors="replace")
        for pattern in PATTERNS:
            for match in pattern.finditer(text):
                reference = match.group(1)
                if not reference.startswith(prefix) and reference not in allowed:
                    found.append(f"{path.relative_to(directory)}: {reference}")
        if path.suffix == ".js":
            for match in PUBLIC_PATH.finditer(text):
                if not match.group(1).startswith(prefix):
                    found.append(f"{path.relative_to(directory)}: a webpack public path of "
                                 f"{match.group(1)}")
    return found


def main(args: list[str]) -> int:
    if len(args) < 2:
        print(__doc__.strip().splitlines()[2], file=sys.stderr)
        return 2
    directory, prefix = Path(args[0]), args[1]
    found = wrong(directory, prefix, set(args[2:]))
    for line in found[:40]:
        print(f"refers to the root, not to {prefix}: {line}", file=sys.stderr)
    if found:
        print(f"{len(found)} references to the root", file=sys.stderr)
        return 1
    print(f"every reference is under {prefix}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
