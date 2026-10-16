"""The bubbles: a module's notices, rising from the bar at the bottom right of
the child's screen, and the bar's bell that keeps them (D98).

The launcher owns `org.freedesktop.Notifications` on the child's session
bus and draws each notice (notices.py) as a bubble on gtk4-layer-shell's
overlay layer, over every module and taking no keyboard, as the bar is
drawn on its top layer (bar.py). The bubbles stand on the bar, above its
right end, the newest nearest the bar. A bubble says which module it is
from, with its tile, or the program's own name; its summary and its text,
plain; a button to close it, and the program's other actions as buttons. A
click on it does the notice's default action.

The bell, at the bar's right end, is a button that opens the last notices
that came, gone or not, so that a child who missed one, or an adult asked
why something did not work, reads it again; it counts the ones that came
since the child last looked, and *Clear* empties it.
"""

import logging
import time

import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gio, GLib, Gtk, Pango  # noqa: E402

from kidux import modules as kidux_modules, paths, scroll  # noqa: E402

from . import notices, words  # noqa: E402
from .bar import HEIGHT as BAR_HEIGHT  # noqa: E402

log = logging.getLogger("kidux.launcher")

#: How wide a bubble is, how far from the screen's right edge, and how far
#: above the bar, which keeps the bottom HEIGHT pixels of the screen (bar.py).
WIDTH = 380
MARGIN = 16
ABOVE_BAR = BAR_HEIGHT + 8
#: The lines of a notice's text shown before it is cut short.
LINES = 6
#: How tall the bell's list may grow before it scrolls.
HISTORY_HEIGHT = 440
#: Who a notice of the launcher's own is from, shown with the mascot.
KIDUX = "Kidux"

CSS = """
window.kidux-bubbles { background-color: transparent; }
.kidux-bubble { background-color: #fdf6f0; color: #3b2f2a; border-radius: 18px;
  padding: 12px 14px; border: 2px solid #e5d3bf;
  box-shadow: 0 3px 8px alpha(#3b2f2a, 0.22); margin: 6px 10px; }
.kidux-bubble-from { font-size: 16px; font-weight: bold; color: #7a6a60; }
.kidux-bubble-when { font-size: 14px; color: #7a6a60; }
.kidux-bubble-summary { font-size: 19px; font-weight: bold; }
.kidux-bubble-body { font-size: 17px; }
.kidux-bubble button { min-height: 40px; min-width: 40px; border-radius: 12px;
  padding: 0 12px; font-size: 16px; }
.kidux-bubble button.kidux-bubble-close { background-color: transparent; padding: 0; }
window.kidux-bar menubutton.kidux-bell > button { padding: 0 10px; min-height: 44px; }
.kidux-bell-count { background-color: #e2703a; color: #fdf6f0; border-radius: 11px;
  padding: 1px 7px; font-size: 14px; font-weight: bold; }
.kidux-history { padding: 8px; }
.kidux-history-title { font-size: 18px; font-weight: bold; }
.kidux-history .kidux-bubble { margin: 4px 0; box-shadow: none; }
.kidux-history-empty { color: #7a6a60; padding: 12px 8px; }
"""


def version() -> str:
    """The launcher's version, which the server says it is."""
    try:
        from importlib.metadata import version as installed
        return installed("kidux-launcher")
    except Exception:  # noqa: BLE001 — a version is not worth a failed answer
        return ""


def clock_of(when: float) -> str:
    """When a notice came, as a clock reads it, in the session's locale."""
    return time.strftime("%H:%M", time.localtime(when))


class Bubbles:
    """The bubbles' window, the bar's bell, and the notices' server on the
    session bus."""

    def __init__(self, application: Gtk.Application, shell, *, translate, drawing,
                 language: str) -> None:
        self._ = translate
        #: Draws an SVG at a size, as the bar draws the mascot (view.drawing).
        self._drawing = drawing
        self._language = language
        self._bubbles: dict[int, Gtk.Widget] = {}
        self._timers: dict[int, int] = {}
        #: Whether the bell's history is open, which shows every notice:
        #: the bubbles, drawn above the bar and its popovers, step aside.
        self._history_open = False
        self._connection = None
        self.notices = notices.Notices(show=self._show, hide=self._hide,
                                       closed=self._send_closed, invoked=self._send_invoked,
                                       history_changed=self._history_changed)

        window = Gtk.Window(application=application, title="Kidux", decorated=False)
        window.add_css_class("kidux")
        window.add_css_class("kidux-bubbles")
        shell.init_for_window(window)
        shell.set_namespace(window, "kidux-bubbles")
        shell.set_layer(window, shell.Layer.OVERLAY)
        for edge, margin in ((shell.Edge.BOTTOM, ABOVE_BAR), (shell.Edge.RIGHT, MARGIN)):
            shell.set_anchor(window, edge, True)
            shell.set_margin(window, edge, margin)
        # Placed by its own margin above the bar, not moved by the bar's
        # exclusive zone: so it stands where it is told whatever else claims
        # an edge.
        shell.set_exclusive_zone(window, -1)
        shell.set_keyboard_mode(window, shell.KeyboardMode.NONE)
        self._stack = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0,
                              valign=Gtk.Align.END)
        self._stack.set_size_request(WIDTH, -1)
        window.set_child(self._stack)
        self._window = window

        self.bell = self._make_bell()

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

    # --- what a notice looks like ---------------------------------------------

    def _from(self, notice) -> tuple[str, str]:
        """Who it is from: the module's name and tile, or the program's name."""
        module = kidux_modules.read(notice.module) if notice.module else None
        if module is not None:
            return kidux_modules.name_in(module, self._language), module.icon
        if notice.app_name == KIDUX:
            return KIDUX, str(paths.MASCOT)
        return notice.app_name, ""

    def _card(self, notice, *, closable: bool, when: bool) -> Gtk.Box:
        """A notice drawn: who it is from and, when `closable`, its close
        button, or, when `when`, the time it came; then its summary and its
        text."""
        name, icon = self._from(notice)
        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        card.add_css_class("kidux-bubble")

        top = Gtk.Box(spacing=8)
        if name == KIDUX and icon:
            top.append(self._drawing(icon, 28, 28))
        elif icon:
            image = Gtk.Image.new_from_gicon(Gio.FileIcon.new(Gio.File.new_for_path(icon)))
            image.set_pixel_size(28)
            top.append(image)
        sender = Gtk.Label(label=name, xalign=0, hexpand=True, ellipsize=Pango.EllipsizeMode.END)
        sender.add_css_class("kidux-bubble-from")
        top.append(sender)
        if when:
            came = Gtk.Label(label=clock_of(notice.when))
            came.add_css_class("kidux-bubble-when")
            top.append(came)
        if closable:
            close = Gtk.Button(icon_name="window-close-symbolic", tooltip_text=self._(words.CLOSE),
                               can_focus=False)
            close.add_css_class("kidux-bubble-close")
            close.connect("clicked",
                          lambda _b, n=notice.id: self.notices.close(n, notices.DISMISSED))
            top.append(close)
        card.append(top)

        for text, css, lines in ((notice.summary, "kidux-bubble-summary", 2),
                                 (notice.body, "kidux-bubble-body", LINES)):
            if text:
                label = Gtk.Label(label=text, xalign=0, wrap=True, lines=lines,
                                  ellipsize=Pango.EllipsizeMode.END, max_width_chars=34,
                                  use_markup=False)
                label.add_css_class(css)
                card.append(label)
        return card

    # --- the bubbles --------------------------------------------------------

    def tell(self, summary: str, body: str = "", *, replaces: int = 0) -> int:
        """A notice of the launcher's own, from Kidux, which stays until it
        is closed, in place of the one numbered `replaces` when that is
        still shown: its number."""
        hints = {"urgency": notices.CRITICAL}
        return self.notices.notify("", KIDUX, replaces, summary, body, [], hints, -1).id

    def _show(self, notice) -> None:
        log.info("notice %d from %s%s", notice.id, notice.module or notice.app_name or "?",
                 ", staying" if notice.stays else "")
        bubble = self._card(notice, closable=True, when=False)

        if notice.buttons:
            row = Gtk.Box(spacing=8, halign=Gtk.Align.END)
            for key, label in notice.buttons:
                button = Gtk.Button(label=label, can_focus=False)
                button.connect("clicked", lambda _b, n=notice.id, k=key: self.notices.act(n, k))
                row.append(button)
            bubble.append(row)

        if any(key == notices.DEFAULT for key, _label in notice.actions):
            click = Gtk.GestureClick()
            click.connect("released",
                          lambda *_a, n=notice.id: self.notices.act(n, notices.DEFAULT))
            bubble.add_controller(click)

        self._bubbles[notice.id] = bubble
        # The newest nearest the bar, which the stack stands on.
        self._stack.append(bubble)
        self._window.set_visible(not self._history_open)
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

    # --- the bell -----------------------------------------------------------

    def _make_bell(self) -> Gtk.MenuButton:
        """The bar's bell: the icon, the count of unseen notices beside it
        while there are any, and the history in a popover above it."""
        box = Gtk.Box(spacing=6, halign=Gtk.Align.CENTER)
        icon = Gtk.Image.new_from_icon_name("preferences-system-notifications-symbolic")
        icon.set_pixel_size(24)
        box.append(icon)
        self._count = Gtk.Label(visible=False)
        self._count.add_css_class("kidux-bell-count")
        box.append(self._count)

        self._history = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self._history.add_css_class("kidux-history")
        self._history.set_size_request(WIDTH, -1)
        title_row = Gtk.Box(spacing=8)
        title = Gtk.Label(label=self._(words.NOTICES), xalign=0, hexpand=True)
        title.add_css_class("kidux-history-title")
        title_row.append(title)
        self._clear = Gtk.Button(label=self._(words.CLEAR_NOTICES), can_focus=False)
        self._clear.add_css_class("kidux-quiet")
        self._clear.connect("clicked", lambda _b: self.notices.clear())
        title_row.append(self._clear)
        self._history.append(title_row)
        self._entries = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        area = scroll.scroller(self._entries, horizontal=False, expand=False)
        area.set_propagate_natural_height(True)
        area.set_max_content_height(HISTORY_HEIGHT)
        self._history.append(area)

        popover = Gtk.Popover(child=self._history, position=Gtk.PositionType.TOP)
        popover.add_css_class("kidux")
        popover.connect("show", self._history_opened)
        popover.connect("hide", self._history_closed)
        bell = Gtk.MenuButton(child=box, can_focus=False, popover=popover,
                              tooltip_text=self._(words.NOTICES))
        bell.add_css_class("kidux-bell")
        bell.update_property([Gtk.AccessibleProperty.LABEL], [self._(words.NOTICES)])
        self._fill_history()
        return bell

    def _history_opened(self, _popover) -> None:
        log.info("notices: the bell opened, %d kept", len(self.notices.history))
        self._history_open = True
        self._window.set_visible(False)
        self.notices.seen()

    def _history_closed(self, _popover) -> None:
        self._history_open = False
        self._window.set_visible(bool(self._bubbles))

    def _history_changed(self) -> None:
        unseen = self.notices.unseen
        self._count.set_label(str(unseen))
        self._count.set_visible(unseen > 0)
        self._fill_history()

    def _fill_history(self) -> None:
        """The history's list drawn afresh: the newest first, a word when
        there is none."""
        while (child := self._entries.get_first_child()) is not None:
            self._entries.remove(child)
        kept = self.notices.history
        self._clear.set_sensitive(bool(kept))
        if not kept:
            empty = Gtk.Label(label=self._(words.NO_NOTICES), xalign=0)
            empty.add_css_class("kidux-history-empty")
            self._entries.append(empty)
            return
        for notice in reversed(kept):
            self._entries.append(self._card(notice, closable=False, when=True))
