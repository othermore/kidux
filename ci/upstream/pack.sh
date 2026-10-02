#!/bin/sh
# The tarball of an upstream build, the same bytes from the same tree (D68).
#
#   pack.sh <directory> <top> <tarball> <epoch>
#
# <directory>'s contents under one top-level directory <top>/, sorted,
# owned by root, every time <epoch> (seconds, the commit's), xz without
# threads so that the compression is the same everywhere.

set -eu

SOURCE="$1"
TOP="$2"
TARBALL="$3"
EPOCH="$4"

tar --format=gnu --sort=name --owner=0 --group=0 --numeric-owner --mtime="@$EPOCH" \
    --transform "s,^\.,$TOP," -C "$SOURCE" -cf - . \
    | xz -T1 -9 > "$TARBALL"
