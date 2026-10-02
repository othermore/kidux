#!/bin/sh
# The tarball a package is built from, or its source tarball, in
# build/upstream/ (D68, D71).
#
#   ci/fetch-upstream.sh <package>            the built tarball
#   ci/fetch-upstream.sh <package> --source   the source tarball beside it
#
# Kept there by the build that made it, or downloaded from the GitHub
# release ci/build-upstream.sh --publish made; either way checked against
# the SHA-256 in packages/<package>/upstream.toml. Prints its path.

set -eu

PACKAGE="${1:?usage: ci/fetch-upstream.sh <package> [--source]}"
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"
field() { python3 ci/upstream/upstream.py "$PACKAGE" "$1"; }

VERSION="$(field version)"
if [ "${2:-}" = --source ]; then
    TARBALL="$(field source)"
    RECORDED="$(field source_sha256)"
else
    TARBALL="$(field tarball)"
    RECORDED="$(field sha256)"
fi
OUT="$REPO_ROOT/build/upstream"

[ -n "$RECORDED" ] || {
    echo "$0: packages/$PACKAGE/upstream.toml records no sum for $TARBALL; build it first:" >&2
    echo "  ci/build-upstream.sh $PACKAGE --publish" >&2
    exit 1
}
mkdir -p "$OUT"
if [ ! -s "$OUT/$TARBALL" ]; then
    echo "==> $TARBALL from the release upstream/$PACKAGE/$VERSION" >&2
    gh release download "upstream/$PACKAGE/$VERSION" --pattern "$TARBALL" --dir "$OUT" >&2
fi
SUM="$(sha256sum "$OUT/$TARBALL" | cut -d' ' -f1)"
[ "$SUM" = "$RECORDED" ] || {
    echo "$0: $TARBALL is $SUM, and upstream.toml records $RECORDED" >&2
    exit 1
}
echo "$OUT/$TARBALL"
