"""The bar along the bottom of the child's screen (D43, launcher.md section 5).

A second window of the launcher, drawn as a layer-shell surface: on top of
every module, along the bottom edge, and with room of its own that the
compositor keeps free, so a maximised window never covers it. *Home*, one
button per open module in the order they were opened, the one on screen
marked (Home when it is the launcher), or, for a child with windows, one per
window, the one in use marked and a minimised one faded (D57); and while a
module is on screen, the time left, the launcher's warning if there is one,
*Close* for that module, and *Lock*, which the launcher's own page already
shows when it is on screen. Home and Close say their key on hover, and
the button Alt+Tab would go to, the next to the right of the one on
screen, says so too (D64, D66); on a Mac the key is written with fn where
fn is needed (`kidux.hardware`). When a module asked
to close is still open, the question whether to close it anyway takes the
place of the time, the warning and Close (D45). While Alt+Tab goes round,
the bar lights the button it points at. It never takes the keyboard:
Super, Alt+Tab and Alt+F4 are the keyboard's way (labwc's configuration),
and the bar is the mouse's.
"""

import logging

import gi

gi.require_version("Gtk", "4.0")

from gi.repository import Gdk, GLib, Gtk  # noqa: E402

from kidux import modules as kidux_modules, scroll, vocabulary  # noqa: E402

from . import words  # noqa: E402
from .desk import title_of  # noqa: E402
from .timeleft import TimeLeft  # noqa: E402

log = logging.getLogger("kidux.launcher")

#: The bar's height in logical pixels: the launcher's buttons, with a margin.
HEIGHT = 56
#: How long the buttons are left to be laid out before the arrows are set
#: and the one in use brought into view, in milliseconds.
SETTLE_MS = 100
#: While Alt+Tab goes round, how often the bar looks at the keyboard's
#: state, in milliseconds. When the state has not shown Alt down within
#: ALT_QUICK_CHECKS looks, it was a quick Alt+Tab, let go before the first,
#: and the round ends; a round Alt holds ends when Alt is let go, or after
#: ALT_LONGEST_CHECKS looks whatever, should its letting go be lost.
ALT_CHECK_MS = 150
ALT_QUICK_CHECKS = 2
ALT_LONGEST_CHECKS = 70


def layer_shell():
    """gtk4-layer-shell, when the launcher runs with it loaded and the
    compositor speaks the protocol; None otherwise."""
    try:
        gi.require_version("Gtk4LayerShell", "1.0")
        from gi.repository import Gtk4LayerShell
    except (ValueError, ImportError):
        return None
    return Gtk4LayerShell if Gtk4LayerShell.is_supported() else None


class Bar:
    def __init__(self, application: Gtk.Application, shell, *, translate, drawing, mascot: str,
                 on_home, on_module, on_lock, on_dismiss, on_close, on_keep, on_end,
                 on_window=None, keys: dict | None = None) -> None:
        self._ = translate
        self._drawing = drawing
        #: How the keys are written on this machine, for the tooltips of
        #: the buttons that do the same (D64): home, close, next.
        self._keys = keys or {}
        #: What Alt+Tab points at while it goes round: "home", a module's id
        #: or a window's number; None when it is not going round.
        self._pointed = None
        self._following = False
        self._alt_checks = 0
        self._alt_seen = False
        self._on_let_go = None
        #: Where Alt+Tab goes, as last logged.
        self._alt_tab_target: str | None = None
        self._on_module = on_module
        self._on_window = on_window
        self._mascot = mascot
        self._shown: list[str] = []
        window = Gtk.Window(application=application, title="Kidux", decorated=False)
        window.add_css_class("kidux")
        window.add_css_class("kidux-bar")
        shell.init_for_window(window)
        shell.set_namespace(window, "kidux-bar")
        shell.set_layer(window, shell.Layer.TOP)
        for edge in (shell.Edge.BOTTOM, shell.Edge.LEFT, shell.Edge.RIGHT):
            shell.set_anchor(window, edge, True)
        shell.set_exclusive_zone(window, HEIGHT)
        shell.set_keyboard_mode(window, shell.KeyboardMode.NONE)
        window.set_default_size(-1, HEIGHT)
        self._window = window

        # Home, the buttons of what is open in all the room up to the time
        # left, Close and Lock (D64): the buttons' strip takes whatever the
        # others leave.
        row = Gtk.Box(spacing=16)
        for side in ("start", "end"):
            getattr(row, f"set_margin_{side}")(12)
        start = Gtk.Box(spacing=8, valign=Gtk.Align.CENTER, hexpand=True)
        self._home = self._button(self._(words.HOME), on_home, picture=mascot,
                                  hint=self._keys.get("home"))
        start.append(self._home)
        self._modules = Gtk.Box(spacing=8)
        # Many windows scroll rather than push Close and Lock off the screen,
        # and show it (D63): an arrow either side of their buttons, there only
        # while they do not all fit, the one at an end faded, each moving
        # them along; a shade along the edge that has more; and the button
        # of the one in use brought into view.
        scroller = Gtk.ScrolledWindow(hscrollbar_policy=Gtk.PolicyType.EXTERNAL,
                                      vscrollbar_policy=Gtk.PolicyType.NEVER,
                                      hexpand=True, child=self._modules)
        scroller.add_css_class("kidux-scroll")
        self._strip = scroller
        self._strip_full = False
        self._strip_settling = 0
        #: The button of what is in use, to bring into view once laid out.
        self._wanted: Gtk.Button | None = None
        self._before = self._arrow("go-previous-symbolic", -1)
        self._after = self._arrow("go-next-symbolic", 1)
        start.append(self._before)
        start.append(scroller)
        start.append(self._after)
        for signal in ("changed", "value-changed"):
            scroller.get_hadjustment().connect(signal, self._strip_moved)
        row.append(start)

        end = Gtk.Box(spacing=16, valign=Gtk.Align.CENTER, visible=False)
        self._end = end
        question = Gtk.Box(spacing=8, visible=False)
        question.add_css_class("kidux-notice")
        self._question_text = Gtk.Label()
        question.append(self._question_text)
        question.append(self._button(self._(vocabulary.CANCEL), on_keep))
        anyway = self._button(self._(words.CLOSE_ANYWAY), on_end)
        anyway.add_css_class("destructive-action")
        question.append(anyway)
        self._question = question
        end.append(question)
        self._warning = Gtk.Button(visible=False)
        self._warning.add_css_class("kidux-notice")
        self._warning.connect("clicked", lambda _b: on_dismiss())
        end.append(self._warning)
        self._time = TimeLeft(can_focus=False)
        end.append(self._time.widget)
        self._close = self._button(self._(words.CLOSE), on_close, icon="window-close-symbolic",
                                   hint=self._keys.get("close"))
        end.append(self._close)
        lock = self._button(self._(vocabulary.LOCK), on_lock, icon="system-lock-screen-symbolic")
        lock.add_css_class("suggested-action")
        end.append(lock)
        row.append(end)
        window.set_child(row)
        # The keyboard's state, which labwc sends every program, the one
        # with the keyboard or not: whether Alt is down while Alt+Tab goes
        # round. A layer-shell window that took the keyboard to hear Alt let
        # go would keep labwc from bringing any window forward.
        self._keyboard = window.get_display().get_default_seat().get_keyboard()
        self._keyboard.connect("notify::modifier-state", self._state_changed)

    def _button(self, label: str, on_click, *, picture: str | None = None,
                icon: str | None = None, hint: str | None = None) -> Gtk.Button:
        box = Gtk.Box(spacing=8, halign=Gtk.Align.CENTER)
        if picture:
            box.append(self._drawing(picture, 32, 32))
        elif icon:
            image = Gtk.Image.new_from_icon_name(icon)
            image.set_pixel_size(24)
            box.append(image)
        box.append(Gtk.Label(label=label))
        # The key that does the same is the tooltip (D64): on hover, so
        # that the bar's room is the modules'.
        button = Gtk.Button(child=box, can_focus=False, tooltip_text=hint)
        button.connect("clicked", lambda _b: on_click())
        return button

    def _arrow(self, icon: str, way: int) -> Gtk.Button:
        button = Gtk.Button(icon_name=icon, can_focus=False, visible=False)
        button.add_css_class("kidux-arrow")
        button.connect("clicked", lambda _b: self._slide(way))
        return button

    def _slide(self, way: int) -> None:
        """The buttons moved along, `way` -1 back or 1 on, by most of what
        is shown, so that the one at the edge stays in view."""
        adjustment = self._strip.get_hadjustment()
        end = adjustment.get_upper() - adjustment.get_page_size()
        value = adjustment.get_value() + way * adjustment.get_page_size() * 0.8
        adjustment.set_value(max(adjustment.get_lower(), min(end, value)))

    def _strip_moved(self, *_args) -> None:
        """The buttons changed or moved: the arrows are set, and the one in
        use brought into view, once GTK has laid the bar out, since neither
        can be while it does."""
        if not self._strip_settling:
            self._strip_settling = GLib.timeout_add(SETTLE_MS, self._strip_settled)

    def _strip_settled(self) -> bool:
        """Both arrows while the buttons do not all fit, each faded at its
        end, none when they do, logged when that changes; and the button of
        what is in use scrolled into view."""
        self._strip_settling = 0
        wanted, self._wanted = self._wanted, None
        viewport = self._modules.get_parent()
        if wanted is not None and wanted.get_parent() is self._modules \
                and isinstance(viewport, Gtk.Viewport):
            viewport.scroll_to(wanted, None)
        adjustment = self._strip.get_hadjustment()
        before, after = scroll.more(adjustment.get_value(), adjustment.get_lower(),
                                    adjustment.get_upper(), adjustment.get_page_size())
        full = (before or after) and self._strip.get_visible()
        for arrow, more in ((self._before, before), (self._after, after)):
            arrow.set_visible(full)
            arrow.set_sensitive(more)
        if full != self._strip_full:
            self._strip_full = full
            log.info("strip: %s", "more than fit" if full else "all fit")
        return GLib.SOURCE_REMOVE

    def _bring_into_view(self, button: Gtk.Button) -> None:
        """The button of what is in use, scrolled into view once laid out."""
        self._wanted = button
        self._strip_moved()

    def _alt_tab(self, target: str | None) -> None:
        """Where Alt+Tab goes, `target`: the id of the module whose button
        says so, or None. Home's tooltip is Home's own key alone, since
        Alt+Tab never goes home (D66); logged when it changes, "none" for
        None."""
        self._home.set_tooltip_text(self._keys.get("home") or None)
        target = target or "none"
        if target != self._alt_tab_target:
            self._alt_tab_target = target
            log.info("alt-tab: %s", target)

    # --- Alt+Tab going round (D64, D66) ------------------------------------------

    def point_at(self, what) -> None:
        """Light the button Alt+Tab points at while it goes round: "home",
        a module's id or a window's number; None puts the light out."""
        self._pointed = what
        self._light()

    def _light(self) -> None:
        if self._pointed == "home":
            self._home.add_css_class("kidux-next")
        else:
            self._home.remove_css_class("kidux-next")
        child = self._modules.get_first_child()
        while child is not None:
            if self._pointed is not None and getattr(child, "kidux_key", None) == self._pointed:
                child.add_css_class("kidux-next")
                self._bring_into_view(child)
            else:
                child.remove_css_class("kidux-next")
            child = child.get_next_sibling()

    def follow_alt(self, on_let_go) -> None:
        """While Alt+Tab goes round, the bar follows the keyboard's state,
        and Alt let go ends the round (`on_let_go`). labwc still sees each
        Alt+Tab, and each goes a step further."""
        self._on_let_go = on_let_go
        if self._following:
            return
        self._following = True
        self._alt_checks = 0
        self._alt_seen = self._alt_down()
        GLib.timeout_add(ALT_CHECK_MS, self._alt_still_down)

    def stop_following(self) -> None:
        self._following = False

    def _alt_down(self) -> bool:
        return bool(self._keyboard.get_modifier_state() & Gdk.ModifierType.ALT_MASK)

    def _state_changed(self, *_args) -> None:
        """The keyboard's state changed: with Alt down, the round holds; up,
        after it was seen down, the round ends."""
        if not self._following:
            return
        if self._alt_down():
            self._alt_seen = True
        elif self._alt_seen:
            self._let_go()

    def _alt_still_down(self) -> bool:
        """Every ALT_CHECK_MS while the round goes: Alt never seen down is a
        quick Alt+Tab, Alt let go in between ends the round, and a round
        that outlasts ALT_LONGEST_CHECKS ends anyway."""
        if not self._following:
            return GLib.SOURCE_REMOVE
        self._alt_checks += 1
        if self._alt_down():
            self._alt_seen = True
        quick = not self._alt_seen and self._alt_checks >= ALT_QUICK_CHECKS
        up = self._alt_seen and not self._alt_down()
        if quick or up or self._alt_checks >= ALT_LONGEST_CHECKS:
            self._let_go()
            return GLib.SOURCE_REMOVE
        return GLib.SOURCE_CONTINUE

    def _let_go(self) -> None:
        if self._following and self._on_let_go is not None:
            self._on_let_go()

    def present(self) -> None:
        self._window.present()

    def show_modules(self, modules: list, current: str | None, language: str,
                     following: str | None = None) -> None:
        """One button per open module (`kidux.modules.Module`), in order; the
        one on screen, `current`, marked, or Home when `current` is None;
        `following`, the module Alt+Tab would go to, says its key."""
        self._alt_tab(following)
        ids = [module.id for module in modules]
        if ids != self._shown:
            self._shown = ids
            log.info("bar: %s", " ".join(ids) or "none")
        if current is None:
            self._home.add_css_class("kidux-current")
        else:
            self._home.remove_css_class("kidux-current")
        while (child := self._modules.get_first_child()) is not None:
            self._modules.remove(child)
        for module in modules:
            button = self._button(kidux_modules.name_in(module, language),
                                  lambda m=module.id: self._on_module(m),
                                  picture=module.icon or self._mascot,
                                  hint=self._keys.get("next") if module.id == following else None)
            button.kidux_key = module.id
            if module.id == current:
                button.add_css_class("kidux-current")
                self._bring_into_view(button)
            self._modules.append(button)
        self._light()

    def show_windows(self, windows: list, home: bool, language: str,
                     following: int | None = None) -> None:
        """For a child with windows (D57): one button per window, as
        (`kidux.modules.Module`, window number, title, active, minimised),
        in the compositor's order; the one in use marked, a minimised one
        faded, Home marked when `home`; `following`, the window Alt+Tab
        would go to, says its key."""
        self._alt_tab(next((module.id for module, window, *_ in windows if window == following),
                           None))
        ids = [f"{module.id}" for module, *_ in windows]
        if ids != self._shown:
            self._shown = ids
            log.info("bar: %s", " ".join(ids) or "none")
        if home:
            self._home.add_css_class("kidux-current")
        else:
            self._home.remove_css_class("kidux-current")
        while (child := self._modules.get_first_child()) is not None:
            self._modules.remove(child)
        for module, window, title, active, minimised in windows:
            button = self._button(title_of(title, kidux_modules.name_in(module, language)),
                                  lambda w=window: self._on_window(w),
                                  picture=module.icon or self._mascot,
                                  hint=self._keys.get("next") if window == following else None)
            button.kidux_key = window
            if active:
                button.add_css_class("kidux-current")
                self._bring_into_view(button)
            if minimised:
                button.add_css_class("kidux-minimised")
            self._modules.append(button)
        self._light()

    def show_time(self, clock: str | None, sentence: str | None, warning: str | None,
                  on_a_module: bool) -> None:
        """The time left, as a clock reads it and in a sentence on hover,
        the warning the launcher shows, Close and Lock, while a module is on
        screen: the bar is what a child looking at one sees."""
        self._end.set_visible(on_a_module)
        if warning:
            self._warning.set_label(warning)
        asking = self._question.get_visible()
        self._warning.set_visible(warning is not None and not asking)
        self._time.show(clock, sentence, room=not asking)

    def show_closing(self, name: str | None, question: str | None) -> None:
        """Close names the module on screen, `name`, for a screen reader;
        `question`, when there is one, is asked in place of the time."""
        if name is not None:
            label = self._(words.CLOSE_MODULE).format(name=name)
            self._close.set_tooltip_text(label)
            self._close.update_property([Gtk.AccessibleProperty.LABEL], [label])
        self._question.set_visible(question is not None)
        if question is not None:
            self._question_text.set_label(question)
            self._warning.set_visible(False)
        # While it asks, Close it anyway is Close: both would not fit beside
        # Lock on a 1280-pixel screen; nor would the other modules' buttons,
        # which step aside with their arrows until it is answered, the
        # question naming the module it is about.
        self._time.widget.set_visible(question is None and self._time.shown)
        self._close.set_visible(question is None)
        if self._strip.get_visible() != (question is None):
            self._strip.set_visible(question is None)
            if question is not None:
                self._before.set_visible(False)
                self._after.set_visible(False)
            self._strip_moved()
