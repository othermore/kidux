"""Mail (phase-4d-plan.md, step 4.22).

kidux-module-mail, Thunderbird as a child's mailbox, is installed through
the daemon, as the panel installs it, and switched on for Leo from the
command line, where an adult also gives Leo's address, name and both
servers: 127.0.0.1, so that nothing leaves the machine and nothing
answers. Leo opens it by keyboard: Thunderbird's window comes up above the
bar with Leo's account in it and no account setup, and what it says about
the server that does not answer comes up as Kidux's bubble, from Mail, and
goes by itself, never as a window of Thunderbird's (D98). A notice sent
from Leo's session as urgent stays until it is closed by its number. Its profile is
Leo's alone, with the user.js the settings make. Alt+F4 closes it and
gives the launcher back; the lock screen's *Log out* ends the session, and
the daemon removes it.
"""

import json
import re

from sessionlib import (
    CHILD,
    CHILD_PASSWORD,
    CREAM,
    Machine,
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

AS = "runuser -u debian -- /usr/local/bin/kidux-as"
PROFILE = f"/home/{CHILD}/.config/kidux/mail/thunderbird"
ADDRESS = "leo@example.org"
#: What an adult gives on the panel: the address, the name, and the servers
#: of a provider Mail cannot find by itself.
SETTINGS = {"email": ADDRESS, "name": "Leo", "imap_host": "127.0.0.1", "smtp_host": "127.0.0.1"}
#: The room above the launcher's bar.
ABOVE_THE_BAR = (0.0, 0.0, 1.0, 0.92)


def daemon(command: str) -> bool:
    """`kidux-as install|remove mail`: the daemon's job, start to end."""
    return root(f"{AS} {command} mail",
                timeout=1500).stdout.startswith(command + ("ed " if command == "install" else "d "))


def thunderbird_pid() -> str:
    return root(f"pgrep -u {CHILD} -f /usr/lib/thunderbird/thunderbird | sort -n | head -1").stdout.strip()


def mail_window() -> dict:
    """Thunderbird's own window, which is named after Leo's account."""
    return next((w for w in windows() if w.get("module") == "mail"
                 and ADDRESS in (w.get("title") or "")), {})


def dialogs() -> list[dict]:
    """Any other window of Thunderbird's: a question, or a notice."""
    return [w for w in windows() if w.get("module") == "mail"
            and ADDRESS not in (w.get("title") or "")]


def notices(text: str = "", after: int = 0) -> list[str]:
    """The launcher's lines about notices, from the `after`th on, that hold
    `text`: a notice's number starts again with each launcher."""
    lines = [line for line in root("journalctl -b -o cat -t kidux-launcher").stdout.splitlines()
             if "INFO: notice " in line]
    return [line for line in lines[after:] if text in line]


#: A notice sent as Leo through the desktop's notifications, as a program
#: does: its number is printed.
NOTIFY = """python3 -c 'from gi.repository import Gio, GLib
bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)
print(bus.call_sync("org.freedesktop.Notifications", "/org/freedesktop/Notifications",
    "org.freedesktop.Notifications", "Notify", GLib.Variant("(susssasa{sv}i)", ("Kidux test",
    0, "", "Test", "An urgent notice", [], {"urgency": GLib.Variant("y", 2)}, -1)),
    GLib.VariantType.new("(u)"), Gio.DBusCallFlags.NONE, 5000, None).unpack()[0])'"""
CLOSE = """python3 -c 'from gi.repository import Gio, GLib
Gio.bus_get_sync(Gio.BusType.SESSION, None).call_sync("org.freedesktop.Notifications",
    "/org/freedesktop/Notifications", "org.freedesktop.Notifications", "CloseNotification",
    GLib.Variant("(u)", ({number},)), None, Gio.DBusCallFlags.NONE, 5000, None)'"""


def run(machine: Machine) -> None:
    report("kidux-module-mail installs from the archive through the daemon, with Thunderbird",
           daemon("install"), root("tail -5 /var/log/apt/term.log").stdout)
    root(f"{AS} enable {CHILD} mail on")
    given = [root(f"{AS} set-setting {CHILD} mail {key} {json.dumps(json.dumps(value))}").returncode
             for key, value in SETTINGS.items()]
    report("an adult gives Leo's address, name and servers",
           given == [0] * len(SETTINGS)
           and json.loads(root(f"runuser -u {CHILD} -- /usr/local/bin/kidux-as my-settings mail"
                               ).stdout or "{}") == SETTINGS,
           root("tail -4 /home/.kidux/state/audit.log").stdout)

    before = journal_count("kidux-launcher", "tiles: mail")
    password = machine.mark()
    machine.key("ret")                           # Leo, the first picture
    machine.shown("password", password)
    machine.submit(CHILD_PASSWORD)
    report("Leo signs in to its tile", wait(lambda: child_session() is not None, 30)
           and wait(lambda: journal_count("kidux-launcher", "tiles: mail") > before, 30)
           and launcher_shown(machine), greeter_log() + launcher_log())

    # From Lock, which has the focus, back to the tile, and Enter.
    told = len(notices())
    machine.key("shift-tab")
    machine.key("ret")
    opened = wait(lambda: mail_window() != {}, 90, 2)
    # The server that does not answer is told of in Kidux's bubble, from
    # Mail, and it goes by itself; never in a window of Thunderbird's.
    bubbled = wait(lambda: notices("from mail", told) != [], 60, 2)
    machine.still(2)
    machine.screenshot("mail-notice")
    said = notices("from mail", told)[0] if bubbled else ""
    number = re.search(r"notice (\d+) from", said)
    report("Thunderbird's notice that the server does not answer is Kidux's bubble, from Mail",
           bubbled and not dialogs(), f"{said}; {dialogs()}\n" + launcher_log())
    report("and it goes by itself",
           number is not None
           and wait(lambda: notices(f"notice {number.group(1)} closed (1)", told) != [], 20, 1),
           "\n".join(notices(after=told)))
    # A question for a password would be a window of its own, which Escape
    # closes.
    machine.still(3)
    for _ in range(3):
        if not dialogs():
            break
        machine.key("esc")
        machine.still(2)
    wait(lambda: on_screen() == "mail", 10)
    machine.still(3)
    picture = machine.screenshot("module-mail")
    window = mail_window()
    report("Leo opens it by keyboard: Thunderbird, above the bar, on Leo's account, with no "
           "account setup and no notice over it",
           opened and on_screen() == "mail" and window.get("app_id") == "thunderbird"
           and window.get("maximized") and not window.get("fullscreen")
           and not dialogs() and colour_share(picture, CREAM, ABOVE_THE_BAR) < 0.2,
           f"{window}; {dialogs()}; {picture}\n" + launcher_log())

    profile = root(f"stat -c '%a %U' {PROFILE}").stdout.strip()
    written = root(f"cat {PROFILE}/user.js").stdout
    report("its profile is Leo's alone, with the account the settings make",
           profile == f"700 {CHILD}"
           and f'user_pref("mail.identity.id1.useremail", "{ADDRESS}");' in written
           and 'user_pref("mail.server.server1.hostname", "127.0.0.1");' in written
           and 'user_pref("mail.smtpserver.smtp1.hostname", "127.0.0.1");' in written,
           f"{profile}\n{written}")

    told = len(notices())
    sent = as_child(NOTIFY).stdout.strip()
    stayed = sent.isdigit() and wait(lambda: notices(f"notice {sent} from", told) != [], 10, 1) \
        and not wait(lambda: notices(f"notice {sent} closed", told) != [], 12, 2)
    as_child(CLOSE.format(number=sent if sent.isdigit() else 0))
    report("an urgent notice stays until it is closed by its number",
           stayed and wait(lambda: notices(f"notice {sent} closed (3)", told) != [], 10, 1),
           f"{sent!r}\n" + "\n".join(notices(after=told)))

    ended = journal_count("kidux-launcher", "module mail ended")
    machine.key("alt-f4")
    report("Alt+F4 closes it, and the launcher comes back",
           wait(lambda: journal_count("kidux-launcher", "module mail ended") > ended, 20)
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
    report("Leo logs out from the lock screen, and Thunderbird goes with the session",
           wait(lambda: child_session() is None and thunderbird_pid() == "", 30), greeter_log())
    machine.shown("choose", choose, 30)

    root(f"{AS} enable {CHILD} mail off")
    report("and the daemon removes it", daemon("remove"), root("tail -5 /var/log/apt/term.log").stdout)
