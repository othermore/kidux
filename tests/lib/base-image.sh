#!/bin/sh
# The stock Debian cloud image every test machine starts from, fetched once.
#
#   tests/lib/base-image.sh        fetch it if it is not there; print its path
#
# Both test machines and ci/vm/try.sh call this. They may start at the same
# moment (ci/test-release.sh runs them side by side), so the fetch holds a
# lock and the second caller waits for the first one's image rather than
# downloading a second copy over it.

set -eu

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
VM_DIR="${KIDUX_VM_DIR:-$REPO_ROOT/build/vm}"
IMAGE_NAME=debian-13-genericcloud-amd64.qcow2
IMAGE="$VM_DIR/$IMAGE_NAME"
IMAGE_URL="https://cloud.debian.org/images/cloud/trixie/latest"

mkdir -p "$VM_DIR"
exec 9>"$VM_DIR/base-image.lock"
flock 9

if [ ! -f "$IMAGE" ]; then
    echo "==> Fetching $IMAGE_NAME" >&2
    curl -fsSL -o "$VM_DIR/SHA512SUMS" "$IMAGE_URL/SHA512SUMS"
    curl -fSL -o "$IMAGE.part" "$IMAGE_URL/$IMAGE_NAME"
    mv "$IMAGE.part" "$IMAGE"
    ( cd "$VM_DIR" && sha512sum -c --ignore-missing SHA512SUMS >&2 ) || {
        rm -f "$IMAGE"
        exit 1
    }
fi

echo "$IMAGE"
