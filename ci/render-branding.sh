#!/bin/sh
# Render the logo, the mascot and the wordmark to PNG at the sizes anyone is
# likely to need, and branding/sheet.png, every piece on one page with its
# name, to look at them together.
#
#   ci/render-branding.sh
#
# The SVG files in branding/svg/ are the originals; branding/png/ is what this
# produces from them, transparent, and is committed so that a page or a slide
# can take a file without installing anything. Run it after editing an SVG and
# commit what changed, the sheet included.

set -eu

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SVG="$REPO_ROOT/branding/svg"
PNG="$REPO_ROOT/branding/png"
SHEET="$REPO_ROOT/branding/sheet.png"

if ! command -v rsvg-convert >/dev/null 2>&1; then
    echo "$0: rsvg-convert is missing. Run: sudo ci/setup-dev-host.sh" >&2
    exit 1
fi

mkdir -p "$PNG"
rm -f "$PNG"/*.png

render() {
    # render <name> <dimension> <sizes...>: dimension is width or height
    name="$1"; dimension="$2"; shift 2
    for size in "$@"; do
        rsvg-convert "--$dimension=$size" --keep-aspect-ratio \
            --output="$PNG/$name-$size.png" "$SVG/$name.svg"
    done
}

# Square things by width; wide things by height, so "wordmark-64" is 64 px tall.
render mascot          width  32 64 128 256 512 1024
render mascot-on-dark  width  32 64 128 256 512 1024
render icon            width  16 32 48 64 128 256 512 1024
render wordmark        height 24 32 48 64 128 256
render wordmark-on-dark height 24 32 48 64 128 256
render wordmark-mono   height 24 32 48 64 128 256
render logo            height 48 64 96 128 256 512
render logo-on-dark    height 48 64 96 128 256 512

python3 - "$PNG" > "$SHEET.svg" <<'PYTHON'
import base64, pathlib, struct, sys

png = pathlib.Path(sys.argv[1])
CREAM, INK, MUTED, LINE, DEEP = "#fff6e9", "#3b2f2a", "#7a6a60", "#e6d9c8", "#141c26"
PAD, GAP, CAPTION = 24, 48, 22          # inside a card; between images; caption line
MARGIN, COLUMN_GAP = 30, 30             # around the page; between cards in a row

def size(name):
    header = (png / name).read_bytes()[:24]
    return struct.unpack(">II", header[16:24])

def uri(name):
    return "data:image/png;base64," + base64.b64encode((png / name).read_bytes()).decode()

class Card:
    """A framed group: a title, then images side by side, each with its size under it."""

    def __init__(self, title, names, dark=False):
        self.title, self.names, self.dark = title, names, dark
        self.sizes = [size(n) for n in names]
        self.content_w = sum(w for w, _ in self.sizes) + GAP * (len(names) - 1)
        self.content_h = max(h for _, h in self.sizes)
        # Wide enough for the images and for the title (about 9 px a character).
        self.min_w = max(self.content_w, len(title) * 9) + 2 * PAD
        self.h = PAD + 20 + PAD + self.content_h + CAPTION + PAD

    def draw(self, x, y, w):
        fill, text, caption = (DEEP, CREAM, "#9aa7b5") if self.dark else ("#ffffff", INK, MUTED)
        out = [f'<rect x="{x}" y="{y}" width="{w}" height="{self.h}" rx="16" fill="{fill}" stroke="{LINE}"/>',
               f'<text x="{x + PAD}" y="{y + PAD + 14}" font-family="sans-serif" font-size="16" font-weight="bold" fill="{text}">{self.title}</text>']
        cx = x + (w - self.content_w) / 2          # images centred as a group
        base = y + PAD + 20 + PAD + self.content_h  # every image sits on this line
        for name, (iw, ih) in zip(self.names, self.sizes):
            out.append(f'<image x="{cx:.0f}" y="{base - ih}" width="{iw}" height="{ih}" xlink:href="{uri(name)}"/>')
            label = name.removesuffix(".png").rsplit("-", 1)[1] + " px"
            out.append(f'<text x="{cx + iw / 2:.0f}" y="{base + CAPTION}" font-family="sans-serif" font-size="13" text-anchor="middle" fill="{caption}">{label}</text>')
            cx += iw + GAP
        return "\n".join(out)

rows = [
    [Card("logo, by height", ["logo-128.png", "logo-96.png", "logo-64.png", "logo-48.png"])],
    [Card("mascot, by width", ["mascot-256.png", "mascot-128.png", "mascot-64.png", "mascot-32.png"]),
     Card("icon, by width", ["icon-128.png", "icon-64.png", "icon-48.png", "icon-32.png", "icon-16.png"])],
    [Card("wordmark, by height", ["wordmark-64.png", "wordmark-48.png", "wordmark-32.png", "wordmark-24.png"]),
     Card("wordmark-mono: one colour, for one-ink printing", ["wordmark-mono-64.png", "wordmark-mono-32.png"])],
    [Card("logo-on-dark, by height, on Deep", ["logo-on-dark-128.png", "logo-on-dark-96.png",
                                                "logo-on-dark-64.png", "logo-on-dark-48.png"], dark=True)],
    [Card("mascot-on-dark, by width, on Deep", ["mascot-on-dark-128.png", "mascot-on-dark-64.png", "mascot-on-dark-32.png"], dark=True),
     Card("wordmark-on-dark, by height, on Deep", ["wordmark-on-dark-64.png", "wordmark-on-dark-48.png", "wordmark-on-dark-32.png"], dark=True)],
]

# The page is as wide as its widest row needs. Cards in a row share its
# height, and the row's spare width is split between them in proportion to
# what each holds, so no card is ever narrower than its content or its title.
WIDTH = max(sum(c.min_w for c in row) + COLUMN_GAP * (len(row) - 1) for row in rows) + 2 * MARGIN
body, y = [], MARGIN
for row in rows:
    available = WIDTH - 2 * MARGIN - COLUMN_GAP * (len(row) - 1)
    spare = available - sum(c.min_w for c in row)
    widths = [c.min_w + spare * c.min_w / sum(k.min_w for k in row) for c in row]
    height = max(c.h for c in row)
    x = MARGIN
    for card, w in zip(row, widths):
        card.h = height
        body.append(card.draw(x, y, round(w)))
        x += w + COLUMN_GAP
    y += height + COLUMN_GAP
HEIGHT = y - COLUMN_GAP + MARGIN

print(f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="{WIDTH}" height="{HEIGHT:.0f}">')
print(f'<rect width="{WIDTH}" height="{HEIGHT:.0f}" fill="{CREAM}"/>')
print("\n".join(body))
print("</svg>")
PYTHON
rsvg-convert --output="$SHEET" "$SHEET.svg"

# kidux-common ships the logo and the mascot for every screen that shows
# them, and a package's source can only hold what is in its own directory.
cp "$SVG/logo.svg" "$SVG/mascot.svg" "$REPO_ROOT/packages/kidux-common/data/branding/"
# The boot splash is drawn by Plymouth, which takes PNG.
cp "$PNG/logo-512.png" "$REPO_ROOT/packages/kidux-session/plymouth/logo.png"
rm -f "$SHEET.svg"
echo "==> $SHEET"
ls "$PNG" | wc -l | sed 's/^/==> PNG files: /'
