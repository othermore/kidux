"""BASIC (phase-4b-plan.md, step 4.10).

kidux-module-basic is installed through the daemon, as the panel installs
it, and switched on for Leo from the command line. Leo opens it by
keyboard: Chromium's application window, filling the room above the bar,
titled BASIC, with the editor on the left holding the keyboard. Leo types a
program that never ends and runs it with Ctrl+Enter: the screen below the
editor turns dark with its words while the guide on the right stays cream.
Escape stops it; Alt+F4 closes the module and gives the launcher back; the
lock screen's *Log out* ends the session, and the daemon removes it. An
adult has switched *Type it in for me* off for Leo first (D90): BASIC's
page is opened with it in its address, which is what hides its buttons.
"""

from sessionlib import (
    CHILD,
    CHILD_PASSWORD,
    CREAM,
    LANGUAGE,
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
#: The machine's screen, below the editor and its buttons on the left half,
#: and the guide, the right half.
SCREEN_BOX = (0.06, 0.55, 0.44, 0.85)
GUIDE_BOX = (0.55, 0.10, 0.98, 0.88)
#: The screen's letters, BASIC's light grey on black.
LETTERS = (0xAA, 0xAA, 0xAA)
#: The key that types a double quote on the machine's keyboard, Spanish or
#: American.
QUOTE = {"es": "shift-2", "en": "shift-apostrophe"}[LANGUAGE]


def daemon(command: str) -> bool:
    """`kidux-as install|remove basic`: the daemon's job, start to end."""
    return root(f"runuser -u debian -- /usr/local/bin/kidux-as {command} basic",
                timeout=1500).stdout.startswith(command + ("ed " if command == "install" else "d "))


def chromium_pid() -> str:
    return root(f"pgrep -u {CHILD} -x chromium | sort -n | head -1").stdout.strip()


def basic_window() -> dict:
    return next((w for w in windows() if w.get("module") == "basic"), {})


def run(machine: Machine) -> None:
    report("kidux-module-basic installs from the archive through the daemon, and the "
           "server answers for it",
           daemon("install")
           and root("curl -fsS http://127.0.0.1:8123/basic/ | grep -q '<title>BASIC</title>'").returncode == 0,
           root("tail -5 /var/log/apt/term.log").stdout)
    root(f"runuser -u debian -- /usr/local/bin/kidux-as enable {CHILD} basic on")
    report("an adult switches Type it in for me off for Leo",
           root(f"runuser -u debian -- /usr/local/bin/kidux-as set-setting {CHILD} basic "
                "type_in false").returncode == 0
           and root(f"runuser -u {CHILD} -- /usr/local/bin/kidux-as my-settings basic"
                    ).stdout.strip() == '{"type_in": false}',
           root("tail -2 /home/.kidux/state/audit.log").stdout)

    before = journal_count("kidux-launcher", "tiles: basic")
    password = machine.mark()
    machine.key("ret")                           # Leo, the first picture
    machine.shown("password", password)
    machine.submit(CHILD_PASSWORD)
    report("Leo signs in to its tile", wait(lambda: child_session() is not None, 30)
           and wait(lambda: journal_count("kidux-launcher", "tiles: basic") > before, 30)
           and launcher_shown(machine), greeter_log() + launcher_log())

    # From Lock, which has the focus, back to the tile, and Enter.
    machine.key("shift-tab")
    machine.key("ret")
    opened = wait(lambda: basic_window().get("title") == "BASIC", 60, 2)
    wait(lambda: on_screen() == "basic", 10)
    machine.still(3)
    window = basic_window()
    report("Leo opens it by keyboard: BASIC, in Chromium, above the bar",
           opened and on_screen() == "basic" and window.get("maximized")
           and not window.get("fullscreen"),
           f"{window}\n" + launcher_log())
    command = root(f"pgrep -a -u {CHILD} -x chromium | head -1").stdout
    report("and its page is told that Type it in for me is off",
           "--app=http://127.0.0.1:8123/basic/?lang=" in command and "&type_in=0" in command,
           command)

    # The editor has the keyboard: a program that prints for ever, run
    # with Ctrl+Enter.
    machine.type("10 PRINT ")
    machine.key(QUOTE)
    machine.type("HOLA")
    machine.key(QUOTE)
    machine.type("\n20 GOTO 10")
    machine.key("ctrl-ret")
    machine.still(2)
    picture = machine.screenshot("module-basic")
    report("Leo types a program in the editor and runs it: the screen is dark with its "
           "words, and the guide beside it is cream",
           colour_share(picture, CREAM, SCREEN_BOX) < 0.2
           and colour_share(picture, LETTERS, SCREEN_BOX) > 0.01
           and colour_share(picture, CREAM, GUIDE_BOX) > 0.5,
           f"screen {colour_share(picture, CREAM, SCREEN_BOX):.2f} cream, "
           f"{colour_share(picture, LETTERS, SCREEN_BOX):.3f} letters, "
           f"guide {colour_share(picture, CREAM, GUIDE_BOX):.2f}; {picture}")
    machine.key("esc")

    # Alt+F4 asks Chromium to close; a page that asks first whether to
    # leave is ended by Alt+F4 again, as the bar's question says (D45).
    ended = journal_count("kidux-launcher", "module basic ended")
    machine.key("alt-f4")
    if not wait(lambda: journal_count("kidux-launcher", "module basic ended") > ended, 20):
        machine.key("alt-f4")
    report("Alt+F4 closes it, and the launcher comes back",
           wait(lambda: journal_count("kidux-launcher", "module basic ended") > ended, 20)
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

    root(f"runuser -u debian -- /usr/local/bin/kidux-as set-setting {CHILD} basic type_in true")
    root(f"runuser -u debian -- /usr/local/bin/kidux-as enable {CHILD} basic off")
    report("and the daemon removes it", daemon("remove"), root("tail -5 /var/log/apt/term.log").stdout)
