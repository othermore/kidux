#!/bin/sh
# Install the current Kidux packages on a throwaway VM and report whether it
# worked.
#
#   tests/run acceptance
#
# Boots stock Debian under QEMU, hands it the checks in seed/user-data through
# cloud-init, and greps the serial console for the verdict. The VM writes
# nothing back: -snapshot keeps every change in memory, so each run starts from
# the same untouched image and there is nothing to clean up.
#
# Needs: a published archive (ci/publish-local.sh) and membership of the kvm
# group. Without kvm it still runs, on emulation, perhaps ten times slower.

set -eu

# Being added to the kvm group does not reach a shell that was already open, and
# asking someone to log out in the middle of a build is a poor trade when sg can
# pick the group up for one command. Re-exec once, and only when that would
# actually change anything.
if [ "${KIDUX_VM_REEXEC:-}" != "1" ] \
   && ! id -nG | tr ' ' '\n' | grep -qx kvm \
   && getent group kvm | grep -q "[:,]$(id -un)\(,\|$\)"; then
    echo "==> Picking up the kvm group for this run"
    KIDUX_VM_REEXEC=1 exec sg kvm -c "$0 $*"
fi

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
VM_DIR="${KIDUX_VM_DIR:-$REPO_ROOT/build/vm}"
SEED_DIR="$REPO_ROOT/tests/lib/seed"
CONSOLE_LOG="$VM_DIR/console.log"
SEED_PORT="${KIDUX_VM_SEED_PORT:-8000}"
VM_MEMORY="${KIDUX_VM_MEMORY:-2048}"
TIMEOUT="${KIDUX_VM_TIMEOUT:-1200}"
ARCHIVE_URL="${KIDUX_ARCHIVE_URL:-http://kidux.local/apt}"

mkdir -p "$VM_DIR"

# --- the archive has to be reachable before the VM asks for it ---------------

if ! curl -fsS -o /dev/null "$ARCHIVE_URL/dists/testing/InRelease"; then
    echo "$0: no archive at $ARCHIVE_URL" >&2
    echo "Publish one with ci/publish-local.sh, and make sure nginx serves it:" >&2
    echo "  sudo ci/setup-dev-host.sh" >&2
    exit 1
fi

# --- base image --------------------------------------------------------------

# Debian with what Kidux needs from Debian already installed, or the stock
# image when KIDUX_VM_COLD=1 (tests/lib/warm-image.sh).
IMAGE="$("$REPO_ROOT/tests/lib/warm-image.sh")"

# --- serve the cloud-init seed ----------------------------------------------

# cloud-init is pointed at this over HTTP through the SMBIOS serial number,
# which saves building an ISO and needs no tooling beyond python3.
# The seed, and beside it every test in tests/acceptance/ with a list of their
# names, which the VM's runner fetches and runs in order. A new test is a new
# file there; nothing here or in user-data needs to know its name.
SERVED="$VM_DIR/acceptance-seed"
rm -rf "$SERVED"
mkdir -p "$SERVED/tests"
cp -r "$SEED_DIR"/. "$SERVED/"
( cd "$REPO_ROOT/tests/acceptance" && find . -maxdepth 1 -type f ! -name '.*' -printf '%f\n' | sort ) \
    > "$SERVED/tests/LIST"
while read -r name; do
    cp "$REPO_ROOT/tests/acceptance/$name" "$SERVED/tests/"
done < "$SERVED/tests/LIST"
echo "==> Serving cloud-init seed and $(wc -l < "$SERVED/tests/LIST") tests on port $SEED_PORT"
python3 -m http.server "$SEED_PORT" --bind 127.0.0.1 --directory "$SERVED" \
    >"$VM_DIR/seed-server.log" 2>&1 &
SEED_PID=$!
# shellcheck disable=SC2064
trap "kill $SEED_PID 2>/dev/null || true" EXIT INT TERM

# --- firmware ----------------------------------------------------------------

# UEFI, because the machines Kidux targets boot that way and the difference
# reaches GRUB and Plymouth later on.
OVMF_CODE=/usr/share/OVMF/OVMF_CODE_4M.fd
OVMF_VARS_TEMPLATE=/usr/share/OVMF/OVMF_VARS_4M.fd
OVMF_VARS="$VM_DIR/OVMF_VARS.fd"
cp -f "$OVMF_VARS_TEMPLATE" "$OVMF_VARS"

if [ -r /dev/kvm ] && [ -w /dev/kvm ]; then
    ACCEL="-enable-kvm -cpu host"
else
    echo "==> No access to /dev/kvm; emulating, which is slow."
    echo "    Fix with: sudo ci/setup-dev-host.sh, then log out and back in."
    ACCEL="-cpu max"
fi

# --- run ---------------------------------------------------------------------

rm -f "$CONSOLE_LOG"
echo "==> Booting the test VM (transcript in $CONSOLE_LOG)"

# shellcheck disable=SC2086
timeout "$TIMEOUT" qemu-system-x86_64 \
    $ACCEL \
    -m "$VM_MEMORY" \
    -smp 2 \
    -machine q35 \
    -drive if=pflash,format=raw,unit=0,readonly=on,file="$OVMF_CODE" \
    -drive if=pflash,format=raw,unit=1,file="$OVMF_VARS" \
    -drive file="$IMAGE",format=qcow2,if=virtio \
    -snapshot \
    -netdev user,id=net0 \
    -device virtio-net-pci,netdev=net0 \
    -smbios "type=1,serial=ds=nocloud;s=http://10.0.2.2:$SEED_PORT/" \
    -nographic \
    -serial "file:$CONSOLE_LOG" \
    -monitor none \
    -display none \
    || true

# --- verdict -----------------------------------------------------------------

echo
if [ ! -s "$CONSOLE_LOG" ]; then
    echo "FAIL: the VM produced no console output at all." >&2
    exit 1
fi

sed -n '/=== Kidux acceptance run/,/KIDUX-ACCEPTANCE/p' "$CONSOLE_LOG" \
    | sed 's/.*cloud-init\[[0-9]*\]: //'

if grep -q 'KIDUX-ACCEPTANCE: PASS' "$CONSOLE_LOG"; then
    echo
    echo "==> Acceptance passed."
    exit 0
fi

echo
if grep -q 'KIDUX-ACCEPTANCE: FAIL' "$CONSOLE_LOG"; then
    echo "==> Acceptance failed. Full transcript: $CONSOLE_LOG" >&2
else
    echo "==> The VM never reached a verdict; it may have hung or failed to" >&2
    echo "    boot. Full transcript: $CONSOLE_LOG" >&2
fi
exit 1
