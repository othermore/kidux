"""Scrolling that shows itself (D63).

Every screen of Kidux is meant to fit its screen whole, but what a screen
holds grows: more children, more modules, more updates, a smaller screen,
a larger scale. Where it does not fit, it scrolls, and says so without
anyone having to try: its scrollbar is drawn for as long as there is more,
where GTK's own, an overlay, hides until the pointer moves; and a shade lies
along each edge beyond which there is more. `scroller` makes such an area,
`CSS` is its look, which each program adds to its style sheet, and `watch`
tells a program when an area does not fit, for its log.

GTK is imported only where a widget is made, so that what needs none of it,
`more`, is tested where there is no display.
"""

#: The scrollbar, in Kidux's browns and wide enough to see and to grab, and
#: the shade along an edge beyond which there is more, as tall as a line of
#: text.
CSS = """
scrolledwindow.kidux-scroll > scrollbar { background-color: transparent; border: none; }
scrolledwindow.kidux-scroll > scrollbar trough {
  background-color: #efe2d2; border-radius: 7px; min-width: 14px; min-height: 14px; }
scrolledwindow.kidux-scroll > scrollbar slider {
  background-color: #9c8778; border-radius: 7px; border: none; margin: 0;
  min-width: 14px; min-height: 48px; }
scrolledwindow.kidux-scroll > scrollbar.horizontal slider { min-width: 48px; min-height: 14px; }
scrolledwindow.kidux-scroll > undershoot.top {
  background-image: linear-gradient(to bottom, alpha(#7a6a60, 0.35), alpha(#7a6a60, 0) 28px); }
scrolledwindow.kidux-scroll > undershoot.bottom {
  background-image: linear-gradient(to top, alpha(#7a6a60, 0.35), alpha(#7a6a60, 0) 28px); }
scrolledwindow.kidux-scroll > undershoot.left {
  background-image: linear-gradient(to right, alpha(#7a6a60, 0.35), alpha(#7a6a60, 0) 28px); }
scrolledwindow.kidux-scroll > undershoot.right {
  background-image: linear-gradient(to left, alpha(#7a6a60, 0.35), alpha(#7a6a60, 0) 28px); }
"""


def more(value: float, lower: float, upper: float, page: float) -> tuple[bool, bool]:
    """Whether an area's content goes on before what is shown and after it,
    from its adjustment's numbers; a pixel of slack either way is none."""
    return value > lower + 1, value + page < upper - 1


def scroller(child, *, horizontal: bool = True, expand: bool = True):
    """`child` in an area that scrolls up and down and, with `horizontal`,
    sideways, only where it does not fit, and shows it: a scrollbar drawn
    while there is more, and a shade along the edge that has more."""
    import gi

    gi.require_version("Gtk", "4.0")
    from gi.repository import Gtk

    area = Gtk.ScrolledWindow(
        hscrollbar_policy=Gtk.PolicyType.AUTOMATIC if horizontal else Gtk.PolicyType.NEVER,
        vscrollbar_policy=Gtk.PolicyType.AUTOMATIC, vexpand=expand, child=child)
    area.set_overlay_scrolling(False)
    area.add_css_class("kidux-scroll")
    return area


#: How long an area's size is let settle before it is judged: a window takes
#: passing sizes while it is first shown, before the compositor maximises it.
SETTLE_MS = 500


def overflows(shown: float, needed: float) -> bool:
    """Whether content `needed` pixels long does not fit in `shown`; a pixel
    of slack is none, and an area not shown yet overflows nothing."""
    return shown > 0 and needed > shown + 1


class Settling:
    """Calls `judge(key)` once `SETTLE_MS` have passed since the last
    `changed(key)`, through `add` and `remove`, GLib's timeouts by default."""

    def __init__(self, judge, add=None, remove=None) -> None:
        if add is None or remove is None:
            from gi.repository import GLib
            add, remove = GLib.timeout_add, GLib.source_remove
        self._judge, self._add, self._remove = judge, add, remove
        self._pending: dict = {}

    def changed(self, key) -> None:
        if key in self._pending:
            self._remove(self._pending.pop(key))
        self._pending[key] = self._add(SETTLE_MS, self._settled, key)

    def _settled(self, key) -> bool:
        self._pending.pop(key, None)
        self._judge(key)
        return False


def watch(area, on_overflow) -> None:
    """Call `on_overflow(way, needed, shown)`, `way` "tall" or "wide", each
    time `area`'s content needs more room than it is given that way, once
    its size has settled."""
    adjustments = {"tall": area.get_vadjustment(), "wide": area.get_hadjustment()}

    def judge(way):
        shown, needed = adjustments[way].get_page_size(), adjustments[way].get_upper()
        if overflows(shown, needed):
            on_overflow(way, int(needed), int(shown))

    settling = Settling(judge)
    for way, adjustment in adjustments.items():
        adjustment.connect("changed", lambda _adjustment, way=way: settling.changed(way))
