#!/bin/sh
# The image the test machines boot: Debian with every package Kidux needs
# from Debian already installed, and nothing of Kidux's own.
#
#   tests/lib/warm-image.sh        make it if it is missing or stale; print
#                                  the path of the image to boot
#
# Most of a test machine's first minutes went on downloading and installing
# the same Debian packages from the mirror: labwc, GTK, PipeWire, a kernel.
# So this boots the stock cloud image once, installs everything the packages
# in the local archive's testing suite would bring from Debian, marks it
# installed as a dependency, as installing Kidux would have, updates, and
# shuts down. The image is a machine that has never seen Kidux: the archive
# it used is removed, and no Kidux package was ever installed on it.
#
# It is stamped with a hash of the stock image and of every Depends,
# Pre-Depends, Recommends and Conflicts line in the archive's testing suite;
# a run whose stamp differs makes it again first, so a dependency added to a
# package is in the next image. Both test machines start from it, except when
# KIDUX_VM_COLD=1, which a release run sets: then this prints the stock image
# and the machines start from Debian exactly as a family's machine would, so
# that a dependency a package forgot but the image has is still caught before
# a release.
#
# The two machines may ask at the same moment; the second waits for the
# first one's image.

set -eu

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
VM_DIR="${KIDUX_VM_DIR:-$REPO_ROOT/build/vm}"
ARCHIVE_URL="${KIDUX_ARCHIVE_URL:-http://kidux.local/apt}"
SEED_PORT="${KIDUX_VM_WARM_PORT:-8004}"
BASE="$("$REPO_ROOT/tests/lib/base-image.sh")"

if [ "${KIDUX_VM_COLD:-}" = 1 ]; then
    echo "$BASE"
    exit 0
fi

WARM="$VM_DIR/debian-13-kidux-deps.qcow2"
STAMP="$WARM.stamp"

exec 8>"$VM_DIR/warm-image.lock"
flock 8

packages="$(curl -fsS "$ARCHIVE_URL/dists/testing/main/binary-amd64/Packages")"
stamp="$( {
    sha256sum < "$BASE"
    sha256sum < "$0"
    printf '%s\n' "$packages" | grep -E '^(Package|Depends|Pre-Depends|Recommends|Conflicts):'
} | sha256sum | cut -d' ' -f1)"

if [ -f "$WARM" ] && [ "$(cat "$STAMP" 2>/dev/null)" = "$stamp" ]; then
    echo "$WARM"
    exit 0
fi

echo "==> Making the warm image, $(basename "$WARM") (log: $VM_DIR/warm-console.log)" >&2
rm -f "$WARM" "$STAMP" "$WARM.part"
qemu-img create -q -f qcow2 -b "$BASE" -F qcow2 "$WARM.part" 12G

SEED="$VM_DIR/warm-seed"
rm -rf "$SEED"
mkdir -p "$SEED"
cp "$REPO_ROOT/tests/lib/seed/network-config" "$SEED/"
printf 'instance-id: kidux-warm-%s\nlocal-hostname: kidux-warm\n' "$(date +%s)" > "$SEED/meta-data"
: > "$SEED/vendor-data"
# Every Kidux package in the suite, and the Debian packages they bring as
# they are installed on a family's machine: the family with Debian's
# recommendations, as `apt-get install kidux-base` brings them, and every
# other package in the suite, the modules and what they share, without, as
# the daemon installs them (daemon.md section 13); less Kidux's own.
names="$(printf '%s\n' "$packages" | awk '/^Package:/ { print $2 }' | sort -u)"
family="kidux-base"
modules="$(printf '%s\n' "$names" | grep -vx "$family" | tr '\n' ' ')"
cat > "$SEED/user-data" <<USERDATA
#cloud-config
hostname: kidux-warm
write_files:
  - path: /etc/hosts
    append: true
    content: |
      10.0.2.2 kidux.local
  - path: /etc/apt/apt.conf.d/99kidux-vm-lean
    content: |
      Acquire::Languages "none";
  - path: /usr/local/sbin/kidux-warm
    permissions: '0755'
    content: |
      #!/bin/sh
      set -eux
      export DEBIAN_FRONTEND=noninteractive
      sed -i 's/^Types: deb deb-src/Types: deb/' /etc/apt/sources.list.d/debian.sources || true
      cd /var/tmp
      curl -fsSLO $ARCHIVE_URL/bootstrap/testing/kidux-archive-keyring.deb
      curl -fsSLO $ARCHIVE_URL/bootstrap/testing/kidux-apt-source.deb
      apt-get install -y --no-install-recommends ./kidux-archive-keyring.deb ./kidux-apt-source.deb
      sed -i 's/^Suites: stable\$/Suites: testing/' /etc/apt/sources.list.d/kidux.sources
      if curl -fsS -o extra-key.pgp $ARCHIVE_URL/extra-key.pgp; then
          cat extra-key.pgp >> /usr/share/keyrings/kidux-archive-keyring.pgp
      fi
      apt-get update
      apt-get -y -o Dpkg::Options::=--force-confold full-upgrade
      kidux="$family $modules"
      wanted=""
      for name in \$( { apt-get install -s $family;
                        apt-get install -s --no-install-recommends $modules; } \
                      | awk '/^Inst / { print \$2 }' | sort -u); do
          case " \$kidux " in *" \$name "*) ;; *) wanted="\$wanted \$name" ;; esac
      done
      apt-get install -y --no-install-recommends \$wanted
      apt-mark auto \$wanted
      apt-get purge -y kidux-apt-source kidux-archive-keyring
      rm -f extra-key.pgp kidux-archive-keyring.deb kidux-apt-source.deb
      apt-get update
      apt-get clean
      cloud-init clean --logs --seed --machine-id
      echo "KIDUX-WARM: DONE"
# It cleans cloud-init's own state as it ends, so the machine powers itself
# off rather than leaving that to cloud-init.
runcmd:
  - [ sh, -c, "/usr/local/sbin/kidux-warm > /dev/console 2>&1 || echo 'KIDUX-WARM: FAILED' > /dev/console; systemctl poweroff" ]
USERDATA

python3 -m http.server "$SEED_PORT" --bind 127.0.0.1 --directory "$SEED" \
    > "$VM_DIR/warm-seed-server.log" 2>&1 &
SERVER=$!
# shellcheck disable=SC2064
trap "kill $SERVER 2>/dev/null || true" EXIT INT TERM

cp -f /usr/share/OVMF/OVMF_VARS_4M.fd "$VM_DIR/OVMF_VARS_warm.fd"
if [ -w /dev/kvm ]; then ACCEL="-enable-kvm -cpu host"; else ACCEL="-cpu max"; fi
rm -f "$VM_DIR/warm-console.log"
# shellcheck disable=SC2086
timeout 1800 qemu-system-x86_64 \
    $ACCEL -m 2048 -smp 2 -machine q35 \
    -drive if=pflash,format=raw,unit=0,readonly=on,file=/usr/share/OVMF/OVMF_CODE_4M.fd \
    -drive if=pflash,format=raw,unit=1,file="$VM_DIR/OVMF_VARS_warm.fd" \
    -drive file="$WARM.part",format=qcow2,if=virtio \
    -netdev user,id=net0 -device virtio-net-pci,netdev=net0 \
    -smbios "type=1,serial=ds=nocloud;s=http://10.0.2.2:$SEED_PORT/" \
    -nographic -serial "file:$VM_DIR/warm-console.log" -monitor none -display none \
    || true

if ! grep -q "KIDUX-WARM: DONE" "$VM_DIR/warm-console.log"; then
    echo "$0: the warm image was not made; see $VM_DIR/warm-console.log" >&2
    rm -f "$WARM.part"
    exit 1
fi
mv "$WARM.part" "$WARM"
echo "$stamp" > "$STAMP"
echo "$WARM"
