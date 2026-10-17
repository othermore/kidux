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
A module's guide there is 300 of the 640 pixels, and the module keeps the
rest (phase-4f-plan.md, step 4.34; D103).
"""

from sessionlib import (
    CHILD,
    CHILD_PASSWORD,
    SEED_SOURCE,
    Machine,
    active_terminal,
    child_session,
    colour_share,
    copy,
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
#: The robin's blue, Kidux's cream; at a scale of 2 the robin's room, left
#: of the guide's pane, 340 of the 640 pixels, and the pane.
BLUE, CREAM = (0x3A, 0x86, 0xFF), (0xFF, 0xF6, 0xE9)
ROBIN_ROOM = (0.02, 0.1, 0.5, 0.85)
PANE = (0.6, 0.3, 0.98, 0.85)


def greeter_at(machine: Machine, scale: str, size: str) -> bool:
    """The machine's scale set, and the sign-in screen started again with
    it: done when it has said the size of its screen and drawn itself."""
    before = journal_count("kidux-greeter", f"screen {size}")
    root(f"{AS} set-config display_scale {scale}")
    drawn = machine.mark()
    root("systemctl restart greetd")
    return (wait(lambda: journal_count("kidux-greeter", f"screen {size}") > before, 30)
            and machine.shown("choose", drawn, 30))


def sign_in(machine: Machine) -> bool:
    """Leo signs in; done when his launcher is up at 640x400."""
    before = journal_count("kidux-launcher", "screen 640x400")
    password = machine.mark()
    machine.key("ret")                           # Leo, the first picture
    machine.shown("password", password)
    machine.submit(CHILD_PASSWORD)
    return (wait(lambda: child_session() is not None, 30)
            and wait(lambda: journal_count("kidux-launcher", "screen 640x400") > before, 30)
            and launcher_shown(machine))


def log_out(machine: Machine) -> None:
    """Log out from the lock screen, past Continue and Adult."""
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


def run(machine: Machine) -> None:
    report("at a scale of 2 the sign-in screen has 640x400 logical pixels",
           greeter_at(machine, "2", "640x400"), greeter_log())
    picture = machine.screenshot("sign-in-scale-2")
    report("too tall at that size, the sign-in screen says so and shows its scrollbar",
           wait(lambda: journal_count("kidux-greeter",
                                      "the choose screen does not fit") > 0, 10)
           and colour_share(picture, SLIDER, RIGHT_EDGE) > 0.02,
           f"{picture}: {colour_share(picture, SLIDER, RIGHT_EDGE):.3f}\n" + greeter_log())

    report("and so has Leo's launcher, under labwc", sign_in(machine), launcher_log())
    picture = machine.screenshot("launcher-scale-2")
    report("and so does Leo's screen, too tall there as well",
           wait(lambda: journal_count("kidux-launcher",
                                      "the child's screen does not fit") > 0, 10)
           and colour_share(picture, SLIDER, RIGHT_EDGE) > 0.02,
           f"{picture}: {colour_share(picture, SLIDER, RIGHT_EDGE):.3f}\n" + launcher_log())

    log_out(machine)

    # The robin, the tests' stand-in module, given a guide of one lesson:
    # opened at this size, the pane beside it is 300 pixels, and the robin
    # fills the 340 left of it.
    robin = "/usr/share/kidux/modules/robin"
    for name, mode in (("module.toml", "0644"), ("icon.svg", "0644"), ("run", "0755")):
        copy(SEED_SOURCE / "modules" / "robin" / name, f"{robin}/{name}", mode=mode)
    root(f"mkdir -p {robin}/content/en && printf '# The robin\\n\\nA lesson.\\n' "
         f"> {robin}/content/en/01-first.md && echo 'guide = true' >> {robin}/module.toml")
    root(f"{AS} enable {CHILD} robin on")
    report("Leo signs in to the robin's tile", sign_in(machine), launcher_log())
    shown = journal_count("kidux-launcher", "guide: robin lessons unfolded")
    machine.key("shift-tab")                     # from Lock back to the tile
    machine.key("ret")
    opened = wait(lambda: journal_count("kidux-launcher",
                                        "guide: robin lessons unfolded") > shown, 30)
    machine.still(4)
    picture = machine.screenshot("guide-scale-2")
    report("the robin opens with its guide beside it, each with its room at 640x400",
           opened and colour_share(picture, BLUE, ROBIN_ROOM) > 0.8
           and colour_share(picture, CREAM, PANE) > 0.5,
           f"{picture}: {colour_share(picture, BLUE, ROBIN_ROOM):.3f} "
           f"{colour_share(picture, CREAM, PANE):.3f}\n" + launcher_log())
    log_out(machine)
    root(f"{AS} enable {CHILD} robin off")
    root(f"rm -rf {robin}")

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
