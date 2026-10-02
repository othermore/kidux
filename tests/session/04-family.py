"""After the wizard: the rest of the children the checks below need."""

import time

from sessionlib import (
    CHILD,
    Machine,
    NIGHT,
    colour_share,
    greeter_log,
    report,
    ssh,
    up,
)



#: Run in every language (tests/lib/session-vm.py): it sets the machine up,
#: or checks what a language can change.
EVERY_LANGUAGE = True

def run(machine: Machine) -> bool:
    before = machine.mark()
    result = ssh(f"/usr/local/bin/kidux-as setup && /usr/local/bin/kidux-as set-policy {CHILD} unlimited 0")
    added = report("two more children are added from the command line", result.returncode == 0,
                   result.stderr)
    # Each child added redraws the screen; the last redraw is a moment behind
    # the first.
    machine.shown("choose", before)
    time.sleep(1)
    sign_in = machine.screenshot("sign-in")
    report("the sign-in screen welcomes with Kidux's logo, large, above the children",
           colour_share(sign_in, NIGHT, (0.4, 0.2, 0.6, 0.4)) > 0.01, str(sign_in))

    # The power button with nobody signed in asks before anything (D16).
    before = machine.mark()
    machine.monitor("system_powerdown")
    asked = machine.shown("power", before)
    machine.screenshot("turn-off")
    report("the power button with nobody signed in asks before turning off",
           asked and up(), greeter_log())
    before = machine.mark()
    machine.key("ret")                       # Cancel has the focus
    machine.shown("choose", before)
    return added
