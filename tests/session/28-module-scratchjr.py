"""ScratchJr, for the youngest (phase-4-plan.md, step 4.6).

Installed through the daemon, as the panel installs it, and switched on for
Leo from the command line. Leo opens it by keyboard: the app, in the
Electron it carries, comes up filling the room above the bar, with the
machine's Chromium options that the panel's Advanced settings keep, and
makes the folder of Leo's Documents it keeps the projects in. Alt+F4 closes it, the
launcher comes back, the folder stays, and the daemon removes the module.

Electron is a large program for the machine's software rendering: the wait
for its window is two minutes.
"""

from sessionlib import (
    CHILD,
    CHILD_PASSWORD,
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

PROJECTS = f"/home/{CHILD}/{SPEAKS['folders'][0]}/ScratchJR"
#: ScratchJr's sky blue, along the top of its first screen, and the bar.
SKY = (0x35, 0xA8, 0xE0)
TOP = (0.0, 0.0, 1.0, 0.3)
BAR = (0xF2, 0xE2, 0xCC)
BAR_BOX = (0.0, 0.94, 1.0, 1.0)


def daemon(command: str) -> bool:
    """`kidux-as install|remove scratchjr`: the daemon's job, start to end."""
    return root(f"runuser -u debian -- /usr/local/bin/kidux-as {command} scratchjr",
                timeout=1500).stdout.startswith(command + ("ed " if command == "install" else "d "))


def scratchjr_pid() -> str:
    return root(f"pgrep -u {CHILD} -x ScratchJr | sort -n | head -1").stdout.strip()


def scratchjr_window() -> dict:
    return next((w for w in windows() if w.get("module") == "scratchjr"), {})


def run(machine: Machine) -> None:
    report("kidux-module-scratchjr installs from the archive through the daemon, as the panel "
           "asks", daemon("install"), root("tail -5 /var/log/apt/term.log").stdout)
    root(f"runuser -u debian -- /usr/local/bin/kidux-as enable {CHILD} scratchjr on")
    # The option the development MacBook's Radeon needs (D52, D75).
    root("runuser -u debian -- /usr/local/bin/kidux-as set-config chromium_flags "
         "'[\"--disable-gpu-compositing\"]'")

    before = journal_count("kidux-launcher", "tiles: scratchjr")
    password = machine.mark()
    machine.key("ret")                           # Leo, the first picture
    machine.shown("password", password)
    machine.submit(CHILD_PASSWORD)
    report("Leo signs in to its tile", wait(lambda: child_session() is not None, 30)
           and wait(lambda: journal_count("kidux-launcher", "tiles: scratchjr") > before, 30)
           and launcher_shown(machine), greeter_log() + launcher_log())

    # From Lock, which has the focus, back to the tile, and Enter.
    machine.key("shift-tab")
    machine.key("ret")
    opened = wait(lambda: scratchjr_window() != {}, 120, 2)
    wait(lambda: on_screen() == "scratchjr", 10)
    machine.still(15)
    picture = machine.screenshot("module-scratchjr")
    window = scratchjr_window()
    report("Leo opens it by keyboard, a window filling the room above the bar",
           opened and on_screen() == "scratchjr" and window.get("maximized")
           and not window.get("fullscreen")
           and colour_share(picture, SKY, TOP, tolerance=16) > 0.4
           and colour_share(picture, BAR, BAR_BOX) > 0.4,
           f"{window}; {picture}\n" + launcher_log())
    arguments = root(f"tr '\\0' ' ' < /proc/{scratchjr_pid()}/cmdline").stdout
    report("it draws with the machine's Chromium options, as the web modules' Chromium does",
           "--disable-gpu-compositing" in arguments, arguments)
    root("runuser -u debian -- /usr/local/bin/kidux-as set-config chromium_flags '[]'")
    report("it keeps Leo's projects in a folder of Leo's Documents",
           wait(lambda: root(f"test -d '{PROJECTS}'").returncode == 0, 30),
           root(f"ls -la /home/{CHILD}/{SPEAKS['folders'][0]}").stdout)

    # Alt+F4 asks it to close; a ScratchJr that asks something first is
    # ended by Alt+F4 again, as the bar's question says (D45).
    ended = journal_count("kidux-launcher", "module scratchjr ended")
    machine.key("alt-f4")
    if not wait(lambda: journal_count("kidux-launcher", "module scratchjr ended") > ended, 20):
        machine.key("alt-f4")
    report("Alt+F4 closes it, and the launcher comes back",
           wait(lambda: journal_count("kidux-launcher", "module scratchjr ended") > ended, 20)
           and wait(lambda: on_screen() == "home", 10) and scratchjr_pid() == "",
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

    root(f"runuser -u debian -- /usr/local/bin/kidux-as enable {CHILD} scratchjr off")
    report("the daemon removes it, and Leo's projects stay in Leo's Documents",
           daemon("remove") and root(f"test -d '{PROJECTS}'").returncode == 0,
           root("tail -5 /var/log/apt/term.log").stdout)
