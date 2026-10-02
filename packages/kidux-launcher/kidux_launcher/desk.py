"""The child's desktop: which window is whose, and what is on screen (D43, D46, D58).

The policy, with no GTK in it, so that its test is the specification. labwc
draws and places the windows as its configuration says (session.md,
section 3); the desk knows which module each window is of, which module is
on screen, and what to ask the compositor (`compositor.py`).

A window is of the module whose manifest claims its app_id
(`kidux.modules.claims`); a dialog is of its parent's module; a window no
manifest claims is of the module started from a tile whose first window
has not come yet, when there is one; any other is a stranger, logged once
and left alone. The launcher's own window is home.

The module on screen is the one whose window is active; home when the
launcher's is. A tile shows its module's window when the module is open,
and otherwise starts it and shows its first window when it comes; the
bar's Home and Super show the launcher's window. A module whose last
window closes leaves the bar, and when it was on screen, home comes back.

For a child without windows, the kiosk: labwc makes every main window fill
the room above the bar, without a frame, and leaves a dialog floating over
its window; the desk also takes back fullscreen, since the bar must stay
reachable, and maximises again a main window that is not, as one that
came up fullscreen is once out of it. For a child with windows (D46, D57),
the desk: every window is in labwc's frame, placed as labwc places it,
several in view at once over the launcher's window, which stays below
them; one that comes up fullscreen is taken out of it once, and fullscreen
asked for afterwards is the child's; home shows the desk, every module's
window minimised, and leaving it by a tile or a window's button on the bar
brings them all back as they were, the one asked for in front. labwc
places a new window as if the minimised ones were not there, so a module
opened from home would otherwise come up exactly over the one before.

A module closes from the bar (D45): the module on screen is asked, each of
its windows sent the close request a window's close button sends, so that
a program with unsaved work can say so and decide. One still open
`CLOSE_SECONDS` later is overdue, and the bar asks the child whether to end
it anyway; only on yes, or on a second request for the same module while
the question is up, is its scope stopped.
"""

import logging

from kidux import modules as kidux_modules

from .compositor import LAUNCHER_APP_ID
from .launch import stop

log = logging.getLogger("kidux.launcher")

#: What is on screen when the launcher's window is: no module.
HOME = ""
#: How long a module asked to close has before the bar asks the child.
CLOSE_SECONDS = 10
#: A window's title on its button is cut to this many characters.
TITLE_CHARACTERS = 24


def installed_module_of(app_id: str) -> str | None:
    """The installed module whose manifest claims a window called `app_id`."""
    for module in kidux_modules.installed():
        if kidux_modules.claims(module, app_id):
            return module.id
    return None


def title_of(title: str, name: str) -> str:
    """A window's title for its button: the module's name when it has
    none, and cut with an ellipsis when it is long."""
    title = (title or name).strip()
    if len(title) > TITLE_CHARACTERS:
        return title[:TITLE_CHARACTERS - 1].rstrip() + "…"
    return title


class Desk:
    def __init__(self, compositor, *, module_of=installed_module_of, on_change=None, end=stop,
                 windows: bool = False) -> None:
        self._compositor = compositor
        self._windows = windows
        self._module_of = module_of
        self._on_change = on_change or (lambda: None)
        self._end = end
        #: Each window of a module, by its number, and its module.
        self._owners: dict[int, str] = {}
        #: The window of each module that was last active, to show it again.
        self._last: dict[str, int] = {}
        #: Open modules, in the order they were opened.
        self._order: list[str] = []
        #: Modules started from a tile whose first window has not come yet,
        #: oldest first: shown when it comes.
        self._waiting: list[str] = []
        self._strangers: set[int] = set()
        #: With windows on, the windows already seen once: fullscreen after
        #: that is the child's.
        self._seen: set[int] = set()
        #: Modules asked to close, and when.
        self._asked: dict[str, float] = {}
        #: The module the bar is asking about, overdue: None when none is.
        self.question: str | None = None
        self.current = HOME
        self._told = ""
        self._bar_shows: tuple = ()
        #: With windows on, the windows home minimised, in the compositor's
        #: order: brought back when home is left by a tile or the bar.
        self._put_away: list[int] = []
        #: While Alt+Tab goes round (D66): the bar's buttons, as (the
        #: bar's key, the window it brings forward), in the bar's order as
        #: it was when the round began, and where it points.
        self._round: list[tuple] | None = None
        self._round_at = 0

    @property
    def modules(self) -> list[str]:
        """The open modules, in the order they were opened."""
        return list(self._order)

    def windows_of(self, module_id: str) -> list:
        return [t for t in self._compositor.toplevels() if self._owners.get(t.id) == module_id]

    @property
    def windows(self) -> list:
        """Every window of a module, as (window, module id), in the order the
        compositor lists them: what the bar shows for a child with windows."""
        return [(t, self._owners[t.id]) for t in self._compositor.toplevels()
                if t.id in self._owners]

    def raise_window(self, window: int) -> None:
        """A window's button on the bar: forward, and back from minimised."""
        if window in self._owners:
            self._come_back()
            self._compositor.activate(window)

    def _come_back(self) -> None:
        """The windows home put away, back as they were; the child's own
        minimised ones stay so."""
        tops = {t.id: t for t in self._compositor.toplevels()}
        for window in self._put_away:
            if window in tops and tops[window].minimized:
                self._compositor.activate(window)
        self._put_away = []

    def opening(self, module_id: str) -> bool:
        return module_id in self._waiting

    def settle(self) -> None:
        """Read every window the compositor lists and put the desk in order:
        whose each is, which modules are open, which is on screen. The same
        whether it runs after one window opened, after ten, or in a launcher
        started again under modules that outlived the last one."""
        before = (self.modules, self.current, self._bar_shows)
        tops = self._compositor.toplevels()
        present = {t.id for t in tops}
        self._owners = {w: m for w, m in self._owners.items() if w in present}
        self._strangers &= present
        self._seen &= present

        for top in tops:
            if top.app_id == LAUNCHER_APP_ID or top.id in self._owners \
                    or top.id in self._strangers:
                continue
            module_id = self._owners.get(top.parent) if top.parent is not None else None
            module_id = module_id or self._module_of(top.app_id)
            if module_id is None and self._waiting:
                module_id = self._waiting[0]
            if module_id is None:
                self._strangers.add(top.id)
                log.warning("window %d (%s) belongs to no module; left alone", top.id, top.app_id)
                continue
            self._owners[top.id] = module_id
            log.info("window %d (%s) of %s", top.id, top.app_id, module_id)
            if module_id in self._waiting:
                self._waiting.remove(module_id)
                self._compositor.activate(top.id)

        open_now: list[str] = []
        for top in tops:
            module_id = self._owners.get(top.id)
            if module_id is not None and module_id not in open_now:
                open_now.append(module_id)
        for module_id in [m for m in self._order if m not in open_now]:
            self._order.remove(module_id)
            self._last.pop(module_id, None)
            if module_id in self._asked:
                log.info("module %s closed", module_id)
            self._asked.pop(module_id, None)
            if self.question == module_id:
                self.question = None
        self._order.extend(m for m in open_now if m not in self._order)

        for top in tops:
            if top.id in self._owners:
                self._arrange(top)

        active = next((t for t in tops if t.activated), None)
        if active is not None:
            if active.app_id == LAUNCHER_APP_ID:
                self.current = HOME
            elif active.id in self._owners:
                self.current = self._owners[active.id]
                self._last[self.current] = active.id
        if self.current != HOME and self.current not in self._order:
            # The module on screen has closed its last window: home, rather
            # than whichever window the compositor puts forward.
            self.current = HOME
            self._show_home(tops)

        # One line for every change, which the session tests read:
        # app_id=module:flags, "home" for the launcher, "-" for a stranger.
        told = " ".join(f"{t.app_id}={self._whose(t)}:{t.flags()}" for t in tops)
        if told != self._told:
            self._told = told
            log.info("toplevels: %s", told or "none")
        self._bar_shows = self._shown() + (self.next_in_bar(),)
        if (self.modules, self.current, self._bar_shows) != before:
            if self.current != before[1]:
                log.info("on screen: %s", self.current or "home")
            self._on_change()

    def whose(self, window: int) -> str:
        """"home" for the launcher's window, the module's id for one of a
        module's, "-" for a stranger's."""
        top = next((t for t in self._compositor.toplevels() if t.id == window), None)
        if top is not None and top.app_id == LAUNCHER_APP_ID:
            return "home"
        return self._owners.get(window, "-")

    def _bar_round(self) -> list[tuple]:
        """The bar's buttons, left to right, as (the bar's key, the window
        Alt+Tab brings forward for it): for a child without windows, each
        open module, its key its id and its window the main one last in use,
        else its first; for a child with windows, each main window, its key
        its number. Home is not among them: Super goes home (D66)."""
        tops = self._compositor.toplevels()
        mains = [t.id for t in tops if t.id in self._owners and t.parent is None]
        if self._windows:
            return [(window, window) for window in mains]
        buttons = []
        for module_id in self._order:
            own = [w for w in mains if self._owners[w] == module_id]
            if own:
                last = self._last.get(module_id)
                buttons.append((module_id, last if last in own else own[0]))
        return buttons

    def _in_use(self):
        """The bar's key of what is on screen: a module's id, or on the desk
        the main window in use, a dialog's own; None on Home."""
        if not self._windows:
            return None if self.current == HOME else self.current
        active = next((t for t in self._compositor.toplevels() if t.activated), None)
        if active is None or active.id not in self._owners:
            return None
        return active.parent if active.parent is not None else active.id

    def _step_from_here(self, buttons: list[tuple], step: int) -> int | None:
        """Where one step of Alt+Tab goes from what is on screen, as an index
        into `buttons`: the next button to the right (step 1) or left (-1),
        the last wrapping to the first; from Home, the first or the last.
        None when there is nowhere else to go."""
        if not buttons:
            return None
        keys = [key for key, _window in buttons]
        here = self._in_use()
        if here not in keys:
            return 0 if step > 0 else len(buttons) - 1
        at = keys.index(here)
        there = (at + step) % len(buttons)
        return None if there == at else there

    def next_in_bar(self):
        """The bar's key of where one Alt+Tab goes now, for the bar's
        tooltip: a module's id, or on the desk a window's number; None when
        it goes nowhere."""
        buttons = self._bar_round()
        there = self._step_from_here(buttons, 1)
        return None if there is None else buttons[there][0]

    def switch(self, step: int) -> int | None:
        """Alt+Tab (step 1) or Alt+Shift+Tab (-1), held down: the window the
        round now points at. It goes round the bar's buttons in the bar's
        order, from the one after what is on screen, the last wrapping to
        the first; None with nowhere to go (D66)."""
        if self._round is None:
            buttons = self._bar_round()
            there = self._step_from_here(buttons, step)
            if there is None:
                return None
            self._round, self._round_at = buttons, there
        else:
            self._round_at = (self._round_at + step) % len(self._round)
        return self._round[self._round_at][1]

    def switch_done(self) -> int | None:
        """Alt let go: the window the round points at brought forward, and
        the round over."""
        if self._round is None:
            return None
        _key, window = self._round[self._round_at]
        self._round = None
        if window in self._owners:
            self.raise_window(window)
        else:
            self._compositor.activate(window)
        return window

    def _shown(self) -> tuple:
        """What the bar shows of each window for a child with windows: its
        title, and whether it is in use or minimised. Nothing without them,
        where the bar shows modules."""
        if not self._windows:
            return ()
        return tuple((t.id, t.title, t.activated, t.minimized) for t, _ in self.windows)

    def _whose(self, top) -> str:
        if top.app_id == LAUNCHER_APP_ID:
            return "home"
        return self._owners.get(top.id, "-")

    def _arrange(self, top) -> None:
        if self._windows:
            if top.id not in self._seen:
                self._seen.add(top.id)
                if top.fullscreen:
                    # Opens as a window all the same: fullscreen is the
                    # child's to ask for once it is there.
                    self._compositor.unfullscreen(top.id)
            return
        if top.fullscreen:
            # The bar must stay reachable: no window keeps the whole screen.
            self._compositor.unfullscreen(top.id)
        elif top.parent is None and not top.maximized and not top.minimized:
            self._compositor.maximize(top.id)

    def _show_home(self, tops=None) -> None:
        for top in tops if tops is not None else self._compositor.toplevels():
            if top.app_id == LAUNCHER_APP_ID:
                self._compositor.activate(top.id)
                return

    def open(self, module_id: str, start) -> None:
        """A tile was activated: show the module if it is open; otherwise
        `start()` it, and show it when its first window comes."""
        if module_id in self._order:
            self.show(module_id)
            return
        if module_id in self._waiting:
            return
        self._come_back()
        self._waiting.append(module_id)
        if not start():
            self._waiting.remove(module_id)

    def ended(self, module_id: str) -> None:
        """A module's program has ended, whether or not it ever had a window."""
        if module_id in self._waiting:
            self._waiting.remove(module_id)
        self.settle()

    def show(self, module_id: str) -> None:
        """Bring the module's window forward: the one last active, or its
        first."""
        windows = self.windows_of(module_id)
        if not windows:
            return
        last = self._last.get(module_id)
        window = next((w for w in windows if w.id == last), None) \
            or next((w for w in windows if w.parent is None), windows[0])
        self._come_back()
        self._compositor.activate(window.id)

    def home(self) -> None:
        """Home, from the bar or Super: the launcher's window forward. On the
        desk it stays below the windows, so they are minimised to show it,
        and remembered to come back."""
        if self._windows:
            for top in self._compositor.toplevels():
                if top.id in self._owners and top.parent is None and not top.minimized:
                    self._compositor.minimize(top.id)
                    self._put_away.append(top.id)
        self._show_home()

    def on_screen(self) -> str | None:
        """The module on screen; None for home."""
        return self.current or None

    def close(self, now: float) -> str:
        """Close the module on screen, as the bar's button or its key asks:
        "asked" when its windows were sent the close request, "ended" when
        the bar was already asking about it and it is ended now, "nothing"
        on home."""
        module_id = self.on_screen()
        if module_id is None:
            return "nothing"
        if self.question == module_id:
            self.end_anyway()
            return "ended"
        log.info("asking %s to close", module_id)
        # Asked again before the wait is over, the wait goes on from the
        # first request: pressing Close again and again must not put the
        # question off.
        self._asked.setdefault(module_id, now)
        for window in self.windows_of(module_id):
            self._compositor.close(window.id)
        return "asked"

    def overdue(self, now: float) -> str | None:
        """The module asked to close longest ago that is still open after
        `CLOSE_SECONDS`, which the bar now asks about; None when none is."""
        self.settle()
        late = [m for m, asked in sorted(self._asked.items(), key=lambda item: item[1])
                if m in self._order and now - asked >= CLOSE_SECONDS]
        if late and self.question is None:
            self.question = late[0]
            log.info("module %s did not close; asking", self.question)
            self._on_change()
        return self.question

    def keep(self) -> None:
        """The child said Cancel: the module stays, and nothing is asked."""
        if self.question is not None:
            log.info("module %s kept open", self.question)
            self._asked.pop(self.question, None)
            self.question = None
            self._on_change()

    def end_anyway(self) -> None:
        """The child said to close it anyway: the module's scope is stopped."""
        module_id = self.question
        if module_id is None:
            return
        log.info("ending %s", module_id)
        self.question = None
        self._end(module_id)
        self._on_change()
