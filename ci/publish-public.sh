#!/bin/sh
# Publish the stable suite at https://kidux.org/apt.
#
#   ci/publish-public.sh            pack stable, send it, and have the site published
#   ci/publish-public.sh --pack     pack it only, into build/kidux-apt.tar
#
# The public archive is the stable suite as it stands in the local archive,
# byte for byte: its indexes with their signature, the packages they name and
# the two bootstrap packages (docs/dev/packaging.md, "The public archive";
# D82). It is packed into one tarball, sent to the repository's `archive`
# release on GitHub, and the site's workflow unpacks it under apt/ beside the
# pages, so that it is served from the same place as the website.
#
# It is run after ci/promote.sh. The suite is refused if it is not signed with
# the key kidux-archive-keyring ships, the one a family's machine checks it
# against, or if it holds a development build.

set -eu

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ARCHIVE_ROOT="${KIDUX_ARCHIVE_ROOT:-/srv/kidux-apt}"
KEYRING="$REPO_ROOT/packages/kidux-archive-keyring/keyrings/kidux-archive-keyring.pgp"
OUT="$REPO_ROOT/build/public-archive"
TARBALL="$REPO_ROOT/build/kidux-apt.tar"
RELEASE=archive
INDEX="$ARCHIVE_ROOT/dists/stable/main/binary-amd64/Packages"

case "${1:-}" in
    ""|--pack) ;;
    *) echo "usage: $0 [--pack]" >&2; exit 2 ;;
esac

if [ ! -s "$INDEX" ]; then
    echo "$0: the stable suite at $ARCHIVE_ROOT holds nothing; run ci/promote.sh" >&2
    exit 1
fi
if ! gpgv --keyring "$KEYRING" "$ARCHIVE_ROOT/dists/stable/InRelease" >/dev/null 2>&1; then
    echo "$0: stable is not signed with the key kidux-archive-keyring ships" >&2
    exit 1
fi
if grep -q '^Version: .*~dev\.' "$INDEX"; then
    echo "$0: stable holds a development build" >&2
    exit 1
fi

echo "==> Packing the stable suite"
rm -rf "$OUT" "$TARBALL"
mkdir -p "$OUT/dists" "$OUT/bootstrap"
cp -r "$ARCHIVE_ROOT/dists/stable" "$OUT/dists/"
cp -r "$ARCHIVE_ROOT/bootstrap/stable" "$OUT/bootstrap/"
awk '/^Filename: / { print $2 }' "$INDEX" | while read -r file; do
    mkdir -p "$OUT/$(dirname "$file")"
    cp "$ARCHIVE_ROOT/$file" "$OUT/$file"
done
# Every package the index names is there, whole.
awk '/^Filename: / { file = $2 } /^SHA256: / { print $2 "  " file }' "$INDEX" \
    | (cd "$OUT" && sha256sum --check --quiet -)
tar -C "$OUT" --sort=name --owner=0 --group=0 --numeric-owner -cf "$TARBALL" .
awk '/^Package: / { name = $2 } /^Version: / { print "    " name " " $2 }' "$INDEX"
echo "    $(du -h "$TARBALL" | cut -f1) in $TARBALL"

if [ "${1:-}" = "--pack" ]; then
    exit 0
fi

echo "==> Sending it to the '$RELEASE' release"
if ! gh release view "$RELEASE" >/dev/null 2>&1; then
    gh release create "$RELEASE" --latest=false --title "Kidux package archive" \
        --notes "The stable suite of Kidux's package archive, as https://kidux.org/apt serves it. ci/publish-public.sh replaces it at each release; the site's workflow unpacks it."
fi
gh release upload "$RELEASE" "$TARBALL" --clobber

echo "==> Publishing the site with it"
gh workflow run site.yml --ref main
echo "    https://kidux.org/apt/dists/stable/InRelease answers with the new suite once"
echo "    the workflow has finished: gh run list --workflow site.yml --limit 1"
