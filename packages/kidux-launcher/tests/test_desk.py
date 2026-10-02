"""The child's desktop (desk.py), against a compositor that only remembers."""

from dataclasses import replace

from kidux_launcher.compositor import LAUNCHER_APP_ID, Toplevel
from kidux_launcher.desk import CLOSE_SECONDS, HOME, Desk

#: Which module each app_id of the tests is of, as the manifests would say.
MODULES = {"org.kidux.tests.Canary": "canary", "org.kidux.tests.Robin": "robin",
           "org.kidux.modules.Hello": "hello"}


class FakeCompositor:
    """labwc as the protocol shows it: activating a window makes it the only
    active one and brings it back from minimised; maximising and taking out
    of fullscreen do what they say."""

    def __init__(self) -> None:
        self.windows_now: list[Toplevel] = []
        self.commands: list[str] = []
        self._next = 10
        self.launcher = self.add(LAUNCHER_APP_ID, maximized=True)
        self.activate(self.launcher.id)
        self.commands.clear()

    def add(self, app_id: str, **states) -> Toplevel:
        self._next += 1
        window = Toplevel(id=self._next, app_id=app_id, **states)
        self.windows_now.append(window)
        return window

    def gone(self, window: int) -> None:
        self.windows_now = [w for w in self.windows_now if w.id != window]

    def change(self, window: int, **states) -> None:
        self.windows_now = [replace(w, **states) if w.id == window else w
                            for w in self.windows_now]

    def toplevels(self):
        return list(self.windows_now)

    def active(self) -> Toplevel | None:
        return next((w for w in self.windows_now if w.activated), None)

    def activate(self, window: int) -> None:
        self.commands.append(f"activate {window}")
        self.windows_now = [replace(w, activated=w.id == window,
                                    minimized=False if w.id == window else w.minimized)
                            for w in self.windows_now]

    def close(self, window: int) -> None:
        self.commands.append(f"close {window}")

    def minimize(self, window: int) -> None:
        self.commands.append(f"minimize {window}")
        self.change(window, minimized=True, activated=False)

    def maximize(self, window: int) -> None:
        self.commands.append(f"maximize {window}")
        self.change(window, maximized=True)

    def unfullscreen(self, window: int) -> None:
        self.commands.append(f"unfullscreen {window}")
        self.change(window, fullscreen=False)


def desk(compositor, changes=None, ended=None, windows=False):
    return Desk(compositor, module_of=MODULES.get,
                on_change=(lambda: changes.append(True)) if changes is not None else None,
                end=(ended.append if ended is not None else lambda _m: None), windows=windows)


def opened(d, compositor, module_id, app_id, **states) -> Toplevel:
    """A tile activated, the module started, and its first window mapped."""
    started = []
    d.open(module_id, lambda: started.append(module_id) or True)
    assert started == [module_id]
    window = compositor.add(app_id, **states)
    d.settle()
    return next(w for w in compositor.windows_now if w.id == window.id)


# --- whose each window is, and what is on screen ---------------------------------


def test_a_module_s_first_window_is_shown_and_the_module_is_on_screen():
    c = FakeCompositor()
    changes = []
    d = desk(c, changes)

    window = opened(d, c, "canary", "org.kidux.tests.Canary", maximized=True)
    d.settle()

    assert f"activate {window.id}" in c.commands
    assert d.modules == ["canary"] and d.on_screen() == "canary" and changes


def test_a_window_no_manifest_claims_is_the_module_s_that_is_waiting_for_one():
    c = FakeCompositor()
    d = desk(c)

    opened(d, c, "hello", "python3", maximized=True)
    d.settle()

    assert d.modules == ["hello"] and not d.opening("hello")


def test_a_dialog_is_its_window_s_module_s():
    c = FakeCompositor()
    d = desk(c)
    main = opened(d, c, "canary", "org.kidux.tests.Canary", maximized=True)
    c.add("python3", parent=main.id)
    d.settle()

    assert [w.app_id for w in d.windows_of("canary")] == ["org.kidux.tests.Canary", "python3"]


def test_a_window_of_no_module_is_left_alone():
    c = FakeCompositor()
    d = desk(c)
    stranger = c.add("org.example.Stranger", fullscreen=True)
    d.settle()
    d.settle()

    assert d.modules == [] and c.commands == []
    assert stranger.id not in [w.id for m in d.modules for w in d.windows_of(m)]


def test_home_is_the_launcher_s_window():
    c = FakeCompositor()
    d = desk(c)
    opened(d, c, "canary", "org.kidux.tests.Canary", maximized=True)
    d.settle()

    d.home()
    d.settle()

    assert c.active().id == c.launcher.id and d.on_screen() is None


def test_a_tile_of_an_open_module_shows_it_and_starts_nothing():
    c = FakeCompositor()
    d = desk(c)
    window = opened(d, c, "canary", "org.kidux.tests.Canary", maximized=True)
    d.home()
    d.settle()

    d.open("canary", lambda: (_ for _ in ()).throw(AssertionError("started twice")))
    d.settle()

    assert c.active().id == window.id and d.on_screen() == "canary"


def test_a_module_starting_is_not_started_twice():
    c = FakeCompositor()
    d = desk(c)
    started = []
    d.open("canary", lambda: started.append(1) or True)
    d.open("canary", lambda: started.append(2) or True)

    assert started == [1] and d.opening("canary")


def test_a_module_that_could_not_start_can_be_tried_again():
    c = FakeCompositor()
    d = desk(c)
    d.open("canary", lambda: False)

    assert not d.opening("canary")


def test_show_brings_back_the_module_s_window_last_active():
    c = FakeCompositor()
    d = desk(c)
    first = opened(d, c, "canary", "org.kidux.tests.Canary", maximized=True)
    second = c.add("org.kidux.tests.Canary", maximized=True)
    d.settle()
    c.activate(second.id)
    d.settle()
    d.home()
    d.settle()

    d.show("canary")

    assert c.active().id == second.id != first.id


def test_a_module_that_closes_leaves_the_bar_and_home_comes_back():
    c = FakeCompositor()
    changes = []
    d = desk(c, changes)
    window = opened(d, c, "canary", "org.kidux.tests.Canary", maximized=True)
    d.settle()
    changes.clear()

    c.gone(window.id)
    d.settle()

    assert d.modules == [] and d.on_screen() is None and changes
    assert c.active().id == c.launcher.id


def test_a_launcher_started_again_finds_the_modules_where_they_are():
    c = FakeCompositor()
    canary = c.add("org.kidux.tests.Canary", maximized=True)
    c.add("org.kidux.tests.Robin", maximized=True)
    c.activate(canary.id)
    c.commands.clear()
    d = desk(c)

    d.settle()

    assert d.modules == ["canary", "robin"] and d.on_screen() == "canary"
    assert c.commands == []


def test_the_bar_hears_of_a_change_and_only_of_a_change():
    c = FakeCompositor()
    changes = []
    d = desk(c, changes)
    opened(d, c, "canary", "org.kidux.tests.Canary", maximized=True)
    d.settle()
    changes.clear()

    d.settle()

    assert changes == []


# --- the kiosk: a child without windows ---------------------------------------------


def test_no_window_keeps_the_whole_screen():
    c = FakeCompositor()
    d = desk(c)
    window = opened(d, c, "canary", "org.kidux.tests.Canary", fullscreen=True)
    d.settle()

    assert f"unfullscreen {window.id}" in c.commands
    # Out of fullscreen at its own size, it fills the room above the bar again.
    assert f"maximize {window.id}" in c.commands


def test_a_main_window_that_is_not_maximised_is_and_a_dialog_is_left():
    c = FakeCompositor()
    d = desk(c)
    main = opened(d, c, "canary", "org.kidux.tests.Canary")
    dialog = c.add("python3", parent=main.id)
    d.settle()

    assert f"maximize {main.id}" in c.commands
    assert f"maximize {dialog.id}" not in c.commands


# --- a child with windows (D46) ---------------------------------------------------


def test_with_windows_a_window_is_placed_by_the_compositor_and_left_so():
    c = FakeCompositor()
    d = desk(c, windows=True)
    opened(d, c, "canary", "org.kidux.tests.Canary")
    d.settle()

    assert not any(cmd.startswith(("maximize", "unfullscreen")) for cmd in c.commands)


def test_with_windows_a_window_opens_as_a_window_even_when_it_asks_for_the_screen():
    c = FakeCompositor()
    d = desk(c, windows=True)
    window = opened(d, c, "canary", "org.kidux.tests.Canary", fullscreen=True)
    d.settle()

    assert c.commands.count(f"unfullscreen {window.id}") == 1
    assert f"maximize {window.id}" not in c.commands


def test_with_windows_fullscreen_asked_for_afterwards_is_the_child_s():
    c = FakeCompositor()
    d = desk(c, windows=True)
    window = opened(d, c, "canary", "org.kidux.tests.Canary")
    c.commands.clear()
    c.change(window.id, fullscreen=True)
    d.settle()

    assert c.commands == []


def test_with_windows_two_modules_are_open_at_once():
    c = FakeCompositor()
    d = desk(c, windows=True)
    opened(d, c, "canary", "org.kidux.tests.Canary")
    robin = opened(d, c, "robin", "org.kidux.tests.Robin")
    d.settle()

    assert d.modules == ["canary", "robin"] and c.active().id == robin.id
    assert d.on_screen() == "robin"


# --- closing from the bar (D45) ---------------------------------------------------


def test_close_asks_every_window_of_the_module_on_screen_and_nothing_else():
    c = FakeCompositor()
    d = desk(c)
    first = opened(d, c, "canary", "org.kidux.tests.Canary", maximized=True)
    second = c.add("org.kidux.tests.Canary", maximized=True)
    d.settle()
    robin = opened(d, c, "robin", "org.kidux.tests.Robin", maximized=True)
    d.show("canary")
    d.settle()

    assert d.on_screen() == "canary"
    assert d.close(now=100.0) == "asked"
    closes = sorted(int(cmd.split()[1]) for cmd in c.commands if cmd.startswith("close"))
    assert closes == sorted([first.id, second.id]) and robin.id not in closes


def test_close_on_home_does_nothing():
    c = FakeCompositor()
    d = desk(c)
    opened(d, c, "canary", "org.kidux.tests.Canary", maximized=True)
    d.home()
    d.settle()

    assert d.close(now=100.0) == "nothing"
    assert not any(cmd.startswith("close") for cmd in c.commands)


def test_a_module_that_closes_when_asked_is_never_asked_about():
    c = FakeCompositor()
    ended = []
    d = desk(c, ended=ended)
    window = opened(d, c, "canary", "org.kidux.tests.Canary", maximized=True)
    d.settle()
    d.close(now=100.0)
    c.gone(window.id)
    d.settle()

    assert d.overdue(now=100.0 + CLOSE_SECONDS + 1) is None
    assert d.question is None and ended == []
    assert c.active().id == c.launcher.id


def test_one_still_open_after_the_wait_is_asked_about_not_ended():
    c = FakeCompositor()
    ended, changes = [], []
    d = desk(c, changes, ended)
    opened(d, c, "robin", "org.kidux.tests.Robin", maximized=True)
    d.settle()
    d.close(now=100.0)

    assert d.overdue(now=100.0 + CLOSE_SECONDS - 1) is None
    changes.clear()
    assert d.overdue(now=100.0 + CLOSE_SECONDS) == "robin"
    assert d.question == "robin" and changes and ended == []


def test_cancel_keeps_it_and_asks_nothing_more():
    c = FakeCompositor()
    ended = []
    d = desk(c, ended=ended)
    opened(d, c, "robin", "org.kidux.tests.Robin", maximized=True)
    d.settle()
    d.close(now=100.0)
    d.overdue(now=200.0)
    d.keep()

    assert d.question is None and ended == []
    assert d.overdue(now=300.0) is None
    assert d.modules == ["robin"]


def test_close_it_anyway_ends_its_scope():
    c = FakeCompositor()
    ended = []
    d = desk(c, ended=ended)
    opened(d, c, "robin", "org.kidux.tests.Robin", maximized=True)
    d.settle()
    d.close(now=100.0)
    d.overdue(now=200.0)
    d.end_anyway()

    assert ended == ["robin"] and d.question is None


def test_a_second_close_while_it_is_asked_about_ends_it():
    c = FakeCompositor()
    ended = []
    d = desk(c, ended=ended)
    opened(d, c, "robin", "org.kidux.tests.Robin", maximized=True)
    d.settle()
    d.close(now=100.0)
    d.overdue(now=200.0)

    assert d.close(now=201.0) == "ended"
    assert ended == ["robin"]


def test_a_second_close_before_the_wait_is_over_only_asks_again():
    c = FakeCompositor()
    ended = []
    d = desk(c, ended=ended)
    opened(d, c, "robin", "org.kidux.tests.Robin", maximized=True)
    d.settle()
    d.close(now=100.0)

    assert d.close(now=101.0) == "asked"
    assert ended == []
    # The wait runs from the first request, not the last.
    assert d.overdue(now=100.0 + CLOSE_SECONDS) == "robin"


def test_the_question_goes_when_the_module_closes_after_all():
    c = FakeCompositor()
    d = desk(c)
    window = opened(d, c, "robin", "org.kidux.tests.Robin", maximized=True)
    d.settle()
    d.close(now=100.0)
    d.overdue(now=200.0)
    c.gone(window.id)
    d.settle()

    assert d.question is None


def test_home_is_what_is_on_screen_before_anything_opens():
    d = desk(FakeCompositor())
    d.settle()

    assert d.on_screen() is None and d.current == HOME


# --- the desk: home, and the bar's windows (D57) -----------------------------------


def test_with_windows_home_shows_the_desk_every_window_minimised():
    c = FakeCompositor()
    d = desk(c, windows=True)
    canary = opened(d, c, "canary", "org.kidux.tests.Canary")
    robin = opened(d, c, "robin", "org.kidux.tests.Robin")
    dialog = c.add("python3", parent=robin.id)
    d.settle()

    d.home()

    assert f"minimize {canary.id}" in c.commands and f"minimize {robin.id}" in c.commands
    assert f"minimize {dialog.id}" not in c.commands
    assert c.active().id == c.launcher.id


def test_with_windows_leaving_home_by_a_tile_brings_the_windows_back():
    c = FakeCompositor()
    d = desk(c, windows=True)
    canary = opened(d, c, "canary", "org.kidux.tests.Canary")
    d.home()
    d.settle()

    robin = opened(d, c, "robin", "org.kidux.tests.Robin")
    d.settle()

    assert not next(w for w in c.windows_now if w.id == canary.id).minimized
    assert c.active().id == robin.id and d.on_screen() == "robin"


def test_with_windows_leaving_home_by_the_bar_brings_them_back_the_one_asked_in_front():
    c = FakeCompositor()
    d = desk(c, windows=True)
    canary = opened(d, c, "canary", "org.kidux.tests.Canary")
    robin = opened(d, c, "robin", "org.kidux.tests.Robin")
    hello = opened(d, c, "hello", "org.kidux.modules.Hello")
    c.minimize(hello.id)                       # the child's own
    d.settle()
    d.home()
    d.settle()
    c.commands.clear()

    d.raise_window(canary.id)
    d.settle()

    assert c.commands[-1] == f"activate {canary.id}"
    assert f"activate {robin.id}" in c.commands and f"activate {hello.id}" not in c.commands
    assert next(w for w in c.windows_now if w.id == hello.id).minimized
    assert d.on_screen() == "canary"


def test_with_windows_windows_come_back_once():
    c = FakeCompositor()
    d = desk(c, windows=True)
    canary = opened(d, c, "canary", "org.kidux.tests.Canary")
    d.home()
    d.settle()
    d.show("canary")
    c.minimize(canary.id)                      # by the child, afterwards
    d.settle()
    c.commands.clear()

    opened(d, c, "robin", "org.kidux.tests.Robin")

    assert f"activate {canary.id}" not in c.commands


def test_in_the_kiosk_home_minimises_nothing():
    c = FakeCompositor()
    d = desk(c)
    opened(d, c, "canary", "org.kidux.tests.Canary", maximized=True)
    d.home()

    assert not any(cmd.startswith("minimize") for cmd in c.commands)


def test_the_bar_s_windows_and_a_button_bringing_one_back():
    c = FakeCompositor()
    d = desk(c, windows=True)
    canary = opened(d, c, "canary", "org.kidux.tests.Canary")
    robin = opened(d, c, "robin", "org.kidux.tests.Robin")
    c.minimize(canary.id)
    d.settle()

    assert [(w.id, m) for w, m in d.windows] == [(canary.id, "canary"), (robin.id, "robin")]
    d.raise_window(canary.id)
    d.settle()
    assert c.active().id == canary.id and not c.active().minimized
    assert d.on_screen() == "canary"
    d.raise_window(c.launcher.id)
    assert c.active().id == canary.id


def test_with_windows_the_bar_hears_of_a_window_minimised():
    c = FakeCompositor()
    changes = []
    d = desk(c, changes, windows=True)
    window = opened(d, c, "canary", "org.kidux.tests.Canary")
    d.settle()
    changes.clear()

    c.minimize(window.id)
    d.settle()

    assert changes


def test_a_window_s_title_on_the_bar():
    from kidux_launcher.desk import TITLE_CHARACTERS, title_of

    assert title_of("", "Canary") == "Canary"
    assert title_of("A very long title of a window indeed", "Canary").endswith("…")
    assert len(title_of("x" * 100, "Canary")) == TITLE_CHARACTERS


# --- Alt+Tab: the bar's order, Home not in it (D66) ------------------------------------


def two_open(windows=False):
    """The canary opened, then the robin, the robin on screen."""
    c = FakeCompositor()
    d = desk(c, windows=windows)
    d.settle()
    canary = opened(d, c, "canary", "org.kidux.tests.Canary", maximized=True)
    d.settle()
    robin = opened(d, c, "robin", "org.kidux.tests.Robin", maximized=True)
    d.settle()
    return c, d, canary, robin


def test_alt_tab_goes_to_the_next_in_the_bar_and_wraps_from_the_last_to_the_first():
    c, d, canary, robin = two_open()
    assert d.next_in_bar() == "canary"           # the robin is last: back to the first
    assert d.switch(1) == canary.id and d.switch_done() == canary.id
    d.settle()
    assert d.on_screen() == "canary"
    assert d.next_in_bar() == "robin"
    assert d.switch(1) == robin.id and d.switch_done() == robin.id
    d.settle()
    assert d.on_screen() == "robin"


def test_alt_tab_held_goes_round_the_bar_and_never_home():
    c, d, canary, robin = two_open()
    assert d.switch(1) == canary.id
    assert d.switch(1) == robin.id               # round again, Home skipped
    assert d.switch(1) == canary.id
    assert d.switch(-1) == robin.id              # and back
    assert d.switch_done() == robin.id
    d.settle()
    assert d.on_screen() == "robin"


def test_alt_shift_tab_goes_the_other_way():
    c, d, canary, robin = two_open()
    c.activate(canary.id)
    d.settle()
    assert d.switch(-1) == robin.id              # from the first, back to the last


def test_from_home_alt_tab_goes_to_the_first_and_alt_shift_tab_to_the_last():
    c, d, canary, robin = two_open()
    d.home()
    d.settle()
    assert d.on_screen() is None
    assert d.next_in_bar() == "canary"
    assert d.switch(1) == canary.id
    d.switch_done()
    d.home()
    d.settle()
    assert d.switch(-1) == robin.id


def test_one_module_on_screen_has_nowhere_to_go():
    c = FakeCompositor()
    d = desk(c)
    d.settle()
    assert d.switch(1) is None and d.switch_done() is None and d.next_in_bar() is None
    opened(d, c, "canary", "org.kidux.tests.Canary", maximized=True)
    d.settle()
    assert d.on_screen() == "canary"
    assert d.next_in_bar() is None and d.switch(1) is None and d.switch_done() is None


def test_one_module_open_from_home_goes_to_it():
    c = FakeCompositor()
    d = desk(c)
    d.settle()
    canary = opened(d, c, "canary", "org.kidux.tests.Canary", maximized=True)
    d.settle()
    d.home()
    d.settle()
    assert d.next_in_bar() == "canary" and d.switch(1) == canary.id


def test_the_order_is_the_bar_s_not_the_order_last_used():
    c, d, canary, robin = two_open()
    hello = opened(d, c, "hello", "org.kidux.modules.Hello", maximized=True)
    d.settle()
    c.activate(canary.id)                        # used last: hello, then the canary
    d.settle()
    assert d.switch(1) == robin.id               # but the next in the bar is the robin
    assert d.switch(1) == hello.id
    d.switch_done()


def test_a_module_s_window_is_the_one_last_in_use():
    c, d, canary, robin = two_open()
    second = c.add("org.kidux.tests.Canary", maximized=True)
    d.settle()
    c.activate(second.id)
    d.settle()
    c.activate(robin.id)
    d.settle()
    assert d.switch(1) == second.id
    d.switch_done()


def test_a_dialog_is_never_a_stop_of_its_own():
    c, d, canary, robin = two_open()
    dialog = c.add("org.kidux.tests.Robin", parent=robin.id)
    d.settle()
    c.activate(dialog.id)
    d.settle()
    assert d.on_screen() == "robin"
    assert d.switch(1) == canary.id


def test_on_the_desk_the_round_is_the_windows_in_the_bar_s_order():
    c, d, canary, robin = two_open(windows=True)
    assert d.next_in_bar() == canary.id          # the robin in use, the last
    assert d.switch(1) == canary.id
    assert d.switch(1) == robin.id
    d.switch_done()
    c.activate(canary.id)
    d.settle()
    assert d.next_in_bar() == robin.id


def test_the_bar_hears_when_alt_tab_s_target_changes():
    c = FakeCompositor()
    changes = []
    d = desk(c, changes)
    canary = opened(d, c, "canary", "org.kidux.tests.Canary", maximized=True)
    d.settle()
    opened(d, c, "robin", "org.kidux.tests.Robin", maximized=True)
    d.settle()
    changes.clear()
    c.activate(canary.id)
    d.settle()
    assert changes


def test_a_launcher_started_again_goes_round_windows_it_never_saw_in_use():
    c = FakeCompositor()
    first = desk(c)
    first.settle()
    canary = opened(first, c, "canary", "org.kidux.tests.Canary", maximized=True)
    first.settle()
    first.home()
    first.settle()
    # A new launcher, on Home, which finds the canary open.
    d = desk(c)
    d.settle()
    assert d.switch(1) == canary.id


def test_whose_window():
    c = FakeCompositor()
    d = desk(c)
    d.settle()
    canary = opened(d, c, "canary", "org.kidux.tests.Canary", maximized=True)
    stranger = c.add("org.example.Stranger")
    d.settle()
    assert d.whose(c.launcher.id) == "home" and d.whose(canary.id) == "canary"
    assert d.whose(stranger.id) == "-"


