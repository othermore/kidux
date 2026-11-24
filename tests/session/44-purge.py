"""Purging kidux-session gives the machine back as Debian. Last: it undoes Kidux."""

from sessionlib import (
    Machine,
    active_terminal,
    reboot,
    report,
    root,
    wait,
)


def run(machine: Machine) -> None:
    result = root("DEBIAN_FRONTEND=noninteractive apt-get purge -y kidux-session", timeout=300)
    report("kidux-session can be purged", result.returncode == 0, result.stderr[-600:])
    report("and the machine comes back up", reboot(machine))
    machine.key("ctrl-alt-f2")
    report("as an ordinary Debian machine: Ctrl+Alt+F2 reaches a login prompt",
           wait(lambda: active_terminal() == "tty2", 10), active_terminal())
    machine.screenshot("after-purge")
    report("with GRUB's own menu back", 'superusers' not in root("cat /boot/grub/grub.cfg").stdout)
