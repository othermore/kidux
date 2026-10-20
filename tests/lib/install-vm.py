#!/usr/bin/python3
"""Kidux installed from its image, as a family installs it.

    tests/run install [image.iso]

docs/dev/image.md, section 4. The newest image in build/image/, or the one
named, is started in a virtual machine and taken through its installer by
keyboard, as an adult takes it, onto an empty disk; the machine then starts
from the disk, and the session tests that take a fresh Kidux machine through
its first start (tests/session/02 to 05) run on it, as on the session
machine installed on Debian. Then the same image installs once more on a
computer that starts with a BIOS, which must reach the first start too, and
starts under Secure Boot, as the installed system does; and once more under
UEFI from the boot menu's English entry, for the English pictures and the
English trial image.

Every picture is left in build/vm/install-NN-<screen>.png, the English
installation's in build/vm/install-en-NN-<screen>.png; those the user
guide shows are listed in tests/lib/doc-screenshots.txt, and the release
copies them. The disks the two UEFI installations made are kept, as
build/vm/install.qcow2 and build/vm/install-en.qcow2, prepared and the
first start not done: the trial images are made from them, the Spanish one
from the first and the English one from the second
(ci/build-trial-image.py).

To be reached by the tests, the installed system gets what a session
machine's cloud-init gives it, and nothing else, before it first starts: an
SSH server with the tests' key for the administrator, `ana`, or `anna` on
the English installation, whom the tests reach the machine as, sudo
without a password for them, the name of the
development archive's address, and its usage identifier, sixteen zeros and
4 (sessionlib.test_identifier). A helper machine, the session machines'
Debian, writes them onto the disk, which the installed system never sees
started without them.

Each check prints PASS or FAIL; the exit status is the number of failures.
"""

import importlib.util
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

os.environ["KIDUX_VM_LANGUAGE"] = "es"
import sessionlib
from sessionlib import BASE, REPO, VM, Machine, report, ssh, up, wait

RUN = "install"
DISK = VM / f"{RUN}.qcow2"
#: The English installation's disk, for the English trial image.
ENGLISH_DISK = VM / f"{RUN}-en.qcow2"
BIOS_DISK = VM / f"{RUN}-bios.qcow2"
KEY = VM / f"{RUN}_key"
HELPER = VM / f"{RUN}-helper.qcow2"
CIDATA = VM / f"{RUN}-cidata"
SSH_PORT = 2224
NUMBER = 4
OVMF_CODE = "/usr/share/OVMF/OVMF_CODE_4M.fd"
OVMF_VARS = "/usr/share/OVMF/OVMF_VARS_4M.fd"
SECURE_CODE = "/usr/share/OVMF/OVMF_CODE_4M.secboot.fd"
#: Variables with Microsoft's keys enrolled and Secure Boot on, as a
#: computer sold with Windows has them.
SECURE_VARS = "/usr/share/OVMF/OVMF_VARS_4M.ms.fd"

# Every helper of sessionlib's reaches this machine: its disk, key, port,
# monitor and pictures.
sessionlib.RUN = RUN
sessionlib.DISK = DISK
sessionlib.KEY = KEY
sessionlib.SSH_PORT = SSH_PORT
sessionlib.MONITOR = VM / f"{RUN}-monitor.sock"
sessionlib.CONSOLE = VM / f"{RUN}-console.log"

#: The installer's colours (kidux-installer's branding.desc): the cream of
#: its sidebar, and the ink of the step it is on.
CREAM = (0xff, 0xf6, 0xe9)
INK = (0x3b, 0x2f, 0x2a)
SIDEBAR = (0.0, 0.15, 0.13, 0.95)
#: The installer's steps, in the order its sidebar lists them.
STEPS = ("welcome", "location", "keyboard", "partitions", "users", "summary", "install",
         "finish")
#: The first start's language buttons, on its cream (tests/session/03).
BUTTON = (0xeb, 0xe2, 0xd5)
#: Where the first of them, English, is.
FIRST_BUTTON = (0.40, 0.555, 0.49, 0.62)
#: The administrator the installer makes, in each language: a name, from
#: which it suggests the login, `ana` or `anna`, and a password.
ADMIN_NAMES = {"es": "Ana", "en": "Anna"}
ADMINS = {"es": "ana", "en": "anna"}
sessionlib.USER = ADMINS["es"]
ADMIN_PASSWORD = "the admin password"
#: The installer's *Next*, by the letter its button underlines.
NEXT = {"es": "alt-s", "en": "alt-n"}
#: The boot menu's highlight, GRUB's light gray, on its first entry and on
#: its second, the English one.
HIGHLIGHT = (152, 152, 152)
MENU_ROWS = {"es": (0.2, 0.228, 0.8, 0.246), "en": (0.2, 0.252, 0.8, 0.27)}
#: How long an installation may take, copying and all.
INSTALL_MINUTES = 30


def qemu(machine: Machine, disk: Path, firmware: str, iso: Path | None = None) -> None:
    """Start a machine on `disk`, from `iso` when one is given: UEFI, a
    BIOS, or UEFI with Secure Boot (`secure`)."""
    sessionlib.MONITOR.unlink(missing_ok=True)
    options = ["-machine", "q35"]
    if firmware in ("uefi", "secure"):
        variables = VM / f"OVMF_VARS_{RUN}-{firmware}.fd"
        shutil.copy(SECURE_VARS if firmware == "secure" else OVMF_VARS, variables)
        options = ["-machine", "q35,smm=on" if firmware == "secure" else "q35",
                   *(["-global", "driver=cfi.pflash01,property=secure,value=on"]
                     if firmware == "secure" else []),
                   "-drive", "if=pflash,format=raw,unit=0,readonly=on,file="
                   + (SECURE_CODE if firmware == "secure" else OVMF_CODE),
                   "-drive", f"if=pflash,format=raw,unit=1,file={variables}"]
    cdrom = (["-drive", f"file={iso},media=cdrom,readonly=on,if=none,id=cd",
              "-device", "ide-cd,drive=cd,bootindex=0"] if iso else [])
    accel = ["-enable-kvm", "-cpu", "host"] if os.access("/dev/kvm", os.W_OK) else ["-cpu", "max"]
    machine.process = subprocess.Popen(
        ["qemu-system-x86_64", *accel, "-m", "4096", "-smp", "2", *options,
         "-drive", f"file={disk},format=qcow2,if=virtio,cache=unsafe,discard=unmap,"
         "detect-zeroes=unmap", *cdrom,
         "-netdev", f"user,id=net0,hostfwd=tcp:127.0.0.1:{SSH_PORT}-:22",
         "-device", "virtio-net-pci,netdev=net0",
         "-vga", "none", "-device", "VGA,edid=on,xres=1280,yres=800",
         "-monitor", f"unix:{sessionlib.MONITOR},server,nowait",
         "-serial", f"file:{sessionlib.CONSOLE}", "-display", "none"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    wait(sessionlib.MONITOR.exists, 10, 0.2)


def power_off(machine: Machine) -> None:
    if machine.process is not None and machine.process.poll() is None:
        try:
            machine.monitor("quit")
        except OSError:
            pass
        try:
            machine.process.wait(30)
        except subprocess.TimeoutExpired:
            machine.process.kill()
    machine.process = None


def fresh_disk(path: Path) -> None:
    path.unlink(missing_ok=True)
    subprocess.run(["qemu-img", "create", "-f", "qcow2", str(path), "40G"],
                   check=True, capture_output=True)


def step_box(step: str) -> tuple:
    """Where the sidebar shows `step`: the one the installer is on is ink
    on its cream, the others cream."""
    middle = (97 + 36 * STEPS.index(step)) / 800
    return (0.01, middle - 0.01, 0.12, middle + 0.01)


def on_step(machine: Machine, step: str, seconds: float = 30) -> bool:
    return machine.showing(INK, step_box(step), share=0.6, seconds=seconds)


def next_step(machine: Machine, step: str, prefix: str, language: str = "es") -> bool:
    """The installer's *Next*, and a picture of the page it opens."""
    machine.key(NEXT[language])
    reached = on_step(machine, step, 60)
    time.sleep(1)
    machine.screenshot(f"{prefix}{step}")
    return reached


def boot_menu(machine: Machine, prefix: str, language: str) -> bool:
    """The image's boot menu, under UEFI: its entry in `language` chosen,
    photographed, and started."""
    shown = machine.showing(HIGHLIGHT, MENU_ROWS["es"], share=0.5, seconds=60)
    if language == "en":
        machine.key("down")
        shown = shown and machine.showing(HIGHLIGHT, MENU_ROWS["en"], share=0.5, seconds=10)
    machine.screenshot(f"{prefix}boot-menu")
    machine.key("ret")
    return shown


def install(machine: Machine, iso: Path, disk: Path, firmware: str, prefix: str,
            language: str = "es") -> bool:
    """The image's installer, from its boot menu's entry in `language`, to
    the end of the installation."""
    label = firmware if language == "es" else f"{firmware}, in English"
    fresh_disk(disk)
    qemu(machine, disk, firmware, iso)
    if firmware == "uefi" and not report(
            f"{label}: the image's boot menu offers Kidux in {language}",
            boot_menu(machine, prefix, language)):
        return False
    shown = on_step(machine, "welcome", 300) and machine.still(10)
    welcome = machine.screenshot(f"{prefix}welcome")
    if not report(f"{label}: the image starts the installer, Kidux's, full screen",
                  shown, str(welcome)):
        return False
    for step in ("location", "keyboard", "partitions", "users"):
        if not report(f"{label}: the installer goes on to its {step} page",
                      next_step(machine, step, prefix, language)):
            return False
    # The name, from which the login comes; the computer's name, which the
    # installer suggests; and the password twice.
    machine.type(ADMIN_NAMES[language])
    for _ in range(3):
        machine.key("tab")
    machine.type(ADMIN_PASSWORD)
    machine.key("tab")
    machine.type(ADMIN_PASSWORD)
    machine.screenshot(f"{prefix}users-filled")
    if not report(f"{label}: the administrator's page takes the name and password",
                  next_step(machine, "summary", prefix, language)):
        return False
    machine.key("alt-i")                 # Install
    time.sleep(2)
    machine.screenshot(f"{prefix}confirm")
    machine.key("ret")                   # Install now, the dialog's default
    started = time.monotonic()
    on_step(machine, "install", 30)
    time.sleep(20)
    machine.screenshot(f"{prefix}installing")
    end = started + INSTALL_MINUTES * 60
    finished = failed = False
    while time.monotonic() < end and not finished and not failed:
        frame = machine.frame()
        finished = sessionlib._ppm_share(frame, INK, step_box("finish"), 16) > 0.6
        # The installer's error fills the screen in place of its pages.
        failed = sessionlib._ppm_share(frame, CREAM, SIDEBAR, 16) < 0.3
        time.sleep(5)
    minutes = (time.monotonic() - started) / 60
    picture = machine.screenshot(f"{prefix}finished" if finished else f"{prefix}failed")
    report(f"{label}: the installer installs Kidux on the disk, in {minutes:.0f} minutes",
           finished, str(picture))
    power_off(machine)
    return finished


def helper_seed() -> None:
    """The helper machine's cloud-init: the installed disk is its second,
    and what the tests need is written onto it."""
    if CIDATA.exists():
        shutil.rmtree(CIDATA)
    CIDATA.mkdir(parents=True)
    public_key = KEY.with_suffix(".pub").read_text().strip()
    identifier = sessionlib.test_identifier(NUMBER)
    admin = sessionlib.USER
    script = f"""#!/bin/sh
set -eux
t=/mnt/kidux
mkdir -p $t
mount /dev/disk/by-partlabel/kidux $t
mount /dev/disk/by-partlabel/kidux-home $t/home
for d in dev proc sys run; do mount --rbind /$d $t/$d; mount --make-rslave $t/$d; done
printf '#!/bin/sh\\nexit 101\\n' > $t/usr/sbin/policy-rc.d
chmod 755 $t/usr/sbin/policy-rc.d
mv $t/etc/resolv.conf $t/etc/resolv.conf.kidux || true
cp -L /etc/resolv.conf $t/etc/resolv.conf
chroot $t apt-get update
chroot $t env DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends openssh-server
rm -f $t/etc/resolv.conf $t/usr/sbin/policy-rc.d
mv $t/etc/resolv.conf.kidux $t/etc/resolv.conf || true
chroot $t install -d -m 700 -o {admin} -g {admin} /home/{admin}/.ssh
echo '{public_key}' > $t/home/{admin}/.ssh/authorized_keys
chroot $t chown {admin}:{admin} /home/{admin}/.ssh/authorized_keys
echo '{admin} ALL=(ALL) NOPASSWD:ALL' > $t/etc/sudoers.d/90-kidux-tests
chmod 440 $t/etc/sudoers.d/90-kidux-tests
echo 'Acquire::http::User-Agent "Debian APT-HTTP/1.3 Kidux/{identifier}";' \\
    > $t/etc/apt/apt.conf.d/99kidux-test-machine
echo 'Acquire::Languages "none";' > $t/etc/apt/apt.conf.d/99kidux-vm-lean
printf '10.0.2.2 kidux.local\\n' >> $t/etc/hosts
umount -R $t
"""
    (CIDATA / "meta-data").write_text(f"instance-id: kidux-install-{int(time.time())}\n"
                                      "local-hostname: kidux-helper\n")
    (CIDATA / "user-data").write_text(
        "#cloud-config\nwrite_files:\n  - path: /usr/local/sbin/kidux-prepare\n"
        "    permissions: '0755'\n    content: |\n"
        + "".join(f"      {line}\n" if line else "\n" for line in script.splitlines())
        + "runcmd:\n"
        '  - [ sh, -c, "/usr/local/sbin/kidux-prepare 2>&1 && echo KIDUX-PREPARED '
        '|| echo KIDUX-NOT-PREPARED" ]\n'
        "power_state:\n  mode: poweroff\n  timeout: 5\n  condition: true\n")
    subprocess.run(["xorriso", "-as", "mkisofs", "-quiet", "-V", "cidata", "-J", "-r",
                    "-o", str(CIDATA.with_suffix(".iso")), str(CIDATA)],
                   check=True, capture_output=True)


def prepare(disk: Path) -> bool:
    """What the tests need, written onto the installed disk by the helper."""
    if not KEY.exists():
        subprocess.run(["ssh-keygen", "-q", "-t", "ed25519", "-N", "", "-f", str(KEY)], check=True)
    helper_seed()
    HELPER.unlink(missing_ok=True)
    subprocess.run(["qemu-img", "create", "-f", "qcow2", "-b", str(BASE), "-F", "qcow2",
                    str(HELPER), "8G"], check=True, capture_output=True)
    log = VM / f"{RUN}-helper.log"
    log.unlink(missing_ok=True)
    accel = ["-enable-kvm", "-cpu", "host"] if os.access("/dev/kvm", os.W_OK) else ["-cpu", "max"]
    helper = subprocess.run(
        ["qemu-system-x86_64", *accel, "-m", "2048", "-smp", "2", "-machine", "q35",
         "-drive", f"file={HELPER},format=qcow2,if=virtio",
         "-drive", f"file={disk},format=qcow2,if=virtio,cache=unsafe",
         "-drive", f"file={CIDATA.with_suffix('.iso')},media=cdrom,readonly=on",
         "-netdev", "user,id=net0", "-device", "virtio-net-pci,netdev=net0",
         "-serial", f"file:{log}", "-display", "none"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=1200)
    HELPER.unlink(missing_ok=True)
    text = log.read_text(errors="replace") if log.exists() else ""
    return report(f"{disk.name} gets the tests' way in, from a helper machine",
                  helper.returncode == 0 and "KIDUX-PREPARED" in text, text[-3000:])


def session_tests(machine: Machine) -> None:
    """The session tests that take a fresh machine through its first start."""
    for name in sorted(path.name for path in (REPO / "tests" / "session").glob("0[2-5]-*.py")):
        print(f"--- {name}", flush=True)
        spec = importlib.util.spec_from_file_location(name[:-3].replace("-", "_"),
                                                      REPO / "tests" / "session" / name)
        test = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(test)
        if test.run(machine) is False:
            report(f"{name} stopped the run", False)
            return


def first_start_shown(machine: Machine, firmware: str, name: str) -> bool:
    """The installed system started, without the image, to the first start's
    wizard: its language buttons, after the boot splash."""
    reached = machine.showing(BUTTON, FIRST_BUTTON, share=0.8, seconds=300)
    picture = machine.screenshot(name)
    return report(f"{firmware}: the installed system starts to Kidux's first start", reached,
                  str(picture))


def secure_boot_on() -> bool:
    """Whether the machine says it started with Secure Boot: the last byte
    of the firmware's SecureBoot variable."""
    value = ssh("od -An -tu1 /sys/firmware/efi/efivars/SecureBoot-8be4df61-93ca-11d2-aa0d-00e098032b8c"
                ).stdout.split()
    return bool(value) and value[-1] == "1"


def main(argv: list[str]) -> int:
    images = sorted((REPO / "build" / "image").glob("kidux-*-amd64.iso"),
                    key=lambda path: path.stat().st_mtime)
    iso = Path(argv[1]) if len(argv) > 1 else (images[-1] if images else None)
    if iso is None or not iso.exists():
        print("tests/run install: no image; ci/build-image.sh makes one", file=sys.stderr)
        return 1
    print(f"==> {iso.name}", flush=True)
    for old in [*VM.glob(f"{RUN}-[0-9][0-9]-*.png"), *VM.glob(f"{RUN}-en-[0-9][0-9]-*.png")]:
        old.unlink()
    machine = Machine()
    try:
        # UEFI: installed, prepared, started, and its first start tested.
        if install(machine, iso, DISK, "uefi", "uefi-") and prepare(DISK):
            work = VM / f"{RUN}-work.qcow2"
            subprocess.run(["qemu-img", "create", "-f", "qcow2", "-b", str(DISK), "-F", "qcow2",
                            str(work)], check=True, capture_output=True)
            qemu(machine, work, "uefi")
            if report("the installed system answers the tests", wait(up, 300, 3),
                      sessionlib.CONSOLE.read_text(errors="replace")[-2000:]):
                version = ssh("dpkg-query -W -f '${Version}' kidux-base").stdout
                left = ssh("dpkg-query -W -f '${Package} ${db:Status-Status}\\n' kidux-installer "
                           "calamares 'live-*' 2>/dev/null | grep ' installed$'").stdout
                report("it is the image's Kidux, with no installer and no live system left",
                       bool(version) and f"kidux-{version}-" in iso.name and not left,
                       f"{version}\n{left}")
                report("the system's top folder is root's, as every system file is",
                       ssh("stat -c %U:%G:%a /").stdout.strip() == "root:root:755"
                       and not ssh("find / -xdev -maxdepth 2 ! -user root ! -path '/home*' "
                                   "! -path '/tmp*' -print -quit").stdout.strip(),
                       ssh("stat -c '%U:%G:%a %n' / /usr /etc").stdout)
                report("the system and /home are partitions of their own",
                       ssh("findmnt -n -o SOURCE /home").stdout.strip()
                       != ssh("findmnt -n -o SOURCE /").stdout.strip(),
                       ssh("findmnt -n -o SOURCE,TARGET / /home /boot/efi").stdout)
                report("the computer's name is the installer's suggestion",
                       ssh("hostname").stdout.strip() == "kidux", ssh("hostname").stdout)
                for tool in ("kidux-as", "kidux-toplevels"):
                    sessionlib.copy(sessionlib.SEED_SOURCE / "tools" / tool, f"/usr/local/bin/{tool}")
                session_tests(machine)
            power_off(machine)
            work.unlink(missing_ok=True)

            # The disk as the installer left it, under Secure Boot.
            work = VM / f"{RUN}-work.qcow2"
            subprocess.run(["qemu-img", "create", "-f", "qcow2", "-b", str(DISK), "-F", "qcow2",
                            str(work)], check=True, capture_output=True)
            qemu(machine, work, "secure")
            if first_start_shown(machine, "Secure Boot", "secure-first-start"):
                report("Secure Boot: the firmware says it is on", wait(up, 120, 3) and secure_boot_on(),
                       ssh("od -An -tu1 /sys/firmware/efi/efivars/SecureBoot-*").stdout)
            power_off(machine)
            work.unlink(missing_ok=True)

        # The image under Secure Boot, to its installer.
        empty = VM / f"{RUN}-empty.qcow2"
        fresh_disk(empty)
        qemu(machine, empty, "secure", iso)
        shown = on_step(machine, "welcome", 300)
        report("Secure Boot: the image starts the installer",
               shown, str(machine.screenshot("secure-installer")))
        power_off(machine)
        empty.unlink(missing_ok=True)

        # A BIOS: installed, and started to the first start.
        if install(machine, iso, BIOS_DISK, "bios", "bios-"):
            qemu(machine, BIOS_DISK, "bios")
            first_start_shown(machine, "bios", "bios-first-start")
            power_off(machine)
        BIOS_DISK.unlink(missing_ok=True)

        # The boot menu's English entry under UEFI, for the English
        # pictures, on a machine whose pictures are its own, and kept,
        # prepared as the Spanish one is, for the English trial image.
        sessionlib.RUN = f"{RUN}-en"
        sessionlib.USER = ADMINS["en"]
        if install(machine, iso, ENGLISH_DISK, "uefi", "uefi-", "en"):
            prepare(ENGLISH_DISK)
        sessionlib.RUN, sessionlib.USER = RUN, ADMINS["es"]
    finally:
        power_off(machine)
    return sessionlib.failures


if __name__ == "__main__":
    sys.exit(main(sys.argv))
