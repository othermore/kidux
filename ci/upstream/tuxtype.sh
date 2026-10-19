#!/bin/sh
# Tux Typing's source as Debian builds it, for kidux-tuxtype (D113).
#
# Run by ci/build-upstream.sh kidux-tuxtype, in an empty directory. Tux
# Typing is in trixie, but Kidux builds it again with patches of its own
# (packages/kidux-tuxtype/patches/, docs/dev/tuxtype.md), so its source is
# taken as Debian publishes it: the upstream tarball and Debian's diff,
# each fetched through ci/upstream/fetch.sh by the address
# packages/kidux-tuxtype/debian-source.toml names and refused unless its
# SHA-256 is the one written there. The diff is applied, its debian/
# directory left out, since the package's debian/ is Kidux's own, and the
# tree is packed, dated by Debian's changelog entry for that version.

set -eu

REPO="$(cd "$(dirname "$UPSTREAM_FETCH")/../.." && pwd)"
LIST="$REPO/packages/$UPSTREAM_PACKAGE/debian-source.toml"
top="$PWD"

python3 - "$LIST" > "$top/list" <<'PYTHON'
import sys
import tomllib

with open(sys.argv[1], "rb") as file:
    listed = tomllib.load(file)
print(listed["debian_version"])
for part in ("orig", "diff"):
    print(listed[part]["url"], listed[part]["name"], listed[part]["sha256"])
PYTHON
debian_version="$(head -1 "$top/list")"

mkdir -p "$top/fetched"
tail -n +2 "$top/list" | while read -r url name sum; do
    sh "$UPSTREAM_FETCH" url "$url" "$top/fetched/$name"
    [ "$(sha256sum "$top/fetched/$name" | cut -d' ' -f1)" = "$sum" ] || {
        echo "$name: not the file debian-source.toml names" >&2
        exit 1
    }
    echo "==> $name"
done

mkdir -p "$top/unpacked"
tar -xzf "$top/fetched/tuxtype_${debian_version%-*}.orig.tar.gz" -C "$top/unpacked"
tree="$top/unpacked/tuxtype-${debian_version%-*}"
zcat "$top/fetched/tuxtype_$debian_version.diff.gz" | patch -s -p1 -d "$tree"
epoch="$(dpkg-parsechangelog -l "$tree/debian/changelog" -S Timestamp)"
[ "$(dpkg-parsechangelog -l "$tree/debian/changelog" -S Version)" = "$debian_version" ] || {
    echo "the diff's changelog is not of $debian_version" >&2
    exit 1
}
rm -rf "$tree/debian"
if [ -n "${UPSTREAM_KEEP:-}" ]; then
    echo "$epoch" > "$UPSTREAM_KEEP/time"
fi

echo "==> Tux Typing as Debian's $debian_version patches it, $(find "$tree" -type f | wc -l) files"
sh "$UPSTREAM_PACK" "$tree" "$UPSTREAM_PACKAGE-$UPSTREAM_VERSION" \
    "$UPSTREAM_OUT/$UPSTREAM_TARBALL" "$epoch"
