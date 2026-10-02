#!/bin/sh
# TurboWarp's editor, Scratch made faster, built for kidux-webapps (D68, D69).
#
# Run by ci/build-upstream.sh kidux-module-turbowarp, in an empty directory,
# with the Node.js release upstream.toml names first in PATH. TurboWarp's
# scratch-gui builds its site into build/ for the path its ROOT names, and
# its static files for STATIC_PATH, so both are /turbowarp/'s, and the site
# is checked to refer to nothing at the root. Its source maps are left out.

set -eu

epoch="$(sh "$UPSTREAM_FETCH" git "$UPSTREAM_REPOSITORY" "$UPSTREAM_COMMIT" .)"

echo "==> node $(node --version), npm $(npm --version)"
# The prepublish script, which npm ci runs, downloads the micro:bit program
# the editor offers to flash, and checks its SHA-256. It is fetched here
# instead, so that the source tarball holds it, and the script reads it,
# and checks it, from that copy.
hex="$PWD/.kidux-fetched/scratch-microbit-1.2.0.hex.zip"
sh "$UPSTREAM_FETCH" url https://packagerdata.turbowarp.org/scratch-microbit-1.2.0.hex.zip "$hex"
python3 - "$hex" <<'PYTHON'
import sys
from pathlib import Path
prepublish = Path("scripts/prepublish.mjs")
text = prepublish.read_text()
old = """    const response = await crossFetch(url);
    const zipBuffer = Buffer.from(await response.arrayBuffer());"""
assert old in text, "prepublish.mjs no longer downloads as it did"
prepublish.write_text(text.replace(old, f"    const zipBuffer = fs.readFileSync({sys.argv[1]!r});"))
PYTHON
export NODE_OPTIONS=--max-old-space-size=6144
export HUSKY=0
npm ci --no-audit --no-fund

echo "==> Building the editor for /turbowarp/"
NODE_ENV=production ROOT=/turbowarp/ STATIC_PATH=/turbowarp/static npm run build

site="build"
[ -f "$site/index.html" ] || {
    echo "no $site/index.html after the build" >&2
    exit 1
}
find "$site" -name '*.map' -delete
# /images/mystuff.png is the picture of the Scratch website's "My Stuff",
# in a menu TurboWarp shows only to someone signed in to that website.
python3 "$UPSTREAM_CHECK_SITE" "$site" /turbowarp/ /images/mystuff.png

out="$PWD/tarball"
mkdir -p "$out"
cp -a "$site/." "$out/"
for licence in LICENSE LICENSE.txt COPYING; do
    [ -f "$licence" ] && cp "$licence" "$out/$licence"
done
echo "==> $(find "$out" -type f | wc -l) files, $(du -sh "$out" | cut -f1)"
sh "$UPSTREAM_PACK" "$out" "$UPSTREAM_PACKAGE-$UPSTREAM_VERSION" \
    "$UPSTREAM_OUT/$UPSTREAM_TARBALL" "$epoch"
