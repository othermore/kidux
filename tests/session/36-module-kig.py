"""Kig, geometry to move (phase-4e-plan.md, step 4.27).

Installed through the daemon, as the panel installs it, with Kig and the
Wayland plugin of its Qt, and switched on for Leo from the command line.
Leo opens it by keyboard: it comes up in a window filling the room above
the bar, in Leo's language, with its settings in the module's own
directory and KDE's actions a child has no business in switched off
there. Alt+F4 closes it, the launcher comes back, and the daemon removes
it, Kig with it (D100).
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

MODULE = "kig"
PROGRAM = "kig"
HOME = f"/home/{CHILD}"
CONFIG = f"{HOME}/.config/kidux/{MODULE}"
#: The room above the launcher's bar, and the bar.
ABOVE_THE_BAR = (0.0, 0.0, 1.0, 0.92)
BAR = (0xF2, 0xE2, 0xCC)
BAR_BOX = (0.0, 0.94, 1.0, 1.0)


def daemon(command: str) -> bool:
    """`kidux-as install|remove <module>`: the daemon's job, start to end."""
    return root(f"runuser -u debian -- /usr/local/bin/kidux-as {command} {MODULE}",
                timeout=1800).stdout.startswith(command + ("ed " if command == "install" else "d "))


def program_pid() -> str:
    return root(f"pgrep -u {CHILD} -x {PROGRAM} | head -1").stdout.strip()


def module_window() -> dict:
    return next((w for w in windows() if w.get("module") == MODULE), {})


def run(machine: Machine) -> None:
    report(f"kidux-module-{MODULE} installs from the archive through the daemon, with "
           f"{PROGRAM} and its Wayland plugin",
           daemon("install") and root(f"dpkg-query -W -f '${{db:Status-Status}} ' {PROGRAM} "
                                     "qtwayland5").stdout == "installed installed ",
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
    opened = wait(lambda: module_window() != {}, 90, 2)
    wait(lambda: on_screen() == MODULE, 10)
    machine.still(5)
    picture = machine.screenshot(f"module-{MODULE}")
    window = module_window()
    report("Leo opens it by keyboard, a window filling the room above the bar",
           opened and on_screen() == MODULE and window.get("maximized")
           and not window.get("fullscreen")
           and colour_share(picture, CREAM, ABOVE_THE_BAR) < 0.2
           and colour_share(picture, BAR, BAR_BOX) > 0.4,
           f"{window}; {picture}\n" + launcher_log())

    pid = program_pid()
    environment = root(f"tr '\\0' '\\n' < /proc/{pid}/environ").stdout
    report("its settings are the module's own, with KDE's actions for a child switched off",
           f"XDG_CONFIG_HOME={CONFIG}" in environment
           and root(f"grep -qx 'ghns=false' {CONFIG}/kdeglobals").returncode == 0
           and root(f"grep -qx 'shell_access=false' {CONFIG}/kdeglobals").returncode == 0,
           environment + root(f"ls -la {CONFIG}").stdout)

    # Alt+F4 asks it to close; one that asks something first is ended by
    # Alt+F4 again, as the bar's question says (D45).
    ended = journal_count("kidux-launcher", f"module {MODULE} ended")
    machine.key("alt-f4")
    if not wait(lambda: journal_count("kidux-launcher", f"module {MODULE} ended") > ended, 20):
        machine.key("alt-f4")
    report("Alt+F4 closes it, and the launcher comes back",
           wait(lambda: journal_count("kidux-launcher", f"module {MODULE} ended") > ended, 20)
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

    root(f"runuser -u debian -- /usr/local/bin/kidux-as enable {CHILD} {MODULE} off")
    report("and the daemon removes it, and the program with it (D100)",
           daemon("remove") and root(f"dpkg-query -W -f '${{db:Status-Status}}' {PROGRAM}"
                                     ).stdout != "installed",
           root("tail -5 /var/log/apt/term.log").stdout)
