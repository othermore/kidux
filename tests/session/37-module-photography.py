"""Photography (phase-4e-plan.md, step 4.28).

kidux-module-photography is installed through the daemon, as the panel
installs it, and switched on for Leo from the command line. Leo opens it by
keyboard: Chromium's application window, filling the room above the bar,
titled Photography in his language, on the guide's first chapter, cream
around its drawing of a dark room. Enter on the button that has the focus,
Next or, with one chapter, Chapters, changes the page. Alt+F4 closes the
module and gives the launcher back; the lock screen's *Log out* ends the
session, and the daemon removes it.
"""

from sessionlib import (
    CHILD,
    CHILD_PASSWORD,
    CREAM,
    NIGHT,
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

#: The room above the launcher's bar, and the middle of it, where the first
#: chapter's drawing is.
ABOVE_THE_BAR = (0.0, 0.0, 1.0, 0.92)
DRAWING_BOX = (0.25, 0.25, 0.75, 0.9)


def daemon(command: str) -> bool:
    """`kidux-as install|remove photography`: the daemon's job, start to end."""
    return root(f"runuser -u debian -- /usr/local/bin/kidux-as {command} photography",
                timeout=1500).stdout.startswith(command + ("ed " if command == "install" else "d "))


def chromium_pid() -> str:
    return root(f"pgrep -u {CHILD} -x chromium | sort -n | head -1").stdout.strip()


def photography_window() -> dict:
    return next((w for w in windows() if w.get("module") == "photography"), {})


def run(machine: Machine) -> None:
    report("kidux-module-photography installs from the archive through the daemon, and "
           "the server answers for it",
           daemon("install")
           and root("curl -fsS http://127.0.0.1:8123/photography/ | grep -q 'Una caja con un agujero'"
                    ).returncode == 0,
           root("tail -5 /var/log/apt/term.log").stdout)
    root(f"runuser -u debian -- /usr/local/bin/kidux-as enable {CHILD} photography on")
    # The guide remembers its chapter in the module's own storage (D89): it
    # starts on the first only in a home that never had it.
    root(f"rm -rf /home/{CHILD}/.local/share/kidux/photography /home/{CHILD}/.config/kidux/photography "
         f"/home/{CHILD}/.cache/kidux/photography")

    before = journal_count("kidux-launcher", "tiles: photography")
    password = machine.mark()
    machine.key("ret")                           # Leo, the first picture
    machine.shown("password", password)
    machine.submit(CHILD_PASSWORD)
    report("Leo signs in to its tile", wait(lambda: child_session() is not None, 30)
           and wait(lambda: journal_count("kidux-launcher", "tiles: photography") > before, 30)
           and launcher_shown(machine), greeter_log() + launcher_log())

    # From Lock, which has the focus, back to the tile, and Enter.
    machine.key("shift-tab")
    machine.key("ret")
    opened = wait(lambda: photography_window().get("title") == SPEAKS["photography"], 60, 2)
    wait(lambda: on_screen() == "photography", 10)
    machine.still(3)
    window = photography_window()
    report(f"Leo opens it by keyboard: {SPEAKS['photography']}, in Chromium, above the bar",
           opened and on_screen() == "photography" and window.get("maximized")
           and not window.get("fullscreen"),
           f"{window}\n" + launcher_log())

    picture = machine.screenshot("module-photography")
    report("on the first chapter: cream around the drawing of a dark room",
           colour_share(picture, CREAM, ABOVE_THE_BAR) > 0.4
           and colour_share(picture, NIGHT, DRAWING_BOX) > 0.02,
           f"cream {colour_share(picture, CREAM, ABOVE_THE_BAR):.2f}, "
           f"night {colour_share(picture, NIGHT, DRAWING_BOX):.3f}; {picture}")

    frame = machine.settled()
    machine.key("ret")
    report("Enter on the button that has the focus changes the page",
           machine.changes(frame), launcher_log())

    ended = journal_count("kidux-launcher", "module photography ended")
    machine.key("alt-f4")
    report("Alt+F4 closes it, and the launcher comes back",
           wait(lambda: journal_count("kidux-launcher", "module photography ended") > ended, 20)
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

    root(f"runuser -u debian -- /usr/local/bin/kidux-as enable {CHILD} photography off")
    report("and the daemon removes it", daemon("remove"), root("tail -5 /var/log/apt/term.log").stdout)
