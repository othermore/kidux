"""GCompris, the first real module (phase-3-plan.md, step 3.6).

Installed through the daemon, as the panel installs it, without Debian's
recommendations, and switched on for Leo from the command line; the
panel's own keys are 17-module-hello.py's. Leo
opens it by keyboard; it comes up filling the room above the bar,
not the whole screen it asks for, straight on its menu with none of its
first-start questions, in Leo's language, with the module's three
directories, and with sound through PipeWire in Leo's session. The lock
and continuing bring the same GCompris back, and the lock screen's *Log
out* ends it with the session. Purged at the end.
"""

from sessionlib import (
    CHILD,
    CHILD_PASSWORD,
    Machine,
    SPEAKS,
    active_terminal,
    as_child,
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

HOME = f"/home/{CHILD}"
CONF = f"{HOME}/.config/kidux/gcompris/gcompris/gcompris-qt.conf"
#: Kidux's cream: the launcher's, and none of GCompris's.
CREAM = (0xFF, 0xF6, 0xE9)
#: The room above the launcher's bar, and the bar.
ABOVE_THE_BAR = (0.0, 0.0, 1.0, 0.92)
BAR = (0xF2, 0xE2, 0xCC)
BAR_BOX = (0.0, 0.94, 1.0, 1.0)


def daemon(command: str) -> bool:
    """`kidux-as install|remove gcompris`: the daemon's job, start to end."""
    return root(f"runuser -u debian -- /usr/local/bin/kidux-as {command} gcompris",
                timeout=1200).stdout.startswith(command + ("ed " if command == "install" else "d "))


def gcompris_pid() -> str:
    return root(f"pgrep -u {CHILD} -x gcompris-qt | head -1").stdout.strip()


def gcompris_window() -> dict:
    return next((w for w in windows() if w.get("module") == "gcompris"), {})


def grass(frame: bytes) -> float:
    """The share of the lower part of a screen dump, above the bar, that is
    green: GCompris's menu stands on a meadow, and its loading screen and
    the launcher have none."""
    parts = frame.split(b"\n", 3)              # P6, width height, 255, pixels
    if len(parts) < 4 or parts[0] != b"P6":
        return 0.0
    pixels = parts[3]
    lower = pixels[len(pixels) * 60 // 100 // 3 * 3:len(pixels) * 90 // 100 // 3 * 3]
    samples = range(0, len(lower) - 2, 3 * 97)
    hits = sum(1 for i in samples if lower[i + 1] > lower[i] + 30 and lower[i + 1] > lower[i + 2] + 10)
    return hits / max(1, len(samples))


def own(name: str) -> tuple[str, str, str]:
    return (f"{HOME}/.config/kidux/{name}", f"{HOME}/.local/share/kidux/{name}",
            f"{HOME}/.cache/kidux/{name}")


def run(machine: Machine) -> None:
    report("kidux-module-gcompris installs from the archive through the daemon, as the panel "
           "asks", daemon("install"), root("tail -5 /var/log/apt/term.log").stdout)
    root(f"runuser -u debian -- /usr/local/bin/kidux-as enable {CHILD} gcompris on")

    before = journal_count("kidux-launcher", "tiles: gcompris")
    password = machine.mark()
    machine.key("ret")                           # Leo, the first picture
    machine.shown("password", password)
    machine.submit(CHILD_PASSWORD)
    report("Leo signs in to its tile", wait(lambda: child_session() is not None, 30)
           and wait(lambda: journal_count("kidux-launcher", "tiles: gcompris") > before, 30)
           and launcher_shown(machine), greeter_log() + launcher_log())

    # From Lock, which has the focus, back to the tile, and Enter. GCompris
    # takes a while to draw its first screen on the machine's software
    # rendering.
    machine.key("shift-tab")
    machine.key("ret")
    opened = wait(lambda: gcompris_window() != {}, 90, 2)
    wait(lambda: on_screen() == "gcompris", 10)
    wait(lambda: grass(machine.frame()) > 0.3, 120, 2)
    machine.still(10)
    picture = machine.screenshot("module-gcompris")
    window = gcompris_window()
    report("Leo opens it by keyboard, filling the room above the bar, not the whole screen",
           opened and on_screen() == "gcompris" and window.get("maximized")
           and not window.get("fullscreen")
           and colour_share(picture, BAR, BAR_BOX) > 0.4,
           f"{window}; "
           f"{picture}\n" + launcher_log())

    settings = root(f"cat {CONF}").stdout
    report("it starts on its menu: its first questions are answered, downloads on",
           "exeCount=" in settings and "enableAutomaticDownloads=true" in settings
           and colour_share(picture, CREAM, ABOVE_THE_BAR) < 0.05, settings + str(picture))

    pid = gcompris_pid()
    environment = root(f"tr '\\0' '\\n' < /proc/{pid}/environ").stdout
    report("it runs in Leo's language, with the module's own three directories",
           f"LANG={SPEAKS['locale']}" in environment
           and all(f"{variable}={path}" in environment for variable, path in zip(
               ("XDG_CONFIG_HOME", "XDG_DATA_HOME", "XDG_CACHE_HOME"), own("gcompris"))),
           environment)
    clients = as_child("timeout 10 pw-cli list-objects Client").stdout
    report("and it is a client of the PipeWire in Leo's session",
           "gcompris" in clients.lower(), clients[-600:])

    # The lock over GCompris, and continuing: the same one comes back.
    locked = machine.mark()
    machine.monitor("system_powerdown")
    wait(lambda: active_terminal() == "tty8", 20)
    machine.shown("locked", locked)
    asked = machine.mark()
    machine.key("ret")                           # Continue
    machine.shown("child_password", asked)
    machine.submit(CHILD_PASSWORD)
    report("the lock and continuing bring the same GCompris back",
           wait(lambda: active_terminal() == "tty7", 15) and wait(lambda: on_screen() == "gcompris", 10)
           and gcompris_pid() == pid, f"{pid} then {gcompris_pid()}")

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
    report("logging out from the lock screen ends GCompris with the session",
           wait(lambda: child_session() is None and gcompris_pid() == "", 30),
           root(f"ps -u {CHILD} -o pid,args").stdout)
    machine.shown("choose", choose, 30)

    root(f"runuser -u debian -- /usr/local/bin/kidux-as enable {CHILD} gcompris off")
    report("and the daemon removes it", daemon("remove"), root("tail -5 /var/log/apt/term.log").stdout)
