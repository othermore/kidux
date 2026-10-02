"""A child's time runs out while they are signed in, an adult gives time, then
unlocks to save.

Tim has an hour a day, and an adult sets what he has left to none, as the
panel's child page does (D50): the session locks at once, as when the time
runs out by itself, which the daemon's tests check minute by minute.

Unlock to save gives minutes nobody is charged for, which the test waits
out without a touch: the machine's `save_minutes` is set to one, not to
wait the five a machine gives, and the session's own idle lock (D67),
five minutes, which would win that race on a machine set as it comes, is
fifteen for Tim's session, the setting it reads when it starts. Both go
back after.
"""

from sessionlib import (
    ADULT_PASSWORD,
    Machine,
    active_terminal,
    greeter_log,
    lock_screen_adult,
    report,
    root,
    ssh,
    wait,
)


AS = "runuser -u debian -- /usr/local/bin/kidux-as"


def run(machine: Machine) -> None:
    root(f"{AS} set-config idle_lock_minutes 15")
    root(f"{AS} set-config save_minutes 1")
    try:
        time_runs_out(machine)
    finally:
        root(f"{AS} set-config idle_lock_minutes 5")
        root(f"{AS} set-config save_minutes 5")


def time_runs_out(machine: Machine) -> None:
    before = machine.mark()
    ssh("/usr/local/bin/kidux-as add tim Tim && /usr/local/bin/kidux-as set-policy tim daily 60")
    machine.shown("choose", before)
    # Leo, Marta, Nora, Tim: End moves to the last picture.
    machine.key("end")
    before = machine.mark()
    machine.key("ret")
    machine.shown("password", before)
    locked = machine.submit("tim password")
    signed_in = wait(lambda: "tim " in ssh("loginctl list-sessions --no-legend").stdout, 30)
    report("a child with an hour a day signs in", signed_in, greeter_log())
    if not signed_in:
        return

    ssh("/usr/local/bin/kidux-as set-time-left tim 0")
    ran_out = wait(lambda: 'lock = "time_up"' in root(
        "cat /home/.kidux/children/tim/usage.toml").stdout, 30, 1)
    report("when an adult sets his time left to none the lock screen comes up at once",
           ran_out and wait(lambda: active_terminal() == "tty8", 20),
           root("cat /home/.kidux/children/tim/usage.toml").stdout)
    machine.shown("locked", locked)
    machine.screenshot("time-is-up")

    before = machine.mark()
    machine.key("ret")                       # no Continue when time is up: Adult has the focus
    if not machine.shown("adult_password", before, 5):
        report("the time-up lock screen offers the adult", False, greeter_log())
        return
    machine.still()
    before = machine.submit(ADULT_PASSWORD)
    machine.shown("adult_choice", before)
    machine.key("ret")                       # fifteen minutes
    report("an adult's time unlocks a session whose time ran out",
           wait(lambda: active_terminal() == "tty7", 15),
           greeter_log() + root("tail -5 /home/.kidux/state/audit.log").stdout)

    # Unlock to save: a few minutes nobody is charged for, then locked again.
    before = machine.mark()
    machine.key("ctrl-alt-esc")
    wait(lambda: active_terminal() == "tty8", 20)
    machine.shown("locked", before)
    lock_screen_adult(machine)
    # 15, 30, 60 minutes, the adult's own number and its button, then Unlock
    # to save work.
    for _ in range(5):
        machine.key("tab")
    machine.key("ret")
    unlocked = wait(lambda: active_terminal() == "tty7", 15)
    used_before = (ssh("/usr/local/bin/kidux-as usage tim").stdout.split() or ["0"])[0]
    relocked = unlocked and wait(lambda: 'lock = "grace"' in root(
        "cat /home/.kidux/children/tim/usage.toml").stdout, 2 * 60 + 30, 10)
    used_after = (ssh("/usr/local/bin/kidux-as usage tim").stdout.split() or ["0"])[0]
    report("unlock to save gives the screen back, charges nothing, and locks again after",
           relocked and used_before == used_after,
           f"unlocked {unlocked}, used {used_before} then {used_after}\n"
           + root("cat /home/.kidux/children/tim/usage.toml").stdout)
    ssh("/usr/local/bin/kidux-as end tim 'tim password'")
    wait(lambda: active_terminal() == "tty7"
         and "greeter" in ssh("loginctl list-sessions --no-legend").stdout, 30)
    ssh("/usr/local/bin/kidux-as delete tim")
    # logind holds the child's user manager for some seconds after their last
    # session; the daemon ends it rather than calling the child signed in.
    report("and the child is removed right after logging out",
           wait(lambda: root("getent passwd tim").returncode != 0, 15),
           root("loginctl list-sessions --no-legend; tail -3 /home/.kidux/state/audit.log").stdout)
    machine.still()
