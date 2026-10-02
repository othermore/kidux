"""GRUB's recovery password, the unattended boot, and the boot splash."""

import time

from sessionlib import (
    Machine,
    boot_id,
    catch_the_splash,
    colour_share,
    report,
    root,
    up,
    wait,
)

#: GRUB's text screen.
BLACK = (0, 0, 0)
#: The firmware's setup screen (OVMF), grey, in the middle of the screen.
FIRMWARE_GREY = (152, 152, 152)
FIRMWARE_BOX = (0.2, 0.15, 0.8, 0.7)


def esc_into_grub(machine: Machine):
    """Esc about once a second through GRUB's hidden second, then 'e':
    the pictures of GRUB's shell and editor. Faster, an Esc lands in the
    firmware's own second and opens its setup screen instead; under a
    loaded machine that second moves, and it can happen at that pace too,
    so a run that ends in the firmware's screen resets the machine and
    tries again."""
    for _ in range(3):
        end = time.monotonic() + 45
        while time.monotonic() < end:
            machine.key("esc")
            time.sleep(0.9)
        shell = machine.screenshot("grub-shell")
        if colour_share(shell, FIRMWARE_GREY, FIRMWARE_BOX) < 0.5:
            machine.key("e")
            time.sleep(1.5)
            return shell, machine.screenshot("grub-edit")
        machine.monitor("system_reset")
    return shell, shell


def run(machine: Machine) -> None:
    config = root("cat /boot/grub/grub.cfg").stdout
    report("GRUB has a recovery password", 'set superusers="kidux"' in config
           and "password_pbkdf2 kidux grub.pbkdf2." in config)
    report("the Kidux entry boots without it", "menuentry 'Kidux' --unrestricted --id kidux" in config)
    debian_entries = [line for line in config.splitlines()
                      if line.lstrip().startswith("menuentry") and "Kidux" not in line]
    report("every other entry needs it",
           debian_entries and all("--unrestricted" not in line for line in debian_entries),
           "\n".join(debian_entries))

    # Try it: reboot and press Esc through GRUB's hidden second. With the menu
    # up, Esc asks for the GRUB shell, which is protected too; 'e' asks to edit
    # the entry. Both should stop at "Enter username:", white text on black.
    before = boot_id()
    root("systemctl reboot", timeout=20)
    shell, edit = esc_into_grub(machine)
    report("GRUB's shell and editor ask for the recovery password",
           colour_share(shell, BLACK) > 0.9 and colour_share(edit, BLACK) > 0.9,
           f"see {shell} and {edit}")

    # Reset without touching a key: the machine has to come up on its own.
    machine.monitor("system_reset")
    splash = catch_the_splash(machine)
    report("and with nobody at the keyboard the machine boots straight through",
           wait(lambda: up() and boot_id() not in ("", before), 240, 3))
    report("showing Kidux's logo while it starts (look at the picture)", splash is not None,
           root("plymouth-set-default-theme; journalctl -b -o cat -u plymouth-start | tail -5").stdout)
