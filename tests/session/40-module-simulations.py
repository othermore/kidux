"""Simulations, PhET's simulations served on the computer (phase-4f-plan.md,
step 4.30).

kidux-module-simulations is installed through the daemon, as the panel
installs it, and switched on for Leo from the command line. Leo opens it by
keyboard: Chromium's application window, filling the room above the bar,
shows the page of Kidux's own that lists the simulations, titled in Leo's
language. Enter on the first tile, which has the focus, opens that
simulation in the page's frame, under the bar that goes back, and the
window takes its title; Alt+Left comes back to the list. Alt+F4 closes it
and gives the launcher back; the lock screen's *Log out* ends the session,
and the daemon removes it.
"""

import time

from sessionlib import (
    CHILD,
    CHILD_PASSWORD,
    CREAM,
    SPEAKS,
    Machine,
    active_terminal,
    child_session,
    colour_share,
    greeter_log,
    journal_count,
    launcher_log,
    launcher_shown,
    on_screen,
    report,
    root,
    wait,
    windows,
)

MODULE = "simulations"
#: The page's title, and the first simulation's, in each language.
TITLES = {"es": ("Simulaciones", "Haz un Diez"), "en": ("Simulations", "Make a Ten")}
#: The room above the launcher's bar, and the bar; the page's own bar over
#: an open simulation is the same colour, along the top.
ABOVE_THE_BAR = (0.0, 0.0, 1.0, 0.92)
BAR = (0xF2, 0xE2, 0xCC)
BAR_BOX = (0.0, 0.94, 1.0, 1.0)
PAGE_BAR = (0.3, 0.0, 1.0, 0.05)


def daemon(command: str) -> bool:
    """`kidux-as install|remove simulations`: the daemon's job, start to end."""
    return root(f"runuser -u debian -- /usr/local/bin/kidux-as {command} {MODULE}",
                timeout=1800).stdout.startswith(command + ("ed " if command == "install" else "d "))


def chromium_pid() -> str:
    return root(f"pgrep -u {CHILD} -x chromium | sort -n | head -1").stdout.strip()


def module_window() -> dict:
    return next((w for w in windows() if w.get("module") == MODULE), {})


def title() -> str:
    return module_window().get("title") or ""


def run(machine: Machine) -> None:
    page, first = TITLES[SPEAKS["lang"]]
    report("kidux-module-simulations installs from the archive through the daemon, and the "
           "server answers for its page and for a simulation",
           daemon("install")
           and root("curl -fsS http://127.0.0.1:8123/simulations/ | grep -q 'Simulaciones'"
                    ).returncode == 0
           and root("curl -fsS -o /dev/null "
                    "http://127.0.0.1:8123/simulations/sims/make-a-ten_all.html").returncode == 0,
           root("tail -5 /var/log/apt/term.log").stdout)
    root(f"runuser -u debian -- /usr/local/bin/kidux-as enable {CHILD} {MODULE} on")

    before = journal_count("kidux-launcher", f"tiles: {MODULE}")
    password = machine.mark()
    machine.key("ret")                           # Leo, the first picture
    machine.shown("password", password)
    machine.submit(CHILD_PASSWORD)
    report("Leo signs in to its tile", wait(lambda: child_session() is not None, 30)
           and wait(lambda: journal_count("kidux-launcher", f"tiles: {MODULE}") > before, 30)
           and launcher_shown(machine), greeter_log() + launcher_log())

    # From Lock, which has the focus, back to the tile, and Enter.
    machine.key("shift-tab")
    machine.key("ret")
    opened = wait(lambda: title() == page, 60, 2)
    wait(lambda: on_screen() == MODULE, 10)
    machine.still(5)
    picture = machine.screenshot(f"module-{MODULE}")
    window = module_window()
    report("Leo opens it by keyboard: the list, in Chromium, above the bar, in Leo's language",
           opened and on_screen() == MODULE and window.get("maximized")
           and not window.get("fullscreen")
           and colour_share(picture, BAR, BAR_BOX) > 0.4,
           f"{window}; {picture}\n" + launcher_log())

    # The first tile has the focus: Enter opens its simulation in the frame.
    machine.key("ret")
    shown = wait(lambda: title() == first, 30, 1)
    time.sleep(8)                                # PhET's own start, to its screens
    machine.still(5)
    picture = machine.screenshot(f"module-{MODULE}-open")
    report("Enter opens the first simulation in the frame, under the bar that goes back",
           shown and colour_share(picture, BAR, PAGE_BAR) > 0.5
           and colour_share(picture, CREAM, ABOVE_THE_BAR) < 0.5,
           f"title {title()!r}; {picture}")

    machine.key("alt-left")
    report("Alt+Left comes back to the list", wait(lambda: title() == page, 20, 1),
           f"title {title()!r}")

    # Alt+F4 asks Chromium to close; a page that asks first whether to
    # leave is ended by Alt+F4 again, as the bar's question says (D45).
    ended = journal_count("kidux-launcher", f"module {MODULE} ended")
    machine.key("alt-f4")
    if not wait(lambda: journal_count("kidux-launcher", f"module {MODULE} ended") > ended, 20):
        machine.key("alt-f4")
    report("Alt+F4 closes it, and the launcher comes back",
           wait(lambda: journal_count("kidux-launcher", f"module {MODULE} ended") > ended, 20)
           and wait(lambda: on_screen() == "home", 10),
           launcher_log())

    locked = machine.mark()
    machine.monitor("system_powerdown")
    wait(lambda: active_terminal() == "tty8", 20)
    machine.shown("locked", locked)
    machine.key("tab")
    machine.key("tab")
    asked = machine.mark()
    machine.key("ret")
    machine.shown("child_password", asked)
    choose = machine.submit(CHILD_PASSWORD)
    report("Leo logs out from the lock screen, and Chromium goes with the session",
           wait(lambda: child_session() is None and chromium_pid() == "", 30), greeter_log())
    machine.shown("choose", choose, 30)

    root(f"runuser -u debian -- /usr/local/bin/kidux-as enable {CHILD} {MODULE} off")
    report("and the daemon removes it", daemon("remove"),
           root("tail -5 /var/log/apt/term.log").stdout)
