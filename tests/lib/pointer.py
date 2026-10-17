#!/usr/bin/python3
"""pointer.py <step>...: a pointer of its own on the test machine, through
uinput, that goes exactly where it is told (sessionlib.pointer).

QEMU's mouse moves by steps the compositor accelerates, so a test cannot
point at a button by them. This is an absolute pointer, as a tablet is,
which libinput maps onto the screen: a step `x,y` puts it at that place,
each a fraction of the screen's width and height; `click` presses and lets
go its left button where it is; a number waits that many seconds. Runs as
root on the test machine.
"""

import fcntl
import os
import struct
import sys
import time

EV_SYN, EV_KEY, EV_ABS = 0, 1, 3
ABS_X, ABS_Y, BTN_LEFT = 0, 1, 0x110
UI_SET_EVBIT, UI_SET_KEYBIT, UI_SET_ABSBIT = 0x40045564, 0x40045565, 0x40045567
UI_DEV_CREATE, UI_DEV_DESTROY = 0x5501, 0x5502
#: The axes' range: a fraction of the screen is a fraction of this.
RANGE = 32767
#: How long the compositor takes to see a new device, in seconds.
SETTLE = 1.5


def main(steps: list[str]) -> None:
    device = os.open("/dev/uinput", os.O_WRONLY | os.O_NONBLOCK)
    fcntl.ioctl(device, UI_SET_EVBIT, EV_KEY)
    fcntl.ioctl(device, UI_SET_KEYBIT, BTN_LEFT)
    fcntl.ioctl(device, UI_SET_EVBIT, EV_ABS)
    fcntl.ioctl(device, UI_SET_ABSBIT, ABS_X)
    fcntl.ioctl(device, UI_SET_ABSBIT, ABS_Y)
    absmax = [0] * 64
    absmax[ABS_X] = absmax[ABS_Y] = RANGE
    setup = struct.pack("80sHHHHi", b"kidux-tests pointer", 3, 1, 3, 1, 0)
    setup += struct.pack("64i", *absmax) + bytes(4 * 64 * 3)
    os.write(device, setup)
    fcntl.ioctl(device, UI_DEV_CREATE)
    time.sleep(SETTLE)

    def emit(kind, code, value):
        os.write(device, struct.pack("llHHi", 0, 0, kind, code, value))

    try:
        for step in steps:
            if step == "click":
                emit(EV_KEY, BTN_LEFT, 1)
                emit(EV_SYN, 0, 0)
                time.sleep(0.08)
                emit(EV_KEY, BTN_LEFT, 0)
                emit(EV_SYN, 0, 0)
            elif "," in step:
                x, y = (float(part) for part in step.split(","))
                emit(EV_ABS, ABS_X, round(x * RANGE))
                emit(EV_ABS, ABS_Y, round(y * RANGE))
                emit(EV_SYN, 0, 0)
            else:
                time.sleep(float(step))
            time.sleep(0.1)
        time.sleep(0.3)
    finally:
        fcntl.ioctl(device, UI_DEV_DESTROY)
        os.close(device)


if __name__ == "__main__":
    main(sys.argv[1:])
