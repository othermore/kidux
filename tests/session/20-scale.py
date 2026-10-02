"""One display scale for every screen (phase-3-plan.md, step 3.12; D49).

The machine's scale set through the daemon, as the panel's System page sets
it, reaches the sign-in screen under cage and a child's launcher under labwc
alike: each logs the size of its screen in logical pixels once it is up,
which on this machine's 1280x800 is 640x400 at a scale of 2 and 1024x640 at
1.25. Automatic, what a machine has until an adult chooses, is 1 here, the
largest quarter at which 1280x800 still fits. The screens scale 2 leaves too
small overflow and scroll; test 13 has already checked they fit at 1. A
screen that scrolls shows it (D63): the sign-in screen and the child's,
both too tall at 640x400, say so in their logs and draw their scrollbar.
"""

from sessionlib import (
    CHILD_PASSWORD,
    Machine,
    active_terminal,
    child_session,
    colour_share,
    greeter_log,
    journal_count,
    launcher_log,
    launcher_shown,
    report,
    root,
    wait,
)

AS = "runuser -u debian -- /usr/local/bin/kidux-as"
#: A scrollbar's slider (kidux.scroll), and the strip along the right edge of
#: the screen where a page's scrollbar is drawn, above the launcher's bar.
SLIDER = (0x9c, 0x87, 0x78)
RIGHT_EDGE = (0.88, 0.05, 0.99, 0.85)


def greeter_at(machine: Machine, scale: str, size: str) -> bool:
    """The machine's scale set, and the sign-in screen started again with
    it: done when it has said the size of its screen and drawn itself."""
    before = journal_count("kidux-greeter", f"screen {size}")
    root(f"{AS} set-config display_scale {scale}")
    drawn = machine.mark()
    root("systemctl restart greetd")
    return (wait(lambda: journal_count("kidux-greeter", f"screen {size}") > before, 30)
            and machine.shown("choose", drawn, 30))


def run(machine: Machine) -> None:
    report("at a scale of 2 the sign-in screen has 640x400 logical pixels",
           greeter_at(machine, "2", "640x400"), greeter_log())
    picture = machine.screenshot("sign-in-scale-2")
    report("too tall at that size, the sign-in screen says so and shows its scrollbar",
           wait(lambda: journal_count("kidux-greeter",
                                      "the choose screen does not fit") > 0, 10)
           and colour_share(picture, SLIDER, RIGHT_EDGE) > 0.02,
           f"{picture}: {colour_share(picture, SLIDER, RIGHT_EDGE):.3f}\n" + greeter_log())

    before = journal_count("kidux-launcher", "screen 640x400")
    password = machine.mark()
    machine.key("ret")                           # Leo, the first picture
    machine.shown("password", password)
    machine.submit(CHILD_PASSWORD)
    report("and so has Leo's launcher, under labwc",
           wait(lambda: child_session() is not None, 30)
           and wait(lambda: journal_count("kidux-launcher", "screen 640x400") > before, 30)
           and launcher_shown(machine), launcher_log())
    picture = machine.screenshot("launcher-scale-2")
    report("and so does Leo's screen, too tall there as well",
           wait(lambda: journal_count("kidux-launcher",
                                      "the child's screen does not fit") > 0, 10)
           and colour_share(picture, SLIDER, RIGHT_EDGE) > 0.02,
           f"{picture}: {colour_share(picture, SLIDER, RIGHT_EDGE):.3f}\n" + launcher_log())

    # Log out from the lock screen, past Continue and Adult.
    locked = machine.mark()
    machine.monitor("system_powerdown")
    wait(lambda: active_terminal() == "tty8", 20)
    machine.shown("locked", locked)
    machine.key("tab")
    machine.key("tab")
    asked = machine.mark()
    machine.key("ret")
    machine.shown("child_password", asked)
    choose = machine.submit(CHILD_PASSWORD)
    wait(lambda: child_session() is None, 30)
    machine.shown("choose", choose, 30)

    # The same start five times: a race between the compositor bringing
    # its output up and the scale being set shows in one start of many
    # (step 3.24), and none of them may stay at 1.
    sizes = [greeter_at(machine, "2", "640x400") for _ in range(5)]
    report("the sign-in screen started five times at scale 2 is 640x400 every time",
           all(sizes), f"{sizes}\n" + root("journalctl -b -o cat -t kidux-session").stdout[-800:])

    report("a scale in quarters is taken as it is: 1.25 is 1024x640",
           greeter_at(machine, "1.25", "1024x640"), greeter_log())
    report("and automatic, which is 1 on a 1280x800 screen, is 1280x800 again",
           greeter_at(machine, "0", "1280x800"), greeter_log())
