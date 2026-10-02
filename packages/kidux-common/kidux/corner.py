"""The corner of a screen: battery, brightness, keyboard light, sound (D61).

The child's screen shows it top right (the launcher), and so do the sign-in
screen, the lock screen and the adult's screens (the greeter): one corner,
made once per program and kept across its screens, since it watches a
file and reads the machine on a timer.

Each indicator is there only when the machine has the thing: a battery
shows its charge and whether it is charging; the screen's brightness, the
keyboard's light and the sound's volume are buttons that open a slider,
the sound's with *Mute* beside it. What they show is read again every few
seconds (`kidux.hardware`), and at once when a key has changed a level:
the key touches `hardware.levels_file`, which the corner watches. A
slider's label follows the slider as it moves, and a slider open under
the child's hand is not read back while it is. The sound, which takes a
program (`wpctl`), is read without waiting for it, so that the launcher's
loop, which answers the compositor, never stops for it.
"""

import logging

import gi

gi.require_version("Gtk", "4.0")

from gi.repository import Gio, GLib, Gtk  # noqa: E402

from . import hardware, vocabulary  # noqa: E402

log = logging.getLogger("kidux.corner")

#: How often the indicators are read again, in seconds.
REFRESH_SECONDS = 5
#: How long a change of the levels' file waits for the next, in
#: milliseconds: a held key is read once, not on every step.
SETTLE_MS = 200

#: The corner's own look, which each program adds to its style sheet.
CSS = """
.kidux-status { font-size: 18px; color: #7a6a60; }
window.kidux menubutton.kidux-status > button { padding: 2px 8px; min-height: 36px; }
"""


def battery_icon(cell: hardware.Battery) -> str:
    """Adwaita's battery icon for a charge, in tens, charging or not."""
    tens = max(0, min(100, round(cell.capacity / 10) * 10))
    return f"battery-level-{tens}{'-charging' if cell.charging else ''}-symbolic"


def volume_icon(percent: int, muted: bool) -> str:
    if muted or percent == 0:
        return "audio-volume-muted-symbolic"
    if percent < 34:
        return "audio-volume-low-symbolic"
    if percent < 67:
        return "audio-volume-medium-symbolic"
    return "audio-volume-high-symbolic"


class _Slider:
    """A button with an icon and a percentage that opens a vertical slider;
    with `mute`, a Mute toggle under it."""

    def __init__(self, icon: str, name: str, on_value, *, floor: int = 0, on_mute=None,
                 compact: bool = False) -> None:
        self._on_value = on_value
        self._on_mute = on_mute
        self._floor = floor
        self._icon = Gtk.Image.new_from_icon_name(icon)
        self._icon.set_pixel_size(24)
        self._label = Gtk.Label(visible=not compact)
        box = Gtk.Box(spacing=6)
        box.append(self._icon)
        box.append(self._label)
        self.button = Gtk.MenuButton(child=box, tooltip_text=name, has_frame=False)
        self.button.add_css_class("kidux-status")
        column = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8,
                         margin_top=8, margin_bottom=8, margin_start=8, margin_end=8)
        self._scale = Gtk.Scale.new_with_range(Gtk.Orientation.VERTICAL, floor, 100, 5)
        self._scale.set_inverted(True)
        self._scale.set_draw_value(False)
        self._scale.set_size_request(-1, 160)
        self._changed = self._scale.connect("value-changed", self._moved)
        column.append(self._scale)
        self._mute = None
        if on_mute is not None:
            self._mute = Gtk.ToggleButton(label=name)
            self._muted = self._mute.connect("toggled", lambda b: self._on_mute(b.get_active()))
            column.append(self._mute)
        self.button.set_popover(Gtk.Popover(child=column))

    def _moved(self, scale) -> None:
        percent = int(scale.get_value())
        self._label.set_label(f"{percent} %")
        self._on_value(percent)

    def show(self, percent: int, icon: str | None = None, muted: bool = False,
             mute_label: str | None = None) -> None:
        """What the machine says; nothing while the slider is open, where
        the child's hand says it."""
        if self.button.get_active():
            return
        self._label.set_label(f"{percent} %")
        if icon is not None:
            self._icon.set_from_icon_name(icon)
        with self._scale.handler_block(self._changed):
            self._scale.set_value(percent)
        if self._mute is not None:
            with self._mute.handler_block(self._muted):
                self._mute.set_active(muted)
            if mute_label is not None:
                self._mute.set_label(mute_label)


class Corner:
    """The corner, `widget`, and the timer and the file watch that keep it
    current, until `close`."""

    def __init__(self, translate, root=hardware.SYS, *, compact: bool = False) -> None:
        """`compact`, on a narrow screen (`kidux.screen.compact_corner`),
        leaves out the percentages: the icons say what is there, the sliders
        say how much."""
        self._ = translate
        self._root = root
        self.widget = Gtk.Box(spacing=8, valign=Gtk.Align.CENTER)
        self._battery = None
        self._screen = self._keyboard = self._sound = None
        if hardware.battery(root) is not None:
            self._battery_icon = Gtk.Image(pixel_size=24)
            self._battery_label = Gtk.Label(visible=not compact)
            self._battery = Gtk.Box(spacing=6, tooltip_text=self._(vocabulary.BATTERY))
            self._battery.add_css_class("kidux-status")
            self._battery.append(self._battery_icon)
            self._battery.append(self._battery_label)
        if hardware.backlight(root) is not None:
            self._screen = _Slider("display-brightness-symbolic", self._(vocabulary.SCREEN_BRIGHTNESS),
                                   self._set_screen, floor=hardware.SCREEN_FLOOR, compact=compact)
        if hardware.keyboard_backlight(root) is not None:
            self._keyboard = _Slider("keyboard-brightness-symbolic", self._(vocabulary.KEYBOARD_LIGHT),
                                     self._set_keyboard, compact=compact)
        self._audio = hardware.volume() is not None
        if self._audio:
            self._sound = _Slider("audio-volume-high-symbolic", self._(vocabulary.VOLUME),
                                  self._set_volume, on_mute=self._set_muted, compact=compact)
        for part in (self._sound, self._keyboard, self._screen):
            if part is not None:
                self.widget.append(part.button)
        if self._battery is not None:
            self.widget.append(self._battery)
        log.info("hardware: %s audio=%s%s", hardware.summary(root),
                 "yes" if self._audio else "no", " compact" if compact else "")
        self._settling = 0
        self._monitor = None
        path = hardware.levels_file()
        if path is not None:
            try:
                path.parent.mkdir(exist_ok=True)
                self._monitor = Gio.File.new_for_path(str(path)).monitor_file(
                    Gio.FileMonitorFlags.NONE, None)
                self._monitor.connect("changed", self._levels_changed)
            except (OSError, GLib.Error) as error:
                log.warning("the levels' file cannot be watched: %s", error)
        self.refresh()
        self._timer = GLib.timeout_add_seconds(REFRESH_SECONDS, self.refresh)

    @property
    def empty(self) -> bool:
        """Nothing of a laptop's on this machine: nothing to show."""
        return self.widget.get_first_child() is None

    def close(self) -> None:
        """The timer and the file watch stopped: the corner is done with."""
        if self._timer:
            GLib.source_remove(self._timer)
            self._timer = 0
        if self._settling:
            GLib.source_remove(self._settling)
            self._settling = 0
        if self._monitor is not None:
            self._monitor.cancel()
            self._monitor = None

    def _levels_changed(self, *_args) -> None:
        """A key changed a level: read everything once the keys settle."""
        if not self._settling:
            self._settling = GLib.timeout_add(SETTLE_MS, self._settled)

    def _settled(self) -> bool:
        self._settling = 0
        self.refresh()
        return False

    def refresh(self) -> bool:
        """Read everything again; True, so that a GLib timer keeps calling."""
        if self._battery is not None:
            cell = hardware.battery(self._root)
            if cell is not None:
                self._battery_icon.set_from_icon_name(battery_icon(cell))
                self._battery_label.set_label(f"{cell.capacity} %")
        if self._screen is not None:
            level = hardware.backlight(self._root)
            if level is not None:
                self._screen.show(level.percent)
        if self._keyboard is not None:
            level = hardware.keyboard_backlight(self._root)
            if level is not None:
                self._keyboard.show(level.percent)
        if self._sound is not None:
            self._read_sound()
        return True

    def _read_sound(self) -> None:
        """`wpctl get-volume`, asked without blocking: its answer, when it
        comes, is shown."""
        def shown(process, result):
            try:
                _ok, out, _err = process.communicate_utf8_finish(result)
            except GLib.Error as error:
                log.debug("wpctl did not answer: %s", error)
                return
            sound = hardware.parse_volume(out or "")
            if sound is not None:
                percent, muted = sound
                self._sound.show(percent, volume_icon(percent, muted), muted,
                                 self._(vocabulary.MUTED) if muted else self._(vocabulary.MUTE))

        try:
            process = Gio.Subprocess.new(["wpctl", "get-volume", hardware.SINK],
                                         Gio.SubprocessFlags.STDOUT_PIPE
                                         | Gio.SubprocessFlags.STDERR_SILENCE)
        except GLib.Error as error:
            log.debug("wpctl did not start: %s", error)
            return
        process.communicate_utf8_async(None, None, shown)

    def _set_screen(self, percent: int) -> None:
        level = hardware.backlight(self._root)
        if level is not None:
            hardware.set_level(level, percent)

    def _set_keyboard(self, percent: int) -> None:
        level = hardware.keyboard_backlight(self._root)
        if level is not None:
            hardware.set_level(level, percent)

    def _set_volume(self, percent: int) -> None:
        hardware.set_volume(percent)
        self.refresh()

    def _set_muted(self, muted: bool) -> None:
        hardware.set_muted(muted)
        self.refresh()
