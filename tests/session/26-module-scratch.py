"""Scratch, the official editor (phase-4-plan.md, step 4.4).

kidux-module-scratch is installed through the daemon, as the panel
installs it, and switched on for Leo from the command line. Leo opens it by
keyboard: Chromium's application window, filling the room above the bar,
shows the editor from the server on the loopback address, its menu bar in
Scratch's purple. Alt+F4 closes it and gives the launcher back; the lock
screen's *Log out* ends the session, and the daemon removes it.

The editor is a large page for the machine's software rendering: the waits
are two minutes.
"""

from sessionlib import (
    CHILD,
    CHILD_PASSWORD,
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

#: Scratch's menu bar along the top of the editor, and the bar below it.
MENU_PURPLE = (0x85, 0x5C, 0xD6)
MENU_BAR = (0.0, 0.0, 1.0, 0.06)
#: The cat of the project the editor starts with, on its stage: there once
#: the project has loaded, which takes longer on a busy machine.
CAT_ORANGE = (0xFF, 0xAB, 0x19)
STAGE = (0.62, 0.12, 0.99, 0.56)
BAR = (0xF2, 0xE2, 0xCC)
BAR_BOX = (0.0, 0.94, 1.0, 1.0)


def daemon(command: str) -> bool:
    """`kidux-as install|remove scratch`: the daemon's job, start to end."""
    return root(f"runuser -u debian -- /usr/local/bin/kidux-as {command} scratch",
                timeout=1500).stdout.startswith(command + ("ed " if command == "install" else "d "))


def chromium_pid() -> str:
    return root(f"pgrep -u {CHILD} -x chromium | sort -n | head -1").stdout.strip()


def scratch_window() -> dict:
    return next((w for w in windows() if w.get("module") == "scratch"), {})


def run(machine: Machine) -> None:
    report("kidux-module-scratch installs from the archive through the daemon, and the server "
           "answers for it",
           daemon("install")
           and root("curl -fsS http://127.0.0.1:8123/scratch/ | grep -qi '<title>'").returncode == 0,
           root("tail -5 /var/log/apt/term.log").stdout)
    root(f"runuser -u debian -- /usr/local/bin/kidux-as enable {CHILD} scratch on")

    before = journal_count("kidux-launcher", "tiles: scratch")
    password = machine.mark()
    machine.key("ret")                           # Leo, the first picture
    machine.shown("password", password)
    machine.submit(CHILD_PASSWORD)
    report("Leo signs in to its tile", wait(lambda: child_session() is not None, 30)
           and wait(lambda: journal_count("kidux-launcher", "tiles: scratch") > before, 30)
           and launcher_shown(machine), greeter_log() + launcher_log())

    # From Lock, which has the focus, back to the tile, and Enter.
    machine.key("shift-tab")
    machine.key("ret")
    opened = wait(lambda: "Scratch" in (scratch_window().get("title") or ""), 120, 2)
    wait(lambda: on_screen() == "scratch", 10)
    # Its title is there before the editor is drawn: wait for its menu bar.
    machine.showing(MENU_PURPLE, MENU_BAR)
    machine.showing(CAT_ORANGE, STAGE, share=0.005)
    machine.still(15)
    picture = machine.screenshot("module-scratch")
    window = scratch_window()
    report("Leo opens it by keyboard: the editor, in Chromium, above the bar",
           opened and on_screen() == "scratch" and window.get("maximized")
           and not window.get("fullscreen")
           and colour_share(picture, MENU_PURPLE, MENU_BAR, tolerance=16) > 0.3
           and colour_share(picture, BAR, BAR_BOX) > 0.4,
           f"{window}; {picture}\n" + launcher_log())

    # Alt+F4 asks Chromium to close; an editor that asks first whether to
    # leave is ended by Alt+F4 again, as the bar's question says (D45).
    ended = journal_count("kidux-launcher", "module scratch ended")
    machine.key("alt-f4")
    if not wait(lambda: journal_count("kidux-launcher", "module scratch ended") > ended, 20):
        machine.key("alt-f4")
    report("Alt+F4 closes it, and the launcher comes back",
           wait(lambda: journal_count("kidux-launcher", "module scratch ended") > ended, 20)
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

    root(f"runuser -u debian -- /usr/local/bin/kidux-as enable {CHILD} scratch off")
    report("and the daemon removes it", daemon("remove"), root("tail -5 /var/log/apt/term.log").stdout)
