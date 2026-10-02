"""A module made for X11, through XWayland (phase-3-plan.md, step 3.19; D58).

The tests' X11 stand-in, a Tk window with no Wayland of its own, is copied
into place with python3-tk, which it needs, and switched on for Leo. Signed
in without windows, he opens it by keyboard: XWayland starts, as Leo, for
it, its window fills the room above the bar like any module's, and a click
over it reaches it through XWayland; the lock
and continuing bring the same one back; Alt+F4 closes it, and XWayland ends
by itself a little later; opened again, logging out leaves nothing of it or
of XWayland. Removed at the end.
"""

from sessionlib import (
    CHILD,
    CHILD_PASSWORD,
    SEED_SOURCE,
    Machine,
    active_terminal,
    child_session,
    colour_share,
    copy,
    greeter_log,
    journal_count,
    launcher_log,
    launcher_shown,
    on_screen,
    report,
    root,
    wait,
    window_of,
)

AS = "runuser -u debian -- /usr/local/bin/kidux-as"
X11 = "x11-canary"
DATA = f"/home/{CHILD}/.local/share/kidux/{X11}"
#: The X11 canary's colour (tests/lib/seed/modules/x11-canary/run), and the
#: room above the bar.
ORANGE = (0xE8, 0x60, 0x3C)
ABOVE_THE_BAR = (0.0, 0.0, 1.0, 0.92)


def pid() -> str:
    return root(f"pgrep -u {CHILD} -f '^/usr/bin/python3 /usr/share/kidux/modules/{X11}/run'"
                ).stdout.strip()


def xwayland() -> bool:
    return root(f"pgrep -u {CHILD} -x Xwayland").returncode == 0


def sign_in(machine: Machine) -> bool:
    before = journal_count("kidux-launcher", f"tiles: {X11}")
    password = machine.mark()
    machine.key("ret")
    machine.shown("password", password)
    machine.submit(CHILD_PASSWORD)
    return (wait(lambda: child_session() is not None, 30)
            and wait(lambda: journal_count("kidux-launcher", f"tiles: {X11}") > before, 30)
            and launcher_shown(machine))


def open_it(machine: Machine, from_lock: bool = True) -> bool:
    root(f"rm -f {DATA}/opened")
    machine.still()
    if from_lock:
        machine.key("shift-tab")
    machine.key("home")
    machine.key("ret")
    return (wait(lambda: root(f"test -s {DATA}/opened").returncode == 0, 30)
            and wait(lambda: window_of(X11).get("maximized") is True, 30)
            and wait(lambda: on_screen() == X11, 10))


def lock_and_continue(machine: Machine) -> None:
    locked = machine.mark()
    machine.monitor("system_powerdown")
    wait(lambda: active_terminal() == "tty8", 20)
    machine.shown("locked", locked)
    asked = machine.mark()
    machine.key("ret")                           # Continue
    machine.shown("child_password", asked)
    machine.submit(CHILD_PASSWORD)
    wait(lambda: active_terminal() == "tty7", 15)


def log_out(machine: Machine) -> bool:
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
    installed = root("DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends "
                     "python3-tk", timeout=600)
    source = SEED_SOURCE / "modules" / X11
    for name, mode in (("module.toml", "0644"), ("icon.svg", "0644"), ("run", "0755")):
        copy(source / name, f"/usr/share/kidux/modules/{X11}/{name}", mode=mode)
    root(f"{AS} enable {CHILD} {X11} on")
    report("the X11 stand-in module is in place, with Tk", installed.returncode == 0,
           installed.stderr[-400:])

    report("Leo signs in to its tile", sign_in(machine), greeter_log() + launcher_log())
    report("he opens it by keyboard, and its window fills the room above the bar",
           open_it(machine), str(window_of(X11)) + launcher_log())
    machine.still()
    picture = machine.screenshot("module-x11")
    seen = dict(line.split("=", 1) for line in root(f"cat {DATA}/opened").stdout.splitlines()
                if "=" in line)
    report("it runs through XWayland, which runs as Leo, on the display labwc gave it",
           xwayland() and seen.get("display", "").startswith(":")
           and colour_share(picture, ORANGE, ABOVE_THE_BAR) > 0.8
           and colour_share(picture, ORANGE, (0.0, 0.0, 1.0, 0.03)) > 0.95,
           f"{seen}; {picture}\n" + root(f"ps -u {CHILD} -o pid,args").stdout)

    machine.click()
    report("a click over it reaches it through XWayland",
           wait(lambda: root(f"cat {DATA}/clicks").stdout != "", 10), root(f"ls -l {DATA}").stdout)

    before = pid()
    lock_and_continue(machine)
    report("the lock and continuing bring the same one back",
           wait(lambda: on_screen() == X11, 10) and pid() == before, f"{before} then {pid()}")

    machine.still()
    machine.key("alt-f4")
    report("Alt+F4 closes it, and the launcher is back",
           wait(lambda: pid() == "", 15) and wait(lambda: on_screen() == "home", 10),
           launcher_log())
    report("and XWayland ends by itself when no X11 program is left",
           wait(lambda: not xwayland(), 30), root(f"ps -u {CHILD} -o pid,args").stdout)

    launcher_shown(machine)
    report("it opens again", open_it(machine, from_lock=False), launcher_log())
    report("logging out leaves nothing of it, nor of XWayland",
           log_out(machine) and wait(lambda: pid() == "" and not xwayland(), 20),
           root(f"ps -u {CHILD} -o pid,args").stdout)

    root(f"{AS} enable {CHILD} {X11} off")
    root(f"rm -rf /usr/share/kidux/modules/{X11}")
