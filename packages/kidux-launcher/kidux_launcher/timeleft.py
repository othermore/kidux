"""The time a child has left, where a child sees it: the child's screen and
the bar (launcher.md sections 2 and 5).

An hourglass and the time as a clock reads it, 00:51, small enough to leave
the bar's room to the modules; the sentence, "51 minutes left", on hover and
on a tap, in a popover. Nothing for a child with no limit.
"""

import gi

gi.require_version("Gtk", "4.0")

from gi.repository import Gio, Gtk  # noqa: E402

from kidux import paths  # noqa: E402


class TimeLeft:
    def __init__(self, *, can_focus: bool = True) -> None:
        icon = Gtk.Image.new_from_gicon(
            Gio.FileIcon.new(Gio.File.new_for_path(str(paths.HOURGLASS))))
        icon.set_pixel_size(24)
        self._clock = Gtk.Label()
        box = Gtk.Box(spacing=6)
        box.append(icon)
        box.append(self._clock)
        self._said = Gtk.Label(wrap=True, max_width_chars=32, margin_top=8, margin_bottom=8,
                               margin_start=12, margin_end=12)
        self.widget = Gtk.MenuButton(child=box, has_frame=False, can_focus=can_focus,
                                     visible=False, popover=Gtk.Popover(child=self._said))
        self.widget.add_css_class("kidux-time")
        self._shown = False

    @property
    def shown(self) -> bool:
        """Whether there is a time left to show: the child has a limit."""
        return self._shown

    def show(self, clock: str | None, sentence: str | None, *, room: bool = True) -> None:
        """The time left, `clock` and its `sentence`; hidden without a limit,
        or while `room` is False, the room given to something else."""
        self._shown = clock is not None
        if clock is not None:
            self._clock.set_label(clock)
            self._said.set_label(sentence or "")
            self.widget.set_tooltip_text(sentence)
        self.widget.set_visible(self._shown and room)
