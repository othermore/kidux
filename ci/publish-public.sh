#!/bin/sh
# Publish the stable suite at https://apt.kidux.org, and at https://kidux.org/apt
# for the machines that still follow it.
#
#   ci/publish-public.sh            pack stable, send it to the hosting and to GitHub, and
#                                   check what the world sees
#   ci/publish-public.sh --pack     pack it only, into build/public-archive and
#                                   build/kidux-apt.tar
#
# The public archive is the stable suite as it stands in the local archive,
# byte for byte: its indexes with their signature, the packages they name and
# the two bootstrap packages (docs/dev/packaging.md, "The public archive";
# D82, D109). It goes to the project's web hosting over SFTP, with the
# credentials in ~/.config/kidux/apt-hosting.netrc (KIDUX_APT_HOSTING names
# another file), in an order a machine can fetch from at any moment: the
# packages first, then the indexes, each put in place whole by a rename, and
# InRelease last; then what no index names any more is removed. What the
# world sees is checked afterwards: InRelease fetched over HTTPS, verified
# against the keyring and compared with the local one, and one package
# compared by its hash.
#
# Then, as long as machines installed before kidux-apt-source 0.1.5 follow
# https://kidux.org/apt, the suite is packed into one tarball, sent to the
# repository's `archive` release, and the site's workflow unpacks it under
# apt/ beside the pages.
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
CHECK="$REPO_ROOT/build/public-check"
RELEASE=archive
INDEX="$ARCHIVE_ROOT/dists/stable/main/binary-amd64/Packages"
PUBLIC_URL="https://apt.kidux.org"
NETRC="${KIDUX_APT_HOSTING:-$HOME/.config/kidux/apt-hosting.netrc}"

case "${1:-}" in
    ""|--pack) ;;
    *) echo "usage: $0 [--pack]" >&2; exit 2 ;;
esac
# The release on GitHub, and the site's run, show when they were made: inside
# the hours Kidux is seen working (D99); ci/push.sh --then-publish keeps to them.
if [ "${1:-}" != "--pack" ] && ! "$REPO_ROOT/ci/hours.py" allowed; then
    exit 2
fi

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
if [ "${1:-}" != "--pack" ] && [ ! -r "$NETRC" ]; then
    echo "$0: no credentials for the hosting at $NETRC (a netrc line: machine <host> login <user> password <password>)" >&2
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

# --- The hosting -------------------------------------------------------------

HOST="$(awk '$1 == "machine" { print $2; exit }' "$NETRC")"
LOGIN="$(awk '{ for (i = 1; i < NF; i++) if ($i == "login") print $(i + 1) }' "$NETRC" | head -1)"
if [ -z "$HOST" ] || [ -z "$LOGIN" ]; then
    echo "$0: $NETRC names no machine or no login" >&2
    exit 1
fi
# The folder the subdomain is served from, under the SFTP user's home; the
# quote commands below need it absolute.
REMOTE_DIR="/home/$LOGIN/apt"
REMOTE="sftp://$HOST$REMOTE_DIR"

sftp() {
    # sftp <curl arguments>: a call on the hosting with the credentials, quiet.
    curl -sS --netrc-file "$NETRC" "$@"
}

# listed <remote directory>: the names in it, without . and ..
listed() {
    sftp -l "$REMOTE/$1" 2>/dev/null | grep -v '^\.\{1,2\}$' || true
}

if ! sftp -l "$REMOTE/" >/dev/null 2>&1; then
    echo "$0: cannot list $REMOTE_DIR on $HOST with $NETRC" >&2
    exit 1
fi

echo "==> Sending the packages to $HOST"
(cd "$OUT" && find pool bootstrap -type f | sort) | while read -r file; do
    sftp --ftp-create-dirs -T "$OUT/$file" "$REMOTE/$file"
    echo "    $file"
done

echo "==> Sending the indexes, InRelease last"
# A machine fetching meanwhile sees each index either old or new, never half
# written: the new one is uploaded under another name and renamed into place.
# The hosting's SFTP refuses to rename over a file, so the old one goes first,
# and the index is missing for that instant rather than wrong.
(cd "$OUT" && find dists -type f ! -name InRelease | sort; echo dists/stable/InRelease) \
    | while read -r file; do
    sftp --ftp-create-dirs -T "$OUT/$file" "$REMOTE/$file.new"
    sftp -Q "rm $REMOTE_DIR/$file" "$REMOTE/" -o /dev/null 2>/dev/null || true
    sftp -Q "rename $REMOTE_DIR/$file.new $REMOTE_DIR/$file" "$REMOTE/" -o /dev/null
    echo "    $file"
done

echo "==> Removing what no index names any more"
for letter in $(listed pool/main); do
    for package in $(listed "pool/main/$letter"); do
        for file in $(listed "pool/main/$letter/$package"); do
            if [ ! -f "$OUT/pool/main/$letter/$package/$file" ]; then
                sftp -Q "rm $REMOTE_DIR/pool/main/$letter/$package/$file" "$REMOTE/" -o /dev/null
                echo "    pool/main/$letter/$package/$file"
            fi
        done
        if [ -z "$(listed "pool/main/$letter/$package")" ]; then
            sftp -Q "rmdir $REMOTE_DIR/pool/main/$letter/$package" "$REMOTE/" -o /dev/null
        fi
    done
done

echo "==> Checking what the world sees at $PUBLIC_URL"
rm -rf "$CHECK"
mkdir -p "$CHECK"
if ! curl -fsS -o "$CHECK/InRelease" "$PUBLIC_URL/dists/stable/InRelease"; then
    echo "$0: $PUBLIC_URL/dists/stable/InRelease cannot be fetched; is the hosting's" >&2
    echo "    certificate issued for apt.kidux.org, and does the name resolve to it?" >&2
    exit 1
fi
if ! gpgv --keyring "$KEYRING" "$CHECK/InRelease" >/dev/null 2>&1; then
    echo "$0: the published InRelease is not signed with the key kidux-archive-keyring ships" >&2
    exit 1
fi
if ! cmp -s "$CHECK/InRelease" "$OUT/dists/stable/InRelease"; then
    echo "$0: the published InRelease is not the one just sent" >&2
    exit 1
fi
first="$(awk '/^Filename: / { print $2; exit }' "$INDEX")"
curl -fsS -o "$CHECK/package.deb" "$PUBLIC_URL/$first"
expected="$(awk -v file="$first" '/^Filename: / { here = ($2 == file) } here && /^SHA256: / { print $2; exit }' "$INDEX")"
if [ "$(sha256sum "$CHECK/package.deb" | cut -d' ' -f1)" != "$expected" ]; then
    echo "$0: $PUBLIC_URL/$first is not the package the index names" >&2
    exit 1
fi
echo "    InRelease verified and identical; $first identical"

# --- The old address, while machines follow it -------------------------------

echo "==> Sending it to the '$RELEASE' release, for https://kidux.org/apt"
if ! gh release view "$RELEASE" >/dev/null 2>&1; then
    gh release create "$RELEASE" --latest=false --title "Kidux package archive" \
        --notes "The stable suite of Kidux's package archive, as https://kidux.org/apt serves it for the machines that still follow that address. ci/publish-public.sh replaces it at each release; the site's workflow unpacks it."
fi
gh release upload "$RELEASE" "$TARBALL" --clobber

echo "==> Publishing the site with it"
gh workflow run site.yml --ref main
echo "    https://kidux.org/apt/dists/stable/InRelease answers with the new suite once"
echo "    the workflow has finished: gh run list --workflow site.yml --limit 1"
