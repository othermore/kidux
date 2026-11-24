"""Expedition Code (phase-4h-plan.md, step 4.42).

kidux-module-expedition-code, a door to the Expedition Code website (D121),
is installed through the daemon, as the panel installs it, and switched on
for Leo from the command line. Leo opens it by keyboard: Chromium's
application window, filling the room above the bar, shows the site's front
page, known by its night blue, since its pages have no title and Chromium
names the window after the address. The test presses nothing on the page:
it makes no explorer on another person's server. The machine reaches the
internet through QEMU's own network; a site that does not answer is said
so, and still fails the test. Alt+F4 closes it and gives the launcher back;
the lock screen's *Log out* ends the session, and the daemon removes it.
"""

from sessionlib import (
    CHILD,
    CHILD_PASSWORD,
    Machine,
    active_terminal,
    child_session,
    greeter_log,
    journal_count,
    launcher_log,
    launcher_shown,
    on_screen,
    pointer,
    report,
    root,
    wait,
    windows,
)

#: The room above the launcher's bar.
ABOVE_THE_BAR = (0.0, 0.0, 1.0, 0.92)
#: The front page's night blue, a gradient within 20 of it over most of the
#: room (phase-4h-plan.md, section 5).
NIGHT_BLUE = (0x14, 0x1A, 0x38)
#: Where the pointer rests for the guide's picture: the page's right margin,
#: over no link, so that no hand and no address under the window show.
ASIDE = "0.97,0.55"


def daemon(command: str) -> bool:
    """`kidux-as install|remove expedition-code`: the daemon's job, start to end."""
    return root(f"runuser -u debian -- /usr/local/bin/kidux-as {command} expedition-code",
                timeout=1500).stdout.startswith(command + ("ed " if command == "install" else "d "))


def chromium_pid() -> str:
    return root(f"pgrep -u {CHILD} -x chromium | sort -n | head -1").stdout.strip()


def expedition_window() -> dict:
    return next((w for w in windows() if w.get("module") == "expedition-code"), {})


def run(machine: Machine) -> None:
    report("kidux-module-expedition-code installs from the archive through the daemon",
           daemon("install"), root("tail -5 /var/log/apt/term.log").stdout)
    root(f"runuser -u debian -- /usr/local/bin/kidux-as enable {CHILD} expedition-code on")

    before = journal_count("kidux-launcher", "tiles: expedition-code")
    password = machine.mark()
    machine.key("ret")                           # Leo, the first picture
    machine.shown("password", password)
    machine.submit(CHILD_PASSWORD)
    report("Leo signs in to its tile", wait(lambda: child_session() is not None, 30)
           and wait(lambda: journal_count("kidux-launcher", "tiles: expedition-code") > before, 30)
           and launcher_shown(machine), greeter_log() + launcher_log())

    # From Lock, which has the focus, back to the tile, and Enter.
    machine.key("shift-tab")
    machine.key("ret")
    wait(lambda: on_screen() == "expedition-code", 30)
    opened = machine.showing(NIGHT_BLUE, ABOVE_THE_BAR, 0.5, 90, tolerance=20)
    pointer(ASIDE)
    machine.still(3)
    picture = machine.screenshot("module-expedition-code")
    window = expedition_window()
    if window and not opened:
        print("      the site did not answer: the window is there, its front page never came",
              flush=True)
    report("Leo opens it by keyboard: the site's front page, in Chromium, above the bar",
           opened and on_screen() == "expedition-code" and window.get("maximized")
           and not window.get("fullscreen")
           and "expeditioncode.com" in (window.get("title") or ""),
           f"{window}; {picture}\n" + launcher_log())

    # Alt+F4 asks Chromium to close; a page that asks first whether to
    # leave is ended by Alt+F4 again, as the bar's question says (D45).
    ended = journal_count("kidux-launcher", "module expedition-code ended")
    machine.key("alt-f4")
    if not wait(lambda: journal_count("kidux-launcher", "module expedition-code ended") > ended, 20):
        machine.key("alt-f4")
    report("Alt+F4 closes it, and the launcher comes back",
           wait(lambda: journal_count("kidux-launcher", "module expedition-code ended") > ended, 20)
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

    root(f"runuser -u debian -- /usr/local/bin/kidux-as enable {CHILD} expedition-code off")
    report("and the daemon removes it", daemon("remove"), root("tail -5 /var/log/apt/term.log").stdout)
