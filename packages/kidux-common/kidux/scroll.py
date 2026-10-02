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


def watch(area, on_overflow) -> None:
    """Call `on_overflow(way, needed, shown)`, `way` "tall" or "wide", each
    time `area`'s content needs more room than it is given that way."""
    def changed(adjustment, way):
        shown, needed = adjustment.get_page_size(), adjustment.get_upper()
        if shown > 0 and needed > shown + 1:
            on_overflow(way, int(needed), int(shown))

    area.get_vadjustment().connect("changed", changed, "tall")
    area.get_hadjustment().connect("changed", changed, "wide")
