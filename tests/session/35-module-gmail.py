"""Gmail (phase-4d-plan.md, step 4.23).

kidux-module-gmail, a door to Gmail's website, is installed through the
daemon, as the panel installs it, and switched on for Leo from the command
line, where an adult also gives Leo's address, a made-up one. Leo opens it
by keyboard: Chromium's application window, filling the room above the bar,
shows Google's sign-in for Gmail, which the address an adult gave fills
in (20-module-gmail.sh checks the address Chromium is given); nothing is
typed there. The machine reaches the internet through QEMU's own network; a site
that does not answer is said so, and still fails the test. Alt+F4 closes it
and gives the launcher back; the lock screen's *Log out* ends the session,
and the daemon removes it.
"""

import json

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

AS = "runuser -u debian -- /usr/local/bin/kidux-as"
ADDRESS = "leo@example.org"
#: The room above the launcher's bar.
ABOVE_THE_BAR = (0.0, 0.0, 1.0, 0.92)


def daemon(command: str) -> bool:
    """`kidux-as install|remove gmail`: the daemon's job, start to end."""
    return root(f"{AS} {command} gmail",
                timeout=1500).stdout.startswith(command + ("ed " if command == "install" else "d "))


def chromium_pid() -> str:
    return root(f"pgrep -u {CHILD} -x chromium | sort -n | head -1").stdout.strip()


def gmail_window() -> dict:
    return next((w for w in windows() if w.get("module") == "gmail"), {})


def run(machine: Machine) -> None:
    report("kidux-module-gmail installs from the archive through the daemon",
           daemon("install"), root("tail -5 /var/log/apt/term.log").stdout)
    root(f"{AS} enable {CHILD} gmail on")
    report("an adult gives Leo's address",
           root(f"{AS} set-setting {CHILD} gmail email {json.dumps(json.dumps(ADDRESS))}"
                ).returncode == 0
           and json.loads(root(f"runuser -u {CHILD} -- /usr/local/bin/kidux-as my-settings gmail"
                               ).stdout or "{}") == {"email": ADDRESS},
           root("tail -2 /home/.kidux/state/audit.log").stdout)

    before = journal_count("kidux-launcher", "tiles: gmail")
    password = machine.mark()
    machine.key("ret")                           # Leo, the first picture
    machine.shown("password", password)
    machine.submit(CHILD_PASSWORD)
    report("Leo signs in to its tile", wait(lambda: child_session() is not None, 30)
           and wait(lambda: journal_count("kidux-launcher", "tiles: gmail") > before, 30)
           and launcher_shown(machine), greeter_log() + launcher_log())

    # From Lock, which has the focus, back to the tile, and Enter.
    machine.key("shift-tab")
    machine.key("ret")
    opened = wait(lambda: "Gmail" in (gmail_window().get("title") or ""), 90, 2)
    wait(lambda: on_screen() == "gmail", 10)
    machine.still(5)
    picture = machine.screenshot("module-gmail")
    window = gmail_window()
    if window and not opened:
        print("      the site did not answer: the window is there, Gmail's title never came",
              flush=True)
    report("Leo opens it by keyboard: Google's sign-in for Gmail, in Chromium, above the bar",
           opened and on_screen() == "gmail" and window.get("maximized")
           and not window.get("fullscreen")
           and colour_share(picture, CREAM, ABOVE_THE_BAR) < 0.2,
           f"{window}; {picture}\n" + launcher_log())

    # Alt+F4 asks Chromium to close; a page that asks first whether to
    # leave is ended by Alt+F4 again, as the bar's question says (D45).
    ended = journal_count("kidux-launcher", "module gmail ended")
    machine.key("alt-f4")
    if not wait(lambda: journal_count("kidux-launcher", "module gmail ended") > ended, 20):
        machine.key("alt-f4")
    report("Alt+F4 closes it, and the launcher comes back",
           wait(lambda: journal_count("kidux-launcher", "module gmail ended") > ended, 20)
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

    root(f"{AS} enable {CHILD} gmail off")
    report("and the daemon removes it", daemon("remove"), root("tail -5 /var/log/apt/term.log").stdout)
