#!/usr/bin/python3
"""keyboard.py <step>...: a keyboard of its own on the test machine, through
uinput, which the compositor takes for a real one (sessionlib.keyboard).

QEMU's `sendkey` presses its keys together and lets them all go when the
next command comes, so it cannot hold Alt down while Tab is pressed twice;
this can. A step is `+key` to press a key, `-key` to let it go, `key` to
press and let go, or a number of seconds to wait. Runs as root on the test
machine.
"""

import fcntl
import os
import struct
import sys
import time

#: The keys it has, by their Linux key codes (linux/input-event-codes.h).
KEYS = {"alt": 56, "tab": 15, "shift": 42, "esc": 1, "super": 125, "f4": 62}

EV_SYN, EV_KEY = 0, 1
UI_SET_EVBIT, UI_SET_KEYBIT = 0x40045564, 0x40045565
UI_DEV_CREATE, UI_DEV_DESTROY = 0x5501, 0x5502
#: How long the compositor takes to see a new keyboard, in seconds.
SETTLE = 1.5


def main(steps: list[str]) -> None:
    device = os.open("/dev/uinput", os.O_WRONLY | os.O_NONBLOCK)
    fcntl.ioctl(device, UI_SET_EVBIT, EV_KEY)
    for code in KEYS.values():
        fcntl.ioctl(device, UI_SET_KEYBIT, code)
    # struct uinput_user_dev: the name, the bus, vendor, product and version,
    # no force feedback, and the four tables of absolute axes, empty.
    os.write(device, struct.pack("80sHHHHi", b"kidux-tests keyboard", 3, 1, 1, 1, 0)
             + bytes(4 * 64 * 4))
    fcntl.ioctl(device, UI_DEV_CREATE)
    time.sleep(SETTLE)

    def key(code: int, down: bool) -> None:
        for kind, number, value in ((EV_KEY, code, int(down)), (EV_SYN, 0, 0)):
            os.write(device, struct.pack("llHHi", 0, 0, kind, number, value))

    for step in steps:
        if step[0] in "+-":
            key(KEYS[step[1:]], step[0] == "+")
        elif step in KEYS:
            key(KEYS[step], True)
            time.sleep(0.05)
            key(KEYS[step], False)
        else:
            time.sleep(float(step))
    time.sleep(0.3)
    fcntl.ioctl(device, UI_DEV_DESTROY)


if __name__ == "__main__":
    main(sys.argv[1:])
