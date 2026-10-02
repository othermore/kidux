#!/bin/sh
# A Node.js release of nodejs.org's own, for the upstream builds (D68).
#
#   ci/upstream/node.sh <version>                prints the directory whose bin/ it is
#   ci/upstream/node.sh <version> --keep <dir>   and copies its archive into <dir>
#
# Downloaded once into build/upstream/node/, its archive checked against
# the SHASUMS256.txt nodejs.org publishes beside it, unpacked into
# v<version>/, and both kept for the next build. --keep copies the archive
# and its sums into a build's source tarball (D71). With NODE_FROM set, a
# directory holding that archive and those sums, as a source tarball does,
# the archive comes from there and nothing is downloaded. Never the
# system's node: the version a build used is part of what its tarball's sum
# stands for.

set -eu

VERSION="${1:?usage: ci/upstream/node.sh <version> [--keep <dir>]}"
REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
NODE_DIR="$REPO_ROOT/build/upstream/node"
HOME_DIR="$NODE_DIR/v$VERSION"
ARCHIVE="node-v$VERSION-linux-x64.tar.xz"
SUMS="node-v$VERSION-SHASUMS256.txt"
URL="https://nodejs.org/dist/v$VERSION"

mkdir -p "$NODE_DIR"
if [ ! -f "$NODE_DIR/$ARCHIVE" ] || [ ! -f "$NODE_DIR/$SUMS" ]; then
    if [ -n "${NODE_FROM:-}" ]; then
        echo "==> Node.js $VERSION from $NODE_FROM" >&2
        cp "$NODE_FROM/$ARCHIVE" "$NODE_FROM/$SUMS" "$NODE_DIR/"
    else
        echo "==> Node.js $VERSION from $URL" >&2
        curl -fsSL -o "$NODE_DIR/$ARCHIVE.part" "$URL/$ARCHIVE"
        curl -fsSL -o "$NODE_DIR/$SUMS" "$URL/SHASUMS256.txt"
        mv "$NODE_DIR/$ARCHIVE.part" "$NODE_DIR/$ARCHIVE"
    fi
fi
( cd "$NODE_DIR" && grep " $ARCHIVE\$" "$SUMS" | sha256sum -c --quiet - >&2 )

if [ ! -x "$HOME_DIR/bin/node" ]; then
    rm -rf "$HOME_DIR.part"
    mkdir -p "$HOME_DIR.part"
    tar -xJf "$NODE_DIR/$ARCHIVE" -C "$HOME_DIR.part" --strip-components=1
    rm -rf "$HOME_DIR"
    mv "$HOME_DIR.part" "$HOME_DIR"
fi

if [ "${2:-}" = --keep ]; then
    mkdir -p "${3:?--keep needs a directory}"
    cp "$NODE_DIR/$ARCHIVE" "$NODE_DIR/$SUMS" "$3/"
fi
echo "$HOME_DIR"
