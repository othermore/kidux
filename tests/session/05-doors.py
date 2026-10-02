"""Every door of session.md section 6 is shut, and SSH still works for adults."""

import time

from sessionlib import (
    Machine,
    active_terminal,
    boot_id,
    report,
    root,
    ssh,
    up,
)


def run(machine: Machine) -> None:
    machine.key("ctrl-alt-f2")
    time.sleep(2)
    report("Ctrl+Alt+F2 does nothing", active_terminal() == "tty7", active_terminal())
    machine.screenshot("after-ctrl-alt-f2")

    before = boot_id()
    machine.key("alt-sysrq-b")
    time.sleep(10)
    report("Alt+SysRq+B does nothing", up() and boot_id() == before)

    values = root("sysctl -n kernel.sysrq kernel.yama.ptrace_scope").stdout.split()
    report("SysRq is off and one process cannot watch another", values == ["0", "2"], values)

    for name, expected in (("NAutoVTs", "u 0"), ("KillUserProcesses", "b true"),
                           ("HandlePowerKey", 's "ignore"'), ("HandleLidSwitch", 's "ignore"')):
        got = ssh("busctl get-property org.freedesktop.login1 /org/freedesktop/login1 "
                  f"org.freedesktop.login1.Manager {name}").stdout.strip()
        report(f"logind {name} is {expected.split()[-1]}", got == expected, got)

    report("no text login is waiting on terminal 2",
           ssh("systemctl is-active getty@tty2.service").stdout.strip() != "active")
    report("Ctrl+Alt+Delete is masked",
           ssh("systemctl is-enabled ctrl-alt-del.target").stdout.strip() == "masked",
           ssh("systemctl is-enabled ctrl-alt-del.target").stdout)

    denied = root("sshd -T -C user=marta,host=x,addr=10.0.2.2 | grep -i '^denygroups'").stdout
    report("a child may not log in over SSH", "kidux-children" in denied, denied)
    report("the administrator still can", up())
