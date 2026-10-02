#!/bin/sh
# Publish built packages into the local apt archive.
#
#   ci/publish-local.sh              put everything in build/ into testing
#   ci/publish-local.sh stable       ... into stable instead
#
# A development build (`tests/run vm push`) is published from a directory of
# its own, named in KIDUX_BUILD_DIR, with KIDUX_DEV_BUILD=1 and a version
# ending ~dev.<time>, which sorts before the version itself (D77). Any other
# publish first removes every such version from the suite, and the version it
# adds replaces the tries on every machine that followed them.
#
# The archive root is outside the repository because it is served by nginx and
# because reprepro keeps a database there that must survive a git checkout.
# Its configuration, which is ours, stays in the repository.

set -eu

SUITE="${1:-testing}"
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BUILD_DIR="${KIDUX_BUILD_DIR:-$REPO_ROOT/build}"
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

case "$SUITE" in
    testing|stable) ;;
    *)
        echo "$0: unknown suite '$SUITE', expected testing or stable" >&2
        exit 1
        ;;
esac

if [ ! -d "$ARCHIVE_ROOT" ]; then
    echo "$0: no archive at $ARCHIVE_ROOT" >&2
    echo "Run: sudo ci/setup-dev-host.sh" >&2
    exit 1
fi

if [ ! -w "$ARCHIVE_ROOT" ]; then
    echo "$0: $ARCHIVE_ROOT is not writable by $(id -un)" >&2
    echo "Run: sudo ci/setup-dev-host.sh" >&2
    exit 1
fi

changes_files="$(find "$BUILD_DIR" -maxdepth 1 -name '*.changes' 2>/dev/null | sort)"
if [ -z "$changes_files" ]; then
    echo "$0: nothing to publish in $BUILD_DIR" >&2
    echo "Run: ci/build-all.sh" >&2
    exit 1
fi

reprepro_run() {
    reprepro --basedir "$ARCHIVE_ROOT" --confdir "$CONF_DIR" "$@"
}

if [ "${KIDUX_DEV_BUILD:-}" != 1 ]; then
    echo "==> Removing development builds from suite '$SUITE'"
    reprepro_run removefilter "$SUITE" 'Version (% *~dev.*)'
fi

echo "==> Publishing into suite '$SUITE' at $ARCHIVE_ROOT"
for changes in $changes_files; do
    echo "  $(basename "$changes")"
    # Two different things are called a distribution here, and they disagree on
    # purpose. A package's changelog says "trixie": the Debian release it is
    # built against, which is a fact about the package. Our suites are called
    # testing and stable and say how far a package has got in our own testing,
    # which is a fact about the moment, decided by whoever runs this script.
    # reprepro warns about the mismatch; --ignore=wrongdistribution says we mean
    # it. The suite comes from the command line, never from the changelog.
    #
    # include replaces any earlier version of the same package in this suite.
    reprepro_run --ignore=wrongdistribution include "$SUITE" "$changes"
done

# Materialise every configured suite, not just the one we wrote to. To apt, an
# empty suite with no Release file is not empty, it is broken: a machine
# following stable would report that the repository has no Release file until
# the first package was ever promoted there.
echo "==> Exporting all suites"
reprepro_run export
"$REPO_ROOT/ci/archive/refresh-bootstrap.sh"
# The key the testing suite is signed with, beside the archive, where a
# machine that follows testing looks for it: the development key, or in CI
# the one made for that run. kidux-archive-keyring ships only stable's.
cp "${KIDUX_ARCHIVE_PUBLIC_KEY:-$REPO_ROOT/ci/archive/development-key.pgp}" \
    "$ARCHIVE_ROOT/extra-key.pgp"

echo
echo "==> $SUITE now holds:"
reprepro_run list "$SUITE"

echo
echo "==> Served at http://kidux.local/apt (suite $SUITE)"
