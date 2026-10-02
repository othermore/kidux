"""A child's session, from signing in to logging out: the launcher, locks, the
adult on the lock screen, the panel, greetd restarting under a lock."""

import time

from sessionlib import (
    CHILD,
    CHILD_PASSWORD,
    Machine,
    NIGHT,
    SPEAKS,
    active_terminal,
    as_child,
    child_session,
    colour_share,
    greeter_log,
    journal_count,
    launcher_pid,
    launcher_shown,
    lock_screen_adult,
    report,
    root,
    ssh,
    up,
    wait,
)

#: The launcher's bar (kidux_launcher/view.py).
BAR = (0xF2, 0xE2, 0xCC)


def run(machine: Machine) -> None:
    # A child's ~/.profile is theirs to write, and must not decide how their
    # session starts: greetd does not run it (source_profile = false).
    root(f"printf 'exec sleep infinity\\n' > /home/{CHILD}/.profile && chown {CHILD}: /home/{CHILD}/.profile")

    # The first picture has the focus; Enter taps it.
    before = machine.mark()
    machine.key("ret")
    machine.shown("password", before)
    machine.screenshot("password")

    # PAM waits three seconds before it says no, and the screen shows the
    # password again with a sentence.
    before = machine.submit("not it")
    machine.shown("password", before)
    machine.screenshot("wrong-password")
    report("a wrong password signs nobody in", child_session() is None, greeter_log())

    machine.type(CHILD_PASSWORD + "\n")
    signed_in = wait(lambda: child_session() is not None, 30)
    report("a child signs in by typing their password on the sign-in screen", signed_in,
           greeter_log() + ssh("loginctl list-sessions --no-legend").stdout)
    if not signed_in:
        return
    sid = child_session()
    properties = ssh(f"loginctl show-session {sid} -p VTNr -p Class -p Active -p Type").stdout
    report("the child's session is on terminal 7 and has the screen",
           "VTNr=7" in properties and "Active=yes" in properties, properties)

    environment = root(f"cat /proc/$(pgrep -u {CHILD} -x labwc | head -1)/environ | tr '\\0' '\\n'").stdout
    report("the session got the child's language from the sign-in screen (D24)",
           f"LANG={SPEAKS['locale']}" in environment
           and f"XKB_DEFAULT_LAYOUT={SPEAKS['keyboard']}" in environment,
           environment)
    report("the child's session runs labwc, with Kidux's kiosk configuration, and the "
           "launcher in it",
           root(f"pgrep -u {CHILD} -f '^labwc -C /usr/share/kidux/labwc/kiosk ' "
                f"&& pgrep -u {CHILD} -f kidux-launcher").returncode == 0,
           root(f"ps -u {CHILD} -o pid,args").stdout)
    # What the machine has, and how its keys are written, as the launcher
    # says at the start (D61): the test machine has none of a laptop's
    # things, and is no Mac.
    # (PipeWire's Dummy Output, the test machine's only sink, is no sound.)
    report("the launcher found no battery, backlight, keyboard light, lid or sound on this machine",
           wait(lambda: journal_count("kidux-launcher", "hardware: battery=none backlight=none "
                                      "keyboard=none lid=no mac=no fn=no audio=no") > 0, 10),
           root("journalctl -b -o cat -t kidux-launcher | grep hardware").stdout)
    report("and writes the keys as a PC's: Win, Alt+F4, Alt+Tab",
           journal_count("kidux-launcher", "keys: home=Win close=Alt+F4 next=Alt+Tab") > 0,
           root("journalctl -b -o cat -t kidux-launcher | grep keys").stdout)
    # The keys, as labwc runs them for the child: nothing to do here, and
    # nothing goes wrong.
    keys = [as_child(f"/usr/libexec/kidux-keys {what}").returncode
            for what in ("volume up", "volume mute", "brightness up", "keyboard down")]
    report("the laptop's keys run for the child, and do nothing on this machine",
           keys == [0, 0, 0, 0], str(keys))
    # The corner reads the levels again at once when a key has changed one:
    # the key touches a file in the child's runtime directory, which the
    # corner watches (step 3.24). Nothing changes here, so the file is not
    # made; the corner has made its directory, to watch it.
    uid = root(f"id -u {CHILD}").stdout.strip()
    report("the corner watches for a key's change, in the child's runtime directory",
           root(f"test -d /run/user/{uid}/kidux").returncode == 0,
           root(f"ls -la /run/user/{uid}").stdout)
    report("the daemon is counting the child's time",
           wait(lambda: "active = true" in root(
               f"cat /home/.kidux/children/{CHILD}/usage.toml").stdout, 15))
    launcher_shown(machine)
    launcher = machine.screenshot("launcher")
    report("the launcher shows the mascot while there is nothing to open, and the logo",
           colour_share(launcher, NIGHT, (0.35, 0.2, 0.65, 0.7)) > 0.02
           and colour_share(launcher, NIGHT, (0.35, 0.8, 0.65, 0.92)) > 0.005, str(launcher))
    report("and the bar along the bottom, below everything else",
           colour_share(launcher, BAR, (0.0, 0.94, 1.0, 1.0)) > 0.4, str(launcher))
    home = root(f"ls /home/{CHILD}").stdout.split()
    report("the child's home has its usual folders, in the child's language",
           all(folder in home for folder in SPEAKS["folders"]), " ".join(home))
    report("a child's own ~/.profile changes nothing about how their session starts",
           launcher_pid() != "", root(f"ps -u {CHILD} -o pid,args").stdout)

    # The launcher's Lock button, which has the focus.
    before = machine.mark()
    machine.key("ret")
    locked = wait(lambda: 'lock = "requested"' in root(
        f"cat /home/.kidux/children/{CHILD}/usage.toml").stdout, 20)
    report("the launcher's Lock button locks the session", locked
           and wait(lambda: active_terminal() == "tty8", 10),
           root(f"cat /home/.kidux/children/{CHILD}/usage.toml").stdout)
    machine.shown("locked", before)
    before = machine.mark()
    machine.key("ret")                       # Continue
    machine.shown("child_password", before)
    machine.type(CHILD_PASSWORD + "\n")
    report("and the child continues into the same launcher",
           wait(lambda: active_terminal() == "tty7", 15) and launcher_pid() != "",
           greeter_log())

    # The daemon restarting under the launcher, and the launcher dying.
    before = launcher_pid()
    root("systemctl restart kidux-daemon")
    # Long enough for a launcher that would die with its daemon to have died.
    time.sleep(3)
    report("the launcher survives the daemon restarting under it",
           launcher_pid() == before and wait(lambda: "active = true" in root(
               f"cat /home/.kidux/children/{CHILD}/usage.toml").stdout, 15),
           root(f"ps -u {CHILD} -o pid,args").stdout)
    root(f"kill -KILL {before}")
    report("a launcher that dies is started again, in the same session",
           wait(lambda: launcher_pid() not in ("", before), 15) and child_session() == sid,
           root(f"ps -u {CHILD} -o pid,args").stdout
           + root("journalctl -b -o cat -t kidux-session | tail -3").stdout)
    launcher_shown(machine)

    # The power button, as the ACPI device reports it.
    before = machine.mark()
    machine.monitor("system_powerdown")
    locked = wait(lambda: 'lock = "power_button"' in root(
        f"cat /home/.kidux/children/{CHILD}/usage.toml").stdout, 20)
    report("the power button locks the session instead of turning the machine off",
           locked and up(), root(f"cat /home/.kidux/children/{CHILD}/usage.toml").stdout)
    report("the lock screen has the screen, on terminal 8", wait(lambda: active_terminal() == "tty8", 10),
           active_terminal())
    frozen = root(f"systemctl show session-{sid}.scope -p FreezerState --value").stdout.strip()
    report("the child's session is frozen", frozen == "frozen", frozen)
    machine.shown("locked", before)
    locked_picture = machine.screenshot("lock-screen")
    report("the lock screen shows Kidux's logo, small, in the bottom middle",
           colour_share(locked_picture, NIGHT, (0.4, 0.88, 0.6, 1.0)) > 0.005, str(locked_picture))

    # Continue has the focus on the lock screen; Enter taps it.
    before = machine.mark()
    machine.key("ret")
    machine.shown("child_password", before)
    machine.screenshot("lock-password")
    machine.type(CHILD_PASSWORD + "\n")
    report("the child continues by typing their own password on the lock screen",
           wait(lambda: active_terminal() == "tty7", 15),
           active_terminal() + "\n" + greeter_log())
    report("and their session is exactly where it was", child_session() == sid
           and root(f"systemctl show session-{sid}.scope -p FreezerState --value").stdout.strip()
           == "running")

    # An adult, on the lock screen: the panel, then time. Locked this time
    # with Ctrl+Alt+Escape, the other secure-attention key (D16).
    before = machine.mark()
    machine.key("ctrl-alt-esc")
    report("Ctrl+Alt+Escape locks the session as the power button does",
           wait(lambda: active_terminal() == "tty8", 20),
           root(f"cat /home/.kidux/children/{CHILD}/usage.toml").stdout)
    machine.shown("locked", before)
    lock_screen_adult(machine)
    machine.screenshot("lock-adult-options")
    # 15, 30, 60 minutes, the adult's own number and its button, save, log
    # out, then the panel.
    for _ in range(7):
        machine.key("tab")
    before = machine.mark()
    machine.key("ret")
    opened = machine.shown("panel_children", before)
    machine.screenshot("panel-children")
    report("the adult panel opens from the lock screen, on the first child's form",
           opened and "could not draw" not in greeter_log(), greeter_log())

    # One page, by keyboard: the focus is in the name. Tab to the picture,
    # open it, take the next one, back to the name, Enter saves.
    profile = f"/home/.kidux/children/{CHILD}/profile.toml"
    avatar_before = root(f"grep ^avatar {profile}").stdout.strip()
    machine.key("tab")
    frame = machine.settled()
    machine.key("ret")
    machine.changes(frame, share=0.05)          # the list, not the button pressed
    machine.screenshot("panel-picture-list")
    machine.key("down")
    frame = machine.settled()
    machine.key("ret")
    machine.changes(frame)
    machine.key("shift-tab")
    saved_before = machine.mark()
    machine.key("ret")
    machine.shown("panel_children", saved_before, 10)
    avatar_after = root(f"grep ^avatar {profile}").stdout.strip()
    machine.screenshot("panel-child")
    report("the child's picture is changed and saved from the one page",
           avatar_after and avatar_after != avatar_before, f"{avatar_before} -> {avatar_after}")

    # Giving time is just above the form: from the name, back past the
    # adult's own number and its button, to 60.
    for _ in range(3):
        machine.key("shift-tab")
    machine.key("ret")
    report("and time is given from the same page",
           wait(lambda: '"source": "panel"' in root(
               "grep '\"grant\"' /home/.kidux/state/audit.log | tail -1").stdout, 10),
           root("tail -3 /home/.kidux/state/audit.log").stdout)

    # The system page: back past the time (five controls), the children,
    # Add and Network, to System.
    machine.still()
    for _ in range(11):
        machine.key("shift-tab")
    before = machine.mark()
    machine.key("ret")
    report("the system page is one form too", machine.shown("panel_system", before, 10),
           greeter_log())
    machine.screenshot("panel-system")
    before = machine.mark()
    machine.key("esc")                       # closes the panel: the lock screen again
    back = machine.shown("locked", before)
    report("closing the panel returns to the lock screen and locks the panel",
           back and "panel locked" in root("tail -20 /home/.kidux/state/audit.log").stdout,
           greeter_log())
    machine.still()
    lock_screen_adult(machine)
    machine.key("ret")                       # fifteen minutes, the first choice
    report("an adult gives time on the lock screen and the session carries on",
           wait(lambda: active_terminal() == "tty7", 15) and child_session() == sid,
           active_terminal() + "\n" + greeter_log())

    # greetd restarting while the child is locked, as it would after a crash:
    # the lock screen must not outlive the session it guarded, and the
    # sign-in screen that comes back must have the keyboard.
    machine.monitor("system_powerdown")
    wait(lambda: active_terminal() == "tty8", 20)
    before = machine.mark()
    root("systemctl restart greetd")
    report("greetd restarting under a locked session takes its lock screen down too",
           wait(lambda: ssh(f"systemctl is-active kidux-locker@{CHILD}").stdout.strip() != "active", 20),
           ssh(f"systemctl status kidux-locker@{CHILD} --no-pager").stdout)
    wait(lambda: active_terminal() == "tty7"
         and "greeter" in ssh("loginctl list-sessions --no-legend").stdout, 30)
    machine.shown("choose", before)
    before = machine.mark()
    machine.key("ret")
    machine.shown("password", before)
    machine.type(CHILD_PASSWORD + "\n")
    report("and the sign-in screen that comes back has the keyboard",
           wait(lambda: child_session() is not None, 30), greeter_log())

    # Log out, from the launcher: Lock has the focus, Log out is next, and it
    # asks once, with Cancel first.
    launcher_shown(machine)
    machine.still()
    machine.key("tab")
    frame = machine.settled()
    machine.key("ret")
    machine.changes(frame)
    machine.screenshot("log-out-question")
    machine.key("tab")
    machine.key("ret")
    report("the child logs out from the launcher and nothing of theirs keeps running",
           wait(lambda: root(f"pgrep -u {CHILD} -x labwc").returncode != 0, 20),
           root(f"ps -u {CHILD} -o pid,args").stdout
           + root("journalctl -b -o cat -t kidux-session -t kidux-launcher | tail -5").stdout)
    report("and the sign-in screen is back", wait(lambda: active_terminal() == "tty7"
           and "greeter" in ssh("loginctl list-sessions --no-legend").stdout, 30))
