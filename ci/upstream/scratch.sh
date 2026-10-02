#!/bin/sh
# Scratch's editor, the official one, built for kidux-webapps (D68, D69).
#
# Run by ci/build-upstream.sh kidux-module-scratch, in an empty directory,
# with the Node.js release upstream.toml names first in PATH. The editor is
# scratch-editor's scratch-gui: its build/, built for the path /scratch/.
# Its source maps are left out; its libraries of characters, backdrops and
# sounds are the Scratch Foundation's servers', which the editor asks when
# a child opens them.

set -eu

epoch="$(sh "$UPSTREAM_FETCH" git "$UPSTREAM_REPOSITORY" "$UPSTREAM_COMMIT" .)"

echo "==> node $(node --version), npm $(npm --version)"
# scratch-gui's prepare script, which npm ci runs, downloads the micro:bit
# program the editor offers to flash. It is fetched here instead, so that
# the source tarball holds it, and the script reads it from that copy.
hex="$PWD/.kidux-fetched/scratch-microbit.hex.zip"
sh "$UPSTREAM_FETCH" url https://downloads.scratch.mit.edu/microbit/scratch-microbit.hex.zip "$hex"
python3 - "$hex" <<'PYTHON'
import sys
from pathlib import Path
prepare = Path("packages/scratch-gui/scripts/prepare.mjs")
text = prepare.read_text()
old = """    const response = await fetch(url);
    const zipBuffer = Buffer.from(await response.arrayBuffer());"""
assert old in text, "prepare.mjs no longer downloads as it did"
prepare.write_text(text.replace(old, f"    const zipBuffer = fs.readFileSync({sys.argv[1]!r});"))
PYTHON
export NODE_OPTIONS=--max-old-space-size=6144
# husky's prepare hook wants a git hooks directory; the build needs none.
export HUSKY=0
npm ci --no-audit --no-fund

# The site is served under /scratch/, so everything in it is built for that
# path: scratch-gui's own site, whose webpack configuration makes build/ with
# an empty public path, for opening it from a folder, and the workspaces it
# bundles, which scratch-webpack-configuration builds for the root by
# default. scratch-storage's web worker, which fetches projects and
# costumes, would be looked for at the server's root, and the editor would
# never get past loading.
python3 - <<'PYTHON'
from pathlib import Path
for path, old, new in (
        ("packages/scratch-gui/webpack.config.js", "publicPath: ''", "publicPath: '/scratch/'"),
        ("node_modules/scratch-webpack-configuration/src/index.cjs", "publicPath = '/'",
         "publicPath = '/scratch/'")):
    config = Path(path)
    text = config.read_text()
    assert text.count(old) == 1, f"{path} no longer sets its public path as it did"
    config.write_text(text.replace(old, new))
PYTHON

echo "==> Building every workspace scratch-gui needs"
NODE_ENV=production npm run build

site="packages/scratch-gui/build"
[ -f "$site/index.html" ] || {
    echo "no $site/index.html after the build" >&2
    exit 1
}
find "$site" -name '*.map' -delete
python3 "$UPSTREAM_CHECK_SITE" "$site" /scratch/

out="$PWD/tarball"
mkdir -p "$out"
cp -a "$site/." "$out/"
cp LICENSE "$out/LICENSE"
[ -f packages/scratch-gui/TRADEMARK ] && cp packages/scratch-gui/TRADEMARK "$out/TRADEMARK"
echo "==> $(find "$out" -type f | wc -l) files, $(du -sh "$out" | cut -f1)"
sh "$UPSTREAM_PACK" "$out" "$UPSTREAM_PACKAGE-$UPSTREAM_VERSION" \
    "$UPSTREAM_OUT/$UPSTREAM_TARBALL" "$epoch"
