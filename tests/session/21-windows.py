"""Windows, a setting of the child: the desk (phase-3-plan.md, steps 3.15,
3.19 and 3.20; D46, D57, D58).

Leo's windows are switched on from the command line, as the panel's switch
does (its picture is taken on his page). Signed in, his session runs labwc's
desk configuration; the robin, which asks for the whole screen, opens as a
window all the same, taken out of it once. Super shows the desk: the robin
minimised, the launcher's tiles in view, and its window still on the bar.
The canary opens from its tile, in labwc's frame, in ink as the window in
use, the robin coming back as home is left, and both are in view at once.
Minimised as its frame's button does, the robin leaves the screen and stays
on the bar, and its tile brings it back; maximised, it fills the room above
the bar and gets the click made over it. A window that asks for fullscreen
afterwards keeps it, and Super still brings the desk back; Alt+F4 closes the
window in use's module. With windows off again, a module whose manifest
needs windows has no tile for him, and the canary fills the room above the
bar. Both are removed at the end.
"""

from sessionlib import (
    CHILD,
    CHILD_PASSWORD,
    SEED_SOURCE,
    Machine,
    active_terminal,
    as_child,
    child_session,
    copy,
    greeter_log,
    journal_count,
    launcher_log,
    launcher_shown,
    colour_share,
    on_screen,
    open_panel,
    report,
    root,
    wait,
    window_of,
)

MODULES = ("canary", "robin")
AS = "runuser -u debian -- /usr/local/bin/kidux-as"
CANARY, ROBIN = "org.kidux.tests.Canary", "org.kidux.tests.Robin"
#: The canary's colour, and the ink of the frame of
#: the window in use (tests/lib/seed/modules/*/run, labwc's themerc-override).
YELLOW, BLUE = (0xF5, 0xC5, 0x18), (0x3A, 0x86, 0xFF)
INK, CREAM = (0x3B, 0x2F, 0x2A), (0xFF, 0xF6, 0xE9)
ABOVE_THE_BAR = (0.0, 0.0, 1.0, 0.92)


def ask(verb: str, app_id: str) -> None:
    """What a program, or a window's button, would ask the compositor, asked
    as Leo (kidux-toplevels)."""
    as_child(f"timeout 10 /usr/local/bin/kidux-toplevels {verb} {app_id}")


def bar() -> str:
    """The launcher's last word on its bar: a module's id per window."""
    lines = root("journalctl -b -o cat -t kidux-launcher | grep 'bar: '").stdout.splitlines()
    return lines[-1].split("bar: ", 1)[1] if lines else ""


def tile(machine: Machine, keys: tuple) -> None:
    """From home, with the focus where the keys start, to a tile, and Enter."""
    machine.still()
    for key in keys:
        machine.key(key)
    machine.key("ret")


def last_tiles() -> str:
    """The launcher's last word on its tiles: their ids, or "none"."""
    lines = root("journalctl -b -o cat -t kidux-launcher | grep 'tiles: '").stdout.splitlines()
    return lines[-1].split("tiles: ", 1)[1] if lines else ""


def sign_in(machine: Machine, tiles: str) -> bool:
    """Leo signs in; done when his new launcher has drawn exactly `tiles`."""
    before = journal_count("kidux-launcher", "tiles: ")
    password = machine.mark()
    machine.key("ret")                           # Leo, the first picture
    machine.shown("password", password)
    machine.submit(CHILD_PASSWORD)
    return (wait(lambda: child_session() is not None, 30)
            and wait(lambda: journal_count("kidux-launcher", "tiles: ") > before, 30)
            and last_tiles() == tiles and launcher_shown(machine))


def log_out(machine: Machine) -> bool:
    """The power button, then Log out on the lock screen, past Continue and
    Adult, and Leo's password."""
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


def run(machine: Machine) -> None:
    for module in MODULES:
        source = SEED_SOURCE / "modules" / module
        for name, mode in (("module.toml", "0644"), ("icon.svg", "0644"), ("run", "0755")):
            copy(source / name, f"/usr/share/kidux/modules/{module}/{name}", mode=mode)
        root(f"{AS} enable {CHILD} {module} on")
    root(f"{AS} set-profile {CHILD} windows on")

    # The panel shows the switch on Leo's page, the first child's.
    report("the panel opens, on Leo's page", open_panel(machine), greeter_log())
    machine.screenshot("panel-child-windows")
    closed = machine.mark()
    machine.key("esc")
    machine.shown("choose", closed)

    report("Leo, with windows, signs in to the two modules' tiles",
           sign_in(machine, "canary robin"), greeter_log() + launcher_log())
    report("his session runs labwc's desk configuration",
           root(f"pgrep -u {CHILD} -f '^labwc -C /usr/share/kidux/labwc/desk '").returncode == 0,
           root(f"ps -u {CHILD} -o pid,args").stdout)

    # The robin, which asks for the whole screen, opens as a window.
    machine.key("shift-tab")
    machine.key("home")
    machine.key("right")
    machine.key("ret")
    opened = wait(lambda: window_of(ROBIN) != {}, 30) and wait(lambda: on_screen() == "robin", 10)
    wait(lambda: window_of(ROBIN).get("fullscreen") is False, 10)
    machine.still()
    picture = machine.screenshot("windows-robin")
    robin = window_of(ROBIN)
    report("the robin, which asks for the whole screen, opens as a window all the same, "
           "taken out of it once",
           opened and not robin.get("fullscreen") and not robin.get("maximized")
           and 0.02 < colour_share(picture, BLUE, ABOVE_THE_BAR) < 0.95,
           f"{robin}; {picture}")

    # Super shows the desk: the robin minimised, on the bar still.
    machine.key("meta_l")
    shown = wait(lambda: on_screen() == "home", 10) \
        and wait(lambda: window_of(ROBIN).get("minimized") is True, 10)
    launcher_shown(machine)
    picture = machine.screenshot("windows-home")
    report("Super shows the desk: the robin minimised, the tiles in view, its window on the bar",
           shown and colour_share(picture, CREAM, ABOVE_THE_BAR) > 0.5 and bar() == "robin",
           f"{window_of(ROBIN)}, bar: {bar()}; {picture}")

    # The canary from its tile: leaving home brings the robin back, and the
    # canary opens over it, placed further down and right, both in view, the
    # canary in labwc's frame, in ink as the window in use.
    tile(machine, ("left",))
    report("the canary opens as a window in labwc's frame, and both are on the bar",
           wait(lambda: window_of(CANARY) != {}, 30) and wait(lambda: on_screen() == "canary", 10)
           and wait(lambda: bar() == "robin canary", 10),
           f"{window_of(CANARY)}, bar: {bar()}\n" + launcher_log())
    wait(lambda: window_of(ROBIN).get("minimized") is False, 10)
    machine.still()
    picture = machine.screenshot("windows-desk")
    canary = window_of(CANARY)
    report("the robin comes back as home is left, both windows in view at once",
           window_of(ROBIN).get("minimized") is False
           and not canary.get("fullscreen") and not canary.get("maximized")
           and colour_share(picture, INK, ABOVE_THE_BAR) > 0.002
           and colour_share(picture, YELLOW, ABOVE_THE_BAR) > 0.02
           and colour_share(picture, BLUE, ABOVE_THE_BAR) > 0.002, f"{canary}; {picture}")

    # Minimised as its frame's button does: off the screen, on the bar; its
    # tile brings it back. Maximised, the room above the bar.
    ask("minimize", ROBIN)
    gone = wait(lambda: window_of(ROBIN).get("minimized") is True, 10)
    machine.still()
    picture = machine.screenshot("windows-minimised")
    report("a minimised window leaves the screen and stays on the bar",
           gone and bar() == "robin canary" and colour_share(picture, BLUE, ABOVE_THE_BAR) < 0.01,
           f"{window_of(ROBIN)}, bar: {bar()}; {picture}")
    machine.key("meta_l")
    wait(lambda: on_screen() == "home", 10)
    tile(machine, ("right",))
    report("and its tile brings it back",
           wait(lambda: window_of(ROBIN).get("minimized") is False, 10)
           and wait(lambda: on_screen() == "robin", 10), str(window_of(ROBIN)))
    ask("maximize", ROBIN)
    wait(lambda: window_of(ROBIN).get("maximized") is True, 10)
    machine.still()
    picture = machine.screenshot("windows-maximised")
    report("maximised, a window fills the room above the bar",
           colour_share(picture, BLUE, ABOVE_THE_BAR) > 0.8, str(picture))
    # The pointer rests over the robin: a click reaches it through labwc's
    # frame bindings.
    machine.click()
    report("a click over it reaches it",
           wait(lambda: root(f"cat /home/{CHILD}/.local/share/kidux/robin/clicks").stdout != "",
                10),
           root(f"ls -l /home/{CHILD}/.local/share/kidux/robin").stdout)

    # A window that asks for the whole screen afterwards keeps it; Super
    # still goes home.
    ask("fullscreen", ROBIN)
    kept = wait(lambda: window_of(ROBIN).get("fullscreen") is True, 10)
    machine.still(3)
    machine.screenshot("windows-fullscreen")
    report("a window that asks for the whole screen keeps it",
           kept and window_of(ROBIN).get("fullscreen") is True, str(window_of(ROBIN)))
    machine.key("meta_l")
    report("and Super still brings the desk back", wait(lambda: on_screen() == "home", 10),
           f"on screen: {on_screen()}")

    # Alt+F4 still closes the module on screen.
    ask("activate", CANARY)
    wait(lambda: on_screen() == "canary", 10)
    machine.key("alt-f4")
    report("Alt+F4 still closes the module on screen",
           wait(lambda: window_of(CANARY) == {}, 15), launcher_log())

    report("logging out ends the session and every window with it", log_out(machine),
           root(f"ps -u {CHILD} -o pid,args").stdout)

    # Windows off, and the robin needing them: no tile for it.
    root(f"{AS} set-profile {CHILD} windows off")
    root("echo 'needs_windows = true' >> /usr/share/kidux/modules/robin/module.toml")
    report("without windows, a module that needs them has no tile for Leo",
           sign_in(machine, "canary"), launcher_log() + last_tiles())
    machine.key("shift-tab")
    machine.key("home")
    machine.key("ret")
    report("and the canary opens as ever, filling the room above the bar",
           wait(lambda: window_of(CANARY).get("maximized") is True, 30)
           and wait(lambda: on_screen() == "canary", 10), str(window_of(CANARY)))
    report("and logging out ends it", log_out(machine), root(f"ps -u {CHILD} -o pid,args").stdout)

    for module in MODULES:
        root(f"{AS} enable {CHILD} {module} off")
        root(f"rm -rf /usr/share/kidux/modules/{module}")
