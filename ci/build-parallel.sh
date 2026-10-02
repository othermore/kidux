#!/bin/sh
# Build several packages at once, into one directory.
#
#   ci/build-parallel.sh <build dir> <package>...
#
# For packages that need nothing from each other to build: ci/build-all.sh
# and tests/lib/reproducible.sh use it once what the others need is built.
# Each build gets its log in <build dir>/logs/<package>.log and sees, as the
# packages it may install, a copy of the directory as it was before any of
# them started, so that none reads a package another is still writing. Says
# how each went, in the order given, with the end of the log of each that
# failed; exits non-zero if any did.
#
# At most KIDUX_BUILD_JOBS builds run at a time, four unless it says
# otherwise: each unpacks a chroot of its own, some hundreds of megabytes,
# and more at once only compete for the same processors.

set -u

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BUILD_DIR="$1"
shift

mkdir -p "$BUILD_DIR/logs"
EXTRA="$BUILD_DIR/extra-packages"
rm -rf "$EXTRA"
mkdir -p "$EXTRA"
if ls "$BUILD_DIR"/*.deb >/dev/null 2>&1; then
    cp "$BUILD_DIR"/*.deb "$EXTRA/"
fi

JOBS="${KIDUX_BUILD_JOBS:-4}"
running=0
for package in "$@"; do
    if [ "$running" -ge "$JOBS" ]; then
        wait
        running=0
    fi
    echo "==> Building $package, in the background (log: ${BUILD_DIR#"$REPO_ROOT"/}/logs/$package.log)"
    (
        KIDUX_BUILD_DIR="$BUILD_DIR" KIDUX_EXTRA_PACKAGES="$EXTRA" \
            "$REPO_ROOT/ci/build-package.sh" "$package" > "$BUILD_DIR/logs/$package.log" 2>&1
        echo "$?" > "$BUILD_DIR/logs/$package.status"
    ) &
    running=$((running + 1))
done
wait

failed=0
for package in "$@"; do
    status="$(cat "$BUILD_DIR/logs/$package.status" 2>/dev/null || echo 1)"
    rm -f "$BUILD_DIR/logs/$package.status"
    if [ "$status" -eq 0 ]; then
        echo "==> $package built into $BUILD_DIR"
    else
        echo "==> $package did not build; the end of its log:" >&2
        tail -n 40 "$BUILD_DIR/logs/$package.log" | sed 's/^/      /' >&2
        failed=$((failed + 1))
    fi
done
rm -rf "$EXTRA"
[ "$failed" -eq 0 ]
