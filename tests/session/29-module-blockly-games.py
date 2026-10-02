"""Blockly Games (phase-4-plan.md, step 4.7).

kidux-module-blockly-games is installed through the daemon, as the panel
installs it, and switched on for Leo from the command line. Leo opens it by
keyboard: Chromium's application window, filling the room above the bar,
shows the games from the server on the loopback address, titled in Leo's
language, and a game opens from them by the address they link it by, its
name without `.html`. Alt+F4 closes it and gives the launcher back; the lock screen's
*Log out* ends the session, and the daemon removes it.
"""

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
    report,
    root,
    wait,
    windows,
)

#: The room above the launcher's bar, and the bar.
ABOVE_THE_BAR = (0.0, 0.0, 1.0, 0.92)
BAR = (0xF2, 0xE2, 0xCC)
BAR_BOX = (0.0, 0.94, 1.0, 1.0)


def daemon(command: str) -> bool:
    """`kidux-as install|remove blockly-games`: the daemon's job, start to end."""
    return root(f"runuser -u debian -- /usr/local/bin/kidux-as {command} blockly-games",
                timeout=1500).stdout.startswith(command + ("ed " if command == "install" else "d "))


def chromium_pid() -> str:
    return root(f"pgrep -u {CHILD} -x chromium | sort -n | head -1").stdout.strip()


def games_window() -> dict:
    return next((w for w in windows() if w.get("module") == "blockly-games"), {})


def run(machine: Machine) -> None:
    report("kidux-module-blockly-games installs from the archive through the daemon, and "
           "the server answers for it",
           daemon("install")
           and root("curl -fsS http://127.0.0.1:8123/blockly-games/ | grep -qi '<title>'").returncode == 0,
           root("tail -5 /var/log/apt/term.log").stdout)
    root(f"runuser -u debian -- /usr/local/bin/kidux-as enable {CHILD} blockly-games on")

    before = journal_count("kidux-launcher", "tiles: blockly-games")
    password = machine.mark()
    machine.key("ret")                           # Leo, the first picture
    machine.shown("password", password)
    machine.submit(CHILD_PASSWORD)
    report("Leo signs in to its tile", wait(lambda: child_session() is not None, 30)
           and wait(lambda: journal_count("kidux-launcher", "tiles: blockly-games") > before, 30)
           and launcher_shown(machine), greeter_log() + launcher_log())

    # From Lock, which has the focus, back to the tile, and Enter.
    machine.key("shift-tab")
    machine.key("ret")
    opened = wait(lambda: SPEAKS["blockly"] in (games_window().get("title") or ""), 60, 2)
    wait(lambda: on_screen() == "blockly-games", 10)
    machine.still(5)
    picture = machine.screenshot("module-blockly-games")
    window = games_window()
    report("Leo opens it by keyboard: the games, in Chromium, above the bar, in Leo's language",
           opened and on_screen() == "blockly-games" and window.get("maximized")
           and not window.get("fullscreen")
           and colour_share(picture, CREAM, ABOVE_THE_BAR) < 0.2
           and colour_share(picture, BAR, BAR_BOX) > 0.4,
           f"{window}; {picture}\n" + launcher_log())

    # The page's links, in order: the page for teachers, then the games,
    # Puzzle and Maze, which opens at maze?lang=…, beside a folder maze/.
    for key in ("tab", "tab", "tab", "ret"):
        machine.key(key)
    report("a game opens from them: Maze, by the address the games' page links to",
           wait(lambda: (games_window().get("title") or "").startswith(SPEAKS["blockly"] + " : "),
                60, 2),
           f"title {games_window().get('title')!r}; {machine.screenshot('module-blockly-games-maze')}")

    # Alt+F4 asks Chromium to close; a page that asks first whether to
    # leave is ended by Alt+F4 again, as the bar's question says (D45).
    ended = journal_count("kidux-launcher", "module blockly-games ended")
    machine.key("alt-f4")
    if not wait(lambda: journal_count("kidux-launcher", "module blockly-games ended") > ended, 20):
        machine.key("alt-f4")
    report("Alt+F4 closes it, and the launcher comes back",
           wait(lambda: journal_count("kidux-launcher", "module blockly-games ended") > ended, 20)
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

    root(f"runuser -u debian -- /usr/local/bin/kidux-as enable {CHILD} blockly-games off")
    report("and the daemon removes it", daemon("remove"), root("tail -5 /var/log/apt/term.log").stdout)
