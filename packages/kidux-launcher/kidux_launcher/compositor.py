"""The compositor, as the launcher sees it: labwc, through the foreign-toplevel protocol (D58).

The launcher owns the policy of the child's desktop (`desk.py`); labwc does
what it is told and what its configuration says. This module is the one
place that speaks to it: `wlr-foreign-toplevel-management-unstable-v1`, the
protocol taskbars use, through `python3-pywayland`, whose Python for the
protocol is made from its XML when the package is built
(protocol/generate.py). It lists every window with its `app_id`, title,
states and parent, and activates, minimises, maximises, takes out of
fullscreen and asks to close any of them. `Toplevels`, the list the
protocol's events build, is pure, so that its test is the specification;
`Labwc` feeds it from the compositor's socket, read in GLib's main loop.

Keys of labwc's configuration reach the launcher as signals, since labwc
has no socket of its own: Alt+F4, `pkill -USR2 -f "^/usr/bin/python3
/usr/libexec/kidux-launcher"`, is the bar's Close (D45); on the desk,
Super, the same with `-USR1`, is the bar's Home (D57).
"""

import logging
import signal
import struct
from dataclasses import dataclass, field, replace

log = logging.getLogger("kidux.launcher")

#: The launcher's own window, which is home.
LAUNCHER_APP_ID = "org.kidux.Launcher"

#: The protocol's states, by the number it sends each as.
STATES = {0: "maximized", 1: "minimized", 2: "activated", 3: "fullscreen"}


@dataclass(frozen=True)
class Toplevel:
    """A window, as the compositor lists it."""
    id: int
    app_id: str = ""
    title: str = ""
    maximized: bool = False
    minimized: bool = False
    activated: bool = False
    fullscreen: bool = False
    #: The window it is a dialog of, when it is one.
    parent: int | None = None

    def flags(self) -> str:
        """Its states as letters, for the log the session tests read: a
        activated, m maximised, i minimised, f fullscreen, d a dialog."""
        return "".join(letter for letter, on in (
            ("a", self.activated), ("m", self.maximized), ("i", self.minimized),
            ("f", self.fullscreen), ("d", self.parent is not None)) if on) or "-"


def states_of(raw: bytes) -> dict[str, bool]:
    """The protocol's array of states, as Toplevel's fields."""
    values = struct.unpack(f"={len(raw) // 4}I", raw[: len(raw) // 4 * 4])
    return {name: number in values for number, name in STATES.items()}


@dataclass
class _Pending:
    current: Toplevel
    next: dict = field(default_factory=dict)


class Toplevels:
    """The windows the protocol has announced, as its events leave them.

    A handle's changes arrive one event at a time and hold from its `done`;
    until then the window keeps what it had. Each handle, whatever object
    the protocol library gives it as, is known by a number of the
    launcher's own, which never repeats.
    """

    def __init__(self) -> None:
        self._handles: dict[object, int] = {}
        self._windows: dict[int, _Pending] = {}
        self._announced: set[int] = set()
        self._next = 1

    def id_of(self, handle) -> int | None:
        return self._handles.get(handle)

    def handle_of(self, window: int):
        return next((h for h, i in self._handles.items() if i == window), None)

    def added(self, handle) -> int:
        number = self._next
        self._next += 1
        self._handles[handle] = number
        self._windows[number] = _Pending(Toplevel(id=number))
        return number

    def changed(self, handle, **fields) -> None:
        number = self._handles.get(handle)
        if number is not None:
            self._windows[number].next.update(fields)

    def parent(self, handle, parent_handle) -> None:
        self.changed(handle, parent=self._handles.get(parent_handle) if parent_handle else None)

    def done(self, handle) -> bool:
        """The changes of a handle hold. True when anything changed."""
        number = self._handles.get(handle)
        if number is None:
            return False
        pending = self._windows[number]
        before = pending.current
        pending.current = replace(before, **pending.next)
        pending.next = {}
        new = number not in self._announced
        self._announced.add(number)
        return new or pending.current != before

    def closed(self, handle) -> bool:
        number = self._handles.pop(handle, None)
        if number is None:
            return False
        self._windows.pop(number, None)
        was_announced = number in self._announced
        self._announced.discard(number)
        return was_announced

    def all(self) -> list[Toplevel]:
        """Every window announced and not closed, in the order they came."""
        return [self._windows[n].current for n in sorted(self._announced)
                if n in self._windows]


class Labwc:
    """labwc itself, on the socket in `WAYLAND_DISPLAY`. The protocol's
    events are read in GLib's main loop, when the socket has something:
    no thread, so that the requests the desk makes and the events it reads
    never meet halfway."""

    def __init__(self) -> None:
        from pywayland.client import Display
        from pywayland.protocol.wayland import WlSeat

        from .protocol.wlr_foreign_toplevel_management_unstable_v1 import (
            ZwlrForeignToplevelManagerV1,
        )

        self.windows_now = Toplevels()
        self._changed = False
        self._display = Display()
        self._display.connect()
        registry = self._display.get_registry()
        found: dict = {}

        def announced(registry, name, interface, version):
            if interface == "zwlr_foreign_toplevel_manager_v1" and "manager" not in found:
                found["manager"] = registry.bind(name, ZwlrForeignToplevelManagerV1,
                                                 min(version, 3))
            elif interface == "wl_seat" and "seat" not in found:
                found["seat"] = registry.bind(name, WlSeat, 1)

        registry.dispatcher["global"] = announced
        self._display.roundtrip()
        if "manager" not in found:
            raise RuntimeError("the compositor offers no foreign-toplevel manager")
        self._seat = found.get("seat")
        found["manager"].dispatcher["toplevel"] = self._toplevel
        self._registry = registry
        self._manager = found["manager"]
        self._display.roundtrip()
        self._display.roundtrip()
        self._changed = False

    def _toplevel(self, _manager, handle) -> None:
        windows = self.windows_now
        windows.added(handle)

        def title(h, text):
            windows.changed(h, title=text)

        def app_id(h, text):
            windows.changed(h, app_id=text)

        def state(h, array):
            windows.changed(h, **states_of(bytes(array)))

        def parent(h, other):
            windows.parent(h, other)

        def done(h):
            if windows.done(h):
                self._changed = True

        def closed(h):
            if windows.closed(h):
                self._changed = True

        handle.dispatcher["title"] = title
        handle.dispatcher["app_id"] = app_id
        handle.dispatcher["state"] = state
        handle.dispatcher["parent"] = parent
        handle.dispatcher["done"] = done
        handle.dispatcher["closed"] = closed

    def toplevels(self) -> list[Toplevel]:
        return self.windows_now.all()

    def on_change(self, handler, on_close=None, on_home=None, on_switch=None) -> None:
        """`handler()` in the main loop whenever windows change; several
        changes read at once are one call. `on_close()` there too when the
        close key is pressed, `on_home()` when the home key is, and
        `on_switch(step)` for Alt+Tab (1) and Alt+Shift+Tab (-1)."""
        from gi.repository import GLib

        def readable(_fd, condition) -> bool:
            if condition & (GLib.IOCondition.HUP | GLib.IOCondition.ERR):
                log.info("the compositor's socket closed: the session is ending")
                return GLib.SOURCE_REMOVE
            try:
                self._display.dispatch(block=True)
                self._display.flush()
            except Exception:  # noqa: BLE001 — the compositor is gone
                log.info("the compositor's events stopped", exc_info=True)
                return GLib.SOURCE_REMOVE
            if self._changed:
                self._changed = False
                handler()
            return GLib.SOURCE_CONTINUE

        GLib.unix_fd_add_full(GLib.PRIORITY_DEFAULT, self._display.get_fd(),
                              GLib.IOCondition.IN | GLib.IOCondition.HUP | GLib.IOCondition.ERR,
                              readable)
        if on_close is not None:
            GLib.unix_signal_add(GLib.PRIORITY_DEFAULT, signal.SIGUSR2,
                                 lambda: on_close() or GLib.SOURCE_CONTINUE)
        if on_home is not None:
            GLib.unix_signal_add(GLib.PRIORITY_DEFAULT, signal.SIGUSR1,
                                 lambda: on_home() or GLib.SOURCE_CONTINUE)
        if on_switch is not None:
            # Alt+Tab and Alt+Shift+Tab (D64). GLib watches only the usual
            # signals, so these two are Python's, which PyGObject's main
            # loop wakes for; the step runs in the loop, never in the handler.
            for number, step in ((signal.SIGRTMIN + 1, 1), (signal.SIGRTMIN + 2, -1)):
                signal.signal(number, lambda _signal, _frame, step=step:
                              GLib.idle_add(lambda: on_switch(step) and False))

    def _request(self, window: int, name: str, *args) -> None:
        handle = self.windows_now.handle_of(window)
        if handle is None:
            return
        getattr(handle, name)(*args)
        self._display.flush()

    def activate(self, window: int) -> None:
        """Bring a window forward and give it the keyboard, back from
        minimised if it was."""
        if self._seat is not None:
            self._request(window, "activate", self._seat)

    def close(self, window: int) -> None:
        """The close request a window's close button sends: the program
        decides what to do with it."""
        self._request(window, "close")

    def minimize(self, window: int) -> None:
        self._request(window, "set_minimized")

    def maximize(self, window: int) -> None:
        self._request(window, "set_maximized")

    def unfullscreen(self, window: int) -> None:
        self._request(window, "unset_fullscreen")


class NoCompositor:
    """What the launcher uses when the compositor cannot be reached: no
    windows, and modules that open over the launcher as best they can."""

    def toplevels(self) -> list[Toplevel]:
        return []

    def on_change(self, handler, on_close=None, on_home=None, on_switch=None) -> None:
        pass

    def activate(self, window: int) -> None:
        pass

    def close(self, window: int) -> None:
        pass

    def minimize(self, window: int) -> None:
        pass

    def maximize(self, window: int) -> None:
        pass

    def unfullscreen(self, window: int) -> None:
        pass
