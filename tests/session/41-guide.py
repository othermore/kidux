"""A module's guide beside it (phase-4f-plan.md, step 4.34; D103).

Kig, which has a guide, is installed through the daemon with hello, which
has none, and both switched on for Leo. Leo opens Kig: the pane is on the
right with Kig's lessons in Leo's language, Kig fills the rest, the bar's
Guide is lit, and the missions are in Leo's Documents. A lesson opens from
the list; Fold leaves the rail and Kig fills the room up to it; the bar's
Guide opens it again at the same lesson. Hello on screen takes the pane
away and Kig shown again brings it back. Leo logs out and in, opens Kig,
and the pane is as Leo left it. Both modules are removed at the end.
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
    pointer,
    report,
    root,
    wait,
    windows,
)

AS = "runuser -u debian -- /usr/local/bin/kidux-as"
#: Where the pane is on a 1280x800 screen, and the room the program has.
PANE = (0.70, 0.10, 0.98, 0.90)
PROGRAM = (0.10, 0.10, 0.60, 0.90)
#: Where Kig's grid reaches when the pane is folded: its third, less the rail.
FOLDED_ROOM = (0.70, 0.10, 0.96, 0.90)
#: The first lesson in the list, the pane's Fold, and the bar's Guide.
FIRST_LESSON = "0.88,0.13"
FOLD = "0.96,0.045"
BAR_GUIDE = "0.66,0.965"
#: The folder Kig's missions are copied to, in each language.
MISSIONS = {"es": "Misiones de Kig", "en": "Missions of Kig"}


def guide_logged(text: str) -> int:
    return journal_count("kidux-launcher", f"guide: {text}")


def kig_window() -> dict:
    return next((w for w in windows() if w.get("module") == "kig"), {})


def sign_in(machine: Machine) -> bool:
    password = machine.mark()
    machine.key("ret")                           # Leo, the first picture
    machine.shown("password", password)
    machine.submit(CHILD_PASSWORD)
    return wait(lambda: child_session() is not None, 30) and launcher_shown(machine)


def open_kig(machine: Machine) -> bool:
    """From Lock, which has the focus, back to the last tile, Kig's."""
    machine.key("shift-tab")
    machine.key("ret")
    return wait(lambda: kig_window() != {}, 90, 2) and wait(lambda: on_screen() == "kig", 10)


def log_out(machine: Machine) -> None:
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
    wait(lambda: child_session() is None, 30)
    machine.shown("choose", choose, 30)


def run(machine: Machine) -> None:
    installed = all(root(f"{AS} install {module}", timeout=1800).stdout.startswith("installed ")
                    for module in ("kig", "hello"))
    for module in ("kig", "hello"):
        root(f"{AS} enable {CHILD} {module} on")
    report("Kig, which has a guide, and hello, which has none, install through the daemon",
           installed and root("grep -qx 'guide = true' /usr/share/kidux/modules/kig/module.toml"
                              ).returncode == 0, root("tail -5 /var/log/apt/term.log").stdout)

    report("Leo signs in", sign_in(machine), greeter_log() + launcher_log())
    unfolded = guide_logged("kig lessons unfolded")
    opened = open_kig(machine)
    shown = wait(lambda: guide_logged("kig lessons unfolded") > unfolded, 20)
    time.sleep(2)
    machine.still(4)
    picture = machine.screenshot("module-kig-guide")
    report("Leo opens Kig: the guide's lessons on the right, Kig filling the rest",
           opened and shown and colour_share(picture, CREAM, PANE) > 0.5
           and colour_share(picture, CREAM, PROGRAM) < 0.1,
           f"{picture}\n" + launcher_log())
    documents = f"/home/{CHILD}/{SPEAKS['folders'][0]}/{MISSIONS[SPEAKS['lang']]}"
    report("and Kig's missions are in Leo's Documents, in a folder of their own",
           root(f"ls {documents}/*.kig").returncode == 0, root(f"ls -la {documents}").stdout)

    lesson = guide_logged("kig lesson 1 unfolded")
    pointer(FIRST_LESSON, "click")
    machine.still(3)
    picture = machine.screenshot("module-guide-lesson")
    report("the first lesson opens from the list",
           wait(lambda: guide_logged("kig lesson 1 unfolded") > lesson, 10),
           f"{picture}\n" + launcher_log())

    folded = guide_logged("kig lesson 1 folded")
    pointer(FOLD, "click")
    machine.still(3)
    picture = machine.screenshot("guide-folded")
    report("Fold leaves the rail, and Kig fills the room up to it",
           wait(lambda: guide_logged("kig lesson 1 folded") > folded, 10)
           and colour_share(picture, CREAM, FOLDED_ROOM) < 0.1,
           f"{picture}\n" + launcher_log())
    again = guide_logged("kig lesson 1 unfolded")
    pointer(BAR_GUIDE, "click")
    report("the bar's Guide opens it again at the same lesson",
           wait(lambda: guide_logged("kig lesson 1 unfolded") > again, 10), launcher_log())

    # Home, then hello's tile, before Kig's: a module without a guide on
    # screen takes the pane away.
    gone = guide_logged("none")
    machine.key("meta_l")
    wait(lambda: on_screen() == "home", 10)
    machine.key("shift-tab")
    machine.key("left")
    machine.key("ret")
    report("hello on screen takes the pane away",
           wait(lambda: on_screen() == "hello", 30) and wait(lambda: guide_logged("none") > gone, 10),
           launcher_log())
    back = guide_logged("kig lesson 1 unfolded")
    machine.key("meta_l")
    wait(lambda: on_screen() == "home", 10)
    machine.key("shift-tab")
    machine.key("ret")
    report("and Kig shown again brings it back as it was",
           wait(lambda: on_screen() == "kig", 10)
           and wait(lambda: guide_logged("kig lesson 1 unfolded") > back, 10), launcher_log())

    log_out(machine)
    report("Leo logs out and in", sign_in(machine), greeter_log())
    remembered = guide_logged("kig lesson 1 unfolded")
    report("and Kig opens with the guide at the lesson Leo left",
           open_kig(machine)
           and wait(lambda: guide_logged("kig lesson 1 unfolded") > remembered, 20),
           launcher_log())
    log_out(machine)

    for module in ("kig", "hello"):
        root(f"{AS} enable {CHILD} {module} off")
    report("and the daemon removes both",
           all(root(f"{AS} remove {module}", timeout=1800).stdout.startswith("removed ")
               for module in ("kig", "hello")),
           root("tail -5 /var/log/apt/term.log").stdout)
