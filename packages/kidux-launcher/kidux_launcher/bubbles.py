"""The bubble: a module's notices, in the top right corner of the child's
screen (D98).

The launcher owns `org.freedesktop.Notifications` on the child's session
bus and draws each notice (notices.py) as a bubble on gtk4-layer-shell's
overlay layer, over every module and taking no keyboard, as the bar is
drawn on its top layer (bar.py). The newest is at the top. A bubble says
which module it is from, with its tile, or the program's own name; its
summary and its text, plain; a button to close it, and the program's other
actions as buttons. A click on it does the notice's default action.
"""

import logging

import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gio, GLib, Gtk, Pango  # noqa: E402

from kidux import modules as kidux_modules  # noqa: E402

from . import notices, words  # noqa: E402

log = logging.getLogger("kidux.launcher")

#: How wide a bubble is, and how far from the screen's right edge and its
#: top, which is below the corner of the battery, the light and the sound
#: (kidux.corner), so that a bubble never hides them.
WIDTH = 380
MARGIN = 16
TOP = 72
#: The lines of a notice's text shown before it is cut short.
LINES = 6

CSS = """
window.kidux-bubbles { background-color: transparent; }
.kidux-bubble { background-color: #fdf6f0; color: #3b2f2a; border-radius: 18px;
  padding: 12px 14px; border: 2px solid #e5d3bf;
  box-shadow: 0 3px 8px alpha(#3b2f2a, 0.22); margin: 10px; }
.kidux-bubble-from { font-size: 16px; font-weight: bold; color: #7a6a60; }
.kidux-bubble-summary { font-size: 19px; font-weight: bold; }
.kidux-bubble-body { font-size: 17px; }
.kidux-bubble button { min-height: 40px; min-width: 40px; border-radius: 12px;
  padding: 0 12px; font-size: 16px; }
.kidux-bubble button.kidux-bubble-close { background-color: transparent; padding: 0; }
"""


def version() -> str:
    """The launcher's version, which the server says it is."""
    try:
        from importlib.metadata import version as installed
        return installed("kidux-launcher")
    except Exception:  # noqa: BLE001 — a version is not worth a failed answer
        return ""


class Bubbles:
    """The bubbles' window, and the notices' server on the session bus."""

    def __init__(self, application: Gtk.Application, shell, *, translate,
                 language: str) -> None:
        self._ = translate
        self._language = language
        self._bubbles: dict[int, Gtk.Widget] = {}
        self._timers: dict[int, int] = {}
        self._connection = None
        self.notices = notices.Notices(show=self._show, hide=self._hide,
                                       closed=self._send_closed, invoked=self._send_invoked)

        window = Gtk.Window(application=application, title="Kidux", decorated=False)
        window.add_css_class("kidux")
        window.add_css_class("kidux-bubbles")
        shell.init_for_window(window)
        shell.set_namespace(window, "kidux-bubbles")
        shell.set_layer(window, shell.Layer.OVERLAY)
        for edge, margin in ((shell.Edge.TOP, TOP), (shell.Edge.RIGHT, MARGIN)):
            shell.set_anchor(window, edge, True)
            shell.set_margin(window, edge, margin)
        shell.set_keyboard_mode(window, shell.KeyboardMode.NONE)
        self._stack = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self._stack.set_size_request(WIDTH, -1)
        window.set_child(self._stack)
        self._window = window

        self._interface = Gio.DBusNodeInfo.new_for_xml(notices.INTERFACE).interfaces[0]
        Gio.bus_own_name(Gio.BusType.SESSION, notices.NAME,
                         Gio.BusNameOwnerFlags.ALLOW_REPLACEMENT | Gio.BusNameOwnerFlags.REPLACE,
                         self._bus_acquired, None, self._name_lost)

    # --- the server ---------------------------------------------------------

    def _bus_acquired(self, connection, _name) -> None:
        self._connection = connection
        connection.register_object(notices.PATH, self._interface, self._call, None, None)

    def _name_lost(self, _connection, name) -> None:
        log.warning("notices: %s is not the launcher's; no bubble will show", name)

    def _call(self, connection, sender, _path, _interface, method, parameters, invocation):
        try:
            if method == "GetCapabilities":
                invocation.return_value(GLib.Variant("(as)", (list(notices.CAPABILITIES),)))
            elif method == "GetServerInformation":
                invocation.return_value(GLib.Variant(
                    "(ssss)", ("Kidux", "Kidux", version(), notices.SPEC_VERSION)))
            elif method == "Notify":
                (app_name, replaces_id, _icon, summary, body, actions, hints,
                 expire_timeout) = parameters.unpack()
                notice = self.notices.notify(self._module_of(connection, sender), app_name,
                                             replaces_id, summary, body, actions, hints,
                                             expire_timeout)
                invocation.return_value(GLib.Variant("(u)", (notice.id,)))
            elif method == "CloseNotification":
                (number,) = parameters.unpack()
                self.notices.close(number, notices.CLOSED)
                invocation.return_value(None)
            else:
                invocation.return_dbus_error("org.freedesktop.DBus.Error.UnknownMethod", method)
        except Exception as error:  # noqa: BLE001 — a bad notice is not worth the launcher
            log.exception("notices: %s failed", method)
            invocation.return_dbus_error("org.freedesktop.DBus.Error.Failed", str(error))

    def _module_of(self, connection, sender: str) -> str:
        """The module whose scope the sender runs in, or ""."""
        try:
            answer = connection.call_sync(
                "org.freedesktop.DBus", "/org/freedesktop/DBus", "org.freedesktop.DBus",
                "GetConnectionUnixProcessID", GLib.Variant("(s)", (sender,)),
                GLib.VariantType.new("(u)"), Gio.DBusCallFlags.NONE, 1000, None)
        except GLib.Error:
            return ""
        return notices.module_of(answer.unpack()[0])

    def _send_closed(self, number: int, reason: int) -> None:
        log.info("notice %d closed (%d)", number, reason)
        self._emit("NotificationClosed", GLib.Variant("(uu)", (number, reason)))

    def _send_invoked(self, number: int, key: str) -> None:
        self._emit("ActionInvoked", GLib.Variant("(us)", (number, key)))

    def _emit(self, signal: str, values) -> None:
        if self._connection is not None:
            self._connection.emit_signal(None, notices.PATH, notices.NAME, signal, values)

    # --- the bubbles --------------------------------------------------------

    def _from(self, notice) -> tuple[str, str]:
        """Who it is from: the module's name and tile, or the program's name."""
        module = kidux_modules.read(notice.module) if notice.module else None
        if module is not None:
            return kidux_modules.name_in(module, self._language), module.icon
        return notice.app_name, ""

    def _show(self, notice) -> None:
        name, icon = self._from(notice)
        log.info("notice %d from %s%s", notice.id, notice.module or notice.app_name or "?",
                 ", staying" if notice.stays else "")
        bubble = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        bubble.add_css_class("kidux-bubble")

        top = Gtk.Box(spacing=8)
        if icon:
            image = Gtk.Image.new_from_gicon(Gio.FileIcon.new(Gio.File.new_for_path(icon)))
            image.set_pixel_size(28)
            top.append(image)
        sender = Gtk.Label(label=name, xalign=0, hexpand=True, ellipsize=Pango.EllipsizeMode.END)
        sender.add_css_class("kidux-bubble-from")
        top.append(sender)
        close = Gtk.Button(icon_name="window-close-symbolic", tooltip_text=self._(words.CLOSE))
        close.add_css_class("kidux-bubble-close")
        close.connect("clicked", lambda _b, n=notice.id: self.notices.close(n, notices.DISMISSED))
        top.append(close)
        bubble.append(top)

        for text, css, lines in ((notice.summary, "kidux-bubble-summary", 2),
                                 (notice.body, "kidux-bubble-body", LINES)):
            if text:
                label = Gtk.Label(label=text, xalign=0, wrap=True, lines=lines, ellipsize=Pango.EllipsizeMode.END,
                                  max_width_chars=34, use_markup=False)
                label.add_css_class(css)
                bubble.append(label)

        if notice.buttons:
            row = Gtk.Box(spacing=8, halign=Gtk.Align.END)
            for key, label in notice.buttons:
                button = Gtk.Button(label=label)
                button.connect("clicked", lambda _b, n=notice.id, k=key: self.notices.act(n, k))
                row.append(button)
            bubble.append(row)

        if any(key == notices.DEFAULT for key, _label in notice.actions):
            click = Gtk.GestureClick()
            click.connect("released",
                          lambda *_a, n=notice.id: self.notices.act(n, notices.DEFAULT))
            bubble.add_controller(click)

        self._bubbles[notice.id] = bubble
        self._stack.prepend(bubble)
        self._window.set_visible(True)
        if not notice.stays:
            self._timers[notice.id] = GLib.timeout_add_seconds(
                notices.SECONDS, self._expire, notice.id)

    def _expire(self, number: int) -> bool:
        self._timers.pop(number, None)
        self.notices.expire(number)
        return GLib.SOURCE_REMOVE

    def _hide(self, number: int) -> None:
        timer = self._timers.pop(number, None)
        if timer is not None:
            GLib.source_remove(timer)
        bubble = self._bubbles.pop(number, None)
        if bubble is not None:
            self._stack.remove(bubble)
        if not self._bubbles:
            self._window.set_visible(False)
