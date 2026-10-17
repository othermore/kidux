#!/usr/bin/python3
"""Makes one of the guide's photographs from a picture found, made or taken.

    pictures/prepare.py <source> <name> [--crop LEFT,TOP,WIDTH,HEIGHT]
                        [--grey | --red-filter] [--stops N] [--light R,G,B]

A development-time tool, run by hand and not installed (docs/dev/photography.md,
section 5). It writes pictures/<name>.jpg: the source, cropped when asked,
no longer than LONG_SIDE pixels on its long side, as a JPEG with no
metadata at all, since a camera's file carries its serial number and often
where it was, and smaller than MAX_BYTES, lowering the quality until it
is. With --stops, the picture is given N stops more light, or fewer when
N is negative, as a camera would have let in: its pixels are taken back to
the light they stand for, multiplied by two to the N, and written again,
which is how the guide shows one photograph too dark and too bright.
With --light, each colour's light is multiplied by its own number, which
is what a camera's white balance does, so that one photograph shows how
it looks under a lamp with the white balance set for daylight. With
--red-filter, the picture is made grey from its red light alone, which is
what a red filter does to black and white: blue things, a sky, go dark.
pictures.toml says in its `made` which of these a photograph had. The
credits are pictures.toml's, written by hand beside it.

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


def exposed(picture: Image.Image, stops: float,
            light: tuple[float, float, float] = (1.0, 1.0, 1.0)) -> Image.Image:
    """`picture` with 2**stops times the light, and each colour's light
    times its number in `light`: through sRGB's curve to linear light and
    back, so that a stop is what it is on a camera."""
    def to_linear(value: float) -> float:
        value /= 255
        return value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4

    def to_srgb(value: float) -> int:
        value = min(1.0, value)
        value = value * 12.92 if value <= 0.0031308 else 1.055 * value ** (1 / 2.4) - 0.055
        return round(value * 255)

    table = []
    for factor in light:
        table += [to_srgb(to_linear(level) * 2 ** stops * factor) for level in range(256)]
    return picture.point(table)


def prepared(source: Path, crop: tuple[int, int, int, int] | None, grey: bool,
             stops: float = 0.0, light: tuple[float, float, float] | None = None,
             red_filter: bool = False) -> bytes:
    with Image.open(source) as opened:
        picture = ImageOps.exif_transpose(opened).convert("RGB")
    if crop is not None:
        left, top, width, height = crop
        picture = picture.crop((left, top, left + width, top + height))
    if grey:
        picture = ImageOps.grayscale(picture).convert("RGB")
    if red_filter:
        red = picture.getchannel("R")
        picture = Image.merge("RGB", (red, red, red))
    if stops or light:
        picture = exposed(picture, stops, light or (1.0, 1.0, 1.0))
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
    shades = parser.add_mutually_exclusive_group()
    shades.add_argument("--grey", action="store_true", help="in shades of grey")
    shades.add_argument("--red-filter", action="store_true",
                        help="in shades of grey from the red light alone")
    parser.add_argument("--stops", type=float, default=0.0,
                        help="this many stops more light, or fewer when negative")
    parser.add_argument("--light", help="R,G,B: each colour's light times its number")
    arguments = parser.parse_args(argv)
    crop = tuple(int(n) for n in arguments.crop.split(",")) if arguments.crop else None
    if crop is not None and len(crop) != 4:
        parser.error("--crop takes four numbers")
    light = tuple(float(n) for n in arguments.light.split(",")) if arguments.light else None
    if light is not None and len(light) != 3:
        parser.error("--light takes three numbers")
    data = prepared(arguments.source, crop, arguments.grey, arguments.stops, light,
                    arguments.red_filter)
    target = PICTURES / f"{arguments.name}.jpg"
    target.write_bytes(data)
    with Image.open(target) as written:
        print(f"{target.name}: {written.width}x{written.height}, {len(data) // 1000} kB")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
