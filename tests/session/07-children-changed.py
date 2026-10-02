"""A child added while the sign-in screen is up appears on it at once."""

from sessionlib import (
    Machine,
    greeter_log,
    report,
    ssh,
)


def run(machine: Machine) -> None:
    before = machine.mark()
    ssh("/usr/local/bin/kidux-as add zoe Zoe")
    report("a child added while the sign-in screen is up appears on it at once",
           machine.shown("choose", before), greeter_log())
    machine.screenshot("child-added")
    before = machine.mark()
    ssh("/usr/local/bin/kidux-as delete zoe")
    machine.shown("choose", before)
