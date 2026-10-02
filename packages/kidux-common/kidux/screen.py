"""The room a screen has, for the programs that fill it (D49).

Every screen fits 1280x800 whole, in logical pixels, the display scale
applied (D30). On a screen with room to spare, `ROOMY` or more each way,
the screens keep their size and the room is space, as the owner put it
(D53): the launcher puts more tiles to a row. The greeter and the launcher
mark their windows `kidux-roomy` on such a screen.

The display scale is the machine's, one for every screen. Unless an adult
chooses one, it is automatic: the largest, in quarters, at which a screen's
mode still has room to spare, `ROOMY` whole, and never less than 1, so
that a screen that can be roomy is (D56). `session-inner` asks this module
for it with the mode `wlr-randr` reports, and exports that mode as
`KIDUX_SCREEN_MODE` for the panel to say what automatic is on this screen:

    python3 -m kidux.screen 2880x1800      prints 1.75
"""

import os
import sys

#: The least room, in logical pixels, that is roomy: 1440x900, the
#: development MacBook at scale 2, is not; 1920x1080 at scale 1 is.
ROOMY_WIDTH, ROOMY_HEIGHT = 1600, 960

#: What every screen fits whole (D30), and so what the automatic scale keeps.
FITS_WIDTH, FITS_HEIGHT = 1280, 800
#: The display scale the machine's settings hold when no adult has chosen one.
AUTOMATIC = 0.0


def roomy(width: int, height: int) -> bool:
    return width >= ROOMY_WIDTH and height >= ROOMY_HEIGHT


#: Under this many logical pixels of width a screen's corner (kidux.corner)
#: is compact, its icons alone without their percentages: the full corner is
#: about 380 pixels wide, and on a screen narrower than this it would reach
#: what is centred at the top of the greeter's screens, the panel's tabs, or
#: crowd the launcher's clock. 1280, the least a screen is drawn for (D30),
#: keeps the full corner.
COMPACT_CORNER_BELOW = 1200


def compact_corner(width: int) -> bool:
    """Whether a screen `width` logical pixels wide gets the compact corner.
    A width of 0, a display not yet measured, gets the full one."""
    return 0 < width < COMPACT_CORNER_BELOW


def logical_size(display) -> tuple[int, int]:
    """The size of a GDK display's first monitor in logical pixels, which is
    what a window on it is laid out in; (0, 0) when it has none."""
    monitors = display.get_monitors()
    if monitors.get_n_items() == 0:
        return 0, 0
    geometry = monitors.get_item(0).get_geometry()
    return geometry.width, geometry.height


def automatic_scale(width: int, height: int) -> float:
    """The display scale for a mode of `width` by `height` pixels when no
    adult has chosen one: the largest quarter that leaves the screen roomy,
    1600x960 or more, and never less than 1. 1.75 for 2880x1800, 1 for
    1920x1080 and for anything smaller."""
    fits = min(width / ROOMY_WIDTH, height / ROOMY_HEIGHT)
    return max(1.0, int(fits * 4) / 4)


def mode_from_environment() -> tuple[int, int] | None:
    """The screen's mode as `session-inner` exports it, `KIDUX_SCREEN_MODE`,
    or None where nothing did."""
    try:
        width, height = (int(n) for n in os.environ.get("KIDUX_SCREEN_MODE", "").split("x"))
    except ValueError:
        return None
    return (width, height) if width > 0 and height > 0 else None


def physical_size(display) -> tuple[int, int]:
    """The size of a GDK display's first monitor in the screen's own pixels,
    its logical size times its scale; (0, 0) when it has none. What the
    panel falls back on when `KIDUX_SCREEN_MODE` is not there."""
    monitors = display.get_monitors()
    if monitors.get_n_items() == 0:
        return 0, 0
    monitor = monitors.get_item(0)
    geometry = monitor.get_geometry()
    scale = monitor.get_scale() if hasattr(monitor, "get_scale") else monitor.get_scale_factor()
    return round(geometry.width * scale), round(geometry.height * scale)


def main(argv: list[str]) -> int:
    try:
        width, height = (int(n) for n in argv[1].lower().split("x"))
    except (IndexError, ValueError):
        print("usage: python3 -m kidux.screen <width>x<height>", file=sys.stderr)
        return 2
    print(f"{automatic_scale(width, height):g}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
