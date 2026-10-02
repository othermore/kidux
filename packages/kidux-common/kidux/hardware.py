"""What the machine has, as the kernel tells it, and how its keys are called (D61).

The launcher shows a battery, the screen's brightness, the keyboard's light
and the sound's volume when the machine has them, and the keys a laptop
gives for those (XF86 keysyms, the same on a MacBook and on a PC) adjust
them through `key`: `kidux-keys` under labwc, the trusted screens themselves
under cage. Every reading here comes from `/sys`, `/proc` or
one small program, and every function takes the root it reads under, so
that its test is a directory of files.

A Mac keyboard's function keys are media keys first: F4 is Alt+(fn)F4
there, as `hid_apple`'s `fnmode` says. What a screen writes for a key comes
from `function_key` and `super_key`, never from a literal.
"""

import fcntl
import logging
import os
import struct
import subprocess
from dataclasses import dataclass
from pathlib import Path

log = logging.getLogger("kidux.hardware")

SYS = Path("/sys")

#: The percentage a key changes a level by, and the least a screen is left
#: at: a child holding the key down must not black the screen out.
STEP = 10
SCREEN_FLOOR = 5


@dataclass(frozen=True)
class Level:
    """Something with a brightness and a maximum: a backlight, a light."""
    name: str
    value: int
    maximum: int

    @property
    def percent(self) -> int:
        return round(100 * self.value / self.maximum) if self.maximum > 0 else 0


@dataclass(frozen=True)
class Battery:
    capacity: int
    status: str
    plugged: bool

    @property
    def charging(self) -> bool:
        return self.status in ("Charging", "Full") or self.plugged


def _read(path: Path) -> str:
    try:
        return path.read_text().strip()
    except OSError:
        return ""


def _int(path: Path, default: int = 0) -> int:
    try:
        return int(_read(path))
    except ValueError:
        return default


# --- power ------------------------------------------------------------------

def battery(root: Path = SYS) -> Battery | None:
    """The machine's own battery, the first the kernel lists that is not a
    peripheral's (a wireless mouse has a `scope` of `Device`); None on a
    desktop."""
    supplies = sorted((root / "class" / "power_supply").glob("*"))
    plugged = any(_read(s / "type") == "Mains" and _int(s / "online") == 1 for s in supplies)
    for supply in supplies:
        if _read(supply / "type") == "Battery" and _read(supply / "scope") != "Device" \
                and (supply / "capacity").exists():
            return Battery(capacity=_int(supply / "capacity"), status=_read(supply / "status"),
                           plugged=plugged)
    return None


# --- lights -----------------------------------------------------------------

#: The kinds of backlight the kernel lists, the one to use first: `raw` is
#: the panel's own, `firmware` the BIOS's way to it.
BACKLIGHT_TYPES = ("raw", "platform", "firmware")


def backlight(root: Path = SYS) -> Level | None:
    """The screen's backlight, when it can be set; None on a machine without
    one (a desktop, or a virtual machine)."""
    found = sorted((root / "class" / "backlight").glob("*"))
    if not found:
        return None
    found.sort(key=lambda d: (BACKLIGHT_TYPES.index(_read(d / "type"))
                              if _read(d / "type") in BACKLIGHT_TYPES else len(BACKLIGHT_TYPES),
                              d.name))
    device = found[0]
    return Level(device.name, _int(device / "brightness"), _int(device / "max_brightness"))


def keyboard_backlight(root: Path = SYS) -> Level | None:
    """The keyboard's light, a LED called `kbd_backlight`; None without one."""
    for led in sorted((root / "class" / "leds").glob("*kbd_backlight*")):
        return Level(led.name, _int(led / "brightness"), _int(led / "max_brightness"))
    return None


def step(percent: int, up: bool, floor: int = 0) -> int:
    """The level a key takes `percent` to: `STEP` more or less, on the
    tens, between `floor` and 100."""
    target = (percent // STEP + 1) * STEP if up else ((percent + STEP - 1) // STEP - 1) * STEP
    return max(floor, min(100, target))


def set_level(level: Level, percent: int) -> bool:
    """Set a backlight or a light to `percent`, through `brightnessctl`, which
    writes `/sys` itself: the user needs group video, which a child and
    `_greetd` are in, and which kidux-session gives a keyboard's light."""
    return _run(["brightnessctl", "--quiet", "--device", level.name, "set", f"{percent}%"])


# --- sound ------------------------------------------------------------------

SINK = "@DEFAULT_AUDIO_SINK@"


def parse_volume(text: str) -> tuple[int, bool] | None:
    """`wpctl get-volume`'s answer, `Volume: 0.45 [MUTED]`, as (45, True)."""
    words = text.split()
    if len(words) < 2 or words[0] != "Volume:":
        return None
    try:
        return round(float(words[1]) * 100), "[MUTED]" in words
    except ValueError:
        return None


def real_output(inspection: str) -> bool:
    """Whether `wpctl inspect`'s default sink is a real output: PipeWire
    keeps a `Dummy Output` (`support.null-audio-sink`) when the machine has
    none, which takes a volume and forgets it."""
    return bool(inspection.strip()) and "support.null-audio-sink" not in inspection


def volume() -> tuple[int, bool] | None:
    """The default output's volume and whether it is muted; None when the
    session has no sound to speak of: no PipeWire, or no real output."""
    if not real_output(_output(["wpctl", "inspect", SINK])):
        return None
    return parse_volume(_output(["wpctl", "get-volume", SINK]))


def set_volume(percent: int) -> bool:
    return _run(["wpctl", "set-volume", "--limit", "1.0", SINK, f"{max(0, min(100, percent))}%"])


def set_muted(muted: bool) -> bool:
    return _run(["wpctl", "set-mute", SINK, "1" if muted else "0"])


# --- the lid ----------------------------------------------------------------

EV_SW, SW_LID = 0x05, 0x00
#: struct input_event on a 64-bit machine: seconds, microseconds, type,
#: code, value.
EVENT = struct.Struct("llHHi")


def lid_devices(root: Path = SYS) -> list[str]:
    """The input devices with a lid switch, as `/dev/input/event*` paths:
    the kernel lists a switch's capabilities in `capabilities/sw`, bit 0 the
    lid. Empty on a machine without a lid."""
    found = []
    for event in sorted((root / "class" / "input").glob("event*")):
        words = _read(event / "device" / "capabilities" / "sw").split()
        try:
            if words and int(words[-1], 16) & (1 << SW_LID):
                found.append(f"/dev/input/{event.name}")
        except ValueError:
            continue
    return found


def lid_closed(fd: int) -> bool:
    """Whether the lid is closed now, asked of an open lid device (EVIOCGSW)."""
    length = 8
    request = (2 << 30) | (length << 16) | (ord("E") << 8) | 0x1B
    answer = fcntl.ioctl(fd, request, bytes(length))
    return bool(answer[0] & (1 << SW_LID))


def lid_events(data: bytes) -> list[bool]:
    """The lid changes in what was read from the device: True for each
    close, False for each opening, in order."""
    changes = []
    for offset in range(0, len(data) - EVENT.size + 1, EVENT.size):
        _s, _us, kind, code, value = EVENT.unpack_from(data, offset)
        if kind == EV_SW and code == SW_LID:
            changes.append(bool(value))
    return changes


# --- the keyboard -----------------------------------------------------------

def is_mac(root: Path = SYS) -> bool:
    return _read(root / "class" / "dmi" / "id" / "sys_vendor").startswith("Apple")


def function_keys_need_fn(root: Path = SYS) -> bool:
    """Whether F1 to F12 want the fn key held: on a Mac, where the function
    keys are media keys first unless `hid_apple`'s `fnmode` is 2 (function
    keys first) or 0 (fn does nothing, function keys plain)."""
    if not is_mac(root):
        return False
    mode = _read(root / "module" / "hid_apple" / "parameters" / "fnmode")
    return mode not in ("0", "2")


def function_key(name: str, root: Path = SYS) -> str:
    """How a screen writes F4: `(fn)F4` where fn is needed, `F4` otherwise."""
    return f"(fn){name}" if function_keys_need_fn(root) else name


def super_key(root: Path = SYS) -> str:
    """How a screen writes the key that goes home: the command key on a Mac,
    the Windows key elsewhere."""
    return "⌘" if is_mac(root) else "Win"


def has_lid(root: Path = SYS) -> bool:
    return bool(lid_devices(root))


#: How a compositor names a laptop's own panel.
PANEL_PREFIXES = ("eDP", "LVDS", "DSI")


def panel_outputs(names: list[str]) -> list[str]:
    """The laptop's own panel among a compositor's outputs: the internal
    ones, or the only output when there is one; an external screen is
    never among them."""
    internal = [name for name in names if name.startswith(PANEL_PREFIXES)]
    return internal or (names if len(names) == 1 else [])


def wlr_randr_outputs(listing: str) -> list[str]:
    """The outputs `wlr-randr` lists: each name starts a line, its details
    are indented under it."""
    return [line.split()[0] for line in listing.splitlines()
            if line.strip() and not line[0].isspace()]


def wlopm_outputs(listing: str) -> list[str]:
    """The outputs `wlopm` lists, one "name on|off" a line."""
    return [line.split()[0] for line in listing.splitlines() if line.split()]


# --- a laptop's keys --------------------------------------------------------

def levels_file(environ=os.environ) -> Path | None:
    """The file a key touches when it has changed a level, so that a corner
    showing the levels reads them again at once: the session's own, under
    its runtime directory; None without one."""
    runtime = environ.get("XDG_RUNTIME_DIR", "")
    return Path(runtime) / "kidux" / "levels" if runtime else None


def note_levels_changed(environ=os.environ) -> None:
    path = levels_file(environ)
    if path is None:
        return
    try:
        path.parent.mkdir(exist_ok=True)
        path.touch()
    except OSError as error:
        log.debug("the levels' file cannot be touched: %s", error)


#: What each key does, as `key` takes it: what, then how.
KEYS = ("brightness up", "brightness down", "keyboard up", "keyboard down",
        "volume up", "volume down", "volume mute")


def key(what: str, how: str, root: Path = SYS) -> bool:
    """A laptop's key: the screen's backlight, the keyboard's light or the
    sound a step up or down, or the sound muted and back. The screen never
    goes under `SCREEN_FLOOR`; a step while muted unmutes first. Nothing on
    a machine without the thing. False for a key that is not one. A level
    changed touches `levels_file`, which a corner watches."""
    if f"{what} {how}" not in KEYS:
        return False
    changed = False
    if what == "brightness":
        level = backlight(root)
        if level is not None:
            changed = set_level(level, step(level.percent, how == "up", SCREEN_FLOOR))
    elif what == "keyboard":
        level = keyboard_backlight(root)
        if level is not None:
            changed = set_level(level, step(level.percent, how == "up"))
    else:
        sound = volume()
        if sound is not None:
            percent, muted = sound
            if how == "mute":
                changed = set_muted(not muted)
            else:
                if muted:
                    set_muted(False)
                changed = set_volume(step(percent, how == "up"))
    if changed:
        note_levels_changed()
    return True


# --- running things ---------------------------------------------------------

def _run(argv: list[str]) -> bool:
    """A program that changes something; its failure is logged with what it
    said, one line, since nothing on screen says it."""
    try:
        done = subprocess.run(argv, capture_output=True, text=True, timeout=5)
    except (OSError, subprocess.TimeoutExpired) as error:
        log.warning("%s did not run: %s", argv[0], error)
        return False
    if done.returncode != 0:
        said = " ".join((done.stderr or done.stdout).split()) or f"status {done.returncode}"
        log.warning("%s: %s", argv[0], said)
        return False
    return True


def _output(argv: list[str]) -> str:
    try:
        done = subprocess.run(argv, capture_output=True, text=True, timeout=5)
    except (OSError, subprocess.TimeoutExpired):
        return ""
    return done.stdout if done.returncode == 0 else ""


def summary(root: Path = SYS) -> str:
    """One line for the log: what this machine has."""
    cell = battery(root)
    light, keys = backlight(root), keyboard_backlight(root)
    return (f"battery={'none' if cell is None else f'{cell.capacity}%'} "
            f"backlight={'none' if light is None else light.name} "
            f"keyboard={'none' if keys is None else keys.name} "
            f"lid={'yes' if has_lid(root) else 'no'} "
            f"mac={'yes' if is_mac(root) else 'no'} "
            f"fn={'yes' if function_keys_need_fn(root) else 'no'}")


def main(argv: list[str]) -> int:
    print(summary(Path(argv[1]) if len(argv) > 1 else SYS))
    return 0


if __name__ == "__main__":
    import sys

    sys.exit(main(sys.argv))
