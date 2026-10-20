# Kidux's image, its installer, and the images to try it in

How the installable image is made, tested and published, and the images
to try Kidux in an emulator that are made from it (D116). What the image
is for an adult is in the user guide, section 2, and in `docs/en/try.md`;
what it was designed to be is `installer.md`.

## 1. What the image is

One hybrid ISO, `kidux-<version>-<date>-amd64.iso`, which starts a
computer with UEFI, with or without Secure Boot, or with a BIOS, from a USB
stick or as a CD. `<version>` is the version of `kidux-base` it carries,
which is Kidux's version; `<date>` is the date of the archive suite it was
built from. It is about 750 MB.

It starts a live system, which is a Kidux machine already, with
Kidux's installer in place of the sign-in screen. The installer copies that
system to the disk, so that an installed Kidux is exactly a Kidux installed
on Debian as the user guide's section 2 does it: Debian 13 with
`kidux-base` and its recommends, Kidux's archive and key, the system and
`/home` on partitions of their own, and the administrator's account. The
first start, the wizard and all, is the same.

What the image holds:

| Path | What it is |
|---|---|
| `.disk/info` | what the image is, which GRUB looks for to find itself |
| `live/vmlinuz`, `live/initrd.img` | the live system's kernel, and its initramfs with `live-boot` |
| `live/filesystem.squashfs` | the live system |
| `pool/grub-pc_*.deb` | GRUB for a disk that starts with a BIOS (section 3) |
| `boot/grub/grub.cfg` | the boot menu, `image/grub/grub.cfg` |
| `boot/grub/i386-pc/` | GRUB for a BIOS, as an El Torito image, and its modules |
| `boot/grub/efi.img` | the EFI system partition: Debian's signed shim and CD GRUB |
| `EFI/boot/` | the same two, on the image itself |

The boot menu has *Instalar Kidux* first, the default after ten seconds,
then *Install Kidux*, and the two again with `nomodeset` under *Gráficos
seguros / Safe graphics*. Each entry passes `boot=live`, `kidux.live`, and
the installer's language and keyboard as `kidux.lang=` and
`kidux.keyboard=`.

## 2. The recipe and the build

`image/` holds the recipe:

- `image/packages`: what goes into the live system besides what
  mmdebstrap's `standard` variant gives: Kidux's keyring, apt source and
  `kidux-base`; the kernel, `sudo` and the console's keyboard; `live-boot`;
  GRUB for both ways a computer starts, with the signed GRUB and the shim;
  and `kidux-installer`.
- `image/grub/grub.cfg`: the boot menu.
- `image/sources`: Debian's sources for the installed system, deb822.

`ci/build-image.sh [testing|stable]` builds it into `build/image/`, without
root:

1. The suite's `Release` date becomes `SOURCE_DATE_EPOCH`, and its
   `kidux-base` the image's version.
2. `mmdebstrap --mode=unshare --variant=standard` makes the live system
   from Debian trixie and the local archive's suite, recommends included,
   as apt installs them on Debian. Its hooks download `grub-pc` into the
   image's `pool/`, set Debian's sources, the hostname `kidux` and an
   empty machine-id, empty apt's lists and caches and AppArmor's cache,
   take the kernel and its initramfs out for the image's own boot and
   leave no initramfs in the live system, since the installer makes the
   installed system's, and write the package list beside the image
   (`<name>.packages`). Downloads are kept in `build/image/cache/`.
3. Its tar output goes straight into `sqfstar`, so that the files keep
   their owners without root, the root directory given to root since the
   tar has no entry for it, compressed with xz, its x86 filter and blocks
   of a mebibyte, every time clamped to the suite's.
4. GRUB's El Torito image for a BIOS (`grub-mkimage`), the EFI system
   partition (`mkfs.fat` with a fixed serial, `mcopy` with the times kept),
   every file touched to the suite's time, and `xorriso` makes the hybrid
   image, with `<name>.iso.sha256` beside it.

It takes about three minutes on the release machine once the cache is
warm. The same suite gives the same bytes: two builds in a row
give identical images.

The release machine needs `mmdebstrap`, `squashfs-tools`, `xorriso`,
`mtools`, `dosfstools`, `grub-pc-bin` and `grub-efi-amd64-bin`, and for
the tests `ovmf` and `qemu-utils` (packaging.md, "Setting up a machine to
build on").

## 3. The installer: `kidux-installer`

Calamares 3.3 from trixie, with Kidux's settings and look, in a package
like every other. It is installed in the live system alone, and the
installer takes it off the installed system.

- **Starting it.** A drop-in for `greetd.service` runs
  `kidux-installer-greetd`, which, when the kernel's command line has
  `kidux.live`, starts greetd with the installer's configuration:
  `kidux-installer-session` on terminal 7, which sets the language and
  keyboard the boot menu chose and runs Calamares full screen under `cage`.
  Without `kidux.live`, greetd starts Kidux's own sign-in screen. A drop-in
  for `kidux-firstboot.service` keeps the first start out of the live
  system.
- **Its pages**: welcome, location, keyboard, disk, the administrator,
  summary; then the installation, and the end, with *Restart now* ticked.
  The welcome page asks for 32 GB of disk and 1.8 GB of memory.
- **The disk**: erased, with no manual layout. GPT and a 512 MiB EFI
  system partition under UEFI, MBR under a BIOS; the system, `kidux`, ext4,
  40 % of the disk between 16 and 64 GB; and `/home`, `kidux-home`, ext4,
  the rest; swap as a file.
- **The administrator**: a name, from which the login is suggested, the
  computer's name, `kidux` suggested, and a password, with `sudo` and no
  root password, as the Debian installer makes it. The *log in
  automatically* box is Calamares' own and does nothing here, since the
  installer configures no display manager: Kidux's sign-in screen is
  always the one.
- **The initramfs, then GRUB.** After the packages module, Calamares'
  initramfs module makes the installed system's initramfs, which the
  image does not carry, so that GRUB's menu, written next, finds it.
  `kidux-installer-grub` runs before Calamares' boot loader module. Under UEFI it tells debconf to keep GRUB on the removable path
  too; under a BIOS it replaces `grub-efi-amd64` with `grub-pc` from the
  image's `pool/` with dpkg, the disk preseeded as its install device, so
  that Debian's GRUB updates later put GRUB on the disk the right way.
  After the boot loader module, `kidux-installer-efi` puts the shim and
  the signed GRUB on the removable path, `EFI/BOOT/BOOTX64.EFI`, so that a
  computer that forgets its boot entries, and every emulator, still starts
  the disk, under Secure Boot too.
- **What it removes**: the packages module takes off `kidux-installer`,
  `calamares` and the live boot packages, and apt's autoremove what they
  alone brought.

Its unit tests check that every setting file parses and names only
modules Calamares has, and the scripts' behaviour with stand-ins.

## 4. The install test: `tests/run install`

`tests/lib/install-vm.py` takes the newest image in `build/image/`:

1. Under UEFI, a machine with an empty 40 GB disk starts the image; the
   test waits for the boot menu, takes its Spanish entry, and takes the
   installer through its pages by keyboard, waiting at each for the
   sidebar to mark it, with the administrator Ana, `ana`; then waits for
   the end, failing at once if the installer's error replaces its pages.
2. A helper machine, the session machines' Debian, mounts the installed
   disk and writes onto it what a session machine's cloud-init gives:
   an SSH server with the tests' key, sudo without a password for `ana`,
   whom the tests reach the machine as, the development archive's
   address, and the test machine's usage identifier (section 7).
3. The installed system starts from its disk, on a copy, and answers over
   SSH. The test checks that it is the image's Kidux, with no installer or
   live system left, that the system's top folders are root's, that the
   system and `/home` are partitions of their own and that the computer
   is called `kidux`; then the session tests 02
   to 05 run on it, which take a fresh machine through its boot, its first
   start, a family and its closed doors.
4. The installed disk, on another copy, starts under Secure Boot (OVMF
   with Microsoft's keys), to the first start, and the firmware says
   Secure Boot is on; the image starts its installer under Secure Boot
   too.
5. Under a BIOS, the image installs again, and the disk starts to the
   first start.
6. Under UEFI once more, from the boot menu's English entry, with the
   administrator Anna, for the English pictures alone.

Every picture is `build/vm/install-NN-<screen>.png`, the English
installation's `build/vm/install-en-NN-<screen>.png`; the boot menu and
the installer's pages that the user guide shows are listed in
`tests/lib/doc-screenshots.txt`, and the release run copies them, as it
copies the session's. The disk of step 1 is kept as
`build/vm/install.qcow2`, prepared and not yet started, for the trial
images.

## 5. The trial images

`ci/build-trial-image.py [es|en]` makes, for each language, from a copy
of `build/vm/install.qcow2`:

1. The machine starts, and through the daemon, as the adult panel does it,
   gets the trial's family: the adult password `kidux`; Leo, password
   `leo`, with no limit of time; the machine and Leo in the image's
   language and keyboard; and BASIC, Tux Typing, Scratch, GCompris,
   Simulations and Kig, installed from the public archive and switched on
   for Leo.
2. Its usage identifier becomes the trial's (section 7).
3. What the tests added goes: the SSH server, the key, sudo without a
   password, the test machine's identifier and the development archive's
   address. The administrator's password, `ana`'s, becomes `kidux`. Apt's
   caches and the journal are emptied, the free space is trimmed, which
   the virtual disk passes on to the image file, and the machine shuts
   down.
4. `qemu-img` converts the disk: `<name>-trial-<language>.qcow2`,
   compressed, for QEMU and UTM; and `<name>-trial-<language>.ova`, a
   streamOptimized VMDK in a plain OVF 1.0 package with a SHA-256
   manifest: two processors, 4 GB of memory, the disk on SATA and NAT
   networking. OVF cannot say that the machine starts with UEFI, so the
   page that offers the images has the visitor tick *Enable EFI* in
   VirtualBox.
5. Each `.qcow2` is started with the very QEMU command the page gives,
   without writing to it: the sign-in screen must come up with Leo, and
   Leo must get their screen, both photographed as
   `build/vm/trial-<language>-NN-<screen>.png`, which the page shows from
   a release run.

A trial is Kidux whole: it signs in, locks, counts time and updates
itself from `apt.kidux.org` like any Kidux machine.

## 6. Publishing: `ci/publish-image.sh`

The images are published at `https://iso.kidux.org`, the hosting's folder
`iso` beside `apt`, over the same SFTP and credentials as the archive.
`ci/publish-image.sh [<name>]` takes one build's files, the newest unless
named:

1. Writes `<name>.SHA256SUMS` and signs it, `<name>.SHA256SUMS.sign`,
   with the archive's key for a release, and the development key for a
   `~dev` build.
2. Uploads each file under another name and renames it into place, the
   images first and the sums last.
3. Writes `.htaccess`, whose redirects give the names without a version:
   `kidux-amd64.iso`, `kidux-trial-<language>.qcow2` and `.ova`,
   `SHA256SUMS` and `SHA256SUMS.sign` lead to the newest release's files,
   which the website and the user guide link to; `kidux-dev-…` lead to the
   newest `~dev` build's, for trying.
4. Removes every image neither of the two holds.
5. Checks what the world sees over HTTPS: the sums identical and their
   signature good, each image's size and its first and last mebibyte, and
   each name without a version leading to its file.

A `~dev` build's images may be published at any hour, since nothing links
to them. A release's go after `ci/publish-public.sh`, in `ci/push.sh
--then-publish`'s chain (packaging.md, "The public archive").

## 7. Counting them

The hosting writes `iso.kidux.org`'s requests to the same logs as
`apt.kidux.org`'s, and `ci/usage.py` keeps both. On the usage page an
image's download is one address fetching one file on one day, a whole
answer or a part of one, however many parts a browser asks for: a table
by day, week, month and since the first day, of the installer's downloads
and the trial images', and the trials run; each file with its downloads;
and the *Images* view, by day and file.

Usage identifiers say which machines are not families':

| Identifier | Machine |
|---|---|
| `00…01` | the Spanish session machine |
| `00…02` | the English session machine |
| `00…03` | the acceptance machine |
| `00…04` | the install test's machine |
| `00…05` | the machine of `ci/vm/try.sh` |
| `ff…01` | the Spanish trial image, every copy of it |
| `ff…02` | the English trial image, every copy of it |

A test machine's identifier is sixteen zeros and its number, sent by
`/etc/apt/apt.conf.d/99kidux-test-machine` from its first boot
(`sessionlib.test_identifier`), and never counted. A trial's is sixteen
f's and its number, in its `config.toml`, listed in
`ci/usage-trial-ids.txt`: since every copy shares it, a trial is counted
apart from the families' machines, one for each address it looks for
updates from.
