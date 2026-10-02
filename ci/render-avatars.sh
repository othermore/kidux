#!/bin/sh
# Render the shipped avatars into one sheet, to look at them.
#
#   ci/render-avatars.sh [output.png]
#
# An avatar is the only part of the sign-in screen a four-year-old can use, so
# it gets looked at rather than taken on trust. Each one appears twice: at the
# 96 px the sign-in screen shows it at, and at 48 px, because a shape that
# works large can be a smudge small — which is exactly how the first whale and
# the first rabbit were caught.

set -eu

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
AVATAR_DIR="$REPO_ROOT/packages/kidux-common/data/avatars"
OUTPUT="${1:-$REPO_ROOT/build/avatars.png}"
LARGE="${KIDUX_AVATAR_SIZE:-96}"
SMALL="${KIDUX_AVATAR_SMALL:-48}"

if ! command -v rsvg-convert >/dev/null 2>&1; then
    echo "$0: rsvg-convert is missing. Run: sudo ci/setup-dev-host.sh" >&2
    exit 1
fi

mkdir -p "$(dirname "$OUTPUT")"
tmpdir="$(mktemp -d)"
trap 'rm -rf "$tmpdir"' EXIT

for svg in "$AVATAR_DIR"/*.svg; do
    rsvg-convert --width="$LARGE" --height="$LARGE" --background-color=white \
        --output="$tmpdir/$(basename "$svg" .svg).png" "$svg"
done

# The sheet embeds the rendered images rather than linking to them, because
# rsvg-convert refuses to follow file references out of an SVG, and rightly so.
# Doing it this way also means no ImageMagick.
python3 - "$tmpdir" "$LARGE" "$SMALL" > "$tmpdir/sheet.svg" <<'PYTHON'
import base64
import pathlib
import sys

tmpdir, large, small = pathlib.Path(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3])
images = sorted(tmpdir.glob("*.png"))
pad, label = 16, 28

width = len(images) * (large + pad) + pad
height = pad + large + 12 + small + label

print(
    f'<svg xmlns="http://www.w3.org/2000/svg" '
    f'xmlns:xlink="http://www.w3.org/1999/xlink" '
    f'width="{width}" height="{height}">'
)
print(f'<rect width="{width}" height="{height}" fill="#ffffff"/>')

for index, image in enumerate(images):
    uri = "data:image/png;base64," + base64.b64encode(image.read_bytes()).decode()
    x = pad + index * (large + pad)
    print(f'<image x="{x}" y="{pad}" width="{large}" height="{large}" xlink:href="{uri}"/>')
    print(
        f'<image x="{x + (large - small) // 2}" y="{pad + large + 12}" '
        f'width="{small}" height="{small}" xlink:href="{uri}"/>'
    )
    print(
        f'<text x="{x + large // 2}" y="{height - 8}" font-family="sans-serif" '
        f'font-size="13" text-anchor="middle" fill="#333">{image.stem}</text>'
    )

print("</svg>")
PYTHON

rsvg-convert --output="$OUTPUT" "$tmpdir/sheet.svg"

echo "==> $OUTPUT"
