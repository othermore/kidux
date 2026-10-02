#!/bin/sh
# Take a picture of what a running test VM has on its screen.
#
#   ci/vm/screenshot.sh [output.png]
#
# From step 9.6 onwards Kidux is a screen: a sign-in screen a four-year-old has
# to be able to use. No test can say whether that screen is right, so it gets
# looked at — and that means being able to get an image out of a VM that has no
# display attached.
#
# QEMU's monitor does it. The VM is started with a monitor on a Unix socket and
# no display at all; this connects to that socket and asks for a screendump.
# `-f png` matters: without it QEMU writes a PPM, which is a valid image and an
# inconvenient one.
#
# The VM has to have been started with a monitor socket — ci/vm/try.sh does.

set -eu

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
VM_DIR="${KIDUX_VM_DIR:-$REPO_ROOT/build/vm}"
MONITOR="${KIDUX_VM_MONITOR:-$VM_DIR/monitor.sock}"
OUTPUT="${1:-$VM_DIR/screen.png}"

if [ ! -S "$MONITOR" ]; then
    echo "$0: no VM monitor at $MONITOR" >&2
    echo "Start a machine first: ci/vm/try.sh" >&2
    exit 1
fi

case "$OUTPUT" in
    /*) ;;
    *) OUTPUT="$(pwd)/$OUTPUT" ;;
esac

mkdir -p "$(dirname "$OUTPUT")"
rm -f "$OUTPUT"

python3 - "$MONITOR" "$OUTPUT" <<'PYTHON'
import socket
import sys
import time

monitor, output = sys.argv[1], sys.argv[2]

connection = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
connection.connect(monitor)
try:
    # The monitor greets before it will take a command, and it echoes every
    # character back, so both sides of the conversation are drained rather than
    # parsed.
    time.sleep(0.4)
    connection.recv(65536)

    connection.sendall(f"screendump {output} -f png\n".encode())
    time.sleep(2)
    connection.recv(65536)
finally:
    connection.close()
PYTHON

if [ ! -s "$OUTPUT" ]; then
    echo "$0: the monitor produced no image" >&2
    exit 1
fi

echo "==> $OUTPUT"
