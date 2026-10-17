"""GTK 4: the pane a module's guide is shown in (launcher.md, section 5; D103).

A third window of the launcher, drawn as a layer-shell surface on the right
edge, from the top down to the bar, with an exclusive zone of its width, so
that every maximised window and the launcher's own fill the room to its
left. Folded, it is a rail along the edge, and its zone the rail's. Which
guide it shows, and what is remembered, is `guides.py`'s; this draws it.

Unfolded, it shows at the top the module's name, or, for a child with
windows and more than one guide open, a list of them to pick from, with
the pin beside it; then *Fold*. Under that, the list of lessons or one
lesson, its blocks (kidux.lessons) drawn one under another; at the
bottom, *Lessons*, *Back* and *Next*. Its keyboard is on demand: a click
in it gives it the keys, a click elsewhere takes them back, so that a
program beside it keeps them while the child works there.
"""

import logging
import math

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Pango", "1.0")
gi.require_version("PangoCairo", "1.0")

from gi.repository import Gdk, GLib, Gtk, Pango, PangoCairo  # noqa: E402

from kidux import modules as kidux_modules, scroll  # noqa: E402

from . import words  # noqa: E402

log = logging.getLogger("kidux.launcher")

#: The pane's width: a third of the screen, never less than this.
NARROWEST = 300
#: The rail a folded pane is, along the edge.
RAIL = 28
#: The mascot beside what it says.
MASCOT_SIZE = 64

CSS = """
window.kidux-guide { background-color: #fff6e9; color: #3b2f2a;
  font-family: "Andika", sans-serif; font-size: 18px;
  border-left: 3px solid #f2e2cc; }
window.kidux-guide button { min-height: 44px; border-radius: 14px; padding: 0 14px;
  font-size: 17px; }
window.kidux-guide button.kidux-rail { min-height: 0; min-width: 0; padding: 6px 0;
  border-radius: 0; background-color: #f2e2cc; }
window.kidux-guide button.kidux-lesson { padding: 8px 14px; }
.kidux-guide-name { font-size: 22px; font-weight: bold; }
.kidux-guide-title { font-size: 24px; font-weight: bold; }
.kidux-guide-heading { font-size: 20px; font-weight: bold; margin-top: 8px; }
.kidux-guide-number { background-color: #3584e4; color: #ffffff; border-radius: 999px;
  min-width: 30px; min-height: 30px; font-weight: bold; }
.kidux-guide-bubble { background-color: #ffffff; border-radius: 16px; padding: 10px 14px; }
.kidux-guide-try { background-color: #ffe9cf; border-radius: 16px; padding: 12px 14px; }
.kidux-guide-try-title { font-weight: bold; }
.kidux-guide-mission { background-color: #dbe8fb; border-radius: 16px; padding: 12px 14px; }
"""


def width_for(logical_width: int) -> int:
    """The pane's width on a screen `logical_width` pixels wide."""
    return max(NARROWEST, logical_width // 3)


def markup(runs) -> str:
    """A run list (kidux.lessons) as Pango markup."""
    parts = []
    for style, text in runs:
        escaped = GLib.markup_escape_text(text)
        parts.append({"bold": f"<b>{escaped}</b>", "italic": f"<i>{escaped}</i>"}
                     .get(style, escaped))
    return "".join(parts)


def text(runs, css: str | None = None) -> Gtk.Label:
    label = Gtk.Label(wrap=True, wrap_mode=Pango.WrapMode.WORD_CHAR, xalign=0.0,
                      halign=Gtk.Align.FILL, hexpand=True)
    label.set_markup(markup(runs))
    if css:
        label.add_css_class(css)
    return label


def picture_height(path: str, width: int) -> int:
    """How tall a picture is at `width`, from its own proportions."""
    try:
        gi.require_version("Rsvg", "2.0")
        from gi.repository import Rsvg
        handle = Rsvg.Handle.new_from_file(path)
        ok, w, h = handle.get_intrinsic_size_in_pixels()
        if ok and w > 0:
            return max(1, round(width * h / w))
    except (ValueError, ImportError, GLib.Error):
        pass
    return round(width * 0.6)


class GuidePane:
    def __init__(self, application: Gtk.Application, shell, *, translate, drawing, mascot: str,
                 windows: bool, width: int, on_fold, on_lesson, on_pick, on_pin,
                 language: str) -> None:
        self._ = translate
        self._drawing = drawing
        self._mascot = mascot
        self._windows = windows
        self._width = width
        self._on_fold = on_fold
        self._on_lesson = on_lesson
        self._on_pick = on_pick
        self._on_pin = on_pin
        self._language = language
        self._shell = shell
        #: What is drawn: the module, its lessons, the lesson shown (None for
        #: the list), folded, the guides open, pinned, and where its missions
        #: are, for the sentence that says how to open one.
        self._module = None
        self._lessons: list = []
        self._lesson: int | None = None
        self._folded = False
        self._open: list = []
        self._pinned = False
        self._missions_folder = ""

        window = Gtk.Window(application=application, title="Kidux", decorated=False)
        window.add_css_class("kidux")
        window.add_css_class("kidux-guide")
        shell.init_for_window(window)
        shell.set_namespace(window, "kidux-guide")
        shell.set_layer(window, shell.Layer.TOP)
        for edge in (shell.Edge.RIGHT, shell.Edge.TOP, shell.Edge.BOTTOM):
            shell.set_anchor(window, edge, True)
        shell.set_keyboard_mode(window, shell.KeyboardMode.ON_DEMAND)
        keys = Gtk.EventControllerKey()
        keys.connect("key-pressed", self._key)
        window.add_controller(keys)
        self._window = window

    # --- what the launcher asks ------------------------------------------

    def show(self, module, lessons: list, *, lesson: int | None, folded: bool, open_: list,
             pinned: bool, missions_folder: str) -> None:
        """The guide of `module` (kidux.modules.Module), its `lessons`, at
        `lesson` (a lesson's number, None for the list), folded or not;
        `open_`, the modules with a guide open, for a child with windows to
        pick from; `pinned`, whether the one shown is."""
        if lesson is not None and not any(item.number == lesson for item in lessons):
            lesson = None
        changed = (module.id if self._module else None, self._lesson, self._folded,
                   [m.id for m in self._open], self._pinned) != (
                   module.id, lesson, folded, [m.id for m in open_], pinned)
        self._module, self._lessons, self._lesson = module, lessons, lesson
        self._folded, self._open, self._pinned = folded, open_, pinned
        self._missions_folder = missions_folder
        if changed or not self._window.get_visible():
            self._draw()
            log.info("guide: %s %s %s%s", module.id,
                     f"lesson {lesson}" if lesson is not None else "lessons",
                     "folded" if folded else "unfolded", " pinned" if pinned else "")
        self._window.present()

    def hide(self) -> None:
        if self._window.get_visible():
            self._window.set_visible(False)
            log.info("guide: none")
        self._module = None

    @property
    def shown(self) -> bool:
        return self._module is not None and self._window.get_visible()

    # --- drawing ---------------------------------------------------------

    def _draw(self) -> None:
        if self._folded:
            self._shell.set_exclusive_zone(self._window, RAIL)
            self._window.set_size_request(RAIL, -1)
            self._window.set_default_size(RAIL, -1)
            self._window.set_child(self._rail())
            return
        self._shell.set_exclusive_zone(self._window, self._width)
        self._window.set_size_request(self._width, -1)
        self._window.set_default_size(self._width, -1)
        page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        for side in ("top", "bottom", "start", "end"):
            getattr(page, f"set_margin_{side}")(14)
        page.append(self._header())
        body = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
        body.set_margin_end(8)
        if self._lesson is None:
            self._list(body)
        else:
            self._one_lesson(body)
        page.append(scroll.scroller(body, horizontal=False))
        if self._lesson is not None:
            page.append(self._footer())
        self._window.set_child(page)

    def _name(self, module) -> str:
        return kidux_modules.name_in(module, self._language)

    def _header(self) -> Gtk.Widget:
        row = Gtk.Box(spacing=8)
        if self._windows and len(self._open) > 1:
            names = Gtk.StringList.new([self._name(m) for m in self._open])
            picker = Gtk.DropDown(model=names, hexpand=True)
            picker.set_selected(next((i for i, m in enumerate(self._open)
                                      if m.id == self._module.id), 0))
            picker.add_css_class("kidux-guide-name")
            picker.connect("notify::selected", self._picked)
            row.append(picker)
        else:
            name = Gtk.Label(label=self._name(self._module), xalign=0.0, hexpand=True,
                             ellipsize=Pango.EllipsizeMode.END)
            name.add_css_class("kidux-guide-name")
            row.append(name)
        if self._windows:
            pin = Gtk.ToggleButton(icon_name="view-pin-symbolic", active=self._pinned,
                                   tooltip_text=self._(words.PIN_HINT))
            pin.update_property([Gtk.AccessibleProperty.LABEL], [self._(words.PIN)])
            pin.connect("toggled", lambda button: self._on_pin(button.get_active()))
            row.append(pin)
        fold = Gtk.Button(icon_name="pan-end-symbolic", tooltip_text=self._(words.FOLD))
        fold.update_property([Gtk.AccessibleProperty.LABEL], [self._(words.FOLD)])
        fold.connect("clicked", lambda _b: self._on_fold(True))
        row.append(fold)
        return row

    def _picked(self, picker, _spec) -> None:
        index = picker.get_selected()
        if 0 <= index < len(self._open) and self._open[index].id != self._module.id:
            self._on_pick(self._open[index].id)

    def _rail(self) -> Gtk.Widget:
        """The folded pane: the book and the module's name written upwards,
        all of it a button that unfolds it."""
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        book = Gtk.Image.new_from_icon_name("accessories-dictionary-symbolic")
        book.set_pixel_size(20)
        box.append(book)
        name = self._name(self._module)
        area = Gtk.DrawingArea(content_width=RAIL - 6, vexpand=True)

        def draw(widget, cairo, w, h):
            layout = PangoCairo.create_layout(cairo)
            layout.set_text(name, -1)
            layout.set_font_description(Pango.FontDescription.from_string("Andika Bold 15"))
            colour = widget.get_color()
            cairo.set_source_rgba(colour.red, colour.green, colour.blue, colour.alpha)
            _ink, logical = layout.get_pixel_extents()
            cairo.translate((w - logical.height) / 2, min(h, logical.width + 4))
            cairo.rotate(-math.pi / 2)
            PangoCairo.show_layout(cairo, layout)

        area.set_draw_func(draw)
        box.append(area)
        button = Gtk.Button(child=box, tooltip_text=self._(words.GUIDE))
        button.add_css_class("kidux-rail")
        button.update_property([Gtk.AccessibleProperty.LABEL], [self._(words.GUIDE)])
        button.connect("clicked", lambda _b: self._on_fold(False))
        return button

    def _list(self, body: Gtk.Box) -> None:
        for item in self._lessons:
            row = Gtk.Box(spacing=12)
            number = Gtk.Label(label=str(item.number), valign=Gtk.Align.CENTER)
            number.add_css_class("kidux-guide-number")
            row.append(number)
            row.append(Gtk.Label(label=item.title, xalign=0.0, wrap=True, hexpand=True))
            button = Gtk.Button(child=row)
            button.add_css_class("kidux-lesson")
            button.connect("clicked", lambda _b, n=item.number: self._on_lesson(n))
            body.append(button)

    def _one_lesson(self, body: Gtk.Box) -> None:
        item = next(item for item in self._lessons if item.number == self._lesson)
        title = Gtk.Label(label=item.title, xalign=0.0, wrap=True)
        title.add_css_class("kidux-guide-title")
        body.append(title)
        for block in item.blocks:
            body.append(self._block(block))

    def _block(self, block) -> Gtk.Widget:
        kind = block[0]
        if kind == "heading":
            label = Gtk.Label(label=block[2], xalign=0.0, wrap=True)
            label.add_css_class("kidux-guide-heading")
            return label
        if kind == "paragraph":
            return text(block[1])
        if kind in ("steps", "bullets"):
            column = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
            for number, item in enumerate(block[1], start=1):
                row = Gtk.Box(spacing=10)
                if kind == "steps":
                    mark = Gtk.Label(label=str(number), valign=Gtk.Align.START)
                    mark.add_css_class("kidux-guide-number")
                else:
                    mark = Gtk.Label(label="•", valign=Gtk.Align.START)
                row.append(mark)
                row.append(text(item))
                column.append(row)
            return column
        if kind == "image":
            width = self._width - 60
            picture = self._drawing(block[1], width, picture_height(block[1], width))
            picture.update_property([Gtk.AccessibleProperty.LABEL], [block[2]])
            return picture
        if kind == "mascot":
            row = Gtk.Box(spacing=10)
            chick = self._drawing(self._mascot, MASCOT_SIZE, MASCOT_SIZE)
            chick.set_valign(Gtk.Align.START)
            row.append(chick)
            row.append(text(block[2], "kidux-guide-bubble"))
            return row
        if kind == "try":
            box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
            box.add_css_class("kidux-guide-try")
            heading = Gtk.Label(label=self._(words.TRY_THIS), xalign=0.0)
            heading.add_css_class("kidux-guide-try-title")
            box.append(heading)
            for inner in block[1]:
                box.append(self._block(inner))
            return box
        if kind == "mission":
            return self._mission(block[1])
        return Gtk.Box()

    def _mission(self, path: str) -> Gtk.Widget:
        """The lesson's mission: where its copy is, in the child's Documents,
        and how to open it from the module's own File, Open, which is itself
        a thing to learn; the module is open whenever its guide is."""
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        box.add_css_class("kidux-guide-mission")
        heading = Gtk.Label(label=self._(words.MISSION), xalign=0.0)
        heading.add_css_class("kidux-guide-try-title")
        box.append(heading)
        sentence = self._(words.OPEN_MISSION_FROM).format(
            name=self._name(self._module), folder=self._missions_folder,
            file=path.rsplit("/", 1)[-1])
        box.append(Gtk.Label(label=sentence, xalign=0.0, wrap=True,
                             wrap_mode=Pango.WrapMode.WORD_CHAR))
        return box

    def _footer(self) -> Gtk.Widget:
        row = Gtk.Box(spacing=8, homogeneous=True)
        numbers = [item.number for item in self._lessons]
        at = numbers.index(self._lesson)
        lessons = Gtk.Button(label=self._(words.LESSONS))
        lessons.connect("clicked", lambda _b: self._on_lesson(None))
        row.append(lessons)
        back = Gtk.Button(label=self._(words.BACK), sensitive=at > 0)
        back.connect("clicked", lambda _b: self._on_lesson(numbers[at - 1]))
        row.append(back)
        following = Gtk.Button(label=self._(words.NEXT), sensitive=at + 1 < len(numbers))
        following.connect("clicked", lambda _b: self._on_lesson(numbers[at + 1]))
        row.append(following)
        return row

    def _key(self, _controller, keyval, _code, _state) -> bool:
        if keyval == Gdk.KEY_Escape and self._lesson is not None:
            self._on_lesson(None)
            return True
        return False
