"""polkit, asked about one of a child's own processes."""

from sessionlib import (
    CHILD,
    Machine,
    report,
    root,
    wait,
)


def run(machine: Machine) -> None:
    # One of the child's own processes, started as a system service so that it
    # is not part of this SSH session: KillUserProcesses would end it the moment
    # the command that started it returned.
    root(f"systemd-run --quiet --uid={CHILD} --unit=kidux-test-probe sleep 300")
    wait(lambda: root("systemctl show -p MainPID --value kidux-test-probe").stdout.strip()
         not in ("", "0"), 10, 0.5)
    pid = root("systemctl show -p MainPID --value kidux-test-probe").stdout.strip()
    if not report("a process of the child's exists to ask polkit about", pid not in ("", "0"), pid):
        return
    for action, allowed in (
        ("org.freedesktop.login1.power-off", True),
        ("org.freedesktop.login1.reboot", True),
        ("org.freedesktop.login1.chvt", False),
        ("org.freedesktop.timedate1.set-time", False),
        ("org.freedesktop.systemd1.manage-units", False),
    ):
        result = root(f"pkcheck --action-id {action} --process {pid}")
        answered = result.returncode in (0, 1, 2)   # authorised, not, or challenge
        verb = "may" if allowed else "may not"
        report(f"a child {verb} {action.rsplit('.', 1)[-1].replace('-', ' ')}",
               answered and (result.returncode == 0) == allowed,
               f"exit {result.returncode}: {result.stdout}{result.stderr}")
    root("systemctl stop kidux-test-probe")
