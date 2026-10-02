"""The reference module, installed from the panel (phase-3-plan.md, steps 3.4
and 3.5).

With nobody signed in, the panel's Modules page offers kidux-module-hello
from the archive, for ages 4 to 8, and hello-web after it (D55), and
installs hello by keyboard: that the daemon's job puts it
where the launcher looks is what is being tested. Switched on for Leo from
the command line, Leo opens it by keyboard; it speaks Spanish, writes its one
file where the launcher told it to, and *Done*, which has the keyboard,
closes it and gives the launcher back. Purged with apt while Leo is signed
in, its tile goes; installed again with apt after Leo has logged out, the
panel's *Remove* takes it away and offers it again.
"""


from sessionlib import (
    CHILD,
    CHILD_PASSWORD,
    CREAM,
    Machine,
    child_session,
    colour_share,
    children_count,
    greeter_log,
    journal_count,
    launcher_log,
    launcher_shown,
    HOME,
    SPEAKS,
    on_screen,
    open_panel,
    report,
    root,
    screens_shown,
    to_the_modules_page,
    wait,
)

OPENED = f"/home/{CHILD}/.local/share/kidux/hello/opened"
HELLO = "/usr/share/kidux/modules/hello"
AUDIT = "/home/.kidux/state/audit.log"
#: The room above the launcher's bar.
ABOVE_THE_BAR = (0.0, 0.0, 1.0, 0.92)
#: What the greeter logs of the Modules page when it has to scroll.
TOO_TALL = "the panel_modules screen does not fit"


def hello_pid() -> str:
    return root(f"pgrep -u {CHILD} -f '^/usr/bin/python3 /usr/libexec/kidux-module-hello'"
                ).stdout.strip()


def apt(command: str) -> bool:
    return root("DEBIAN_FRONTEND=noninteractive apt-get " + command
                + " -y -o DPkg::Lock::Timeout=600 kidux-module-hello", timeout=900).returncode == 0


def audited(action: str) -> int:
    return int(root(f"grep -c '\"action\": \"{action}\"' {AUDIT}").stdout.strip() or 0)


def panel_modules_log() -> str:
    return greeter_log() + root(f"tail -3 {AUDIT}").stdout


def done_redrawing(name: str, seconds: float = 30) -> bool:
    """Wait until the panel stops drawing `name` again: it redraws the page
    once a second while a job runs, and the last one, which says how it
    went, asks apt again what the archive offers, which takes a few
    seconds more."""
    last = [-1]

    def same() -> bool:
        now = screens_shown(name)
        stopped, last[0] = now == last[0], now
        return stopped

    return wait(same, seconds, 5)


def offered_in_the_pages_order(listed: str) -> list[str]:
    """The ids of the modules `kidux-as modules-available` lists as
    available, in the order the Modules page shows them: `<id> available
    <version> <ages> <before> <name…>`, the ages as `4-8`, `2-` or `-`."""
    found = []
    for line in listed.splitlines():
        parts = line.split()
        if len(parts) < 6 or parts[1] != "available":
            continue
        least, _, most = parts[3].partition("-")
        name = " ".join(parts[5:])
        found.append((name.startswith("["), int(least or 0), int(most or 0), name.lower(),
                      parts[0]))
    return [entry[-1] for entry in sorted(found)]


def run(machine: Machine) -> None:
    # The page drawn too tall for the screen, counted from here: 15-modules.py
    # checks the page as it was before.
    too_tall = journal_count("kidux-greeter", TOO_TALL)
    # The Modules page, with nothing installed: the first Install has the
    # focus, and the modules offered are by age, the test modules last
    # (D73, panel.ordered), so hello's is as many Tabs on as there are
    # offered before it in that order.
    listed = root("runuser -u debian -- /usr/local/bin/kidux-as modules-available").stdout
    offered = offered_in_the_pages_order(listed)
    report("the adult panel opens from the sign-in screen", open_panel(machine), greeter_log())
    # hello's package names it in the machine's language before it is
    # installed (D47).
    report("its Modules page offers kidux-module-hello from the archive, by its name in the "
           "machine's language",
           to_the_modules_page(machine) and "hello" in offered
           and any(line.startswith("hello available ") and line.endswith(f" {SPEAKS['hello']}")
                   for line in listed.splitlines()),
           greeter_log() + listed)
    # Who each is for (D55), which the page says under the description:
    # hello from 4 to 8, and hello-web after hello.
    report("with hello's ages, and hello to do before hello-web",
           any(line.startswith("hello available ") and " 4-8 - " in line
               for line in listed.splitlines())
           and any(line.startswith("hello-web available ") and " 4-8 hello " in line
                   for line in listed.splitlines()), listed)
    machine.screenshot("panel-modules-available")
    for _ in range(offered.index("hello") if "hello" in offered else 0):
        machine.key("tab")
    installs = audited("module installed")
    drawn = machine.mark()
    machine.key("ret")
    machine.shown("panel_modules", drawn)
    machine.screenshot("panel-modules-installing")
    report("Install there installs it through the daemon",
           wait(lambda: audited("module installed") > installs, 300, 2)
           and root(f"test -f {HELLO}/module.toml").returncode == 0, panel_modules_log())
    report("and the page shows it installed, with a switch for each child",
           done_redrawing("panel_modules"), greeter_log())
    machine.screenshot("panel-modules-installed")
    closed = machine.mark()
    machine.key("esc")                           # the panel closes
    machine.shown("choose", closed)

    root(f"runuser -u debian -- /usr/local/bin/kidux-as enable {CHILD} hello on")
    root(f"rm -rf /home/{CHILD}/.local/share/kidux/hello")

    before = journal_count("kidux-launcher", "tiles: hello")
    password = machine.mark()
    machine.key("ret")                           # Leo, the first picture
    machine.shown("password", password)
    machine.submit(CHILD_PASSWORD)
    report("Leo signs in to its tile", wait(lambda: child_session() is not None, 30)
           and wait(lambda: journal_count("kidux-launcher", "tiles: hello") > before, 30)
           and launcher_shown(machine), greeter_log() + launcher_log())

    # From Lock, which has the focus, back to the tile, and Enter.
    machine.key("shift-tab")
    machine.key("ret")
    opened = wait(lambda: hello_pid() != "" and root(f"test -s {OPENED}").returncode == 0, 30)
    wait(lambda: on_screen() == "hello", 10)
    picture = machine.screenshot("module-hello")
    report("Leo opens it by keyboard, and it writes its one file where the launcher said",
           opened and root(f"cat {OPENED}").stdout.strip() == root("date -I").stdout.strip(),
           launcher_log() + root(f"ls -la /home/{CHILD}/.local/share/kidux/").stdout)
    report("it fills the room above the bar, in the cream of Kidux's screens",
           on_screen() == "hello" and colour_share(picture, CREAM, ABOVE_THE_BAR) > 0.5,
           f"on screen: {on_screen()}; {picture}")
    environment = root(f"tr '\\0' '\\n' < /proc/{hello_pid()}/environ").stdout
    done = root(f"runuser -u {CHILD} -- env LANG={SPEAKS['locale']} python3 -c 'import gettext; "
                f"print(gettext.translation(\"kidux-module-hello\", fallback=True)"
                f".gettext(\"Done\"))'").stdout
    report("it speaks the machine's language, in its own words",
           f"LANG={SPEAKS['locale']}" in environment and done.strip() == SPEAKS["done"],
           f"{done}{picture}")

    # Done has the keyboard: Enter closes it, and the launcher is back.
    ended = journal_count("kidux-launcher", "module hello ended")
    machine.key("ret")
    report("Done closes it, and the launcher is back",
           wait(lambda: journal_count("kidux-launcher", "module hello ended") > ended, 15)
           and hello_pid() == "" and wait(lambda: on_screen() == HOME, 10), launcher_log())

    # Purged with Leo still signed in: the tile goes.
    emptied = journal_count("kidux-launcher", "tiles: none")
    report("the package purges", apt("purge"), root("tail -5 /var/log/apt/term.log").stdout)
    report("and its tile is gone from the launcher, open all along",
           wait(lambda: journal_count("kidux-launcher", "tiles: none") > emptied, 45), launcher_log())

    # Log out: Lock has the focus, Log out is next, and it asks once, with
    # Cancel first.
    machine.still()
    machine.key("tab")
    frame = machine.settled()
    machine.key("ret")
    machine.changes(frame)
    machine.key("tab")
    choose_before = machine.mark()
    machine.key("ret")
    wait(lambda: root(f"pgrep -u {CHILD} -x labwc").returncode != 0, 20)
    machine.shown("choose", choose_before, 30)

    # Back on the panel with hello installed again: the first switch has the
    # focus, Remove is after the children's switches, and it asks first,
    # Cancel before Remove.
    report("kidux-module-hello installs again with apt", apt("install"),
           root("tail -5 /var/log/apt/term.log").stdout)
    report("the panel opens again", open_panel(machine), greeter_log())
    to_the_modules_page(machine)
    for _ in range(children_count()):
        machine.key("tab")
    asked = machine.mark()
    machine.key("ret")
    machine.shown("panel_modules", asked)
    removals = audited("module removed")
    machine.key("tab")                           # from Cancel to Remove
    drawn = machine.mark()
    machine.key("ret")
    machine.shown("panel_modules", drawn)
    report("Remove on the panel removes it, once asked",
           wait(lambda: audited("module removed") > removals, 300, 2)
           and root(f"test -e {HELLO}").returncode != 0, panel_modules_log())
    report("and the archive offers it again", "hello available" in root(
        "runuser -u debian -- /usr/local/bin/kidux-as modules-available").stdout, greeter_log())
    closed = machine.mark()
    machine.key("esc")
    machine.shown("choose", closed)
    root(f"runuser -u debian -- /usr/local/bin/kidux-as enable {CHILD} hello off")
    report("the Modules page, with the modules on offer and who each is for, fits the screen",
           journal_count("kidux-greeter", TOO_TALL) == too_tall,
           root(f"journalctl -b -o cat -t kidux-greeter | grep '{TOO_TALL}' | tail -3").stdout)
