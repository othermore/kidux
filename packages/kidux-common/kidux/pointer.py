"""The pointer's speed and the touchpad's scroll, the machine's
(phase-4c-plan.md, 4.19).

An adult sets each on the panel's Advanced page, as one of five steps,
slower to faster, -2 to 2. The daemon keeps the steps in the machine's
configuration and writes them where a child's session reads them,
/etc/kidux/input.xml, as the `<libinput>` part of labwc's configuration;
the session puts that part into the rc.xml it gives labwc each time it
starts. labwc 0.8.3 sets libinput's pointer speed, -1 to 1, for every
pointer, and the scroll factor for a touchpad's two fingers.

The middle step is libinput's own pointer speed, and half of labwc's own
scroll factor, which scrolls a page too far for a child's two fingers on a
MacBook's touchpad; the top step is labwc's own.
"""

import xml.etree.ElementTree as ElementTree
from pathlib import Path

#: The steps, slower to faster.
STEPS = (-2, -1, 0, 1, 2)
#: libinput's pointer speed for each step.
POINTER_SPEED = {-2: -0.6, -1: -0.3, 0: 0.0, 1: 0.3, 2: 0.6}
#: labwc's scroll factor for a touchpad, for each step.
SCROLL_FACTOR = {-2: 0.25, -1: 0.35, 0: 0.5, 1: 0.7, 2: 1.0}


def step(value) -> int:
    """A step as the panel sends it; ValueError for anything else."""
    if isinstance(value, bool) or not isinstance(value, int) or value not in STEPS:
        raise ValueError(f"a step is a whole number from {STEPS[0]} to {STEPS[-1]}")
    return value


def libinput(pointer: int, scroll: int) -> str:
    """The `<libinput>` part of labwc's configuration for the two steps.

    A touchpad is a category of its own, which takes nothing from the
    default one, so it is given the pointer's speed too."""
    speed, factor = POINTER_SPEED[step(pointer)], SCROLL_FACTOR[step(scroll)]
    return (
        "<libinput>\n"
        f'  <device category="default"><pointerSpeed>{speed}</pointerSpeed></device>\n'
        f'  <device category="touchpad"><pointerSpeed>{speed}</pointerSpeed>'
        f"<scrollFactor>{factor}</scrollFactor></device>\n"
        "</libinput>\n"
    )


def read(path: Path) -> tuple[float, float]:
    """The pointer's speed and the touchpad's scroll factor in `path`, as
    libinput() writes them; the middle steps' when the file is not there or
    says anything else."""
    default = POINTER_SPEED[0], SCROLL_FACTOR[0]
    try:
        root = ElementTree.parse(path).getroot()
        touchpad = root.find("device[@category='touchpad']")
        speed = float(touchpad.findtext("pointerSpeed"))
        factor = float(touchpad.findtext("scrollFactor"))
    except (OSError, ElementTree.ParseError, AttributeError, TypeError, ValueError):
        return default
    if root.tag != "libinput" or speed not in POINTER_SPEED.values() \
            or factor not in SCROLL_FACTOR.values():
        return default
    return speed, factor


def rc_xml(template: str, path: Path) -> str:
    """labwc's rc.xml, `template`, with the `<libinput>` part `path` says,
    or the middle steps', before its closing tag."""
    speed, factor = read(path)
    pointer = next(s for s, value in POINTER_SPEED.items() if value == speed)
    scroll = next(s for s, value in SCROLL_FACTOR.items() if value == factor)
    head, closing, tail = template.rpartition("</labwc_config>")
    if not closing:
        raise ValueError("not labwc's configuration: no </labwc_config>")
    return f"{head}{libinput(pointer, scroll)}{closing}{tail}"
