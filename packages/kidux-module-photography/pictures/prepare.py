#!/usr/bin/python3
"""Makes one of the guide's photographs from a picture found, made or taken.

    pictures/prepare.py <source> <name> [--crop LEFT,TOP,WIDTH,HEIGHT] [--grey]

A development-time tool, run by hand and not installed (docs/dev/photography.md,
section 5). It writes pictures/<name>.jpg: the source, cropped when asked,
no longer than LONG_SIDE pixels on its long side, as a JPEG with no
metadata at all, since a camera's file carries its serial number and often
where it was, and smaller than MAX_BYTES, lowering the quality until it
is. The credits are pictures.toml's, written by hand beside it.

It needs python3-pil, which only the development machine has: the package
ships the files it made, and its build never runs it.
"""

import argparse
import io
import sys
from pathlib import Path

from PIL import Image, ImageOps

PICTURES = Path(__file__).resolve().parent
LONG_SIDE = 1400
MAX_BYTES = 400_000
QUALITY = 82


def prepared(source: Path, crop: tuple[int, int, int, int] | None, grey: bool) -> bytes:
    with Image.open(source) as opened:
        picture = ImageOps.exif_transpose(opened).convert("RGB")
    if crop is not None:
        left, top, width, height = crop
        picture = picture.crop((left, top, left + width, top + height))
    if grey:
        picture = ImageOps.grayscale(picture).convert("RGB")
    picture.thumbnail((LONG_SIDE, LONG_SIDE), Image.Resampling.LANCZOS)
    for quality in range(QUALITY, 40, -6):
        out = io.BytesIO()
        # A new image has no EXIF, XMP or ICC of the source's: nothing is
        # carried over but the pixels.
        Image.frombytes("RGB", picture.size, picture.tobytes()).save(
            out, "JPEG", quality=quality, optimize=True, progressive=True)
        if out.tell() <= MAX_BYTES:
            return out.getvalue()
    raise SystemExit(f"{source}: still over {MAX_BYTES} bytes at the lowest quality")


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("source", type=Path)
    parser.add_argument("name", help="the file's name in pictures/, without .jpg")
    parser.add_argument("--crop", help="LEFT,TOP,WIDTH,HEIGHT in the source's pixels")
    parser.add_argument("--grey", action="store_true", help="in shades of grey")
    arguments = parser.parse_args(argv)
    crop = tuple(int(n) for n in arguments.crop.split(",")) if arguments.crop else None
    if crop is not None and len(crop) != 4:
        parser.error("--crop takes four numbers")
    data = prepared(arguments.source, crop, arguments.grey)
    target = PICTURES / f"{arguments.name}.jpg"
    target.write_bytes(data)
    with Image.open(target) as written:
        print(f"{target.name}: {written.width}x{written.height}, {len(data) // 1000} kB")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
