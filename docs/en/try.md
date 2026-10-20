# Trying Kidux in an emulator

*[Versión en español](../es/try.md)*

**Kidux can be tried on the computer you use every day, before you give it a computer of its own.** This is done with an emulator: a program that runs a complete computer inside a window. The emulator starts Kidux from an image prepared especially for this trial, with a family already in it, one child and several learning modules switched on for them. Nothing is installed on your computer apart from the emulator itself, and when you close the window everything is left exactly as it was.

What you see in the window is the whole of Kidux, not a cut-down demonstration. It is the same system the installer puts on a computer, with its sign-in screen, the child's screen, the time limits, the lock screen and the adult panel. It even updates itself from Kidux's package archive, as any computer with Kidux installed would.

## The family in the trial image

The image comes prepared with these details, so that you can start trying it as soon as it has started:

| | |
|---|---|
| **The child** | Is called **Leo**, and their password is `leo`. |
| **The adult password** | Is `kidux`. It opens the adult panel from the sign-in screen or from the lock screen. |
| **The administrator** | Is the account `anna`, with the password `kidux`. It is for the text console, which a normal trial never needs. |
| **Learning modules** | Leo has six modules installed and switched on: BASIC, Tux Typing, Scratch, GCompris, Simulations and Kig. The others can be installed from the adult panel. |
| **Time** | Leo has no time limit at all, so that you can try at leisure. If you want to see how the limits work, the adult panel lets you set one. |
| **Languages** | There are two images: one in Spanish and one in English. |
| **What it needs** | About 4 GB of memory free for the emulator, and around 10 GB of disk space. |

Once it has started, Kidux shows its sign-in screen with Leo's picture. After Leo's password is typed, their screen appears with the six modules:

![The sign-in screen of the trial image, with Leo](../images/en/trial-sign-in.png)

![Leo's screen, with six learning modules](../images/en/trial-leo.png)

## Which image to download, for your computer

There are two image formats, because each emulator prefers its own. The `.ova` file is for VirtualBox, and the `.qcow2` file is for UTM and for QEMU. This table says which emulator and which image suit each case:

| Your computer | The emulator | The image |
|---|---|---|
| **Windows** | [VirtualBox](https://www.virtualbox.org/), free | [kidux-trial-en.ova](https://iso.kidux.org/kidux-trial-en.ova) |
| **Mac with an Intel processor** | VirtualBox, or else [UTM](https://mac.getutm.app/) | The `.ova` for VirtualBox, or the `.qcow2` for UTM |
| **Mac with an Apple processor** (M1 and later) | [UTM](https://mac.getutm.app/), free | [kidux-trial-en.qcow2](https://iso.kidux.org/kidux-trial-en.qcow2) |
| **Linux** | QEMU, or else VirtualBox | The `.qcow2` for QEMU, or the `.ova` for VirtualBox |

The Spanish images are called `kidux-trial-es.ova` and `kidux-trial-es.qcow2`, and they are at the same address. Each file is about 1.5 GB.

If you want to check that the download arrived whole, the SHA-256 sums of every image are in [SHA256SUMS](https://iso.kidux.org/SHA256SUMS). Bear one detail in mind: each file's full name includes the version of Kidux, and that full name is the one that appears in the list of sums and the one a browser saves the file under. If your download program saved it under the link's short name instead, look in the list for the line of its language and its format, and compare the sum by hand.

## Windows, or a Mac or Linux, with VirtualBox

1. **Install VirtualBox and download the `.ova` image.** VirtualBox is a free download from its website, and installs like any other program.

2. **Import the image.** In VirtualBox, choose the menu **File > Import Appliance**, select the `.ova` file you downloaded and press **Finish**. VirtualBox creates a machine that is already configured: two processors, 4 GB of memory and UEFI start-up, like that of any computer bought in the last ten years. No setting needs changing.

3. **Start the machine.** Select it in the list and press **Start**. Kidux's logo appears and, shortly after, its sign-in screen with Leo.

To see Kidux's screens whole, the window should be at least 1280 by 800 points. You can also use the menu **View > Full-screen Mode**.

## A Mac with UTM

1. **Install UTM and download the `.qcow2` image.** UTM is a free download from its website.

2. **Create a new machine.** In UTM, press **Create a New Virtual Machine**. Then choose **Emulate** and, after that, **Other**.

3. **Choose the hardware.** On the **Hardware** screen, leave the machine **Intel ICH9 based PC (2009, x86_64)** chosen and the memory at **4096 MiB**. In **CPU Cores**, type **4**; if your Mac has more than 8 cores, type half of what it has. Press **Continue**.

4. **Leave the machine without a boot disk.** On the next screen, under **Boot Device**, choose **None**. Leave the **UEFI Boot** box ticked, as it already comes, and press **Continue**.

5. **Finish the assistant.** On **Storage**, press **Continue** without changing anything: the disk it proposes is replaced in the next step. On **Shared Directory**, press **Continue** without choosing anything. On **Summary**, name it *Kidux*, tick the **Open VM Settings** box and press **Save**.

6. **Swap the disk for Kidux's image.** In the settings window that opens, go down the left-hand column to the **Drives** section. Select **IDE Drive**, press **Delete** and confirm that you want to remove it. Then press **New...**, change **Interface** to **VirtIO**, press **Import...** and choose the `.qcow2` file you downloaded. To finish, press **Save**.

7. **Start the machine.** Press the triangle beside its name. First UTM's logo appears, then Kidux's and, in under a minute, its sign-in screen with Leo. It is normal for the screen to stay black for a few seconds in between: just wait.

When it imports the image, UTM makes its own copy, which takes up about 3.5 GB. So once it is imported, the downloaded file can safely be deleted.

Bear in mind that Kidux is made for PC computers. On a Mac with an Apple processor, UTM has to emulate a complete PC processor, so everything works, but more slowly than on a real computer. The more cores you give the machine, the better it runs: with 2 cores it is very slow, with 4 it is usable, and with 8 it runs quite well. On a Mac with an Intel processor nothing needs emulating, and both UTM and VirtualBox run Kidux at full speed.

## Linux with QEMU

Install QEMU and its UEFI firmware. On Debian or Ubuntu they are the packages `qemu-system-x86` and `ovmf`. Then download the `.qcow2` image and, from the folder it is in, start it with this command:

```
qemu-system-x86_64 -enable-kvm -cpu host -m 4096 -smp 2 -machine q35 \
    -bios /usr/share/ovmf/OVMF.fd \
    -drive file=kidux-trial-en.qcow2,if=virtio \
    -vga none -device VGA,xres=1280,yres=800 \
    -device qemu-xhci -device usb-tablet -nic user,model=virtio-net-pci
```

Kidux's logo appears and then its sign-in screen with Leo. Everything you change during the trial is kept in the image file itself. If you want to start again from the beginning, just download the image once more.

## What a trial cannot show

An emulator shows almost everything Kidux does, but there are a few things that can only be seen on a real computer:

- **The real computer's own parts.** Its Wi-Fi, its lid, its battery or its brightness and volume keys. Inside an emulator, Kidux sees the emulator's network as if it were a cable, and finds neither a battery nor a lid.
- **The speed of a real computer.** An emulator is always slower than the same computer with Kidux installed, and much slower when it also has to emulate a different processor.
- **The keys the computer keeps for itself.** Some combinations, such as Ctrl+Alt+Del, are received by the computer around the emulator, and never reach Kidux.

When you have seen enough, [the user guide](user-guide.md#2-installing-kidux) explains how to install Kidux on a computer of its own.
