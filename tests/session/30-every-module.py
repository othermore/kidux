"""Every learning module at once, as a family has them (docs/dev/website.md).

The six modules a child is meant to use are installed through the daemon, as
the panel installs them, and switched on for Leo. Signed in, his launcher
shows a tile for each: the picture the website and the README open with.
Logged out, given windows and signed in again, he opens Blockly Games from
its tile and Tux Typing from the desk, each a window in labwc's frame, both
in view at once and both on the bar: the website's picture of windows. Both
are closed, windows are switched off again, Leo logs out, and the daemon
removes the six.

GCompris's and Scratch's packages are large: an installation may take half
an hour.
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

#: The modules, in the order of their tiles.
MODULES = ("blockly-games", "gcompris", "scratch", "scratchjr", "turbowarp", "tuxtype")
AS = "runuser -u debian -- /usr/local/bin/kidux-as"
#: A tile's white, and where the row of tiles is.
WHITE, TILES = (0xFF, 0xFF, 0xFF), (0.08, 0.33, 0.92, 0.63)
#: The blue of Tux Typing's menu, drawn after a black screen of its makers',
#: and the middle of the screen, where its window opens.
TUX_BLUE, MIDDLE = (0x1A, 0x48, 0x98), (0.25, 0.2, 0.75, 0.8)


def daemon(command: str, module: str) -> bool:
    """`kidux-as install|remove <module>`: the daemon's job, start to end."""
    return root(f"{AS} {command} {module}", timeout=1800).stdout.startswith(
        command + ("ed " if command == "install" else "d "))


def last(word: str) -> str:
    """The launcher's last word on its `tiles` or its `bar`: modules' ids."""
    lines = root(f"journalctl -b -o cat -t kidux-launcher | grep '{word}: '").stdout.splitlines()
    return lines[-1].split(f"{word}: ", 1)[1] if lines else ""


def window(module: str) -> dict:
    return next((w for w in windows() if w.get("module") == module), {})


def sign_in(machine: Machine) -> bool:
    """Leo signs in; done when his new launcher has drawn the six tiles."""
    before = journal_count("kidux-launcher", "tiles: ")
    password = machine.mark()
    machine.key("ret")                           # Leo, the first picture
    machine.shown("password", password)
    machine.submit(CHILD_PASSWORD)
    return (wait(lambda: child_session() is not None, 30)
            and wait(lambda: journal_count("kidux-launcher", "tiles: ") > before, 30)
            and last("tiles") == " ".join(MODULES) and launcher_shown(machine))


def log_out(machine: Machine) -> bool:
    """The power button, then Log out on the lock screen, and Leo's password."""
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
    ended = wait(lambda: child_session() is None, 30)
    machine.shown("choose", choose, 30)
    return ended


def close(machine: Machine, module: str) -> bool:
    """Alt+F4 on the window in use; again for a module that asks first (D45)."""
    ended = journal_count("kidux-launcher", f"module {module} ended")
    machine.key("alt-f4")
    if not wait(lambda: journal_count("kidux-launcher", f"module {module} ended") > ended, 20):
        machine.key("alt-f4")
    return wait(lambda: journal_count("kidux-launcher", f"module {module} ended") > ended, 20)


def run(machine: Machine) -> None:
    installed = [module for module in MODULES if daemon("install", module)]
    report("the six modules install from the archive through the daemon",
           installed == list(MODULES), f"{installed}\n" + root("tail -5 /var/log/apt/term.log").stdout)
    for module in MODULES:
        root(f"{AS} enable {CHILD} {module} on")

    report("Leo signs in to a tile for each", sign_in(machine),
           f"tiles: {last('tiles')}\n" + greeter_log() + launcher_log())
    machine.still(5)
    picture = machine.screenshot("launcher-modules")
    report("his launcher shows the six tiles in a row",
           colour_share(picture, WHITE, TILES) > 0.3, str(picture))
    report("Leo logs out", log_out(machine), greeter_log())

    root(f"{AS} set-profile {CHILD} windows on")
    report("with windows, Leo signs in to the same tiles", sign_in(machine),
           f"tiles: {last('tiles')}\n" + greeter_log() + launcher_log())

    # From Lock, which has the focus, back to the tiles, the first: Blockly Games.
    machine.key("shift-tab")
    machine.key("home")
    machine.key("ret")
    opened = wait(lambda: window("blockly-games") != {}, 90, 2)
    machine.still(8)
    games = window("blockly-games")
    report("Blockly Games opens as a window",
           opened and not games.get("maximized") and not games.get("fullscreen"), str(games))

    # Super shows the desk, the focus on the tile last used; End is the last
    # tile, Tux Typing.
    machine.key("meta_l")
    wait(lambda: on_screen() == "home", 10)
    launcher_shown(machine)
    machine.key("end")
    machine.key("ret")
    opened = wait(lambda: window("tuxtype") != {}, 60, 2)
    drawn = machine.showing(TUX_BLUE, MIDDLE, share=0.4, seconds=60, tolerance=40)
    machine.still(5)
    picture = machine.screenshot("windows-modules")
    typing, games = window("tuxtype"), window("blockly-games")
    report("Tux Typing opens over it: two windows in view at once, both on the bar",
           opened and drawn and last("bar") == "blockly-games tuxtype"
           and not typing.get("maximized") and not typing.get("fullscreen")
           and games.get("minimized") is False,
           f"{typing}, {games}, bar: {last('bar')}; {picture}")

    report("Alt+F4 closes each in turn", close(machine, "tuxtype") and close(machine, "blockly-games"),
           launcher_log())
    root(f"{AS} set-profile {CHILD} windows off")
    report("Leo logs out", log_out(machine), greeter_log())

    for module in MODULES:
        root(f"{AS} enable {CHILD} {module} off")
    removed = [module for module in MODULES if daemon("remove", module)]
    report("and the daemon removes the six", removed == list(MODULES),
           f"{removed}\n" + root("tail -5 /var/log/apt/term.log").stdout)
