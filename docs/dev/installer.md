# The installable image and the installer, as designed

Plan phase 2. This is the experience the image and the installer are built
to give an adult with no Linux knowledge, written from that adult's side so
that it can be judged before anything is built. When the image exists, the
user guide describes what it does; this document is what it has to do.

## What you need

- A computer with a **64-bit processor** (almost any PC or laptop from 2008 onwards),
  at least **2 GB of memory** (4 GB recommended) and **32 GB of disk**.
- A **USB stick of 4 GB or more**. Everything on it will be erased.
- Another computer to download the image and write it to the stick.
- The disk of the target computer will be erased completely on a fresh install.
  If it contains anything you want, copy it somewhere else first.

## 1. Download the image

Download the latest `.iso` file and its checksum from the releases page. Compare the
checksum before writing:

```
Windows (PowerShell):  Get-FileHash .\kidux-*.iso -Algorithm SHA256
macOS / Linux:         shasum -a 256 kidux-*.iso
```

## 2. Write the USB stick

- **Windows / macOS / Linux:** use balenaEtcher or Raspberry Pi Imager: choose the
  `.iso`, choose the stick, write.
- **Command line (macOS / Linux):**

  ```bash
  sudo dd if=kidux-*.iso of=/dev/<stick> bs=4M status=progress
  ```

## 3. Start the computer from the stick

1. Plug the stick in and power the computer on.
2. Open the boot menu: usually `F12`, `F11`, `F8`, `Esc` or `F2` right after power on
   (the logo screen often says which key). On a Mac, hold `Option (Alt)`.
3. Choose the USB stick. The first screen you see is the child's launcher itself,
   running from the stick: you can try it before installing anything.
4. Click **Install** (the adult button; nothing is protected yet at this point).

## 4. The installer

The installer is translated. Every step has a short explanation on screen.

1. **Language** of the installer and of the system. It can be changed per child later.
2. **Keyboard.**
3. **Disk:**
   - **Erase the disk and install** for a fresh install. The installer creates a
     system partition and a separate *data* partition automatically.
   - **Reinstall, keep my data** if Kidux was already installed: only the
     system partition is rewritten; children's work and your settings stay.
4. **Administrator account:** your name, a user name and a password. This is the
   account that can repair the machine from the network if something goes wrong. It is
   not an account any child uses, and it is not what opens the adult panel.
5. Install, remove the stick, restart.

Tip: set a firmware (BIOS/UEFI) password so a child cannot start another system from
a USB stick. The installer explains how to reach the firmware setup on common brands.

## 5. First start

The first time the computer starts it asks you to set three things up:

1. The **language and keyboard** of the machine. Each child can have their own later.
2. The **adult password**. This is what opens the adult panel from now on. It is free
   text, as long or as short as you like; there is no rule about digits. Choose
   something the children will not guess and will not see you type.
3. The **first child**: their name, their avatar, their own password, and how much time
   they may use the computer. More children can be added at any moment.

After that the computer starts at the sign-in screen, where each child signs in with
their own password. Press **Adult** there to open the panel and switch on the modules
you want. Everything is off by default.

## 6. Updates

- **Security updates** install themselves in the background. Nothing to do.
- **Feature updates:** the adult panel shows *Update available*. One click, a
  restart, done. Children's work is never touched.
- **New Debian versions** (every two years or so): offered from the same place once
  we have tested the upgrade. Same rule: data stays.

## 7. Reinstalling without losing anything

If the system ever breaks, start from the USB stick again and choose **Reinstall,
keep my data**. Children's accounts, their work and your settings come back exactly
as they were, because they live on the data partition, which the installer never
formats in this mode.

## 8. Getting help

Open an issue on the project's GitHub page, in English or Spanish.
