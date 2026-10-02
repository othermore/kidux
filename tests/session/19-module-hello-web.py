"""The reference web application (phase-3-plan.md, step 3.7).

kidux-module-hello-web is installed through the daemon, as the panel
installs it, which brings kidux-webapps and Chromium without Debian's
recommendations, and switched on for Leo from the command line.
Leo opens it by keyboard: a Chromium application window, with no tabs and
no address bar, filling the room above the bar, shows hello's
page in Spanish from the server on the loopback address. The lock and
continuing bring the same Chromium back, and *Done*, which has the
keyboard, closes it and gives the launcher back. Opened again, the link on it to a page on the
internet is refused by Chromium's policy, and back is the page again; with
two pages in its history Chromium no longer lets *Done* close the window,
and Alt+F4, the bar's *Close*, does (D45). Opened once more, *Save* opens
the file dialog in Leo's Downloads, and its Save button keeps the page,
from the blob: address the page made, as Scratch saves a project (D75, D76); and the
lock screen's *Log out* ends it with the session. Purged at the end.

Chromium on the machine's software rendering is slow to start: the waits
are a minute.
"""

from sessionlib import (
    HOME,
    CHILD,
    CHILD_PASSWORD,
    Machine,
    SPEAKS,
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
    shlex_quote,
    wait,
    windows,
)

#: Kidux's cream, which the page is drawn on, and the bar below it.
CREAM = (0xFF, 0xF6, 0xE9)
ABOVE_THE_BAR = (0.0, 0.0, 1.0, 0.92)
BAR = (0xF2, 0xE2, 0xCC)
BAR_BOX = (0.0, 0.94, 1.0, 1.0)
#: The page's title is its heading, in the machine's language.
HEADING = SPEAKS["heading"]
#: The file Save makes, in Leo's Downloads.
SAVED = f"/home/{CHILD}/{SPEAKS['folders'][1]}/{SPEAKS['saved']}"


def daemon(command: str) -> bool:
    """`kidux-as install|remove hello-web`: the daemon's job, start to end."""
    return root(f"runuser -u debian -- /usr/local/bin/kidux-as {command} hello-web",
                timeout=1500).stdout.startswith(command + ("ed " if command == "install" else "d "))


def chromium_pid() -> str:
    return root(f"pgrep -u {CHILD} -x chromium | sort -n | head -1").stdout.strip()


def chromium_window() -> dict:
    return next((w for w in windows() if w.get("module") == "hello-web"), {})


def dialog() -> dict:
    """Chromium's file dialog: a window of Chromium's own, not the page's
    application window, and of no module."""
    return next((w for w in windows() if w.get("app_id") == "chromium"), {})


def title() -> str:
    return chromium_window().get("title") or ""


def open_it(machine: Machine, keys=("shift-tab", "ret")) -> bool:
    """From Lock, which has the focus after signing in, back to the tile, and
    Enter; done when Chromium shows the page, whose title is its heading."""
    for key in keys:
        machine.key(key)
    shown = wait(lambda: title() == HEADING, 90, 2)
    machine.still(10)
    return shown


def sign_in(machine: Machine) -> bool:
    before = journal_count("kidux-launcher", "tiles: hello-web")
    password = machine.mark()
    machine.key("ret")                           # Leo, the first picture
    machine.shown("password", password)
    machine.submit(CHILD_PASSWORD)
    return (wait(lambda: child_session() is not None, 30)
            and wait(lambda: journal_count("kidux-launcher", "tiles: hello-web") > before, 30)
            and launcher_shown(machine))


def lock_and_log_out(machine: Machine) -> bool:
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
    ended = wait(lambda: child_session() is None and chromium_pid() == "", 30)
    machine.shown("choose", choose, 30)
    return ended


def run(machine: Machine) -> None:
    # Without Debian's recommendations, as the daemon installs: Chromium's
    # setuid sandbox is one, and Chromium runs without it.
    report("kidux-module-hello-web installs from the archive through the daemon, with its "
           "server and Chromium, and without Chromium's recommendations",
           daemon("install") and root("systemctl is-active kidux-webapps").stdout.strip() == "active"
           and root("dpkg -s chromium-sandbox").returncode != 0,
           root("tail -5 /var/log/apt/term.log").stdout)
    root(f"runuser -u debian -- /usr/local/bin/kidux-as enable {CHILD} hello-web on")

    report("Leo signs in to its tile", sign_in(machine), greeter_log() + launcher_log())
    opened = open_it(machine)
    picture = machine.screenshot("module-hello-web")
    window = chromium_window()
    report("Leo opens it by keyboard: hello's page in Leo's language, in Chromium, above "
           "the bar",
           opened and on_screen() == "hello-web" and window.get("maximized")
           and not window.get("fullscreen")
           and colour_share(picture, CREAM, ABOVE_THE_BAR) > 0.5
           and colour_share(picture, BAR, BAR_BOX) > 0.4,
           f"title {title()!r}, {window}; "
           f"{picture}\n" + launcher_log())
    pid = chromium_pid()
    arguments = root(f"tr '\\0' ' ' < /proc/{pid}/cmdline").stdout
    report("Chromium runs as an application window on the local server, with a profile of "
           "the module's own",
           f"--app=http://127.0.0.1:8123/hello-web/?lang={SPEAKS['lang']}" in arguments
           and f"--user-data-dir=/home/{CHILD}/.config/kidux/hello-web/chromium" in arguments,
           arguments)
    # Its own words in Leo's language: that translation is what the browser
    # has loaded.
    report("Chromium's own words are in Leo's language: its translation loaded",
           f"--lang={SPEAKS['lang']} " in arguments
           and root(f"grep -c 'locales/{SPEAKS['pak']}.pak' /proc/{pid}/maps"
                    ).stdout.strip() not in ("", "0"),
           root(f"grep 'locales/' /proc/{pid}/maps | awk '{{print $6}}' | sort -u").stdout)

    # The lock over Chromium, and continuing: the same one comes back.
    locked = machine.mark()
    machine.monitor("system_powerdown")
    wait(lambda: active_terminal() == "tty8", 20)
    machine.shown("locked", locked)
    asked = machine.mark()
    machine.key("ret")                           # Continue
    machine.shown("child_password", asked)
    machine.submit(CHILD_PASSWORD)
    report("the lock and continuing bring the same Chromium back",
           wait(lambda: active_terminal() == "tty7", 15) and wait(lambda: on_screen() == "hello-web", 10)
           and chromium_pid() == pid, f"{pid} then {chromium_pid()}")
    machine.still(10)

    # Done has the focus.
    ended = journal_count("kidux-launcher", "module hello-web ended")
    machine.key("ret")
    report("Done closes it, and the launcher is back",
           wait(lambda: journal_count("kidux-launcher", "module hello-web ended") > ended, 30)
           and wait(lambda: on_screen() == HOME, 10), launcher_log())

    # Opened again, with Enter: the tile has kept the focus. The link to the
    # internet is two stops before Done, Save between them.
    launcher_shown(machine)
    report("it opens again", open_it(machine, ("ret",)), title())
    machine.key("shift-tab")
    machine.key("shift-tab")
    machine.key("ret")
    left = wait(lambda: title() not in ("", HEADING), 30, 1)
    blocked = machine.screenshot("module-hello-web-link")
    # debian.org's own page is titled "Debian -- The Universal Operating
    # System"; the page Chromium shows in its place is named after the address.
    report("the link to a page on the internet leads nowhere: Chromium's policy blocks it",
           left and "Debian --" not in title(), f"title {title()!r}; {blocked}")
    machine.key("alt-left")
    report("and back is the page again", wait(lambda: title() == HEADING, 30, 1), title())
    machine.still(10)
    ended = journal_count("kidux-launcher", "module hello-web ended")
    machine.key("alt-f4")
    report("after the link, Alt+F4, the bar's Close, closes Chromium, and the launcher is back",
           wait(lambda: journal_count("kidux-launcher", "module hello-web ended") > ended, 30)
           and chromium_pid() == "" and wait(lambda: on_screen() == HOME, 10), launcher_log())

    launcher_shown(machine)
    report("it opens once more", open_it(machine, ("ret",)), title())
    # Save is the stop before Done.
    root(f"rm -f {SAVED}")
    machine.key("shift-tab")
    machine.key("ret")
    asked = wait(lambda: dialog() != {}, 30, 1)
    machine.still(3)
    picture = machine.screenshot("module-hello-web-save")
    report("Save asks where to keep the page, in the file dialog",
           asked, f"{windows()}; {picture}")
    # The name has the focus, and Enter there does nothing in Chromium's
    # dialog: Tab past the search button to Save, and press it.
    for key in ("tab", "tab", "spc"):
        machine.key(key)
    report("and its Save keeps it in Leo's Downloads, downloaded from its blob: address",
           wait(lambda: root(f"grep -qF {shlex_quote(HEADING)} {SAVED}").returncode == 0, 30)
           and root(f"stat -c %U {SAVED}").stdout.strip() == CHILD
           and wait(lambda: dialog() == {}, 10),
           root(f"ls -la /home/{CHILD}/{SPEAKS['folders'][1]}").stdout)
    report("the lock screen's Log out ends it with the session", lock_and_log_out(machine),
           root(f"ps -u {CHILD} -o pid,args").stdout)

    root(f"runuser -u debian -- /usr/local/bin/kidux-as enable {CHILD} hello-web off")
    report("and the daemon removes it", daemon("remove"), root("tail -5 /var/log/apt/term.log").stdout)
