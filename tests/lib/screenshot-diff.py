#!/usr/bin/python3
"""Compare two sets of screen pictures and say what changed.

    tests/lib/screenshot-diff.py OLD_DIR NEW_DIR REPORT_DIR

Pictures are matched by name, ignoring the number the harness puts in front
(`session-07-lock-screen.png` and `session-09-lock-screen.png` are the same
screen). For each pair the report gives the share of pixels that differ, and
a picture of the new screen with the changed pixels in red; pictures only in
one set are listed as new or gone. The report is REPORT_DIR/index.html, to be
looked at by a person: whether a change is right is a judgement, not a test.
The exit status is 0 whatever changed.

Only the standard library, so it runs anywhere the harness runs: QEMU writes
8-bit RGB or RGBA PNGs, which is all this decodes.
"""

import html
import re
import struct
import sys
import zlib
from pathlib import Path

#: Two pixels differ when any channel differs by more than this, so that a
#: renderer's rounding is not reported as a change.
TOLERANCE = 16
#: A picture whose share of differing pixels is at or below this is "the
#: same": the clock on the sign-in screen changes every minute.
UNCHANGED = 0.005


def read_png(path: Path) -> tuple[int, int, list[bytes]]:
    """Width, height and rows of RGB bytes."""
    data = path.read_bytes()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError(f"{path} is not a PNG")
    pos, idat, width = 8, b"", 0
    while pos < len(data):
        length, kind = struct.unpack(">I4s", data[pos:pos + 8])
        body = data[pos + 8:pos + 8 + length]
        if kind == b"IHDR":
            width, height, depth, colour, _, _, interlace = struct.unpack(">IIBBBBB", body)
            if depth != 8 or colour not in (2, 6) or interlace:
                raise ValueError(f"{path}: only 8-bit RGB or RGBA, not interlaced")
            channels = 3 if colour == 2 else 4
        elif kind == b"IDAT":
            idat += body
        pos += 12 + length
    raw = zlib.decompress(idat)
    stride = width * channels
    rows, previous = [], bytearray(stride)
    for y in range(height):
        start = y * (stride + 1)
        kind, line = raw[start], bytearray(raw[start + 1:start + 1 + stride])
        for x in range(stride):
            a = line[x - channels] if x >= channels else 0
            b = previous[x]
            c = previous[x - channels] if x >= channels else 0
            if kind == 1:
                line[x] = (line[x] + a) & 0xFF
            elif kind == 2:
                line[x] = (line[x] + b) & 0xFF
            elif kind == 3:
                line[x] = (line[x] + (a + b) // 2) & 0xFF
            elif kind == 4:
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                line[x] = (line[x] + (a if pa <= pb and pa <= pc else b if pb <= pc else c)) & 0xFF
        previous = line
        if channels == 4:
            line = bytearray(b for i, b in enumerate(line) if i % 4 != 3)
        rows.append(bytes(line))
    return width, height, rows


def write_png(path: Path, width: int, height: int, rows: list[bytes]) -> None:
    raw = b"".join(b"\x00" + row for row in rows)
    def chunk(kind, body):
        return struct.pack(">I", len(body)) + kind + body + struct.pack(">I", zlib.crc32(kind + body))
    path.write_bytes(b"\x89PNG\r\n\x1a\n"
                     + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
                     + chunk(b"IDAT", zlib.compress(raw, 6)) + chunk(b"IEND", b""))


def compare(old: Path, new: Path, marked: Path) -> float:
    """The share of pixels that differ; the new picture, changes in red, to `marked`."""
    ow, oh, orows = read_png(old)
    nw, nh, nrows = read_png(new)
    if (ow, oh) != (nw, nh):
        write_png(marked, nw, nh, nrows)
        return 1.0
    changed, out = 0, []
    for orow, nrow in zip(orows, nrows):
        line = bytearray()
        for x in range(0, len(nrow), 3):
            o, n = orow[x:x + 3], nrow[x:x + 3]
            if max(abs(o[i] - n[i]) for i in range(3)) > TOLERANCE:
                changed += 1
                line += b"\xff\x00\x00"
            else:
                # The unchanged picture, faded, so the red stands out.
                line += bytes(200 + v // 5 for v in n)
        out.append(bytes(line))
    write_png(marked, nw, nh, out)
    return changed / (nw * nh)


def screen_name(path: Path) -> str:
    """The screen a picture is of, without its number: `sign-in` for the
    Spanish run's session-06-sign-in.png, `en/sign-in` for the English run's
    session-en-06-sign-in.png."""
    return re.sub(r"^session-(?:([a-z]{2})-)?\d+-",
                  lambda found: f"{found.group(1)}/" if found.group(1) else "", path.stem)


def main() -> int:
    old_dir, new_dir, report = (Path(a) for a in sys.argv[1:4])
    report.mkdir(parents=True, exist_ok=True)
    old = {screen_name(p): p for p in sorted(old_dir.glob("*.png"))}
    new = {screen_name(p): p for p in sorted(new_dir.glob("*.png"))}

    rows, summary = [], {"changed": [], "same": [], "new": [], "gone": []}
    for name in sorted(set(old) | set(new), key=lambda n: (new.get(n) or old[n]).name):
        if name not in old:
            summary["new"].append(name)
            rows.append((name, "new", None, None, new[name]))
        elif name not in new:
            summary["gone"].append(name)
            rows.append((name, "gone", None, old[name], None))
        else:
            marked = report / f"{name.replace('/', '-')}-changes.png"
            share = compare(old[name], new[name], marked)
            state = "changed" if share > UNCHANGED else "same"
            summary[state].append(name)
            rows.append((name, state, share, old[name], new[name], marked))

    def img(path):
        return f'<img src="{html.escape(str(path.resolve()))}" width="420">' if path else ""

    parts = ["<!doctype html><meta charset=utf-8><title>Kidux screens</title>",
             "<style>body{font-family:sans-serif;background:#fff6e9;color:#3b2f2a}"
             "td{vertical-align:top;padding:8px}.changed{color:#b3261e}.new{color:#1b6e3a}</style>",
             f"<h1>Screens: {len(summary['changed'])} changed, {len(summary['new'])} new, "
             f"{len(summary['gone'])} gone, {len(summary['same'])} the same</h1>",
             "<table><tr><th>screen</th><th>before</th><th>now</th><th>what changed</th></tr>"]
    for row in rows:
        name, state = row[0], row[1]
        share = f" ({row[2]:.1%})" if row[2] is not None else ""
        marked = row[5] if len(row) > 5 and state == "changed" else None
        parts.append(f'<tr><td class="{state}"><b>{html.escape(name)}</b><br>{state}{share}</td>'
                     f"<td>{img(row[3])}</td><td>{img(row[4])}</td><td>{img(marked)}</td></tr>")
    parts.append("</table>")
    (report / "index.html").write_text("\n".join(parts))

    for state in ("changed", "new", "gone"):
        for name in summary[state]:
            print(f"{state.upper():8} {name}")
    print(f"==> {len(summary['same'])} the same; report in {report / 'index.html'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
