#!/bin/sh
# Build Kidux's installable image, a hybrid ISO for UEFI, with Secure Boot,
# and for a BIOS, from trixie and a suite of Kidux's archive (D116).
#
#   ci/build-image.sh [testing|stable]      build/image/kidux-<version>-<date>-amd64.iso
#
# Without root, as the packages are built. The live system is made by
# mmdebstrap in a user namespace, from Debian's mirror and the local
# archive's suite (testing while trying, stable for a release), with the
# packages image/packages names; it is the system the installer copies to
# a disk, so it is a Kidux machine as the user guide installs one on Debian,
# with Kidux's installer beside it (kidux-installer). It goes into a
# squashfs straight from mmdebstrap's tar (sqfstar), so that its files keep
# their owners without root; the tar has no entry for the root directory
# itself, which is root's too, not the builder's. It carries no initramfs:
# the live system boots from the image's own, and the installer makes the
# installed system's (kidux-installer). The image around it:
#
#   .disk/info                 what the image is, which GRUB looks for
#   live/vmlinuz, initrd.img   the live system's kernel, and its initramfs
#                              with live-boot
#   live/filesystem.squashfs   the live system
#   pool/grub-pc_*.deb         GRUB for a disk that starts with a BIOS
#                              (kidux-installer-grub)
#   boot/grub/grub.cfg         the boot menu, image/grub/grub.cfg
#   boot/grub/i386-pc/         GRUB for a BIOS, its El Torito image
#   boot/grub/efi.img          the EFI system partition: Debian's signed
#                              shim and CD GRUB, which find the menu by
#                              .disk/info
#   EFI/boot/                  the same two, on the image itself
#
# Every time in it is the suite's, its Release file's date, as
# SOURCE_DATE_EPOCH, and the image is named by that date and by the version
# of kidux-base it carries, which is Kidux's. What it holds is listed beside
# it, one package and version a line, and its SHA-256 in SHA256SUMS.
#
# Downloads are kept in build/image/cache/ between builds. The tools it
# needs are packaging.md's: mmdebstrap, squashfs-tools, xorriso, mtools,
# dosfstools, grub-pc-bin and grub-efi-amd64-bin.

set -eu

# mkfs.fat is in /usr/sbin, which a user's PATH may not have.
PATH="$PATH:/usr/sbin:/sbin"
SUITE="${1:-testing}"
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ARCHIVE="${KIDUX_ARCHIVE_URL:-http://127.0.0.1/apt}"
OUT="${KIDUX_IMAGE_DIR:-$REPO_ROOT/build/image}"
CACHE="$OUT/cache"
WORK="$OUT/work"
MIRROR="${KIDUX_DEBIAN_MIRROR:-http://deb.debian.org/debian}"
SECURITY="${KIDUX_DEBIAN_SECURITY:-http://security.debian.org/debian-security}"

case "$SUITE" in
    testing) KEY="$REPO_ROOT/ci/archive/development-key.pgp" ;;
    stable) KEY="$REPO_ROOT/packages/kidux-archive-keyring/keyrings/kidux-archive-keyring.pgp" ;;
    *) echo "usage: $0 [testing|stable]" >&2; exit 2 ;;
esac

for tool in mmdebstrap sqfstar xorriso mcopy mkfs.fat grub-mkimage; do
    command -v "$tool" >/dev/null || {
        echo "$0: $tool is missing; packaging.md lists what this machine needs" >&2
        exit 2
    }
done
[ -d /usr/lib/grub/i386-pc ] || { echo "$0: grub-pc-bin is missing" >&2; exit 2; }

# The suite as it stands: its date, which every time in the image is, and
# the version of kidux-base it holds.
RELEASE="$(curl -fsS "$ARCHIVE/dists/$SUITE/Release")"
SOURCE_DATE_EPOCH="$(date -u -d "$(printf '%s\n' "$RELEASE" | sed -n 's/^Date: //p')" +%s)"
export SOURCE_DATE_EPOCH
VERSION="$(curl -fsS "$ARCHIVE/dists/$SUITE/main/binary-amd64/Packages" \
    | awk '/^Package: kidux-base$/ { found = 1; next } found && /^Version: / { print $2; exit }')"
[ -n "$VERSION" ] || { echo "$0: the $SUITE suite holds no kidux-base" >&2; exit 1; }
DATE="$(date -u -d "@$SOURCE_DATE_EPOCH" +%Y%m%d)"
NAME="kidux-$VERSION-$DATE-amd64"
echo "==> $NAME, from Debian trixie and Kidux's $SUITE suite of $(date -u -d "@$SOURCE_DATE_EPOCH" '+%F %T') UTC"

rm -rf "$WORK"
mkdir -p "$WORK/iso/live" "$WORK/iso/pool" "$WORK/iso/.disk" "$WORK/boot" "$CACHE"
# The suite's key where apt reads it as its own unprivileged user, who may
# not enter a home directory.
KEYDIR="$(mktemp -d /tmp/kidux-image-key.XXXXXX)"
trap 'rm -rf "$KEYDIR"' EXIT
chmod 755 "$KEYDIR"
cp "$KEY" "$KEYDIR/kidux.gpg"
chmod 644 "$KEYDIR/kidux.gpg"

include="$(grep -v '^#' "$REPO_ROOT/image/packages" | grep -v '^$' | tr '\n' ',' | sed 's/,$//')"

# The live system. Recommends are installed, as apt installs them on Debian;
# Kidux's suite comes from the local archive, and the installed system's
# sources are Debian's and apt.kidux.org's stable, as kidux-apt-source
# ships it.
echo "==> The live system (log: ${OUT#"$REPO_ROOT"/}/mmdebstrap.log)"
mmdebstrap --mode=unshare --variant=standard --components=main,non-free-firmware \
    --aptopt='APT::Install-Recommends "true"' \
        --include="$include" \
    --skip=download/empty \
    --setup-hook='mkdir -p "$1"/var/cache/apt/archives/' \
    --setup-hook="sync-in '$CACHE' /var/cache/apt/archives/" \
    --customize-hook="sync-out /var/cache/apt/archives '$CACHE'" \
    --customize-hook='rm -f "$1"/var/cache/apt/archives/*.deb' \
    --customize-hook='chroot "$1" sh -c "mkdir -p /tmp/pool && cd /tmp/pool && apt-get download grub-pc"' \
    --customize-hook="sync-out /tmp/pool '$WORK/iso/pool'" \
    --customize-hook='rm -rf "$1"/tmp/pool' \
    --customize-hook="upload '$REPO_ROOT/image/sources' /etc/apt/sources.list.d/debian.sources" \
    --customize-hook='rm -f "$1"/etc/apt/sources.list' \
    --customize-hook='echo kidux > "$1"/etc/hostname' \
    --customize-hook='printf "127.0.0.1\tlocalhost\n127.0.1.1\tkidux\n::1\tlocalhost ip6-localhost ip6-loopback\n" > "$1"/etc/hosts' \
    --customize-hook='rm -rf "$1"/var/lib/apt/lists/* && : > "$1"/etc/machine-id && rm -f "$1"/var/lib/dbus/machine-id' \
    --customize-hook='rm -rf "$1"/var/cache/apparmor/* "$1"/var/cache/apt/archives/partial/*' \
    --customize-hook="upload '$REPO_ROOT/image/forget-host' /tmp/forget-host" \
    --customize-hook='sh "$1"/tmp/forget-host "$1" && rm -f "$1"/tmp/forget-host' \
    --customize-hook='touch -d "@$SOURCE_DATE_EPOCH" "$1"/var/cache/apt/archives "$1"/var/cache/apt/archives/partial' \
    --customize-hook='chroot "$1" dpkg-query -W -f "\${Package} \${Version}\n" > "$1"/tmp/packages' \
    --customize-hook="download /tmp/packages '$WORK/packages'" \
    --customize-hook='rm -f "$1"/tmp/packages' \
    --customize-hook="sync-out /boot '$WORK/boot'" \
    --customize-hook='rm -f "$1"/boot/initrd.img-*' \
    trixie - \
    "deb $MIRROR trixie main non-free-firmware" \
    "deb $MIRROR trixie-updates main non-free-firmware" \
    "deb $SECURITY trixie-security main non-free-firmware" \
    "deb [signed-by=$KEYDIR/kidux.gpg] $ARCHIVE $SUITE main" \
    2> "$OUT/mmdebstrap.log" \
    | sqfstar -quiet -comp xz -Xbcj x86 -b 1M -no-progress -root-uid 0 -root-gid 0 -root-mode 0755 \
        "$WORK/iso/live/filesystem.squashfs" \
    > "$OUT/sqfstar.log" 2>&1

# What it holds, as dpkg lists it.
sort "$WORK/packages" > "$OUT/$NAME.packages"
grep -q "^kidux-base $VERSION\$" "$OUT/$NAME.packages" || {
    echo "$0: the live system has no kidux-base $VERSION; see the log" >&2
    exit 1
}

kernel="$(ls "$WORK"/boot/vmlinuz-* | sort -V | tail -1)"
cp "$kernel" "$WORK/iso/live/vmlinuz"
cp "$WORK/boot/initrd.img-${kernel##*/vmlinuz-}" "$WORK/iso/live/initrd.img"
ls "$WORK"/iso/pool/grub-pc_*.deb >/dev/null
printf 'Kidux %s amd64 (%s)\n' "$VERSION" "$DATE" > "$WORK/iso/.disk/info"

# GRUB for a BIOS: the El Torito image, and the modules it loads from the
# image.
echo "==> GRUB, for UEFI and for a BIOS"
mkdir -p "$WORK/iso/boot/grub/i386-pc"
cp /usr/lib/grub/i386-pc/*.mod /usr/lib/grub/i386-pc/*.lst "$WORK/iso/boot/grub/i386-pc/"
grub-mkimage -O i386-pc-eltorito -d /usr/lib/grub/i386-pc -p /boot/grub \
    -o "$WORK/iso/boot/grub/i386-pc/eltorito.img" biosdisk iso9660 part_msdos part_gpt
cp "$REPO_ROOT/image/grub/grub.cfg" "$WORK/iso/boot/grub/grub.cfg"

# GRUB for UEFI: the shim and Debian's signed CD GRUB, from the live system's
# own packages, on an EFI system partition and on the image.
mkdir -p "$WORK/signed" "$WORK/iso/EFI/boot"
for package in shim-signed grub-efi-amd64-signed; do
    deb="$(ls "$CACHE"/${package}_*.deb | sort -V | tail -1)"
    dpkg-deb -x "$deb" "$WORK/signed"
done
cp "$WORK/signed/usr/lib/shim/shimx64.efi.signed" "$WORK/iso/EFI/boot/bootx64.efi"
cp "$WORK/signed/usr/lib/grub/x86_64-efi-signed/gcdx64.efi.signed" "$WORK/iso/EFI/boot/grubx64.efi"

# Every file of the image at the suite's time, and so every file of the EFI
# system partition, which mtools copies with its time and dates by
# SOURCE_DATE_EPOCH; then the partition and the folder it is made in.
find "$WORK/iso" -exec touch -h -d "@$SOURCE_DATE_EPOCH" {} +
mkfs.fat -C -n KIDUX_EFI -i 4b494458 "$WORK/iso/boot/grub/efi.img" 4096 >/dev/null
mcopy -s -m -i "$WORK/iso/boot/grub/efi.img" "$WORK/iso/EFI" ::/
find "$WORK/iso" -exec touch -h -d "@$SOURCE_DATE_EPOCH" {} +

echo "==> The image"
rm -f "$OUT/$NAME.iso"
xorriso -as mkisofs -quiet -iso-level 3 -full-iso9660-filenames -joliet -joliet-long \
    -rational-rock -volid KIDUX -appid "Kidux $VERSION" -publisher "Kidux" \
    --modification-date="$(date -u -d "@$SOURCE_DATE_EPOCH" +%Y%m%d%H%M%S00)" \
    --grub2-mbr /usr/lib/grub/i386-pc/boot_hybrid.img \
    -partition_offset 16 --mbr-force-bootable \
    -append_partition 2 0xef "$WORK/iso/boot/grub/efi.img" -appended_part_as_gpt \
    -iso_mbr_part_type a2a0d0ebe5b9334487c068b6b72699c7 \
    -c boot/grub/boot.cat \
    -b boot/grub/i386-pc/eltorito.img -no-emul-boot -boot-load-size 4 -boot-info-table \
    --grub2-boot-info \
    -eltorito-alt-boot -e --interval:appended_partition_2:all:: -no-emul-boot \
    -o "$OUT/$NAME.iso" "$WORK/iso"

( cd "$OUT" && sha256sum "$NAME.iso" > "$NAME.iso.sha256" )
rm -rf "$WORK"
echo "==> $OUT/$NAME.iso: $(du -h "$OUT/$NAME.iso" | cut -f1), sha256 $(cut -d' ' -f1 "$OUT/$NAME.iso.sha256")"
