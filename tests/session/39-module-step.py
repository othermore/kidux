"""Step, a physics playground (phase-4f-plan.md, step 4.29), with its guide
(phase-4g-plan.md, step 4.36), whose first mission opens in Step.

Installed through the daemon, as the panel installs it, with Step and the
Wayland plugin of its Qt, and switched on for Leo from the command line.
Leo opens it by keyboard: it comes up in a window filling the room above
the bar, in Leo's language, with its settings in the module's own
directory and the module's restrictions on KDE's actions read first. A
web page it asks the desktop to open is Kidux's bubble, and no browser
starts (phase-4g-plan.md, step 4.38). Alt+F4 closes it, the launcher
comes back, and the daemon removes it, Step with it (D100).
"""

from sessionlib import (
    SPEAKS,
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

MODULE = "step"
PROGRAM = "step"
#: The Wayland plugin of the program's Qt, which its own package does not bring.
PLUGIN = "qt6-wayland"
HOME = f"/home/{CHILD}"
CONFIG = f"{HOME}/.config/kidux/{MODULE}"
KDE = f"/usr/share/kidux/modules/{MODULE}/kde"
#: The room above the launcher's bar, and the bar.
ABOVE_THE_BAR = (0.0, 0.0, 1.0, 0.92)
#: Step's room, left of its guide's pane.
STEP_ROOM = (0.0, 0.0, 0.6, 0.92)
#: Lesson 1's mission, as the guide copies it into Leo's Documents.
MISSION = {"es": "Misiones de Step/caida.step", "en": "Missions of Step/fall.step"}
BAR = (0xF2, 0xE2, 0xCC)
BAR_BOX = (0.0, 0.94, 1.0, 1.0)


def daemon(command: str) -> bool:
    """`kidux-as install|remove <module>`: the daemon's job, start to end."""
    return root(f"runuser -u debian -- /usr/local/bin/kidux-as {command} {MODULE}",
                timeout=1800).stdout.startswith(command + ("ed " if command == "install" else "d "))


def program_pid() -> str:
    return root(f"pgrep -u {CHILD} -x {PROGRAM} | head -1").stdout.strip()


def module_window() -> dict:
    return next((w for w in windows() if w.get("module") == MODULE), {})


def run(machine: Machine) -> None:
    report(f"kidux-module-{MODULE} installs from the archive through the daemon, with "
           f"{PROGRAM} and its Wayland plugin",
           daemon("install") and root(f"dpkg-query -W -f '${{db:Status-Status}} ' {PROGRAM} "
                                     f"{PLUGIN}").stdout == "installed installed ",
           root("tail -5 /var/log/apt/term.log").stdout)
    root(f"runuser -u debian -- /usr/local/bin/kidux-as enable {CHILD} {MODULE} on")

    before = journal_count("kidux-launcher", f"tiles: {MODULE}")
    password = machine.mark()
    machine.key("ret")                           # Leo, the first picture
    machine.shown("password", password)
    machine.submit(CHILD_PASSWORD)
    report("Leo signs in to its tile", wait(lambda: child_session() is not None, 30)
           and wait(lambda: journal_count("kidux-launcher", f"tiles: {MODULE}") > before, 30)
           and launcher_shown(machine), greeter_log() + launcher_log())

    # From Lock, which has the focus, back to the tile, and Enter.
    machine.key("shift-tab")
    machine.key("ret")
    opened = wait(lambda: module_window() != {}, 90, 2)
    wait(lambda: on_screen() == MODULE, 10)
    machine.still(5)
    picture = machine.screenshot(f"module-{MODULE}")
    window = module_window()
    report("Leo opens it by keyboard, a window filling the room above the bar",
           opened and on_screen() == MODULE and window.get("maximized")
           and not window.get("fullscreen")
           and colour_share(picture, CREAM, STEP_ROOM) < 0.2
           and colour_share(picture, BAR, BAR_BOX) > 0.4,
           f"{window}; {picture}\n" + launcher_log())

    pid = program_pid()
    environment = root(f"tr '\\0' '\\n' < /proc/{pid}/environ").stdout
    report("its settings are the module's own, and it reads the module's restrictions on KDE's "
           "actions first",
           f"XDG_CONFIG_HOME={CONFIG}" in environment
           and f"XDG_CONFIG_DIRS={KDE}:" in environment
           and root(f"grep -qx 'ghns=false' {KDE}/kdeglobals").returncode == 0
           and root(f"grep -qx 'action/fullscreen=false' {KDE}/kdeglobals").returncode == 0
           and root(f"test ! -e {CONFIG}/kdeglobals").returncode == 0,
           environment + root(f"ls -la {CONFIG} {KDE}").stdout)

    # Links out of it: with Step's own environment, the desktop asked to
    # open a web page, as Step's Open in browser asks, or a site, answers
    # each with Kidux's bubble and opens nothing (D107).
    page = f"{HOME}/page.html"
    root(f"printf '%s\\n' '<!DOCTYPE html>' '<html><head><title>Step</title></head>' "
         f"'<body><p>Step</p></body></html>' > {page} && chown {CHILD} {page}")
    told = journal_count("kidux-launcher", "from Kidux")
    asked = [root(f"runuser -u {CHILD} -- xargs -0 -a /proc/{pid}/environ "
                  f"sh -c 'exec env -i \"$@\" timeout 30 xdg-open {link}' sh")
             for link in (page, "https://phet.colorado.edu/")]
    report("a web page or a site it asks the desktop to open is Kidux's bubble, "
           "and no browser starts",
           f"XDG_CONFIG_DIRS={KDE}:/usr/share/kidux/session/xdg:" in environment
           and all(answer.returncode == 0 for answer in asked)
           and wait(lambda: journal_count("kidux-launcher", "from Kidux") >= told + 2, 10)
           and root(f"pgrep -u {CHILD} chromium").returncode == 1,
           "".join(answer.stdout + answer.stderr for answer in asked) + launcher_log())
    root(f"rm -f {page}")

    # Alt+F4 asks it to close; one that asks something first is ended by
    # Alt+F4 again, as the bar's question says (D45).
    ended = journal_count("kidux-launcher", f"module {MODULE} ended")
    machine.key("alt-f4")
    if not wait(lambda: journal_count("kidux-launcher", f"module {MODULE} ended") > ended, 20):
        machine.key("alt-f4")
    report("Alt+F4 closes it, and the launcher comes back",
           wait(lambda: journal_count("kidux-launcher", f"module {MODULE} ended") > ended, 20)
           and wait(lambda: on_screen() == "home", 10),
           launcher_log())

    # Lesson 1's mission, copied when the guide first showed, given to the
    # starter as a file, opens in Step, titled with its name.
    mission = f"{HOME}/{SPEAKS['folders'][0]}/{MISSION[SPEAKS['lang']]}"
    uid = root(f"id -u {CHILD}").stdout.strip()
    root(f"runuser -u {CHILD} -- env XDG_RUNTIME_DIR=/run/user/{uid} systemd-run --user "
         f"--quiet --unit=step-mission -p Environment=XDG_CONFIG_HOME={CONFIG} "
         f"/usr/libexec/kidux-module-{MODULE} '{mission}'", timeout=60)
    name = mission.rsplit("/", 1)[-1]
    titled = wait(lambda: name in (module_window().get("title") or ""), 60, 2)
    report("lesson 1's mission is in Leo's Documents and opens in Step by its name",
           root(f"test -f '{mission}'").returncode == 0 and titled,
           f"{module_window()}\n" + root(f"ls -la '{HOME}/{SPEAKS['folders'][0]}'").stdout)
    root(f"runuser -u {CHILD} -- env XDG_RUNTIME_DIR=/run/user/{uid} "
         "systemctl --user stop step-mission")
    wait(lambda: module_window() == {}, 20)

    # Log out from the lock screen, past Continue and Adult.
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
    report("Leo logs out from the lock screen", wait(lambda: child_session() is None, 30),
           greeter_log())
    machine.shown("choose", choose, 30)

    root(f"runuser -u debian -- /usr/local/bin/kidux-as enable {CHILD} {MODULE} off")
    report("and the daemon removes it, and the program with it (D100)",
           daemon("remove") and root(f"dpkg-query -W -f '${{db:Status-Status}}' {PROGRAM}"
                                     ).stdout != "installed",
           root("tail -5 /var/log/apt/term.log").stdout)
