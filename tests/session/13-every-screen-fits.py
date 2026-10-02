"""Every screen the run has shown so far fits the screen whole.

The machine has not restarted since it booted into Kidux, so the greeter's
log for this boot covers every screen: the wizard, sign-in, the lock screen
and the panel. The greeter logs a screen that has to scroll (greeter.md,
section 1), and the test machine's screen is 1280x800, the size every screen
is meant to fit.
"""

from sessionlib import Machine, report, root



#: Run in every language (tests/lib/session-vm.py): a longer word is what
#: makes a screen not fit.
EVERY_LANGUAGE = True

def run(machine: Machine) -> None:
    too_tall = root("journalctl -b --no-pager -o cat -t kidux-greeter "
                    "| grep 'does not fit' | sort -u").stdout.strip()
    report("every screen shown so far fits 1280x800 whole", not too_tall, too_tall)
    # A screen that fails to draw becomes the emergency screen, and the
    # greeter says so in its log (`View.show` in view.py).
    undrawn = root("journalctl -b --no-pager -o cat -t kidux-greeter "
                   "| grep 'could not draw' | sort -u").stdout.strip()
    report("and every screen shown so far was drawn", not undrawn, undrawn)
