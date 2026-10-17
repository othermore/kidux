"""Modules on the panel and on the launcher (phase-3-plan.md, step 3.1).

The tests' stand-in module is copied into place over SSH, switched on for
Leo from the panel by keyboard, shown as a tile on Leo's launcher, switched
off again from the panel over the lock screen while the launcher stays open,
and removed at the end. Sound is checked in Leo's session while it is open.
At the end the Modules page is made taller than the screen with more
stand-ins: Remove on the last one asks in its row and in view, Cancel leaves
the page where it was, and the canary, a folder no package put there, is
removed from the panel (phase-4e-plan.md, step 4.27).
"""

from sessionlib import (
    CHILD,
    CHILD_PASSWORD,
    NIGHT,
    SEED_SOURCE,
    Machine,
    active_terminal,
    child_session,
    children_count,
    colour_share,
    copy,
    greeter_log,
    journal_count,
    launcher_shown,
    logged,
    lock_screen_adult,
    open_panel,
    to_the_modules_page,
    report,
    root,
    shlex_quote,
    wait,
)

CANARY = "/usr/share/kidux/modules/canary"
#: The stand-ins that make the Modules page taller than the screen, named to
#: come before the canary.
BIRD, BIRDS = "/usr/share/kidux/modules/bird", 7
AUDIT = "/home/.kidux/state/audit.log"
#: The canary's icon (tests/lib/seed/modules/canary/icon.svg).
YELLOW = (0xF5, 0xC5, 0x18)


def switched(action: str) -> bool:
    return f'"child": "{CHILD}", "module": "canary"' in root(
        f"grep '\"action\": \"{action}\"' {AUDIT} | tail -1").stdout


def listed() -> str:
    return root(f"runuser -u debian -- /usr/local/bin/kidux-as modules {CHILD}").stdout.strip()


def bird(number: int) -> str:
    return (f'id = "bird-{number}"\nname = "[Test] Bird {number}"\n'
            'description = "A folder the tests put here."\nlaunch = { exec = "/bin/true" }\n')


def room_kept() -> tuple[int, str]:
    """Where the Modules page last settled, in pixels from its top, and
    whether what has the focus is in view, as the panel logged it."""
    line = root("journalctl -b -o cat -t kidux-greeter | grep 'modules room kept at' "
                "| tail -1").stdout.strip()
    if not line:
        return (-1, "")
    kept, _, focus = line.split("modules room kept at ", 1)[1].partition(", the focus ")
    return (int(kept.split()[0]), focus)


def tiles() -> str:
    """The launcher's last word on its tiles: the ids, or "none"."""
    lines = root("journalctl -b -o cat -t kidux-launcher | grep 'tiles: '").stdout.splitlines()
    return lines[-1].split("tiles: ", 1)[1] if lines else ""


def run(machine: Machine) -> None:
    # The machine left up may still hold the stand-ins of an earlier run, or
    # of a hand test: the page starts with the canary alone.
    root(f"rm -rf {BIRD}-*")
    since = root("date +%s").stdout.strip()
    for name in ("module.toml", "icon.svg"):
        copy(SEED_SOURCE / "modules" / "canary" / name, f"{CANARY}/{name}", mode="0644")
    report("the tests' stand-in module is in place, switched off for Leo",
           listed() == "canary off", listed())

    report("the adult panel opens from the sign-in screen", open_panel(machine), greeter_log())
    machine.still()
    report("its Modules page lists the module", to_the_modules_page(machine), greeter_log())
    machine.still()
    # The focus is on the first switch: the module's, under Leo, the first child.
    machine.key("ret")
    report("an adult switches it on for Leo by keyboard",
           wait(lambda: switched("module enabled"), 10) and listed() == "canary on",
           root(f"tail -3 {AUDIT}").stdout)
    machine.screenshot("panel-modules")
    choose_before = machine.mark()
    machine.key("esc")                           # the panel closes
    machine.shown("choose", choose_before)

    before = machine.mark()
    machine.key("ret")                           # Leo, the first picture
    machine.shown("password", before)
    machine.submit(CHILD_PASSWORD)
    signed_in = wait(lambda: child_session() is not None, 30)
    report("Leo signs in", signed_in, greeter_log())
    if not signed_in:
        return
    drawn = wait(lambda: tiles() == "canary", 20)
    launcher_shown(machine)
    picture = machine.screenshot("launcher-tile")
    report("and Leo's launcher shows the module's tile",
           drawn and colour_share(picture, YELLOW, (0.0, 0.15, 1.0, 0.85)) > 0.01,
           f"tiles: {tiles()}; {picture}")

    uid = root(f"id -u {CHILD}").stdout.strip()
    sound = root(f"runuser -u {CHILD} -- env XDG_RUNTIME_DIR=/run/user/{uid} pw-cli info 0",
                 timeout=60)
    report("the child's session has sound: PipeWire answers in it",
           sound.returncode == 0 and "PipeWire:Interface:Core" in sound.stdout,
           sound.stdout[-400:] + sound.stderr[-400:])

    # Off again, from the panel over the lock screen, with the launcher open.
    before = machine.mark()
    machine.monitor("system_powerdown")
    wait(lambda: active_terminal() == "tty8", 20)
    machine.shown("locked", before)
    lock_screen_adult(machine)
    # 15, 30, 60 minutes, the adult's own number and its button, save, log
    # out, then the panel.
    for _ in range(7):
        machine.key("tab")
    before = machine.mark()
    machine.key("ret")
    machine.shown("panel_children", before)
    to_the_modules_page(machine)
    machine.still()
    machine.key("ret")
    report("the panel over the lock screen switches it off again",
           wait(lambda: switched("module disabled"), 10) and listed() == "canary off",
           root(f"tail -3 {AUDIT}").stdout + greeter_log())
    locked_before = machine.mark()
    machine.key("esc")                           # the panel closes: the lock screen
    machine.shown("locked", locked_before)
    before = machine.mark()
    machine.key("ret")                           # Continue
    machine.shown("child_password", before)
    machine.type(CHILD_PASSWORD + "\n")
    back = wait(lambda: active_terminal() == "tty7", 15)
    emptied = wait(lambda: tiles() == "none", 20)
    # The launcher says so before it draws it: the night of the empty grid.
    machine.showing(NIGHT, (0.35, 0.2, 0.65, 0.7), share=0.02, seconds=10, tolerance=10)
    picture = machine.screenshot("launcher-tile-gone")
    report("and the launcher, open all along, shows nothing to open again",
           back and emptied and colour_share(picture, NIGHT, (0.35, 0.2, 0.65, 0.7)) > 0.02,
           f"tiles: {tiles()}; {picture}")

    # Log out: Lock has the focus, Log out is next, and it asks once, with
    # Cancel first. The first key after continuing from the lock screen
    # reaches the launcher (daemon.md section 10, unlock step 3).
    machine.key("tab")
    frame = machine.settled()
    machine.key("ret")
    machine.changes(frame)
    machine.key("tab")
    choose_before = machine.mark()
    machine.key("ret")
    wait(lambda: root(f"pgrep -u {CHILD} -x labwc").returncode != 0, 20)
    machine.shown("choose", choose_before, 30)

    # Remove on a page that scrolls (phase-4e-plan.md, step 4.27): stand-ins
    # enough for the list to go below the fold, with the canary last, by its
    # name, among the test modules; it is a folder no package put there.
    for number in range(1, BIRDS + 1):
        root(f"mkdir -p {BIRD}-{number} && printf '%s' {shlex_quote(bird(number))} "
             f"> {BIRD}-{number}/module.toml")
    open_panel(machine)
    machine.still()
    to_the_modules_page(machine)
    machine.still()
    for _ in range((children_count() + 1) * (BIRDS + 1) - 1):
        machine.key("tab")                       # the canary's Remove
    machine.still()
    before = journal_count("kidux-greeter", "modules room kept at")
    machine.key("ret")
    report("Remove on the last module, below the fold, asks in its row and in view",
           logged("kidux-greeter", "modules room kept at", before)
           and room_kept()[0] > 0 and room_kept()[1] == "in view",
           greeter_log())
    machine.screenshot("panel-modules-remove-asks")
    before = journal_count("kidux-greeter", "modules room kept at")
    asked_at = room_kept()[0]
    machine.key("ret")                           # Cancel, which has the focus
    report("Cancel leaves the page where it was, with the focus on that Remove",
           logged("kidux-greeter", "modules room kept at", before)
           and abs(room_kept()[0] - asked_at) < 80 and room_kept()[1] == "in view",
           greeter_log())
    machine.key("ret")                           # Remove, asked again
    machine.still()
    machine.key("tab")                           # from Cancel to Remove
    machine.key("ret")
    report("the panel removes the canary, a module that is only a folder (D101)",
           wait(lambda: root(f"test -e {CANARY}").returncode != 0, 60)
           and wait(lambda: '"module": "canary"' in root(
               f"grep '\"action\": \"module removed\"' {AUDIT} | tail -1").stdout, 10),
           root(f"tail -3 {AUDIT}").stdout + greeter_log())
    machine.key("esc")
    root(f"rm -rf {CANARY} {BIRD}-*")

    # Since this run began: the machine left up logs that the choose screen
    # does not fit each time its screen blanks, which is not this page's.
    too_tall = root(f"journalctl -b --since=@{since} --no-pager -o cat -t kidux-greeter "
                    "| grep -e 'does not fit' -e 'could not draw' | sort -u").stdout.strip()
    report("the Modules page, with a module on it, fits the screen and was drawn",
           not too_tall, too_tall)
