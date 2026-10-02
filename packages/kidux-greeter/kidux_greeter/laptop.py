"""A laptop's keys on the trusted screens (D61, docs/dev/keys.md).

Under cage no configuration binds a key: every key reaches the screen, and
the sign-in and lock screens answer a laptop's own keys for the screen's
brightness, the keyboard's light and the sound themselves, as `kidux-keys`
does in a child's session, through `kidux.hardware.key`. No GTK here, so
that the table is tested as it is.

The keys are matched by their keysym, the number xkb gives them, and not
by name: GTK 4 names them without xkb's `XF86` prefix (`MonBrightnessUp`
for xkb's `XF86MonBrightnessUp`), and a table of xkb's names matched none.
"""

import logging

from kidux import hardware as kidux_hardware

log = logging.getLogger("kidux.greeter")

#: Each key's xkb keysym, its xkb name, as keys.md and labwc's rc.xml write
#: it, and what `kidux.hardware.key` does for it.
KEYSYMS = {
    0x1008FF02: ("XF86MonBrightnessUp", ("brightness", "up")),
    0x1008FF03: ("XF86MonBrightnessDown", ("brightness", "down")),
    0x1008FF05: ("XF86KbdBrightnessUp", ("keyboard", "up")),
    0x1008FF06: ("XF86KbdBrightnessDown", ("keyboard", "down")),
    0x1008FF13: ("XF86AudioRaiseVolume", ("volume", "up")),
    0x1008FF11: ("XF86AudioLowerVolume", ("volume", "down")),
    0x1008FF12: ("XF86AudioMute", ("volume", "mute")),
}


def press(keyval: int, hardware=kidux_hardware) -> bool:
    """Do what a laptop's key does; True when `keyval` is one of them, so
    that the screen takes no further notice of it."""
    entry = KEYSYMS.get(keyval)
    if entry is None:
        return False
    _name, action = entry
    log.info("laptop key: %s %s", *action)
    hardware.key(*action)
    return True
