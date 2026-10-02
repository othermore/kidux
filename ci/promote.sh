#!/bin/sh
# Promote packages from testing to stable.
#
#   ci/promote.sh                    promote everything currently in testing
#   ci/promote.sh kidux-base         promote one package
#
# stable is what an installed machine follows and upgrades to unattended, so a
# package reaches it only after tests/run acceptance has installed it on a
# clean machine and found it good.
#
# This copies what is already in testing rather than publishing a fresh build:
# the bits a family gets are then, byte for byte, the bits that were tested.

set -eu

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CONF_DIR="$REPO_ROOT/ci/archive/conf"
# In CI the archive is signed with a key made for that run alone
# (ci/setup-ci-host.sh): the real key is never there. reprepro takes the key
# from the configuration, so the run gets a copy of it that names its own.
if [ -n "${KIDUX_SIGNING_KEY:-}" ]; then
    RUN_CONF="$REPO_ROOT/build/archive-conf"
    rm -rf "$RUN_CONF"
    cp -r "$CONF_DIR" "$RUN_CONF"
    sed -i "s/^SignWith: .*/SignWith: $KIDUX_SIGNING_KEY/" "$RUN_CONF/distributions"
    CONF_DIR="$RUN_CONF"
fi
ARCHIVE_ROOT="${KIDUX_ARCHIVE_ROOT:-/srv/kidux-apt}"

reprepro_run() {
    reprepro --basedir "$ARCHIVE_ROOT" --confdir "$CONF_DIR" "$@"
}

if [ ! -w "$ARCHIVE_ROOT" ]; then
    echo "$0: $ARCHIVE_ROOT is not writable by $(id -un)" >&2
    echo "Run: sudo ci/setup-dev-host.sh" >&2
    exit 1
fi

if [ "$#" -gt 0 ]; then
    packages="$*"
else
    # Only what differs: a package already in stable at the version testing
    # holds has nothing to promote.
    testing="$(reprepro_run --list-format '${package} ${version}\n' list testing | sort -u)"
    stable="$(reprepro_run --list-format '${package} ${version}\n' list stable | sort -u)"
    packages="$(printf '%s\n' "$testing" | while read -r name version; do
        [ -n "$name" ] || continue
        printf '%s\n' "$stable" | grep -qx "$name $version" || echo "$name"
    done)"
fi

# A development build (tests/run vm push) is for trying a change, never for a
# family.
dev="$(reprepro_run --list-format '${package} ${version}\n' list testing | grep '~dev\.' || true)"
if [ -n "$dev" ]; then
    echo "$0: testing holds development builds; publish the tree's own build first:" >&2
    printf '  %s\n' "$dev" >&2
    exit 1
fi

if [ -z "$packages" ]; then
    echo "==> stable already holds everything in testing."
    reprepro_run list stable
    exit 0
fi

echo "==> Promoting to stable:"
for package in $packages; do
    echo "  $package"
done
echo

# shellcheck disable=SC2086
reprepro_run copy stable testing $packages
"$REPO_ROOT/ci/archive/refresh-bootstrap.sh"

echo
echo "==> stable now holds:"
reprepro_run list stable
