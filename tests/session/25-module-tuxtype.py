"""Tux Typing, the typing course (phase-4-plan.md, step 4.3).

Installed through the daemon, as the panel installs it, and switched on for
Leo from the command line. Leo opens it by keyboard: it comes up in a
window of its own, through XWayland, its pictures scaled to fill the room
above the bar, with the words of Leo's language where Tux Typing has them
(Spanish, `--theme espanol`), and its home the module's own directory, not
Leo's. Alt+F4 closes it, the launcher comes back, and the daemon removes it.
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

HOME = f"/home/{CHILD}"
DATA = f"{HOME}/.local/share/kidux/tuxtype"
#: The room above the launcher's bar, and the bar.
ABOVE_THE_BAR = (0.0, 0.0, 1.0, 0.92)
BAR = (0xF2, 0xE2, 0xCC)
BAR_BOX = (0.0, 0.94, 1.0, 1.0)


def daemon(command: str) -> bool:
    """`kidux-as install|remove tuxtype`: the daemon's job, start to end."""
    return root(f"runuser -u debian -- /usr/local/bin/kidux-as {command} tuxtype",
                timeout=1200).stdout.startswith(command + ("ed " if command == "install" else "d "))


def tuxtype_pid() -> str:
    return root(f"pgrep -u {CHILD} -x tuxtype | head -1").stdout.strip()


def tuxtype_window() -> dict:
    return next((w for w in windows() if w.get("module") == "tuxtype"), {})


def run(machine: Machine) -> None:
    report("kidux-module-tuxtype installs from the archive through the daemon, as the panel "
           "asks", daemon("install"), root("tail -5 /var/log/apt/term.log").stdout)
    root(f"runuser -u debian -- /usr/local/bin/kidux-as enable {CHILD} tuxtype on")

    before = journal_count("kidux-launcher", "tiles: tuxtype")
    password = machine.mark()
    machine.key("ret")                           # Leo, the first picture
    machine.shown("password", password)
    machine.submit(CHILD_PASSWORD)
    report("Leo signs in to its tile", wait(lambda: child_session() is not None, 30)
           and wait(lambda: journal_count("kidux-launcher", "tiles: tuxtype") > before, 30)
           and launcher_shown(machine), greeter_log() + launcher_log())

    # From Lock, which has the focus, back to the tile, and Enter.
    machine.key("shift-tab")
    machine.key("ret")
    opened = wait(lambda: tuxtype_window() != {}, 60, 2)
    wait(lambda: on_screen() == "tuxtype", 10)
    # Past Tux4Kids' splash, to its menu.
    time.sleep(8)
    machine.still(5)
    picture = machine.screenshot("module-tuxtype")
    window = tuxtype_window()
    report("Leo opens it by keyboard, a window filling the room above the bar",
           opened and on_screen() == "tuxtype" and window.get("maximized")
           and not window.get("fullscreen")
           and colour_share(picture, CREAM, ABOVE_THE_BAR) < 0.2
           and colour_share(picture, BAR, BAR_BOX) > 0.4,
           f"{window}; {picture}\n" + launcher_log())

    pid = tuxtype_pid()
    arguments = root(f"tr '\\0' ' ' < /proc/{pid}/cmdline").stdout
    environment = root(f"tr '\\0' '\\n' < /proc/{pid}/environ").stdout
    theme = "--theme espanol" if SPEAKS["lang"] == "es" else ""
    report("in a window, with the words of Leo's language, at home in its own directory",
           "--window" in arguments and "SDL_VIDEODRIVER=" not in environment
           and (theme in arguments if theme else "--theme" not in arguments)
           and f"HOME={DATA}" in environment
           and root(f"test -d {DATA}/.tuxtype").returncode == 0,
           arguments + "\n" + root(f"ls -la {DATA}").stdout)

    # Alt+F4 asks it to close; a Tux Typing that asks something first is
    # ended by Alt+F4 again, as the bar's question says (D45).
    ended = journal_count("kidux-launcher", "module tuxtype ended")
    machine.key("alt-f4")
    if not wait(lambda: journal_count("kidux-launcher", "module tuxtype ended") > ended, 20):
        machine.key("alt-f4")
    report("Alt+F4 closes it, and the launcher comes back",
           wait(lambda: journal_count("kidux-launcher", "module tuxtype ended") > ended, 20)
           and wait(lambda: on_screen() == "home", 10),
           launcher_log())

    # Log out from the lock screen, past Continue and Adult.
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
    report("Leo logs out from the lock screen", wait(lambda: child_session() is None, 30),
           greeter_log())
    machine.shown("choose", choose, 30)

    root(f"runuser -u debian -- /usr/local/bin/kidux-as enable {CHILD} tuxtype off")
    report("and the daemon removes it", daemon("remove"), root("tail -5 /var/log/apt/term.log").stdout)
