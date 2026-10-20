#!/usr/bin/python3
"""Build the images to try Kidux in an emulator, from the installed disk.

    ci/build-trial-image.py [es|en …]       both languages unless named

docs/dev/image.md, section 5. The disk tests/run install left,
build/vm/install.qcow2, is Kidux installed from the image by its own
installer and not yet started. A copy of it starts once more, and through
the daemon, as the adult panel does it, gets the trial's family: the adult
password `kidux`, one child, Leo, password `leo`, and the modules
TRIAL_MODULES names, installed from the archive and switched on for Leo.
The machine speaks the image's language, and its usage identifier is the
trial's own (ci/usage-trial-ids.txt): sixteen f's and 01 for Spanish, 02
for English, which every copy shares, so that the archive's usage page
counts the trials apart from the families' machines. Then what the tests
added to the disk goes (tests/lib/install-vm.py: the SSH server and its
key, sudo without a password, the test machine's identifier and the
development archive's address), the administrator's password becomes
`kidux` too, Leo has no limit of time, for a trial, the free space is given back, and the machine is shut down.

Each qcow2 is then started as docs/en/try.md starts it, with QEMU's
command given there, changing nothing in it: the sign-in screen must come
up with Leo, and Leo must get their screen, both photographed as
build/vm/trial-<language>-NN-<screen>.png.

Out of it come, into build/image/ beside the installer, with the name the
installer has and `-trial-<language>`:

    .qcow2   compressed, for QEMU, and for UTM on a Mac
    .ova     a VMDK in an OVF package, for VirtualBox

Without root: the virtual machine is QEMU's, the conversions qemu-img's.
"""

import hashlib
import importlib.util
import os
import subprocess
import sys
import tarfile
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "tests" / "lib"))
spec = importlib.util.spec_from_file_location("install_vm", REPO / "tests" / "lib" / "install-vm.py")
install_vm = importlib.util.module_from_spec(spec)
spec.loader.exec_module(install_vm)
sessionlib = install_vm.sessionlib

OUT = Path(os.environ.get("KIDUX_IMAGE_DIR", REPO / "build" / "image"))
DISK = install_vm.DISK
#: The trial's family, and its passwords, which the page that offers the
#: images says (docs/en/try.md).
ADULT_PASSWORD = "kidux"
CHILD, CHILD_NAME, CHILD_PASSWORD = "leo", "Leo", "leo"
#: What the trial shows, decided by the owner (phase-2-plan.md, section 2):
#: programming, typing, play, and two of the sciences, a web one and a Qt one.
TRIAL_MODULES = ("basic", "tuxtype", "scratch", "gcompris", "simulations", "kig")
LANGUAGES = {
    "es": {"locale": "es_ES.UTF-8", "keyboard": "es", "number": 1},
    "en": {"locale": "en_US.UTF-8", "keyboard": "us", "number": 2},
}


def trial_identifier(number: int) -> str:
    return "f" * 30 + f"{number:02x}"


def step(name: str, command: str, timeout: float = 1800) -> bool:
    result = sessionlib.root(command, timeout=timeout)
    ok = result.returncode == 0
    print(("    " if ok else "    FAILED: ") + name, flush=True)
    if not ok:
        print(result.stdout[-2000:] + result.stderr[-2000:], flush=True)
    return ok


def as_adult(arguments: str) -> str:
    return f"KIDUX_AS_ADULT={ADULT_PASSWORD} /usr/local/bin/kidux-as {arguments}"


def ova(qcow2: Path, name: str) -> Path:
    """The disk as a VMDK in an OVF package, with its manifest."""
    work = OUT / f"{name}.ova-work"
    work.mkdir(exist_ok=True)
    vmdk = work / f"{name}-disk1.vmdk"
    vmdk.unlink(missing_ok=True)
    subprocess.run(["qemu-img", "convert", "-O", "vmdk", "-o", "subformat=streamOptimized",
                    str(qcow2), str(vmdk)], check=True)
    capacity = int(subprocess.run(["qemu-img", "info", "--output=json", str(qcow2)],
                                  capture_output=True, text=True, check=True)
                   .stdout.split('"virtual-size":')[1].split(",")[0])
    ovf = work / f"{name}.ovf"
    ovf.write_text(OVF.format(name=name, disk=vmdk.name, size=vmdk.stat().st_size,
                              capacity=capacity))
    manifest = work / f"{name}.mf"
    manifest.write_text("".join(
        f"SHA256({path.name})= {hashlib.sha256(path.read_bytes()).hexdigest()}\n"
        for path in (ovf, vmdk)))
    target = OUT / f"{name}.ova"
    target.unlink(missing_ok=True)
    with tarfile.open(target, "w", format=tarfile.USTAR_FORMAT) as package:
        for path in (ovf, manifest, vmdk):
            info = package.gettarinfo(str(path), arcname=path.name)
            info.uid = info.gid = 0
            info.uname = info.gname = ""
            info.mtime = int(os.environ.get("SOURCE_DATE_EPOCH", time.time()))
            with path.open("rb") as data:
                package.addfile(info, data)
    for path in (ovf, manifest, vmdk):
        path.unlink()
    work.rmdir()
    return target


def tried(qcow2: Path, language: str) -> bool:
    """The image started as the page on trying Kidux says, without writing
    to it: the sign-in screen with Leo, then Leo's own screen."""
    sessionlib.RUN = f"trial-{language}"
    sessionlib.MONITOR.unlink(missing_ok=True)
    machine = sessionlib.Machine()
    machine.process = subprocess.Popen(
        ["qemu-system-x86_64", "-enable-kvm", "-cpu", "host", "-m", "4096", "-smp", "2",
         "-machine", "q35", "-bios", "/usr/share/ovmf/OVMF.fd",
         "-drive", f"file={qcow2},if=virtio", "-vga", "none", "-device", "VGA,xres=1280,yres=800",
         "-device", "qemu-xhci", "-device", "usb-tablet", "-nic", "user,model=virtio-net-pci",
         "-snapshot", "-display", "none", "-monitor", f"unix:{sessionlib.MONITOR},server,nowait"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    sessionlib.wait(sessionlib.MONITOR.exists, 10, 0.2)
    try:
        # The sign-in screen's cream, and a while for the boot splash,
        # which is cream too, to give way to it.
        shown = machine.showing(sessionlib.CREAM, (0, 0, 1, 0.2), share=0.9, seconds=240)
        time.sleep(30)
        greeter = machine.settled()
        machine.screenshot("sign-in")
        machine.key("ret")                   # Leo, the only picture, has the focus
        time.sleep(3)
        machine.type(CHILD_PASSWORD + "\n")
        time.sleep(30)
        signed_in = sessionlib.difference(greeter, machine.settled()) > 0.2
        picture = machine.screenshot("leo")
        print(("    " if shown and signed_in else "    FAILED: ")
              + f"started as the page says, Leo signs in: {picture.name}", flush=True)
        return shown and signed_in
    finally:
        install_vm.power_off(machine)


def build(language: str, name: str) -> bool:
    speaks = LANGUAGES[language]
    print(f"==> {name}-trial-{language}", flush=True)
    work = sessionlib.VM / f"trial-{language}.qcow2"
    work.unlink(missing_ok=True)
    subprocess.run(["qemu-img", "create", "-f", "qcow2", "-b", str(DISK), "-F", "qcow2",
                    str(work)], check=True, capture_output=True)
    machine = sessionlib.Machine()
    install_vm.qemu(machine, work, "uefi")
    try:
        if not sessionlib.wait(sessionlib.up, 300, 3):
            print("    FAILED: the machine never answered", flush=True)
            return False
        sessionlib.copy(sessionlib.SEED_SOURCE / "tools" / "kidux-as", "/usr/local/bin/kidux-as")
        locale, keyboard = speaks["locale"], speaks["keyboard"]
        steps = [
            ("the machine's language and keyboard",
             f"grep -qx '{locale} UTF-8' /etc/locale.gen || echo '{locale} UTF-8' >> /etc/locale.gen; "
             f"locale-gen >/dev/null && localectl set-locale LANG={locale} "
             f"&& localectl set-x11-keymap {keyboard} && setupcon --save-only 2>/dev/null; true"),
            ("the family: the adult password and Leo",
             f"runuser -u debian -- env {as_adult(f'family {CHILD} {CHILD_NAME} {CHILD_PASSWORD}')}"),
            ("Kidux in the machine's language, set up",
             "runuser -u debian -- env " + as_adult(f"set-config default_language '\"{locale}\"'")
             + " && runuser -u debian -- env " + as_adult(f"set-config default_keyboard '\"{keyboard}\"'")
             + " && runuser -u debian -- env " + as_adult("set-config setup_complete true")),
            ("Leo in the machine's language, with no limit of time to try it in",
             "runuser -u debian -- env " + as_adult(f"set-profile {CHILD} language {locale}")
             + " && runuser -u debian -- env " + as_adult(f"set-profile {CHILD} keyboard {keyboard}")
             + " && runuser -u debian -- env " + as_adult(f"set-policy {CHILD} unlimited 0")),
        ]
        for module in TRIAL_MODULES:
            steps.append((f"{module}, installed and switched on for Leo",
                          "runuser -u debian -- env " + as_adult(f"install {module}")
                          + " | grep -q '^installed ' && runuser -u debian -- env "
                          + as_adult(f"enable {CHILD} {module} on")))
        identifier = trial_identifier(speaks["number"])
        steps += [
            ("the trial's usage identifier",
             f"sed -i 's/^apt_statistics_id = .*/apt_statistics_id = \"{identifier}\"/' "
             f"/home/.kidux/config.toml && grep -q '{identifier}' /home/.kidux/config.toml "
             "&& systemctl restart kidux-daemon && sleep 3 "
             f"&& grep -q 'Kidux/{identifier}' /etc/apt/apt.conf.d/61kidux-statistics"),
            ("the administrator's password, the trial's",
             f"echo 'debian:{ADULT_PASSWORD}' | chpasswd"),
            ("what only the tests needed, gone, and the free space given back",
             "rm -f /etc/sudoers.d/90-kidux-tests /etc/apt/apt.conf.d/99kidux-test-machine "
             "/etc/apt/apt.conf.d/99kidux-vm-lean /usr/local/bin/kidux-as /usr/local/bin/kidux-toplevels "
             "&& sed -i '/kidux.local/d' /etc/hosts && rm -rf /home/debian/.ssh "
             "&& DEBIAN_FRONTEND=noninteractive apt-get purge -y openssh-server >/dev/null "
             "&& apt-get autoremove --purge -y >/dev/null && apt-get clean "
             "&& rm -rf /var/lib/apt/lists/* && journalctl --rotate && journalctl --vacuum-time=1s "
             "&& fstrim -av && sync "
             # The last thing the tests' way in can ask: the machine shuts
             # down a moment after this answer, since no way in is left.
             "&& systemd-run --quiet --on-active=5 /usr/bin/systemctl poweroff"),
        ]
        for name_, command in steps:
            if not step(name_, command):
                return False
        machine.process.wait(300)
    finally:
        install_vm.power_off(machine)
    print("    converting", flush=True)
    qcow2 = OUT / f"{name}-trial-{language}.qcow2"
    qcow2.unlink(missing_ok=True)
    subprocess.run(["qemu-img", "convert", "-c", "-O", "qcow2", str(work), str(qcow2)], check=True)
    package = ova(qcow2, f"{name}-trial-{language}")
    work.unlink(missing_ok=True)
    for path in (qcow2, package):
        print(f"    {path.name}: {path.stat().st_size / 2**30:.2f} GiB", flush=True)
    return tried(qcow2, language)


#: The OVF package's descriptor, plain OVF 1.0, which every importer
#: reads: two processors, 4 GB of memory, the disk on SATA and a NAT
#: network. OVF cannot say that the machine starts with UEFI, which the
#: page on trying Kidux has the visitor tick.
OVF = """<?xml version="1.0"?>
<Envelope ovf:version="1.0" xml:lang="en-US" xmlns="http://schemas.dmtf.org/ovf/envelope/1" xmlns:ovf="http://schemas.dmtf.org/ovf/envelope/1" xmlns:rasd="http://schemas.dmtf.org/wbem/wscim/1/cim-schema/2/CIM_ResourceAllocationSettingData" xmlns:vssd="http://schemas.dmtf.org/wbem/wscim/1/cim-schema/2/CIM_VirtualSystemSettingData" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:vbox="http://www.virtualbox.org/ovf/machine">
  <References>
    <File ovf:id="file1" ovf:href="{disk}" ovf:size="{size}"/>
  </References>
  <DiskSection>
    <Info>The disk</Info>
    <Disk ovf:capacity="{capacity}" ovf:diskId="vmdisk1" ovf:fileRef="file1" ovf:format="http://www.vmware.com/interfaces/specifications/vmdk.html#streamOptimized"/>
  </DiskSection>
  <NetworkSection>
    <Info>The network</Info>
    <Network ovf:name="NAT">
      <Description>The computer's own connection</Description>
    </Network>
  </NetworkSection>
  <VirtualSystem ovf:id="{name}">
    <Info>Kidux, to try in an emulator</Info>
    <ProductSection>
      <Info>The product</Info>
      <Product>Kidux</Product>
      <Vendor>Kidux</Vendor>
      <ProductUrl>https://kidux.org</ProductUrl>
    </ProductSection>
    <OperatingSystemSection ovf:id="96">
      <Info>The operating system</Info>
      <Description>Debian_64</Description>
      <vbox:OSType ovf:required="false">Debian_64</vbox:OSType>
    </OperatingSystemSection>
    <VirtualHardwareSection>
      <Info>The machine</Info>
      <System>
        <vssd:ElementName>Virtual Hardware Family</vssd:ElementName>
        <vssd:InstanceID>0</vssd:InstanceID>
        <vssd:VirtualSystemIdentifier>{name}</vssd:VirtualSystemIdentifier>
        <vssd:VirtualSystemType>virtualbox-2.2</vssd:VirtualSystemType>
      </System>
      <Item>
        <rasd:Caption>2 virtual CPU</rasd:Caption>
        <rasd:ElementName>2 virtual CPU</rasd:ElementName>
        <rasd:InstanceID>1</rasd:InstanceID>
        <rasd:ResourceType>3</rasd:ResourceType>
        <rasd:VirtualQuantity>2</rasd:VirtualQuantity>
      </Item>
      <Item>
        <rasd:AllocationUnits>MegaBytes</rasd:AllocationUnits>
        <rasd:Caption>4096 MB of memory</rasd:Caption>
        <rasd:ElementName>4096 MB of memory</rasd:ElementName>
        <rasd:InstanceID>2</rasd:InstanceID>
        <rasd:ResourceType>4</rasd:ResourceType>
        <rasd:VirtualQuantity>4096</rasd:VirtualQuantity>
      </Item>
      <Item>
        <rasd:Address>0</rasd:Address>
        <rasd:Caption>sataController0</rasd:Caption>
        <rasd:ElementName>sataController0</rasd:ElementName>
        <rasd:InstanceID>3</rasd:InstanceID>
        <rasd:ResourceSubType>AHCI</rasd:ResourceSubType>
        <rasd:ResourceType>20</rasd:ResourceType>
      </Item>
      <Item>
        <rasd:AddressOnParent>0</rasd:AddressOnParent>
        <rasd:Caption>disk1</rasd:Caption>
        <rasd:ElementName>disk1</rasd:ElementName>
        <rasd:HostResource>/disk/vmdisk1</rasd:HostResource>
        <rasd:InstanceID>4</rasd:InstanceID>
        <rasd:Parent>3</rasd:Parent>
        <rasd:ResourceType>17</rasd:ResourceType>
      </Item>
      <Item>
        <rasd:AutomaticAllocation>true</rasd:AutomaticAllocation>
        <rasd:Caption>Ethernet adapter on 'NAT'</rasd:Caption>
        <rasd:Connection>NAT</rasd:Connection>
        <rasd:ElementName>Ethernet adapter on 'NAT'</rasd:ElementName>
        <rasd:InstanceID>5</rasd:InstanceID>
        <rasd:ResourceSubType>E1000</rasd:ResourceSubType>
        <rasd:ResourceType>10</rasd:ResourceType>
      </Item>
    </VirtualHardwareSection>
  </VirtualSystem>
</Envelope>
"""


def main(argv: list[str]) -> int:
    languages = argv[1:] or list(LANGUAGES)
    if not DISK.exists():
        print(f"{argv[0]}: no {DISK}; tests/run install leaves it", file=sys.stderr)
        return 1
    images = sorted(OUT.glob("kidux-*-amd64.iso"), key=lambda path: path.stat().st_mtime)
    if not images:
        print(f"{argv[0]}: no installer in {OUT}", file=sys.stderr)
        return 1
    name = images[-1].name[:-len("-amd64.iso")]
    # Its own port, monitor and files, so that it never meets a machine of
    # the tests.
    sessionlib.SSH_PORT = install_vm.SSH_PORT = 2225
    sessionlib.RUN = install_vm.RUN = "trial"
    sessionlib.MONITOR = sessionlib.VM / "trial-monitor.sock"
    sessionlib.CONSOLE = sessionlib.VM / "trial-console.log"
    failed = 0
    for language in languages:
        started = time.monotonic()
        if build(language, name):
            print(f"    built in {(time.monotonic() - started) / 60:.0f} minutes", flush=True)
        else:
            failed += 1
    return failed


if __name__ == "__main__":
    sys.exit(main(sys.argv))
