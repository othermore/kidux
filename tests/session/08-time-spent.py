"""A child whose day is spent is told so, and an adult gives them more. A
child on a day of the week not ticked for them is told that (D54), and the
day ticked again on the panel, by keyboard, lets them in."""

import datetime
import time

from sessionlib import (
    ADULT_PASSWORD,
    CHILD,
    CHILD_PASSWORD,
    Machine,
    active_terminal,
    open_panel,
    child_session,
    greeter_log,
    report,
    root,
    shlex_quote,
    ssh,
    wait,
)


def run(machine: Machine) -> None:
    ssh(f"/usr/local/bin/kidux-as set-policy {CHILD} daily 0")
    machine.still()
    before = machine.mark()
    machine.key("ret")
    machine.shown("password", before)
    before = machine.submit(CHILD_PASSWORD)
    machine.shown("blocked", before)
    machine.screenshot("time-spent")
    report("a child with no time left is not signed in", child_session() is None, greeter_log())

    # "An adult can give me more time" has the focus.
    before = machine.mark()
    machine.key("ret")
    machine.shown("needs_adult", before)
    machine.screenshot("adult-gives-time")
    # The adult password, then Enter moves to the first choice, 15 minutes.
    machine.type(ADULT_PASSWORD + "\n")
    time.sleep(1)
    machine.key("ret")
    signed_in = wait(lambda: child_session() is not None, 30)
    report("an adult gives time on the sign-in screen and the session starts", signed_in,
           greeter_log() + root(f"cat /home/.kidux/children/{CHILD}/access.toml").stdout)
    _, left = (ssh(f"/usr/local/bin/kidux-as usage {CHILD}").stdout.split() + ["", ""])[:2]
    report("with the fifteen minutes the adult gave", left.isdigit() and 0 < int(left) <= 15 * 60,
           left)
    # Back to everyone's pictures, drawn and still, before a key is pressed.
    choose = machine.mark()
    ssh(f"/usr/local/bin/kidux-as end {CHILD} {shlex_quote(CHILD_PASSWORD)}")
    ssh(f"/usr/local/bin/kidux-as set-policy {CHILD} unlimited 0")
    wait(lambda: active_terminal() == "tty7"
         and "greeter" in ssh("loginctl list-sessions --no-legend").stdout, 30)
    machine.shown("choose", choose, 30)

    # Every day but today, from the command line, as the panel's boxes do;
    # today is the accounting day the daemon has for Leo.
    ssh(f"/usr/local/bin/kidux-as check-access {CHILD}")
    last_day = root(f"grep ^last_day /home/.kidux/children/{CHILD}/usage.toml").stdout
    today = datetime.date.fromisoformat(last_day.split('"')[1]).weekday()
    days = "".join("0" if day == today else "1" for day in range(7))
    ssh(f"/usr/local/bin/kidux-as set-policy {CHILD} daily 60 {days}")
    # What the adult gave above is for today, and would still let him in.
    ssh(f"/usr/local/bin/kidux-as set-time-left {CHILD} 0")
    machine.still()
    before = machine.mark()
    machine.key("ret")
    machine.shown("password", before)
    before = machine.submit(CHILD_PASSWORD)
    machine.shown("blocked", before)
    machine.screenshot("day-off")
    report("on a day not ticked for them a child is not signed in, and is told so",
           child_session() is None and "day_off" in ssh(
               f"/usr/local/bin/kidux-as check-access {CHILD}").stdout, greeter_log())
    before = machine.mark()
    machine.key("esc")
    machine.shown("choose", before)

    # On his page the focus is in the name: past the picture, the language,
    # the two passwords, the mode and the minutes, to the days, Monday
    # first; Space ticks today's; back to the name, and Enter saves.
    report("the panel opens, on Leo's page", open_panel(machine), greeter_log())
    forward = 6 + today + 1
    for _ in range(forward):
        machine.key("tab")
    machine.key("spc")
    for _ in range(forward):
        machine.key("shift-tab")
    saved = machine.mark()
    machine.key("ret")
    machine.shown("panel_children", saved, 10)
    access = root(f"cat /home/.kidux/children/{CHILD}/access.toml").stdout
    report("today's box ticked by keyboard and saved gives the day back",
           "false" not in access
           and "allowed" in ssh(f"/usr/local/bin/kidux-as check-access {CHILD}").stdout, access)
    closed = machine.mark()
    machine.key("esc")
    machine.shown("choose", closed)

    before = machine.mark()
    machine.key("ret")
    machine.shown("password", before)
    machine.submit(CHILD_PASSWORD)
    report("and the child signs in", wait(lambda: child_session() is not None, 30),
           greeter_log())
    # Back to everyone's pictures, drawn and still, before a key is pressed.
    choose = machine.mark()
    ssh(f"/usr/local/bin/kidux-as end {CHILD} {shlex_quote(CHILD_PASSWORD)}")
    ssh(f"/usr/local/bin/kidux-as set-policy {CHILD} unlimited 0")
    wait(lambda: active_terminal() == "tty7"
         and "greeter" in ssh("loginctl list-sessions --no-legend").stdout, 30)
    machine.shown("choose", choose, 30)
