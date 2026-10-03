"""Updates from the panel, by keyboard: looked for, found, installed (plan step 9.8).

The package it updates is made in the machine and served from a directory
(`kidux-as canary`); the real archive is never touched. Then the System
page's Advanced settings (D52): Chromium's options, set from the command
line before the panel opened, shown on their page, and saved again from it.
"""

import time

from sessionlib import (
    Machine,
    children_count,
    greeter_log,
    open_panel,
    report,
    root,
    wait,
)

AUDIT = "/home/.kidux/state/audit.log"


def audit_line(action: str, outcome: str) -> bool:
    lines = root(f"grep '\"action\": \"{action}\"' {AUDIT}").stdout.splitlines()
    return any(f'"outcome": "{outcome}"' in line for line in lines)


def run(machine: Machine) -> None:
    made = root("/usr/local/bin/kidux-as canary")
    report("a package to update waits in a local repository", made.returncode == 0,
           made.stdout + made.stderr)
    root("runuser -u debian -- /usr/local/bin/kidux-as set-config chromium_flags "
         "'[\"--disable-gpu-compositing\"]'")

    report("the adult panel opens from the sign-in screen", open_panel(machine), greeter_log())
    machine.still()
    # From the first child's name: back past the five controls that give
    # time, every child, Add and Network, to System.
    children = children_count()
    for _ in range(5 + children + 3):
        machine.key("shift-tab")
    before = machine.mark()
    machine.key("ret")
    report("the system page", machine.shown("panel_system", before, 10), greeter_log())
    machine.screenshot("panel-updates-none")

    # From the current password, back past Show, to Look for updates.
    machine.key("shift-tab")
    machine.key("shift-tab")
    machine.key("ret")
    found = wait(lambda: audit_line("update check", "ok"), 180, 2)
    time.sleep(2)                                # the page asks the daemon once a second
    machine.screenshot("panel-updates-found")
    report("looking for updates from the panel finds the one there is", found,
           root(f"tail -3 {AUDIT}").stdout)

    machine.key("shift-tab")
    machine.key("shift-tab")
    machine.key("ret")                           # Install
    time.sleep(2)
    machine.screenshot("panel-updates-progress")
    finished = wait(lambda: audit_line("update finished", "ok"), 300, 2)
    time.sleep(2)                                # the page asks the daemon once a second
    machine.screenshot("panel-updates-done")
    version = root("dpkg-query -W -f='${Version}' kidux-test-canary").stdout.strip()
    report("and installing it from the panel puts it in place", finished and version == "1.1",
           version + "\n" + root(f"tail -3 {AUDIT}").stdout)

    # The page drawn again has the focus on the current password: past the
    # new one twice, Save, language, keyboard, scale, and the two minutes and
    # Set of a computer left alone, to the button under Advanced.
    for _ in range(10):
        machine.key("tab")
    before = machine.mark()
    machine.key("ret")
    shown = machine.shown("panel_advanced", before, 10)
    machine.screenshot("panel-system-advanced")
    report("Advanced, on the System page, shows the pointer's steps and Chromium's options "
           "for this machine",
           shown and root("cat /etc/kidux/chromium-flags").stdout == "--disable-gpu-compositing\n",
           greeter_log())
    saves = int(root(f"grep -c '\"action\": \"config set\"' {AUDIT}").stdout.strip() or 0)
    # From the pointer's speed, past the scroll's and the options, to Save.
    for _ in range(3):
        machine.key("tab")
    before = machine.mark()
    machine.key("ret")
    machine.shown("panel_advanced", before, 10)
    report("and Save there keeps them, in the file Chromium's starter reads",
           wait(lambda: int(root(f"grep -c '\"action\": \"config set\"' {AUDIT}").stdout.strip()
                            or 0) > saves, 10)
           and root("stat -c '%U %a' /etc/kidux/chromium-flags").stdout.strip() == "root 644"
           and root("cat /etc/kidux/chromium-flags").stdout == "--disable-gpu-compositing\n",
           root(f"tail -2 {AUDIT}").stdout)
    root("runuser -u debian -- /usr/local/bin/kidux-as set-config chromium_flags '[]'")

    # The page drawn again has the focus on the pointer's speed: on to the
    # touchpad's scroll, whose list opens with no step chosen until a key
    # moves in it; Home is its first, Much slower.
    machine.key("tab")
    machine.key("ret")
    machine.still(2)
    machine.key("home")
    before = machine.mark()
    machine.key("ret")
    machine.shown("panel_advanced", before, 10)
    machine.screenshot("panel-system-advanced-scroll")
    report("choosing Much slower for two fingers writes it where a child's session reads it",
           wait(lambda: "<scrollFactor>0.25</scrollFactor>"
                in root("cat /etc/kidux/input.xml").stdout, 10)
           and root("stat -c '%U %a' /etc/kidux/input.xml").stdout.strip() == "root 644",
           root("cat /etc/kidux/input.xml").stdout + root(f"tail -2 {AUDIT}").stdout)
    root("runuser -u debian -- /usr/local/bin/kidux-as set-config scroll_speed 0")

    before = machine.mark()
    machine.key("esc")                           # the panel closes
    machine.shown("choose", before)
    root("rm -f /etc/apt/sources.list.d/kidux-test-canary.list")
    machine.still()
