"""Kydux (phase-4h-plan.md, step 4.41).

kidux-module-kydux, a door to the Kidux family's game for learning Python
(D120), is installed through the daemon, as the panel installs it, and
switched on for Leo from the command line. Leo opens it by keyboard:
Chromium's application window, filling the room above the bar, shows the
game's question about cookies, which Leo answers *Refuse* and then *Yes,
refuse them*, by keyboard; the game's welcome page follows, in Leo's
language. The machine reaches the internet through QEMU's own network; a
site that does not answer is said so, and still fails the test. For the
test's length the machine sends the game's counting of visits nowhere,
since a test machine is not one of its players. Alt+F4 closes it and gives
the launcher back; the lock screen's *Log out* ends the session, and the
daemon removes the module, leaving Leo's games in Leo's home (D89).
"""

from sessionlib import (
    CHILD,
    CHILD_PASSWORD,
    SPEAKS,
    Machine,
    active_terminal,
    child_session,
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

#: The module's Chromium profile in Leo's home, where the game keeps its
#: saved games and the answer about cookies (D89).
PROFILE = f"/home/{CHILD}/.config/kidux/kydux"
#: The host the game counts every visit on, whatever the answer about
#: cookies; sent to no address while the test runs.
COUNTING = "kidux.goatcounter.com"
#: Where the pointer rests for the guide's picture: the page's right margin,
#: over no link, so that no hand and no address under the window show.
ASIDE = "0.97,0.55"


def daemon(command: str) -> bool:
    """`kidux-as install|remove kydux`: the daemon's job, start to end."""
    return root(f"runuser -u debian -- /usr/local/bin/kidux-as {command} kydux",
                timeout=1500).stdout.startswith(command + ("ed " if command == "install" else "d "))


def chromium_pid() -> str:
    return root(f"pgrep -u {CHILD} -x chromium | sort -n | head -1").stdout.strip()


def kydux_window() -> dict:
    return next((w for w in windows() if w.get("module") == "kydux"), {})


def title() -> str:
    return kydux_window().get("title") or ""


def run(machine: Machine) -> None:
    root(f"echo '0.0.0.0 {COUNTING}  # kidux-tests' >> /etc/hosts")
    try:
        play(machine)
    finally:
        root("sed -i '/  # kidux-tests$/d' /etc/hosts")


def play(machine: Machine) -> None:
    # Leo starts as a child who never opened the game: a refusal of its
    # cookies is kept for a day and a half, so on a machine this test ran on
    # before the game would ask nothing.
    root(f"rm -rf {PROFILE}")
    report("kidux-module-kydux installs from the archive through the daemon",
           daemon("install"), root("tail -5 /var/log/apt/term.log").stdout)
    root(f"runuser -u debian -- /usr/local/bin/kidux-as enable {CHILD} kydux on")

    before = journal_count("kidux-launcher", "tiles: kydux")
    password = machine.mark()
    machine.key("ret")                           # Leo, the first picture
    machine.shown("password", password)
    machine.submit(CHILD_PASSWORD)
    report("Leo signs in to its tile", wait(lambda: child_session() is not None, 30)
           and wait(lambda: journal_count("kidux-launcher", "tiles: kydux") > before, 30)
           and launcher_shown(machine), greeter_log() + launcher_log())

    # From Lock, which has the focus, back to the tile, and Enter.
    machine.key("shift-tab")
    machine.key("ret")
    opened = wait(lambda: "Kydux" in title(), 90, 2)
    wait(lambda: on_screen() == "kydux", 10)
    asked = wait(lambda: "cookies" in title(), 30)
    machine.still(3)
    window = kydux_window()
    if window and not opened:
        print("      the site did not answer: the window is there, Kydux's title never came",
              flush=True)
    report("Leo opens it by keyboard: the game asks about cookies, in Chromium, above the bar",
           opened and asked and on_screen() == "kydux" and window.get("maximized")
           and not window.get("fullscreen"),
           f"{window}\n" + launcher_log())

    # The game's own keys (phase-4h-plan.md, section 5): from the page as it
    # loads, Tab reaches Accept and Tab again Refuse, which shows the whole
    # of why with the focus on Accept the cookies; Tab reaches Yes, refuse
    # them.
    for key in ("tab", "tab", "ret"):
        machine.key(key)
    machine.still(2)
    for key in ("tab", "ret"):
        machine.key(key)
    report("Leo answers Refuse and confirms it, and the welcome page follows, in Leo's language",
           wait(lambda: title() == SPEAKS["kydux"], 30),
           f"title {title()!r}, expected {SPEAKS['kydux']!r}")
    pointer(ASIDE)
    machine.still(3)
    machine.screenshot("module-kydux")

    # Alt+F4 asks Chromium to close; a page that asks first whether to
    # leave is ended by Alt+F4 again, as the bar's question says (D45).
    ended = journal_count("kidux-launcher", "module kydux ended")
    machine.key("alt-f4")
    if not wait(lambda: journal_count("kidux-launcher", "module kydux ended") > ended, 20):
        machine.key("alt-f4")
    report("Alt+F4 closes it, and the launcher comes back",
           wait(lambda: journal_count("kidux-launcher", "module kydux ended") > ended, 20)
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

    root(f"runuser -u debian -- /usr/local/bin/kidux-as enable {CHILD} kydux off")
    report("and the daemon removes it", daemon("remove"), root("tail -5 /var/log/apt/term.log").stdout)
    report("and what the game kept in Leo's browser stays in Leo's home (D89)",
           root(f"test -d '{PROFILE}/chromium/Default/Local Storage'").returncode == 0,
           root(f"ls -la {PROFILE}/chromium/Default").stdout)
