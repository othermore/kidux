# Phase 2: the installable image, and images to try Kidux in an emulator

The plan for the image the user documents say is coming (D81), built and
published with every release so that it always installs the current
versions, and for the ready-made images someone runs in an emulator to
see Kidux before installing it. `installer.md` says what the image has to
be for the adult who uses it; this says how it is made, tested and
published, in steps that each leave something working.

## 1. What is decided here

- **The image is built on the release machine, not on GitHub.** The
  owner does not want the project to depend on GitHub (D39), its runners
  are few and the hours rule binds them (D114); a build that needs root
  there needs none here. `ci/build-image.sh` builds it, the battery tests
  it, the release publishes it.
- **Without root.** `live-build` wants root for its chroots. The image is
  made the way the packages are: a root file system by `mmdebstrap
  --mode=unshare` from trixie plus Kidux's archive, packed with
  `mksquashfs`, and a hybrid ISO, UEFI and BIOS, by `grub-mkrescue` and
  `xorriso`, all of it in trixie and all of it runnable by a user. The
  same tree gives the same bytes: `SOURCE_DATE_EPOCH` from the release,
  `mksquashfs -mkfs-time`, `xorriso` with fixed dates, as `tests/run
  reproducible` will check.
- **What the ISO holds.** Debian trixie with every package a Kidux
  machine installs (the dependencies of `kidux-base`, Chromium among
  them), `firmware-linux` (D74), the signed shim and GRUB so that UEFI
  machines with Secure Boot start it, Plymouth with Kidux's splash, and
  Kidux's own packages from `stable` as they are the day it is built. No
  learning module: the adult panel installs them from the archive, as on
  a machine installed on Debian. Under two gigabytes if the sizes allow
  it, which the first build will say.
- **The live system starts the installer.** The first image boots to
  Calamares, full screen, in the languages Kidux has, with Kidux's
  branding; the live session that is the kiosk itself, to try before
  installing, is a later step (section 6). Calamares and
  `calamares-settings-debian` are in trixie (3.3.14 and 13.0.13); Kidux's
  settings and branding are a package, `kidux-installer`, in the archive
  like every other, installed in the live system alone and removed by
  Calamares' last module from the system it installs, as Debian's own
  settings have it done.
- **The installed system is a Kidux installed on Debian.** Two
  partitions, the system and `/home`, as the user guide's installation
  on Debian makes; `kidux-base` and Kidux's apt source and keyring from
  the archive; the first start as it is today, the wizard and all. An
  image installs nothing the guide's section 2 does not, so that the two
  ways give the same machine.
- **Named by what it installs.** `kidux-<kidux-base version>-<date>-amd64.iso`,
  the date the release's (`ci/hours.py` dates it, never a hand), with a
  `SHA256SUMS` beside it signed with the production key, and a copy under
  a name without a date, `kidux-amd64.iso`, which the website's download
  button points at. The date is in the name because the image changes
  whenever the packages it carries do, kidux-base's version or not.
- **Published on the project's hosting**, in a folder served as
  `https://iso.kidux.org/` beside `apt.kidux.org`, by
  `ci/publish-image.sh` over the same SFTP, the file first and the sums
  last, verified over HTTPS afterwards. GitHub's releases take no file
  over two gigabytes and the trial images will pass it. The owner creates
  the folder and its address in the hosting's panel, as for `apt`.
- **The trial images come from the installer.** The battery's new install
  test (section 4) installs Kidux from the ISO in a virtual machine and
  keeps the disk; the trial image is that disk with the first start done
  for a demonstration family, converted for each emulator. What a family
  gets and what a visitor tries are then the same bytes, made by the same
  installer.

## 2. What the owner decides

Each has a default this plan works with, to be changed if the owner says
so.

1. **The hosting folder and its address**: `iso.kidux.org`, a folder `iso`
   of the hosting, as `apt.kidux.org` is the folder `apt`. The owner sets
   both up in the panel, with the certificate; nothing can be published
   before.
2. **The trial image's family**: one child, *Leo*, password `leo`, the
   adult password `kidux`, Spanish machine with a second image in
   English; both passwords written on the page that offers the image.
   Modules switched on for the child: Tux Typing and BASIC, which need no
   internet and weigh little; GCompris if the size stays reasonable.
3. **Staging**: the first image installs fresh, erasing the disk; *Reinstall,
   keep my data* and the live kiosk come after it works (section 6).

## 3. The image, step by step

Each step is a commit or a few, with its tests, and a `~dev` round in the
quick loop before the battery.

- **3.1 `kidux-installer`.** A package of Calamares' settings for Kidux:
  `settings.conf` with the sequence (welcome, locale, keyboard, partition,
  users, summary, install, finished), the partition module's layout (`/`
  and `/home`, swap as a file), the branding (name, logo, the product
  pictures from `branding/`, the colours of the style guide, the slide
  shown while it installs), the strings in both languages, the users
  module asking for the administrator account alone (installer.md, 4),
  and the `packages` module's last step removing `kidux-installer`,
  `calamares` and the live packages from the installed system. Its tests
  check every setting file parses and names only modules Calamares has.
- **3.2 `image/`**: the recipe. `image/packages` (what goes in),
  `image/hooks/` (what is set in the root file system: Plymouth, the
  autostart of Calamares in the live session, the apt source and keyring
  for the installed system, the locale list), `image/grub/` (the boot
  menu, in the project's identity: *Install Kidux*, *Install Kidux (safe
  graphics)*, and memory test), and `ci/build-image.sh`, which makes the
  root file system with `mmdebstrap --mode=unshare`, the squashfs, the
  kernel and initrd with `live-boot`, and the ISO with `grub-mkrescue`,
  into `build/image/`. Reproducible: built twice in `tests/run
  reproducible image`, the same bytes.
- **3.3 Boot and install, tested.** `tests/lib/install-vm.py`: a machine
  started from the ISO under OVMF, and once more under BIOS, that boots
  to the installer (a screenshot, compared as the session ones are), and
  under OVMF is taken through Calamares by keyboard and pointer, as the
  session tests drive the panel, to a disk with Kidux on it; the machine
  restarts from the disk, and the session tests 01 to 05, which take a
  fresh machine through its first start, run on it. A new kind,
  `tests/run install`, in the battery after acceptance. Secure Boot is
  tried once by hand on a machine that has it.
- **3.4 The release.** `ci/test-release.sh --release` builds the image
  after the packages are published to testing and before the tests, since
  the ISO carries the packages; the battery builds it from `~dev` builds
  as it builds everything else. `ci/publish-image.sh` after
  `ci/publish-public.sh`, in `ci/push.sh --then-publish`'s chain. The
  image is part of a release from the day it exists: a release with no
  image is not a release.
- **3.5 Documents.** The user guide's *With Kidux's image* written as the
  finished thing (installer.md, sections 1 to 5; the guide loses *coming
  soon* and D81's exception closes), the README and the website
  (`download` in `site/site.toml`, the system requirements already
  there), `docs/dev/image.md` from `installer.md` and this plan's results,
  `packaging.md`'s release order, the roadmap, and D116 in the log.

## 4. The trial images

- **4.1 From the install test's disk.** `ci/build-trial-image.sh` takes
  the disk the install test left, starts it once more under QEMU with the
  test harness, answers the first start as the session tests do (the
  demonstration family of section 2), installs the chosen modules through
  the daemon, shuts it down, and converts the disk: `qcow2` for QEMU and
  UTM, `vmdk` inside an OVA for VirtualBox and VMware, each compressed,
  with `SHA256SUMS`. One of each per language the image has.
- **4.2 The page.** `docs/en/try.md` and `docs/es/try.md`: what the image
  is, the family inside it and its passwords, and for each system what to
  install and what to click: QEMU on Linux (one command, given whole),
  VirtualBox on Windows (import the OVA, start), UTM on macOS (import the
  qcow2; on an Apple Silicon Mac Kidux runs under emulation of a 64-bit
  PC and is slow, said plainly), VirtualBox on an Intel Mac. The website
  gets a *Try it* button beside *Download*. A screen of 1280 by 800, which
  the emulators give by default or by one setting, said where it is not.
- **4.3 Tested.** The battery boots the `qcow2` once and checks that the
  sign-in screen comes up with the demonstration child, and that the
  modules switched on open; the OVA is imported into VirtualBox by hand on
  the owner's Mac once, and its import checked on every release by
  `VBoxManage import --dry-run` where VirtualBox is installed, and
  otherwise by the OVF's own checksum.

## 5. Order and size

3.1 and 3.2 first, until an ISO boots to the installer by hand in QEMU;
then 3.3, the test that installs; then 3.4, the release; 3.5 as each
piece lands. 4 after 3.3, since it needs the installed disk. The first
build says the sizes, which decide whether the ISO fits GitHub's releases
as a second home or the hosting alone serves it.

## 6. After this plan

- *Reinstall, keep my data*: Calamares told to keep the `/home` partition
  a Kidux left and format the system one, a module of `kidux-installer`'s
  that finds it; installer.md, sections 3 and 7.
- The live session as the kiosk itself, with *Install* as the adult
  button, to try Kidux from the stick (installer.md, 3; the roadmap's
  phase 2).
- Updates that announce themselves on the sign-in screen and the panel
  (roadmap, phase 7).
