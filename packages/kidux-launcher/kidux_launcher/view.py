"""GTK 4: the child's screen (launcher.md section 2).

Top: the child's picture and name, the clock, the time left. Middle: the
modules enabled for them, or the mascot saying there is nothing yet.
Bottom: Lock, Kidux's logo, Log out and Turn off. Everything it knows about
time comes from `model.py`; everything it asks goes through `daemon.py`; a
module is started with the command `launch.py` makes, and its windows
known and shown by `desk.py`; the bar along the bottom is `bar.py`.
"""

import logging
import os
import pwd
import shlex
import time

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gdk, Gio, GLib, Gtk, Pango  # noqa: E402

from kidux import avatars, i18n, paths, scroll, vocabulary  # noqa: E402
from kidux import hardware  # noqa: E402
from kidux import modules as kidux_modules  # noqa: E402

from . import launch, words  # noqa: E402
from .bar import Bar  # noqa: E402
from .desk import CLOSE_SECONDS, HOME  # noqa: E402
from .daemon import DaemonError  # noqa: E402
from .lid import Lid  # noqa: E402
from .model import Model  # noqa: E402
from .timeleft import TimeLeft  # noqa: E402
from kidux import screen as kidux_screen  # noqa: E402
from kidux.corner import CSS as CORNER_CSS, Corner  # noqa: E402

log = logging.getLogger("kidux.launcher")

#: How often the daemon is asked for the time left; the label moves every
#: fifteen seconds in between, counted here.
ASK_SECONDS = 30
#: Tiles to a row: six fit 1280 pixels; a roomy screen's room is space,
#: and takes eight (D49, D53).
TILES_PER_ROW = {False: 6, True: 8}
TICK_SECONDS = 15
#: How the keys are written in the bar's tooltips (D61, D64): the key that
#: goes home, the one that closes, and the one that goes round the windows.
KEYS = {"home": hardware.super_key(), "close": f"Alt+{hardware.function_key('F4')}",
        "next": "Alt+Tab"}

#: The least time between two steps of Alt+Tab's round, in milliseconds:
#: a held Tab repeats faster than a child reads the bar.
SWITCH_STEP_MS = 120
#: A module that ends sooner than this, with a status other than 0, did not
#: open: the program is missing, or systemd-run refused.
FAILED_START_SECONDS = 2

LOGO = str(paths.LOGO)
MASCOT = str(paths.MASCOT)

CSS = """
window.kidux { background-color: #fff6e9; color: #3b2f2a;
  font-family: "Andika", sans-serif; font-size: 20px; }
.kidux-name { font-size: 24px; font-weight: bold; }
.kidux-clock { font-size: 40px; font-weight: bold; color: #7a6a60; }
.kidux-time { font-size: 22px; font-weight: bold; }
.kidux-hint { font-size: 13px; opacity: 0.7; margin-left: 2px; }
.kidux-title { font-size: 30px; font-weight: bold; }
.kidux-notice { font-size: 20px; background-color: #ffe2c6; color: #7a3310;
  border-radius: 14px; padding: 10px 20px; }
window.kidux button { min-height: 56px; min-width: 56px; border-radius: 18px;
  padding: 0 20px; font-size: 18px; }
window.kidux button.kidux-quiet { background-color: transparent; color: #7a6a60; }
window.kidux flowboxchild.kidux-tile { padding: 16px; border-radius: 24px;
  background-color: #ffffff; }
window.kidux flowboxchild.kidux-tile:hover { background-color: #ffe9cf; }
window.kidux flowboxchild.kidux-tile:focus-visible { outline: 4px solid #3b2f2a;
  outline-offset: 2px; }
.kidux-tile-name { font-size: 20px; font-weight: bold; }
window.kidux-bar { background-color: #f2e2cc; font-size: 18px; }
window.kidux-bar button { min-height: 44px; min-width: 44px; border-radius: 14px;
  padding: 0 14px; margin: 6px 0; font-size: 18px; }
window.kidux-bar button.kidux-current { background-color: #3b2f2a; color: #fff6e9; }
window.kidux-bar button.kidux-minimised { opacity: 0.55; }
window.kidux-bar button.kidux-arrow { min-width: 36px; padding: 0 4px; }
window.kidux-bar button.kidux-next { box-shadow: inset 0 0 0 3px #3584e4;
  background-color: #dbe8fb; color: #3b2f2a; }
window.kidux-bar menubutton.kidux-time > button { padding: 2px 10px; min-height: 44px; }
window.kidux-bar .kidux-notice { padding: 4px 14px; font-size: 18px; }
"""


def child_name() -> str:
    """The name the child was given, from their own account."""
    entry = pwd.getpwuid(os.getuid())
    return entry.pw_gecos.split(",")[0] or entry.pw_name


def install_style(display: Gdk.Display) -> None:
    provider = Gtk.CssProvider()
    provider.load_from_string(CSS + CORNER_CSS + scroll.CSS)
    Gtk.StyleContext.add_provider_for_display(display, provider,
                                              Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)


def svg(path: str, size: int) -> Gtk.Image:
    image = Gtk.Image.new_from_gicon(Gio.FileIcon.new(Gio.File.new_for_path(path)))
    image.set_pixel_size(size)
    return image


def drawing(path: str, width: int, height: int) -> Gtk.Widget:
    """An SVG drawn at exactly width by height, sharp at any display scale.

    Drawn with librsvg into the area GTK gives it, rather than loaded as a
    picture: a picture grows to the size its file says, whatever is asked."""
    try:
        gi.require_version("Rsvg", "2.0")
        from gi.repository import Rsvg
        handle = Rsvg.Handle.new_from_file(path)
    except (ValueError, ImportError, GLib.Error):
        return Gtk.Box()
    area = Gtk.DrawingArea(content_width=width, content_height=height,
                           halign=Gtk.Align.CENTER, valign=Gtk.Align.CENTER)

    def draw(_area, cairo, w, h):
        viewport = Rsvg.Rectangle()
        viewport.x, viewport.y, viewport.width, viewport.height = 0, 0, w, h
        try:
            handle.render_document(cairo, viewport)
        except Exception:  # noqa: BLE001 — a missing picture is not worth a crash
            log.exception("could not draw %s", path)

    area.set_draw_func(draw)
    return area


class Launcher:
    def __init__(self, window: Gtk.Window, daemon, desk, *, on_log_out) -> None:
        self._window = window
        self._daemon = daemon
        self._desk = desk
        self._bar = None
        self._last_step = 0
        self._on_log_out = on_log_out
        self._model = Model()
        self._language = os.environ.get("LANG", "")
        #: Whether this child's modules open in windows (D46), as the
        #: sign-in screen started the session.
        self._windows = os.environ.get("KIDUX_WINDOWS") == "1"
        self._t = i18n.translations(self._language)
        self._modules: list = []
        #: A sentence over the tiles, after a module that did not open.
        self._problem: str | None = None
        window.add_css_class("kidux")
        self._build()
        self.refresh()
        daemon.subscribe(warning=self._warned, changed=self.refresh)
        GLib.timeout_add_seconds(ASK_SECONDS, self._ask)
        GLib.timeout_add_seconds(TICK_SECONDS, self._tick)
        self._lid = None
        log.info("keys: home=%s close=%s next=%s", KEYS["home"], KEYS["close"], KEYS["next"])

    def present(self, application: Gtk.Application, shell) -> None:
        """Show the window, which labwc maximises under every other, and the
        bar along the bottom when there is layer-shell to draw it with (bar.py);
        then the modules already open, if any outlived the launcher before
        this one."""
        self._window.present()
        if shell is not None:
            self._bar = Bar(application, shell, translate=self._, drawing=drawing,
                            mascot=MASCOT, on_home=self._desk.home, on_module=self._desk.show,
                            on_lock=self._lock, on_dismiss=self._dismiss,
                            on_close=self.close_module, on_keep=self._desk.keep,
                            on_end=self._desk.end_anyway, on_window=self._desk.raise_window,
                            keys=KEYS)
            self._bar.present()
            # The lid, under labwc, which powers the panel off and on, and
            # locks the session when it closes (lid.py, D67).
            devices = hardware.lid_devices()
            if devices:
                self._lid = Lid(devices, on_closed=self._lid_closed)
        else:
            log.warning("no layer-shell: the launcher runs without its bar")
        self._desk.settle()
        self.desk_changed()

    def desk_changed(self) -> None:
        """The open modules, or the one on screen, changed: the bar follows."""
        if self._bar is None:
            return
        opened, current, name = [], None, None
        for module_id in self._desk.modules:
            module = kidux_modules.read(module_id)
            if module is None:
                continue
            opened.append(module)
            if module_id == self._desk.current:
                current = module_id
                name = kidux_modules.name_in(module, self._language)
        if self._windows:
            windows = []
            for top, module_id in self._desk.windows:
                module = kidux_modules.read(module_id)
                if module is not None and top.parent is None:
                    windows.append((module, top.id, top.title, top.activated, top.minimized))
            self._bar.show_windows(windows, current is None, self._language,
                                   following=self._desk.next_in_bar())
        else:
            self._bar.show_modules(opened, current, self._language,
                                   following=self._desk.next_in_bar())
        question = None
        if current is not None and self._desk.question == current:
            question = self._(words.NOT_CLOSED).format(name=name)
        self._bar.show_closing(name, question)
        self._draw_time()

    def close_module(self) -> None:
        """Close, on the bar or its key (D45): the module on screen is asked,
        and the bar asks the child if it is still open `CLOSE_SECONDS` later."""
        if self._desk.close(time.monotonic()) == "asked":
            GLib.timeout_add(CLOSE_SECONDS * 1000 + 200, self._closing_overdue)

    def _closing_overdue(self) -> bool:
        self._desk.overdue(time.monotonic())
        return GLib.SOURCE_REMOVE

    def _(self, message: str) -> str:
        return self._t.gettext(message)

    def _roomy(self) -> bool:
        return self._window.has_css_class("kidux-roomy")

    # --- the parts that stay --------------------------------------------------

    def _build(self) -> None:
        # The bars above and below stay small: the room between them is the
        # modules', and every screen is meant to fit 1280x800 whole.
        page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        for side in ("top", "bottom", "start", "end"):
            getattr(page, f"set_margin_{side}")(24)

        top = Gtk.CenterBox()
        who = Gtk.Box(spacing=16)
        avatar = avatars.resolve(os.environ.get("KIDUX_AVATAR"))
        who.append(svg(str(avatars.path_for(avatar)), 64))
        # A name may be 64 characters: cut with an ellipsis, so that the
        # clock and the corner keep their room.
        name = Gtk.Label(label=child_name(), ellipsize=Pango.EllipsizeMode.END,
                         max_width_chars=24)
        name.add_css_class("kidux-name")
        who.append(name)
        top.set_start_widget(who)
        self._clock = Gtk.Label()
        self._clock.add_css_class("kidux-clock")
        top.set_center_widget(self._clock)
        self._time = TimeLeft()
        corner = Gtk.Box(spacing=16, valign=Gtk.Align.CENTER)
        corner.append(self._time.widget)
        # The corner: battery, brightness, keyboard light, sound (kidux.corner),
        # compact on a narrow screen, so that the clock keeps its room.
        width, _height = kidux_screen.logical_size(self._window.get_display())
        self._corner = Corner(self._, compact=kidux_screen.compact_corner(width))
        corner.append(self._corner.widget)
        top.set_end_widget(corner)
        page.append(top)

        self._banner = Gtk.Revealer()
        self._warning = Gtk.Button(halign=Gtk.Align.CENTER)
        self._warning.add_css_class("kidux-notice")
        self._warning.connect("clicked", lambda _b: self._dismiss())
        self._banner.set_child(self._warning)
        page.append(self._banner)

        self._middle = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20,
                               valign=Gtk.Align.CENTER, halign=Gtk.Align.CENTER, vexpand=True)
        # More modules than the screen holds scroll, and show it (D63); the
        # bars stay put.
        self._overflowed: set[str] = set()
        middle_area = scroll.scroller(self._middle)
        scroll.watch(middle_area, self._check_fits)
        page.append(middle_area)

        self._bottom = Gtk.CenterBox()
        page.append(self._bottom)
        self._window.set_content(page)
        self._show_home()

    def _button(self, message: str, on_click, *, icon: str | None = None,
                suggested=False, quiet=False, destructive=False) -> Gtk.Button:
        box = Gtk.Box(spacing=12, halign=Gtk.Align.CENTER)
        if icon:
            image = Gtk.Image.new_from_icon_name(icon)
            image.set_pixel_size(28)
            box.append(image)
        box.append(Gtk.Label(label=self._(message)))
        button = Gtk.Button(child=box)
        for flag, css in ((suggested, "suggested-action"), (quiet, "kidux-quiet"),
                          (destructive, "destructive-action")):
            if flag:
                button.add_css_class(css)
        button.connect("clicked", lambda _b: on_click())
        return button

    # --- Alt+Tab going round (D64, D66) ------------------------------------------

    def switch(self, step: int) -> None:
        """Alt+Tab (step 1) or Alt+Shift+Tab (-1), from labwc: a step round
        the windows, in the order they were last in use; the bar lights the
        one it points at and follows Alt until it is let go. The round is
        the bar's buttons in the bar's order, Home not among them (D66)."""
        # Tab held repeats: at most a step every SWITCH_STEP_MS, as fast as
        # a child can read the bar, and no faster than the launcher can
        # draw it.
        now = GLib.get_monotonic_time() // 1000
        if now - self._last_step < SWITCH_STEP_MS:
            return
        self._last_step = now
        target = self._desk.switch(step)
        if target is None:
            log.info("switch: nowhere")
            return
        whose = self._desk.whose(target)
        log.info("switch: %s", whose)
        if self._bar is None:
            self._switched()
            return
        self._bar.point_at(target if self._windows else whose)
        self._bar.follow_alt(self._switched)

    def _switched(self) -> None:
        """Alt let go: to the window the round points at."""
        if self._bar is not None:
            self._bar.stop_following()
            self._bar.point_at(None)
        target = self._desk.switch_done()
        if target is not None:
            log.info("switched: %s", self._desk.whose(target))

    def _check_fits(self, way: str, needed: int, shown: int) -> None:
        """Say so in the log, once each way, "tall" or "wide", when the
        child's screen has to scroll; the session tests read it."""
        if way not in self._overflowed:
            self._overflowed.add(way)
            log.warning("the child's screen does not fit: %d pixels %s, %d shown",
                        needed, way, shown)

    def _clear(self) -> None:
        while (child := self._middle.get_first_child()) is not None:
            self._middle.remove(child)

    # --- home -----------------------------------------------------------------

    def _show_home(self) -> None:
        self._clear()
        if self._problem:
            notice = Gtk.Label(label=self._(self._problem), wrap=True,
                               justify=Gtk.Justification.CENTER)
            notice.add_css_class("kidux-notice")
            self._middle.append(notice)
        if self._modules:
            self._middle.append(self._tiles())
        else:
            self._middle.append(drawing(MASCOT, 128, 128))
            empty = Gtk.Label(label=self._(words.NOTHING_YET), wrap=True,
                              justify=Gtk.Justification.CENTER)
            empty.set_max_width_chars(36)
            self._middle.append(empty)

        lock = self._button(vocabulary.LOCK, self._lock, icon="system-lock-screen-symbolic",
                            suggested=True)
        self._bottom.set_start_widget(lock)
        self._bottom.set_center_widget(drawing(LOGO, 100, 40))
        right = Gtk.Box(spacing=16)
        right.append(self._button(vocabulary.LOG_OUT, self._ask_log_out,
                                  icon="system-log-out-symbolic", quiet=True))
        right.append(self._button(vocabulary.TURN_OFF, self._lock,
                                  icon="system-shutdown-symbolic", quiet=True))
        self._bottom.set_end_widget(right)
        # Once the new bar is in place: grabbed at once, while the Lock it
        # replaces is still being taken away, the focus does not hold, and
        # the first key a child presses goes somewhere else.
        GLib.idle_add(self._focus, lock)

    def _focus(self, widget: Gtk.Widget) -> bool:
        widget.grab_focus()
        return GLib.SOURCE_REMOVE

    def _ask_log_out(self) -> None:
        self._clear()
        question = Gtk.Label(label=self._(words.SAVED_YOUR_WORK))
        question.add_css_class("kidux-title")
        self._middle.append(question)
        row = Gtk.Box(spacing=16, halign=Gtk.Align.CENTER)
        cancel = self._button(vocabulary.CANCEL, self._show_home, icon="window-close-symbolic")
        row.append(cancel)
        row.append(self._button(vocabulary.LOG_OUT, self._on_log_out,
                                icon="system-log-out-symbolic", destructive=True))
        self._middle.append(row)
        cancel.grab_focus()

    def _tiles(self) -> Gtk.FlowBox:
        """One tile per module: its picture over its name in the child's
        language, six to a row. Tab reaches the tiles as one stop, the arrows
        move between them, and Enter, a tap or a click opens one."""
        # No more places in a row than there are tiles, so that a few tiles
        # sit in the middle rather than in the first places of a row of six.
        grid = Gtk.FlowBox(selection_mode=Gtk.SelectionMode.NONE, homogeneous=True,
                           min_children_per_line=1,
                           max_children_per_line=min(TILES_PER_ROW[self._roomy()],
                                                     max(1, len(self._modules))),
                           column_spacing=20, row_spacing=20, halign=Gtk.Align.CENTER,
                           activate_on_single_click=True)
        language = os.environ.get("LANG", "")
        for module in self._modules:
            tile = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
            tile.append(drawing(module.icon or MASCOT, 128, 128))
            name = Gtk.Label(label=kidux_modules.name_in(module, language), wrap=True,
                             justify=Gtk.Justification.CENTER, max_width_chars=12)
            name.add_css_class("kidux-tile-name")
            tile.append(name)
            cell = Gtk.FlowBoxChild(child=tile)
            cell.add_css_class("kidux-tile")
            grid.append(cell)
        grid.connect("child-activated",
                     lambda _grid, cell: self._open(self._modules[cell.get_index()]))
        return grid

    def _open(self, module) -> None:
        """A tile: the module's window if it is open, otherwise the module
        started, and its window shown when it comes."""
        if self._problem:
            self._problem = None
            self._show_home()
        self._desk.open(module.id, lambda: self._start(module))

    def _start(self, module) -> bool:
        """Start a module in a scope of its own; False if it could not be."""
        home = os.path.expanduser("~")
        # The manifest as it is now, not as it was when the tile was drawn: a
        # module apt replaced meanwhile starts as its new manifest says.
        module = kidux_modules.read(module.id) or module
        if module.id in launch.running():
            # Still starting from before this launcher, with no window yet.
            log.info("%s is already running", module.id)
            return False
        try:
            argv = launch.command(module, home)
            for directory in launch.directories(home, module.id):
                os.makedirs(directory, mode=0o700, exist_ok=True)
                os.chmod(directory, 0o700)
            launch.share_user_dirs(home, module.id)
            # stdout and stderr are inherited: a module's complaints go to
            # the session's journal. The layer-shell library the launcher
            # runs with (main.py) is the launcher's, not the module's.
            launcher = Gio.SubprocessLauncher.new(Gio.SubprocessFlags.NONE)
            launcher.unsetenv("LD_PRELOAD")
            process = launcher.spawnv(argv)
        except (ValueError, OSError, GLib.Error) as error:
            log.warning("module %s did not open: %s", module.id, error)
            self._problem = words.DID_NOT_OPEN
            self._show_home()
            return False
        log.info("opening %s: %s", module.id, shlex.join(argv))
        started = time.monotonic()
        process.wait_async(None, lambda done, result: self._ended(done, result, module.id,
                                                                  argv, started))
        return True

    def _ended(self, process: Gio.Subprocess, result, module_id: str, argv: list,
               started: float) -> None:
        try:
            process.wait_finish(result)
        except GLib.Error:
            log.debug("could not wait for %s", module_id, exc_info=True)
        self._desk.ended(module_id)
        if (process.get_if_exited() and process.get_exit_status() != 0
                and time.monotonic() - started < FAILED_START_SECONDS):
            log.warning("module %s did not open: %s ended with status %d", module_id,
                        shlex.join(argv), process.get_exit_status())
            self._problem = words.DID_NOT_OPEN
            self._desk.home()
            self._show_home()
        else:
            log.info("module %s ended", module_id)

    def _lock(self) -> None:
        # Turn off does the same: the lock screen, which is trusted, has the
        # real Turn off (D16).
        try:
            self._daemon.lock()
        except DaemonError as error:
            log.warning("could not lock: %s", error)

    def _lid_closed(self) -> None:
        try:
            self._daemon.lock_for("lid")
        except DaemonError as error:
            log.warning("could not lock for the lid: %s", error)

    # --- time -----------------------------------------------------------------

    def refresh(self) -> None:
        """Ask the daemon for the time and the modules, and redraw."""
        try:
            used, left = self._daemon.usage()
            self._model.update(used, left)
            ids = self._daemon.modules()
        except DaemonError as error:
            log.info("the daemon is away: %s", error)
            self._model.daemon_away()
        else:
            # A module the daemon lists whose manifest no longer reads gets
            # no tile, nor one that needs windows for a child without them.
            modules = [m for m in (kidux_modules.read(i) for i in ids)
                       if m is not None and (self._windows or not m.needs_windows)]
            if [m.id for m in modules] != [m.id for m in self._modules]:
                self._modules = modules
                log.info("tiles: %s", " ".join(m.id for m in modules) or "none")
                self._show_home()
        self._draw_time()

    def _ask(self) -> bool:
        self.refresh()
        return GLib.SOURCE_CONTINUE

    def _tick(self) -> bool:
        self._draw_time()
        return GLib.SOURCE_CONTINUE

    def _draw_time(self) -> None:
        self._clock.set_label(GLib.DateTime.new_now_local().format("%H:%M"))
        self._time.show(self._model.time_clock(), self._model.time_text(self._t))
        warning = self._model.warning_text(self._t)
        if warning:
            self._warning.set_label(warning)
        self._banner.set_reveal_child(warning is not None)
        if self._bar is not None:
            self._bar.show_time(self._model.time_clock(), self._model.time_text(self._t),
                                warning, self._desk.current != HOME)

    def _warned(self, seconds_left: int) -> None:
        self._model.warn(seconds_left)
        self.refresh()

    def _dismiss(self) -> None:
        self._model.dismiss()
        self._draw_time()
