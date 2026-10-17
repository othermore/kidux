"""Kidux's answer to a link out of a module (D104, docs/dev/session.md
section 3).

A program that asks the desktop to open a web page or an HTML file, as
Step's *Open in browser* or a link in a program's help does, reaches
`kidux-closed` instead of a browser: the child's session makes it the
default for web pages and links. It says so in a bubble, from the module
whose scope it runs in, which the launcher finds itself, and opens
nothing. A module that is a web page starts its browser itself and never
comes here.
"""

import sys
from collections.abc import Callable

from .i18n import N_, _

#: What the bubble says.
CLOSED = N_("That opens the internet, which is closed here.")

#: Who the notice is from when no module's scope holds the caller.
SENDER = "Kidux"


def request(text: str) -> tuple:
    """The arguments of org.freedesktop.Notifications.Notify for `text`:
    a notice of its own, with no icon, buttons or hints, that goes away on
    its own."""
    return (SENDER, 0, "", text, "", [], {}, -1)


def notify(arguments: tuple) -> None:
    """Sends a notice on the session's bus."""
    from gi.repository import Gio, GLib

    bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)
    bus.call_sync("org.freedesktop.Notifications", "/org/freedesktop/Notifications",
                  "org.freedesktop.Notifications", "Notify",
                  GLib.Variant("(susssasa{sv}i)", arguments), GLib.VariantType.new("(u)"),
                  Gio.DBusCallFlags.NONE, 5000, None)


def main(args: list[str], *, send: Callable[[tuple], None] = notify,
         translate: Callable[[str], str] = _) -> int:
    """kidux-closed [<link>...]: the bubble, whatever the links; 0 even
    when it cannot be sent, so that the program that asked is not told the
    desktop failed."""
    print(f"kidux-closed: not opened: {' '.join(args) or '(nothing)'}", file=sys.stderr)
    try:
        send(request(translate(CLOSED)))
    except Exception as error:  # noqa: BLE001 — nothing to open, so nothing to fail
        print(f"kidux-closed: no bubble: {error}", file=sys.stderr)
    return 0
