#!/bin/sh
# Boot a throwaway machine, turn it into Kidux, and let you use it.
#
#   ci/vm/try.sh [suite]
#
# For using Kidux rather than checking it. The machine installs Kidux from the
# local archive the way a family's Debian machine would, restarts into it and
# shows the first-run wizard. Its screen is offered over VNC, on this machine
# only, with the password "kidux"; this terminal is its serial console, with a
# root prompt for looking underneath.
#
# From another computer, forward the port over SSH and point a VNC viewer at
# it (docs/dev/packaging.md, "Using it"):
#
#   ssh -N -L 5901:127.0.0.1:5900 <you>@kidux.local
#   open vnc://127.0.0.1:5901            # macOS; any VNC viewer elsewhere
#
# The suite is testing unless named: that is where every new build goes, and
# stable only holds what was promoted. Leave with poweroff at the root prompt,
# or Ctrl-A then X. Nothing is kept: the machine's disk is deleted with it.

set -eu

# Being added to the kvm group does not reach a shell that was already open.
if [ "${KIDUX_VM_REEXEC:-}" != "1" ] \
   && ! id -nG | tr ' ' '\n' | grep -qx kvm \
   && getent group kvm | grep -q "[:,]$(id -un)\(,\|$\)"; then
    KIDUX_VM_REEXEC=1 exec sg kvm -c "$0 $*"
fi

SUITE="${1:-testing}"
REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
VM_DIR="${KIDUX_VM_DIR:-$REPO_ROOT/build/vm}"
SEED_SOURCE="$REPO_ROOT/ci/vm/seed-interactive"
SEED_DIR="$VM_DIR/try-seed"
DISK="$VM_DIR/try-disk.qcow2"
SEED_PORT="${KIDUX_VM_SEED_PORT:-8001}"
VM_MEMORY="${KIDUX_VM_MEMORY:-2048}"
ARCHIVE_URL="${KIDUX_ARCHIVE_URL:-http://kidux.local/apt}"
# The VNC display: 0 is port 5900.
VNC_DISPLAY="${KIDUX_VM_VNC:-0}"
# How QEMU turns a VNC viewer's keys into key presses, for viewers that send
# characters rather than keys (macOS Screen Sharing does). It must match the
# keyboard chosen in the wizard.
KEYMAP="${KIDUX_VM_KEYMAP:-es}"

case "$SUITE" in
    testing|stable) ;;
    *) echo "usage: $0 [testing|stable]" >&2; exit 2 ;;
esac

if ! curl -fsS -o /dev/null "$ARCHIVE_URL/bootstrap/$SUITE/kidux-apt-source.deb"; then
    echo "$0: no $SUITE suite at $ARCHIVE_URL" >&2
    echo "Publish one with ci/publish-local.sh." >&2
    exit 1
fi

IMAGE="$("$REPO_ROOT/tests/lib/base-image.sh")"

rm -rf "$SEED_DIR"
mkdir -p "$SEED_DIR"
for part in meta-data network-config vendor-data; do
    cp "$SEED_SOURCE/$part" "$SEED_DIR/$part"
done
sed "s/@SUITE@/$SUITE/g" "$SEED_SOURCE/user-data" > "$SEED_DIR/user-data"

python3 -m http.server "$SEED_PORT" --bind 127.0.0.1 --directory "$SEED_DIR" \
    >"$VM_DIR/try-seed.log" 2>&1 &
SEED_PID=$!

MONITOR="$VM_DIR/monitor.sock"
rm -f "$MONITOR" "$DISK"
# A disk of its own on top of the base image, large enough for a kernel with
# display drivers, and deleted when the machine is.
qemu-img create -q -f qcow2 -b "$IMAGE" -F qcow2 "$DISK" 12G
# shellcheck disable=SC2064
trap "kill $SEED_PID 2>/dev/null || true; rm -f '$DISK'" EXIT INT TERM

OVMF_VARS="$VM_DIR/OVMF_VARS_try.fd"
cp -f /usr/share/OVMF/OVMF_VARS_4M.fd "$OVMF_VARS"

if [ -r /dev/kvm ] && [ -w /dev/kvm ]; then
    ACCEL="-enable-kvm -cpu host"
else
    echo "==> No access to /dev/kvm; this will be slow."
    ACCEL="-cpu max"
fi

# QEMU starts VNC with a password but no password set; the monitor sets it
# once it is up. VNC passwords are at most eight characters.
(
    for _ in $(seq 100); do
        [ -S "$MONITOR" ] && break
        sleep 0.1
    done
    python3 - "$MONITOR" <<'PYTHON'
import socket, sys, time
monitor = socket.socket(socket.AF_UNIX)
monitor.connect(sys.argv[1])
monitor.sendall(b"set_password vnc kidux\n")
time.sleep(0.5)
PYTHON
) &

cat <<BANNER

    Booting a throwaway Kidux machine from the $SUITE suite. It installs
    Kidux, restarts into it and shows the first-run wizard: a few minutes.

    Its screen:  VNC on 127.0.0.1:$((5900 + VNC_DISPLAY)), password "kidux".
                 From another computer:
                   ssh -N -L 5901:127.0.0.1:$((5900 + VNC_DISPLAY)) <you>@kidux.local
                 then a VNC viewer on 127.0.0.1:5901.
    Pictures:    ci/vm/screenshot.sh, from another terminal.
    This window: the machine's serial console, a root prompt once it is up.

    To leave: poweroff at the root prompt, or Ctrl-A then X.

BANNER

# Not exec: that would replace this shell and the trap above would never fire,
# leaving the seed server running and the disk behind after the machine is gone.
# shellcheck disable=SC2086
qemu-system-x86_64 \
    $ACCEL \
    -m "$VM_MEMORY" \
    -smp 2 \
    -machine q35 \
    -drive if=pflash,format=raw,unit=0,readonly=on,file=/usr/share/OVMF/OVMF_CODE_4M.fd \
    -drive if=pflash,format=raw,unit=1,file="$OVMF_VARS" \
    -drive file="$DISK",format=qcow2,if=virtio \
    -netdev user,id=net0 \
    -device virtio-net-pci,netdev=net0 \
    -smbios "type=1,serial=ds=nocloud;s=http://10.0.2.2:$SEED_PORT/" \
    -vga std \
    -usb -device usb-tablet \
    -k "$KEYMAP" \
    -monitor "unix:$MONITOR,server,nowait" \
    -serial mon:stdio \
    -display "vnc=127.0.0.1:$VNC_DISPLAY,password=on"

echo
echo "==> The machine is gone. Nothing was kept."
