"""CodeCombat (phase-4b-plan.md, step 4.13).

kidux-module-codecombat, a door to the CodeCombat website (D86), is
installed through the daemon, as the panel installs it, and switched on for
Leo from the command line. Leo opens it by keyboard: Chromium's application
window, filling the room above the bar, shows CodeCombat's front page from
the internet. The machine reaches the internet through QEMU's own network;
a site that does not answer is said so, and still fails the test. Alt+F4
closes it and gives the launcher back; the lock screen's *Log out* ends the
session, and the daemon removes it.
"""

from sessionlib import (
    CHILD,
    CHILD_PASSWORD,
    CREAM,
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

#: The room above the launcher's bar.
ABOVE_THE_BAR = (0.0, 0.0, 1.0, 0.92)


def daemon(command: str) -> bool:
    """`kidux-as install|remove codecombat`: the daemon's job, start to end."""
    return root(f"runuser -u debian -- /usr/local/bin/kidux-as {command} codecombat",
                timeout=1500).stdout.startswith(command + ("ed " if command == "install" else "d "))


def chromium_pid() -> str:
    return root(f"pgrep -u {CHILD} -x chromium | sort -n | head -1").stdout.strip()


def combat_window() -> dict:
    return next((w for w in windows() if w.get("module") == "codecombat"), {})


def run(machine: Machine) -> None:
    report("kidux-module-codecombat installs from the archive through the daemon",
           daemon("install"), root("tail -5 /var/log/apt/term.log").stdout)
    root(f"runuser -u debian -- /usr/local/bin/kidux-as enable {CHILD} codecombat on")

    before = journal_count("kidux-launcher", "tiles: codecombat")
    password = machine.mark()
    machine.key("ret")                           # Leo, the first picture
    machine.shown("password", password)
    machine.submit(CHILD_PASSWORD)
    report("Leo signs in to its tile", wait(lambda: child_session() is not None, 30)
           and wait(lambda: journal_count("kidux-launcher", "tiles: codecombat") > before, 30)
           and launcher_shown(machine), greeter_log() + launcher_log())

    # From Lock, which has the focus, back to the tile, and Enter.
    machine.key("shift-tab")
    machine.key("ret")
    opened = wait(lambda: "CodeCombat" in (combat_window().get("title") or ""), 90, 2)
    wait(lambda: on_screen() == "codecombat", 10)
    machine.still(5)
    picture = machine.screenshot("module-codecombat")
    window = combat_window()
    if window and not opened:
        print("      the site did not answer: the window is there, CodeCombat's title never came",
              flush=True)
    report("Leo opens it by keyboard: CodeCombat's front page, in Chromium, above the bar",
           opened and on_screen() == "codecombat" and window.get("maximized")
           and not window.get("fullscreen")
           and colour_share(picture, CREAM, ABOVE_THE_BAR) < 0.2,
           f"{window}; {picture}\n" + launcher_log())

    # Alt+F4 asks Chromium to close; a page that asks first whether to
    # leave is ended by Alt+F4 again, as the bar's question says (D45).
    ended = journal_count("kidux-launcher", "module codecombat ended")
    machine.key("alt-f4")
    if not wait(lambda: journal_count("kidux-launcher", "module codecombat ended") > ended, 20):
        machine.key("alt-f4")
    report("Alt+F4 closes it, and the launcher comes back",
           wait(lambda: journal_count("kidux-launcher", "module codecombat ended") > ended, 20)
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

    root(f"runuser -u debian -- /usr/local/bin/kidux-as enable {CHILD} codecombat off")
    report("and the daemon removes it", daemon("remove"), root("tail -5 /var/log/apt/term.log").stdout)
