"""The packages install on a stock Debian, and the machine reboots into Kidux."""

from sessionlib import (
    ARCHIVE,
    Machine,
    SEED_SOURCE,
    copy,
    reboot,
    report,
    root,
)



#: Run in every language (tests/lib/session-vm.py): it sets the machine up,
#: or checks what a language can change.
EVERY_LANGUAGE = True

def run(machine: Machine) -> bool:
    steps = [
        ("the bootstrap packages install by hand",
         f"cd /var/tmp && curl -fsSLO {ARCHIVE}/bootstrap/testing/kidux-archive-keyring.deb "
         f"&& curl -fsSLO {ARCHIVE}/bootstrap/testing/kidux-apt-source.deb "
         "&& DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends "
         "/var/tmp/kidux-archive-keyring.deb /var/tmp/kidux-apt-source.deb "
         "&& sed -i 's/^Suites: stable$/Suites: testing/' /etc/apt/sources.list.d/kidux.sources "
         # In CI, the run's own signing key, published beside the archive.
         f"&& {{ ! curl -fsS -o /var/tmp/extra-key.pgp {ARCHIVE}/extra-key.pgp "
         "|| cat /var/tmp/extra-key.pgp >> /usr/share/keyrings/kidux-archive-keyring.pgp; }"),
        ("kidux-base installs, and brings the session and the sign-in screen",
         "apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y kidux-base "
         "&& dpkg -s kidux-session kidux-greeter >/dev/null"),
    ]
    for name, command in steps:
        result = root(command, timeout=900)
        if not report(name, result.returncode == 0, result.stdout[-800:] + result.stderr[-800:]):
            return False

    copy(SEED_SOURCE / "tools/kidux-as", "/usr/local/bin/kidux-as")
    copy(SEED_SOURCE / "tools/kidux-toplevels", "/usr/local/bin/kidux-toplevels")

    return report("the machine reboots into Kidux", reboot(machine))
