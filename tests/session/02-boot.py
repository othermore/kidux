"""The Kidux entry boots, quietly, into the sign-in screen, with the splash set,
and the lid's watcher beside it."""

from sessionlib import (
    Machine,
    active_terminal,
    report,
    root,
    ssh,
    wait,
)



#: Run in every language (tests/lib/session-vm.py): it sets the machine up,
#: or checks what a language can change.
EVERY_LANGUAGE = True

def run(machine: Machine) -> None:
    cmdline = ssh("cat /proc/cmdline").stdout
    report("the machine boots the Kidux entry", "kidux.boot" in cmdline, cmdline)
    report("with no boot messages on the screen",
           "quiet" in cmdline and "loglevel=3" in cmdline and "systemd.show_status=false" in cmdline,
           cmdline)
    report("into the sign-in screen on terminal 7", wait(lambda: active_terminal() == "tty7", 60),
           active_terminal() + "\n" + root("systemctl status greetd --no-pager").stdout)
    theme = root("plymouth-set-default-theme; lsinitramfs /boot/initrd.img-$(uname -r) "
                 "| grep -c plymouth/themes/kidux/").stdout.split()
    report("the boot splash is Kidux's, and in the initramfs",
           len(theme) == 2 and theme[0] == "kidux" and theme[1] != "0", theme)
    # The plugin the initramfs hook copies for any theme but Debian's own,
    # and warns about at every kernel update when it is missing:
    # kidux-session depends on plymouth-label, so it is there.
    label = root("lsinitramfs /boot/initrd.img-$(uname -r) | grep -c label-pango.so").stdout
    report("and so is the label plugin Plymouth's hook asks for", label.strip() not in ("", "0"),
           label)
    report("greetd is running the sign-in screen",
           wait(lambda: "greeter" in ssh("loginctl list-sessions --no-legend").stdout, 30),
           ssh("loginctl list-sessions --no-legend").stdout)
    # The corner over the sign-in screen looks at the machine as the
    # launcher's does (D61): nothing of a laptop's on the test machine.
    report("the sign-in screen's corner found no battery, backlight, keyboard light or lid here",
           wait(lambda: "hardware: battery=none backlight=none keyboard=none lid=no" in root(
               "journalctl -b -o cat -t kidux-greeter").stdout, 30),
           root("journalctl -b -o cat -t kidux-greeter | grep hardware").stdout)
    # A laptop's key on the sign-in screen, which answers it itself under
    # cage (D61): the test machine has no backlight, but a volume key
    # reaches the screen, which says so, and does nothing here.
    before = root("journalctl -b -o cat -t kidux-greeter | grep -c 'laptop key: volume up'"
                  ).stdout.strip()
    machine.key("volumeup")
    report("the sign-in screen answers a laptop's volume key",
           wait(lambda: root("journalctl -b -o cat -t kidux-greeter "
                             "| grep -c 'laptop key: volume up'").stdout.strip() != before, 10),
           root("journalctl -b -o cat -t kidux-greeter | tail -5").stdout)
    # The lid's watcher starts beside the sign-in screen under cage (D61):
    # the test machine has no lid, and it says so and ends.
    report("the lid's watcher started with the sign-in screen, and found no lid here",
           wait(lambda: "no lid switch on this machine" in root(
               "journalctl -b -o cat -t kidux-lid-watch").stdout, 30),
           root("journalctl -b -o cat -t kidux-lid-watch").stdout)
