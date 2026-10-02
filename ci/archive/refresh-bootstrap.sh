#!/bin/sh
# Keep the two bootstrap packages at a fixed address in each suite.
#
#   ci/archive/refresh-bootstrap.sh
#
# Nothing in Kidux can be verified before apt has the key, so the keyring and
# the apt source are fetched by hand, once (docs/dev/packaging.md, "The
# bootstrap problem"). Instructions and tests that name a version go stale the
# day it changes, so each suite's current pair is also copied to
#
#   bootstrap/<suite>/kidux-archive-keyring.deb
#   bootstrap/<suite>/kidux-apt-source.deb
#
# ci/publish-local.sh and ci/promote.sh run this after every change.

set -eu

ARCHIVE_ROOT="${KIDUX_ARCHIVE_ROOT:-/srv/kidux-apt}"

for suite in testing stable; do
    index="$ARCHIVE_ROOT/dists/$suite/main/binary-amd64/Packages"
    [ -f "$index" ] || continue
    mkdir -p "$ARCHIVE_ROOT/bootstrap/$suite"
    for package in kidux-archive-keyring kidux-apt-source; do
        file="$(awk -v want="$package" '
            /^Package: / { found = ($2 == want) }
            found && /^Filename: / { print $2; exit }' "$index")"
        if [ -n "$file" ]; then
            cp "$ARCHIVE_ROOT/$file" "$ARCHIVE_ROOT/bootstrap/$suite/$package.deb.new"
            mv "$ARCHIVE_ROOT/bootstrap/$suite/$package.deb.new" \
               "$ARCHIVE_ROOT/bootstrap/$suite/$package.deb"
        fi
    done
done
echo "==> Bootstrap packages refreshed in $ARCHIVE_ROOT/bootstrap/"
