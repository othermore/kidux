"""Modules on the panel and on the launcher (phase-3-plan.md, step 3.1).

The tests' stand-in module is copied into place over SSH, switched on for
Leo from the panel by keyboard, shown as a tile on Leo's launcher, switched
off again from the panel over the lock screen while the launcher stays open,
and removed at the end. Sound is checked in Leo's session while it is open.
"""

from sessionlib import (
    CHILD,
    CHILD_PASSWORD,
    NIGHT,
    SEED_SOURCE,
    Machine,
    active_terminal,
    child_session,
    colour_share,
    copy,
    greeter_log,
    launcher_shown,
    lock_screen_adult,
    open_panel,
    to_the_modules_page,
    report,
    root,
    wait,
)

CANARY = "/usr/share/kidux/modules/canary"
AUDIT = "/home/.kidux/state/audit.log"
#: The canary's icon (tests/lib/seed/modules/canary/icon.svg).
YELLOW = (0xF5, 0xC5, 0x18)


def switched(action: str) -> bool:
    return f'"child": "{CHILD}", "module": "canary"' in root(
        f"grep '\"action\": \"{action}\"' {AUDIT} | tail -1").stdout


def listed() -> str:
    return root(f"runuser -u debian -- /usr/local/bin/kidux-as modules {CHILD}").stdout.strip()


def tiles() -> str:
    """The launcher's last word on its tiles: the ids, or "none"."""
    lines = root("journalctl -b -o cat -t kidux-launcher | grep 'tiles: '").stdout.splitlines()
    return lines[-1].split("tiles: ", 1)[1] if lines else ""


def run(machine: Machine) -> None:
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
    root(f"rm -rf {CANARY}")

    too_tall = root("journalctl -b --no-pager -o cat -t kidux-greeter "
                    "| grep -e 'does not fit' -e 'could not draw' | sort -u").stdout.strip()
    report("the Modules page, with a module on it, fits the screen and was drawn",
           not too_tall, too_tall)
