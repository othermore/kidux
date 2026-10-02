"""Modules opened from the launcher, several at once (phase-3-plan.md, steps
3.2 and 3.3).

The tests' two stand-in modules, the canary and the robin, are copied into
place over SSH and switched on for Leo from the command line (the panel's
switch is 15-modules.py's). Leo opens the canary by keyboard: it runs in its
own scope with its own settings directory, sees and writes the child's home
like every module (D42), reaches the network as any program of the child's
does, fills the room above the launcher's bar with no frame, and gets the
click made over it. Super
brings the launcher back, the robin, which asks for the whole screen,
opens over the canary with the room above the bar instead (D43), and
Alt+Tab goes round the modules in the bar's order, never home (D66): with
one module on screen it goes nowhere, from Home to the first, from the
last to the first, Alt held down lighting each step on the bar and Alt
let go going there, Alt+Shift+Tab the other way; the robin finds the note
the canary left in Leo's home. The lock freezes both and continuing
brings the same module back; a launcher that crashes comes back home with
both in its bar; a module that ends leaves the bar, and when it was on
screen the launcher comes back. Alt+F4, the bar's *Close* by keyboard,
asks the module on screen to close (D45): the canary goes at once; the
robin, which refuses as a program with unsaved work would, is asked about
on the bar ten seconds later, and Alt+F4 again ends it (*Cancel* and
*Close it anyway* on the bar are the pointer's, which the launcher's unit
tests hold to the same policy). Logging out from the lock screen ends the
session and every module with it. Both are removed at the end.
"""

import time

from sessionlib import (
    CHILD,
    CHILD_PASSWORD,
    CREAM,
    SEED_SOURCE,
    Machine,
    active_terminal,
    as_child,
    child_session,
    colour_middle,
    colour_share,
    copy,
    greeter_log,
    journal_count,
    keyboard,
    launcher_log,
    launcher_shown,
    launcher_pid,
    on_screen,
    report,
    root,
    wait,
    window_of,
)

MODULES = ("canary", "robin")
HOME = f"/home/{CHILD}"
#: What `on_screen` says when the launcher's window is active.
LAUNCHER = "home"
SHARED = f"{HOME}/canary-note.txt"
#: The stand-in modules' windows (tests/lib/seed/modules/*/run), and the bar.
YELLOW = (0xF5, 0xC5, 0x18)
BLUE = (0x3A, 0x86, 0xFF)
#: Lock on the bar: the end of the button, whatever the word's length in
#: the machine's language, and the margin beyond it, which a Lock pushed off
#: the screen would cover.
LOCK = (0x35, 0x84, 0xE4)
LOCK_END = (0.982, 0.94, 0.988, 0.98)
BEYOND_LOCK = (0.994, 0.94, 1.0, 0.98)
BAR = (0xF2, 0xE2, 0xCC)
#: A button of the bar lit while Alt+Tab goes round, and where Home is.
LIT = (0xDB, 0xE8, 0xFB)
HOME_BUTTON = (0.0, 0.94, 0.11, 1.0)
AFTER_HOME = (0.11, 0.94, 1.0, 1.0)
#: Where the bar is on a 1280x800 screen, and the room above it.
BAR_BOX = (0.0, 0.94, 1.0, 1.0)
ABOVE_THE_BAR = (0.0, 0.0, 1.0, 0.92)
#: The top of the screen, where a title bar would be.
TOP_STRIP = (0.0, 0.0, 1.0, 0.03)


def own(module: str) -> tuple[str, str, str]:
    return (f"{HOME}/.local/share/kidux/{module}", f"{HOME}/.config/kidux/{module}",
            f"{HOME}/.cache/kidux/{module}")


def scope_state(module: str) -> str:
    return as_child(f"systemctl --user is-active kidux-module-{module}.scope").stdout.strip()


def pid_of(module: str) -> str:
    return root(f"pgrep -u {CHILD} -f '^/usr/bin/python3 /usr/share/kidux/modules/{module}/run'"
                ).stdout.strip()


def bar() -> str:
    """The launcher's last word on its bar: the open modules, or "none"."""
    lines = root("journalctl -b -o cat -t kidux-launcher | grep 'bar: '").stdout.splitlines()
    return lines[-1].split("bar: ", 1)[1] if lines else ""


def clicks(module: str) -> int:
    """How many presses a stand-in module's window got (its `clicks` note)."""
    return len(root(f"cat {own(module)[0]}/clicks").stdout.splitlines())


def facts(module: str) -> dict:
    """What a stand-in module saw from inside (its `opened` note)."""
    lines = root(f"cat {own(module)[0]}/opened").stdout.splitlines()
    return dict(line.split("=", 1) for line in lines if "=" in line)


def sign_in(machine: Machine) -> bool:
    """Leo, the first picture, then his password; done when his new launcher
    has drawn the tiles, and not before: a key pressed earlier is lost."""
    before = journal_count("kidux-launcher", "tiles: canary robin")
    password = machine.mark()
    machine.key("ret")
    machine.shown("password", password)
    machine.submit(CHILD_PASSWORD)
    return (wait(lambda: child_session() is not None, 30)
            and wait(lambda: journal_count("kidux-launcher", "tiles: canary robin") > before, 30)
            and launcher_shown(machine))


def open_the_first_tile(machine: Machine, module: str, from_lock: bool = True) -> bool:
    """From Lock, which has the focus, back to the tiles, to the first, and
    Enter; or from a tile, which keeps the focus after it opened a module.
    Done when the module's note is written."""
    root(f"rm -f {own(module)[0]}/opened")
    machine.still()
    if from_lock:
        machine.key("shift-tab")
    machine.key("home")
    machine.key("ret")
    return wait(lambda: pid_of(module) != ""
                and root(f"test -s {own(module)[0]}/opened").returncode == 0, 30)


def show_by_its_tile(machine: Machine, module: str) -> bool:
    """From the launcher, with Lock focused, to the first tile, and Enter:
    the module, already open, comes forward."""
    machine.still()
    machine.key("shift-tab")
    machine.key("home")
    machine.key("ret")
    return wait(lambda: on_screen() == module, 10)


def log_out_from_the_lock_screen(machine: Machine) -> bool:
    """The power button, then Log out on the lock screen, past Continue and
    Adult, and Leo's password."""
    before = machine.mark()
    machine.monitor("system_powerdown")
    if not wait(lambda: active_terminal() == "tty8", 20):
        return False
    machine.shown("locked", before)
    machine.key("tab")
    machine.key("tab")
    before = machine.mark()
    machine.key("ret")
    machine.shown("child_password", before)
    machine.type(CHILD_PASSWORD + "\n")
    return wait(lambda: child_session() is None, 30)


def alt_tab() -> str:
    """The launcher's last word on where Alt+Tab goes."""
    lines = root("journalctl -b -o cat -t kidux-launcher | grep 'alt-tab: '").stdout.splitlines()
    return lines[-1].split("alt-tab: ", 1)[1] if lines else ""


def run(machine: Machine) -> None:
    for module in MODULES:
        source = SEED_SOURCE / "modules" / module
        for name, mode in (("module.toml", "0644"), ("icon.svg", "0644"), ("run", "0755")):
            copy(source / name, f"/usr/share/kidux/modules/{module}/{name}", mode=mode)
        root(f"runuser -u debian -- /usr/local/bin/kidux-as enable {CHILD} {module} on")
        root(f"rm -rf {' '.join(own(module))}")

    report("Leo signs in to the two modules' tiles", sign_in(machine),
           greeter_log() + launcher_log())

    # Ctrl+Alt+F2 inside a child's session: the compositor has the key built
    # in, and logind refuses the child the switch (session.md section 6).
    machine.key("ctrl-alt-f2")
    time.sleep(2)
    report("Ctrl+Alt+F2 in the child's session leaves the screen where it is",
           active_terminal() == "tty7", active_terminal())

    # The canary: the room above the bar, not the whole screen.
    report("Leo opens the canary by keyboard", open_the_first_tile(machine, "canary"),
           launcher_log())
    wait(lambda: on_screen() == "canary", 10)
    machine.still()
    picture = machine.screenshot("module-open")
    report("it fills the room above the launcher's bar, with no frame",
           on_screen() == "canary" and colour_share(picture, YELLOW, ABOVE_THE_BAR) > 0.8
           and colour_share(picture, YELLOW, TOP_STRIP) > 0.95
           and colour_share(picture, BAR, BAR_BOX) > 0.4 and bar() == "canary",
           f"on screen: {on_screen()}, bar: {bar()}; {picture}")
    # One module open and on screen: Alt+Tab never goes home, so it has
    # nowhere to go, and no button says Alt+Tab (D66).
    nowhere = journal_count("kidux-launcher", "switch: nowhere")
    machine.key("alt-tab")
    report("with one module open, on it, Alt+Tab goes nowhere, and no button says it",
           wait(lambda: journal_count("kidux-launcher", "switch: nowhere") > nowhere, 10)
           and on_screen() == "canary" and alt_tab() == "none",
           f"alt-tab: {alt_tab()}, on screen: {on_screen()}\n" + launcher_log())
    # The pointer rests over the canary: a click reaches it.
    machine.click()
    report("a click over it reaches it", wait(lambda: clicks("canary") > 0, 10),
           root(f"ls -l {own('canary')[0]}").stdout)
    report("it runs in its own scope under Leo's user manager", scope_state("canary") == "active",
           as_child("systemctl --user list-units --no-pager 'kidux-module-*'").stdout)
    seen = facts("canary")
    report("its settings, data and cache directories are its own, made for it and closed",
           seen.get("data") == own("canary")[0]
           and root(f"stat -c %a {' '.join(own('canary'))}").stdout.split() == ["700"] * 3,
           str(seen))
    report("what it writes in the child's home is there for every module to see",
           root(f"cat {SHARED}").stdout.strip() == "written by the canary",
           root(f"ls -la {HOME}").stdout)
    report("it reaches the network, as any program of the child's does",
           seen.get("network") == "reached", str(seen))

    # Super, home; from Home, Alt+Tab goes to the first module in the bar,
    # and Super home again; then the robin over the canary.
    machine.key("meta_l")
    home = wait(lambda: on_screen() == LAUNCHER, 10)
    picture = machine.screenshot("launcher-with-module-open")
    report("Super brings the launcher back, with the canary in the bar",
           home and colour_share(picture, CREAM, ABOVE_THE_BAR) > 0.5
           and colour_share(picture, YELLOW, (0.0, 0.94, 0.5, 1.0)) > 0.01,
           f"on screen: {on_screen()}; {picture}")
    report("and the canary's button says Alt+Tab goes to it", wait(lambda: alt_tab() == "canary", 10),
           f"alt-tab: {alt_tab()}")
    machine.key("alt-tab")
    report("from Home, Alt+Tab goes to the first module in the bar",
           wait(lambda: on_screen() == "canary", 10), f"on screen: {on_screen()}")
    machine.key("meta_l")
    wait(lambda: on_screen() == LAUNCHER, 10)
    # The canary's tile kept the focus; the robin's is the next.
    root(f"rm -f {own('robin')[0]}/opened")
    machine.key("right")
    machine.key("ret")
    opened = wait(lambda: pid_of("robin") != ""
                  and root(f"test -s {own('robin')[0]}/opened").returncode == 0, 30)
    report("the robin opens over it, and both are in the bar",
           opened and wait(lambda: on_screen() == "robin", 10) and bar() == "canary robin",
           f"on screen: {on_screen()}, bar: {bar()}\n" + launcher_log())
    robin = {}
    wait(lambda: robin.update(window_of("org.kidux.tests.Robin"))
         or (robin.get("maximized") is True and robin.get("fullscreen") is False), 10)
    report("it asked for the whole screen and has the room above the bar",
           robin.get("maximized") is True and robin.get("fullscreen") is False, str(robin))
    report("and finds in Leo's home the note the canary left there",
           "canary-note.txt" in facts("robin").get("home", "").split(","), str(facts("robin")))
    # The bar is Home, the canary, the robin, and the robin is on screen:
    # Alt+Tab goes to the next to its right, and from the last to the first
    # (D66). A quick one twice: the canary, then the robin again.
    report("the canary's button says Alt+Tab goes to it, from the last",
           wait(lambda: alt_tab() == "canary", 10), f"alt-tab: {alt_tab()}")
    visited = []
    for _ in range(2):
        before = on_screen()
        machine.key("alt-tab")
        wait(lambda: on_screen() != before, 5)
        visited.append(on_screen())
    machine.still()
    picture = machine.screenshot("module-alt-tab")
    report("Alt+Tab goes to the next module in the bar, and from the last to the first",
           visited == ["canary", "robin"] and colour_share(picture, BLUE, ABOVE_THE_BAR) > 0.8,
           f"visited {visited}; {picture}")
    # Alt held down and Tab twice: the canary lit on the bar, then the robin,
    # Home never; and Alt let go stays on the robin, where the round ended.
    steps = {whose: journal_count("kidux-launcher", f"switch: {whose}")
             for whose in ("canary", "robin")}
    switched = journal_count("kidux-launcher", "switched: robin")
    keyboard("+alt", "0.3", "tab", "2.5", "tab", "3", "-alt", background=True)
    lit = []
    for whose in ("canary", "robin"):
        stepped = wait(lambda: journal_count("kidux-launcher", f"switch: {whose}")
                       > steps[whose], 10, 0.2)
        time.sleep(0.3)
        picture = machine.screenshot(f"module-alt-tab-held-{whose}")
        where = colour_middle(picture, LIT, AFTER_HOME)
        lit.append((whose, stepped, on_screen(), round(colour_share(picture, LIT, HOME_BUTTON), 3),
                    None if where is None else round(where, 3)))
    report("Alt held down goes round the bar, lighting each step, never Home, the robin on screen",
           [(w, s, o) for w, s, o, *_ in lit] == [("canary", True, "robin"), ("robin", True, "robin")]
           and all(home_lit < 0.02 for *_, home_lit, _ in lit)
           and lit[0][4] is not None and lit[1][4] is not None and lit[1][4] > lit[0][4],
           f"{lit}\n" + launcher_log())
    report("and Alt let go goes to the one lit",
           wait(lambda: journal_count("kidux-launcher", "switched: robin") > switched, 10)
           and on_screen() == "robin",
           f"on screen: {on_screen()}\n" + launcher_log())
    # Alt+Shift+Tab goes the other way: from the robin to the canary; a
    # quick Alt+Tab back to the robin.
    machine.key("alt-shift-tab")
    report("Alt+Shift+Tab goes the other way", wait(lambda: on_screen() == "canary", 10),
           f"on screen: {on_screen()}")
    machine.key("alt-tab")
    report("and a quick Alt+Tab goes back", wait(lambda: on_screen() == "robin", 10),
           f"on screen: {on_screen()}")

    # The lock over two open modules, and continuing.
    pids = {module: pid_of(module) for module in MODULES}
    before = machine.mark()
    machine.monitor("system_powerdown")
    report("the power button locks over the modules", wait(lambda: active_terminal() == "tty8", 20),
           active_terminal())
    uid = root(f"id -u {CHILD}").stdout.strip()
    manager = f"systemctl show user@{uid}.service -p FreezerState --value"
    report("and the modules are frozen with the session",
           wait(lambda: root(manager).stdout.strip() == "frozen", 10), root(manager).stdout)
    machine.shown("locked", before)
    before = machine.mark()
    machine.key("ret")                           # Continue
    machine.shown("child_password", before)
    machine.type(CHILD_PASSWORD + "\n")
    wait(lambda: active_terminal() == "tty7", 15)
    wait(lambda: on_screen() == "robin", 10)
    machine.still()
    picture = machine.screenshot("module-after-lock")
    report("continuing brings the same modules back, the same one on screen",
           {module: pid_of(module) for module in MODULES} == pids and on_screen() == "robin"
           and colour_share(picture, BLUE, ABOVE_THE_BAR) > 0.8,
           f"pids {pids}, on screen: {on_screen()}")

    # The launcher crashing under open modules: started again, its window
    # comes forward, home, and it finds the modules still open.
    before = launcher_pid()
    # Started again, it lists them in the order the compositor does.
    drawn = journal_count("kidux-launcher", "bar: ")
    root(f"kill -KILL {before}")
    restarted = wait(lambda: launcher_pid() not in ("", before), 15)
    rebuilt = wait(lambda: journal_count("kidux-launcher", "bar: ") > drawn
                   and sorted(bar().split()) == ["canary", "robin"], 20)
    launcher_shown(machine)
    picture = machine.screenshot("module-after-crash")
    report("a launcher that crashes comes back home, with both modules in its bar",
           restarted and rebuilt and wait(lambda: on_screen() == LAUNCHER, 10)
           and {module: pid_of(module) for module in MODULES} == pids
           and colour_share(picture, CREAM, ABOVE_THE_BAR) > 0.5
           and colour_share(picture, BAR, BAR_BOX) > 0.4,
           root(f"ps -u {CHILD} -o pid,args").stdout + launcher_log())

    # A module that ends leaves the bar; when it was on screen, home.
    shown = show_by_its_tile(machine, "canary")
    machine.still()
    picture = machine.screenshot("module-two-open")
    report("an open module's tile brings it forward, with no frame, both in the bar",
           shown and sorted(bar().split()) == ["canary", "robin"]
           and colour_share(picture, YELLOW, TOP_STRIP) > 0.95,
           f"on screen: {on_screen()}, bar: {bar()}; {picture}\n" + launcher_log())
    root(f"kill {pids['canary']}")
    gone = wait(lambda: bar() == "robin", 15)
    wait(lambda: on_screen() == LAUNCHER, 10)
    machine.still()
    picture = machine.screenshot("launcher-after-module")
    report("a module that ends leaves the bar, and the launcher comes back",
           gone and on_screen() == LAUNCHER and colour_share(picture, CREAM, ABOVE_THE_BAR) > 0.5
           and colour_share(picture, YELLOW, (0.0, 0.15, 1.0, 0.85)) > 0.01,
           f"bar: {bar()}, on screen: {on_screen()}\n" + launcher_log())

    # Again, from the launcher that came back; then closed from the bar's
    # key, Alt+F4: the canary goes when asked.
    # Its tile kept the focus, as a tile does after it opened a module.
    report("the canary opens again from the launcher that came back",
           open_the_first_tile(machine, "canary", from_lock=False)
           and wait(lambda: on_screen() == "canary", 10),
           launcher_log())
    asked = journal_count("kidux-launcher", "asking canary to close")
    machine.key("alt-f4")
    report("Alt+F4 asks the canary to close, and it goes at once, the launcher back",
           wait(lambda: journal_count("kidux-launcher", "asking canary to close") > asked, 10)
           and wait(lambda: pid_of("canary") == "" and bar() == "robin", 15)
           and wait(lambda: on_screen() == LAUNCHER, 10),
           f"bar: {bar()}, on screen: {on_screen()}\n" + launcher_log())

    # The robin refuses: asked about on the bar, and Alt+F4 again ends it.
    machine.key("alt-tab")
    wait(lambda: on_screen() == "robin", 10)
    questions = journal_count("kidux-launcher", "module robin did not close; asking")
    machine.key("alt-f4")
    asked = wait(lambda: journal_count("kidux-launcher", "module robin did not close; asking")
                 > questions, 20)
    time.sleep(1)
    picture = machine.screenshot("launcher-close-question")
    report("the robin refuses to close, and ten seconds later the bar asks, the robin "
           "still open above it",
           asked and pid_of("robin") == pids["robin"] and on_screen() == "robin"
           and colour_share(picture, BLUE, ABOVE_THE_BAR) > 0.8,
           f"on screen: {on_screen()}; {picture}\n" + launcher_log())
    # The question takes the room of the time, of Close and of the other
    # modules' buttons, so that Lock stays whole on the bar (D63).
    ends = (colour_share(picture, LOCK, LOCK_END), colour_share(picture, LOCK, BEYOND_LOCK))
    report("and Lock stays whole on the bar while it asks",
           ends[0] > 0.8 and ends[1] < 0.1, f"{picture}: {ends[0]:.2f}, {ends[1]:.2f}")
    machine.key("alt-f4")
    report("Alt+F4 again, while the bar asks, ends it: its scope stopped",
           wait(lambda: pid_of("robin") == "" and bar() == "none", 15)
           and scope_state("robin") != "active" and wait(lambda: on_screen() == LAUNCHER, 10),
           f"bar: {bar()}\n" + launcher_log())

    # Logging out from the lock screen ends the session, and every module
    # with it.
    report("the canary opens once more, from its tile, which kept the focus",
           open_the_first_tile(machine, "canary", from_lock=False)
           and wait(lambda: on_screen() == "canary", 10),
           launcher_log())
    choose = machine.mark()
    report("logging out from the lock screen ends the session, and every module with it",
           log_out_from_the_lock_screen(machine)
           and wait(lambda: pid_of("canary") == ""
                    and root(f"pgrep -u {CHILD} -x labwc").returncode != 0, 20),
           root("loginctl list-sessions --no-legend").stdout + greeter_log())
    machine.shown("choose", choose, 30)

    for module in MODULES:
        root(f"runuser -u debian -- /usr/local/bin/kidux-as enable {CHILD} {module} off")
        root(f"rm -rf /usr/share/kidux/modules/{module}")
    root(f"rm -f {SHARED}")
