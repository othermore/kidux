"""The sign-in screen without its daemon, and a minute without a touch."""

from sessionlib import (
    CHILD_PASSWORD,
    Machine,
    greeter_log,
    report,
    root,
)


def run(machine: Machine) -> None:
    root("systemctl mask --runtime kidux-daemon && systemctl stop kidux-daemon")
    before = machine.mark()
    machine.key("ret")
    machine.shown("password", before)
    waited = machine.shown("waiting", machine.submit(CHILD_PASSWORD), 30)
    machine.screenshot("waiting")
    report("with the daemon away, signing in waits instead of failing", waited, greeter_log())
    before = machine.mark()
    root("systemctl unmask --runtime kidux-daemon && systemctl start kidux-daemon")
    report("and the pictures come back by themselves when it returns",
           machine.shown("choose", before, 30), greeter_log())

    before = machine.mark()
    machine.key("ret")                       # Leo's password screen, then nothing
    report("a minute without a touch goes back to everyone's pictures",
           machine.shown("choose", before, 90), greeter_log())
