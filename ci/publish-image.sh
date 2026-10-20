#!/bin/sh
# Publish Kidux's images at https://iso.kidux.org: the installer and the
# images to try Kidux in an emulator (D116).
#
#   ci/publish-image.sh            the images of the newest build in build/image/
#   ci/publish-image.sh <name>     those of kidux-<version>-<date>, the name
#                                  every file of one build begins with
#
# One build's files are the installer, kidux-<version>-<date>-amd64.iso
# (ci/build-image.sh), and the trial images, kidux-<version>-<date>-trial-
# <language>.qcow2 and .ova (ci/build-trial-image.py), whichever were made.
# Beside them goes kidux-<version>-<date>.SHA256SUMS, their sums, and
# kidux-<version>-<date>.SHA256SUMS.sign, its signature: by the archive's
# key, which kidux-archive-keyring ships, for a release; by the development
# key for a `~dev` build, which is never a release.
#
# They go to the project's web hosting, the folder iso beside apt, over
# SFTP with the same credentials (~/.config/kidux/apt-hosting.netrc, or the
# file KIDUX_APT_HOSTING names), each uploaded under another name and put
# in place whole by a rename, the images first and the sums last. Then
# .htaccess sends the names without a version to the newest release's files,
# which the website's buttons and the user guide link to: kidux-amd64.iso,
# kidux-trial-<language>.qcow2 and .ova, and SHA256SUMS and SHA256SUMS.sign;
# and kidux-dev-… to the newest `~dev` build's, for trying. What neither the
# newest release nor the newest `~dev` build holds is removed.
#
# What the world sees is checked afterwards over HTTPS: the sums, identical
# and their signature good; each image's size, and its first and last
# mebibyte, the same as here; and each name without a version answering
# with the file it names.
#
# A release's images are published after ci/publish-public.sh, in
# ci/push.sh --then-publish's chain, inside the hours Kidux is seen
# working (D99); a `~dev` build's at any hour, since nothing links to them.

set -eu

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="${KIDUX_IMAGE_DIR:-$REPO_ROOT/build/image}"
NETRC="${KIDUX_APT_HOSTING:-$HOME/.config/kidux/apt-hosting.netrc}"
PUBLIC_URL="https://iso.kidux.org"
CHECK="$REPO_ROOT/build/image-check"
RELEASE_KEY=27E3FC17DBA9E4578268F8EEB3768AF190169C5E
DEVELOPMENT_KEY=C5635C3123C0A599645929CF813EF459076E9055
KEYRING="$REPO_ROOT/packages/kidux-archive-keyring/keyrings/kidux-archive-keyring.pgp"
DEVELOPMENT_KEYRING="$REPO_ROOT/ci/archive/development-key.pgp"

if [ $# -gt 0 ]; then
    NAME="$1"
else
    newest="$(ls -t "$OUT"/kidux-*-amd64.iso 2>/dev/null | head -1)"
    [ -n "$newest" ] || { echo "$0: no image in $OUT; ci/build-image.sh makes one" >&2; exit 1; }
    NAME="$(basename "$newest" -amd64.iso)"
fi
case "$NAME" in
    kidux-*~dev.*) dev=1; KEY="$DEVELOPMENT_KEY"; CHECK_KEYRING="$DEVELOPMENT_KEYRING"; ALIAS=kidux-dev ;;
    kidux-*) dev=0; KEY="$RELEASE_KEY"; CHECK_KEYRING="$KEYRING"; ALIAS=kidux ;;
    *) echo "usage: $0 [kidux-<version>-<date>]" >&2; exit 2 ;;
esac
if [ "$dev" = 0 ] && ! "$REPO_ROOT/ci/hours.py" allowed; then
    exit 2
fi
[ -r "$NETRC" ] || { echo "$0: no credentials for the hosting at $NETRC" >&2; exit 1; }

FILES="$(cd "$OUT" && ls "$NAME-amd64.iso" "$NAME"-trial-*.qcow2 "$NAME"-trial-*.ova 2>/dev/null || true)"
case "$FILES" in
    *"$NAME-amd64.iso"*) ;;
    *) echo "$0: $OUT has no $NAME-amd64.iso" >&2; exit 1 ;;
esac

echo "==> The sums of $NAME, signed with $KEY"
(cd "$OUT" && sha256sum $FILES > "$NAME.SHA256SUMS")
rm -f "$OUT/$NAME.SHA256SUMS.sign"
gpg --batch --yes --quiet --local-user "$KEY" --armor --detach-sign \
    --output "$OUT/$NAME.SHA256SUMS.sign" "$OUT/$NAME.SHA256SUMS"
sed 's/^/    /' "$OUT/$NAME.SHA256SUMS"

# --- The hosting -------------------------------------------------------------

HOST="$(awk '$1 == "machine" { print $2; exit }' "$NETRC")"
LOGIN="$(awk '{ for (i = 1; i < NF; i++) if ($i == "login") print $(i + 1) }' "$NETRC" | head -1)"
[ -n "$HOST" ] && [ -n "$LOGIN" ] || { echo "$0: $NETRC names no machine or no login" >&2; exit 1; }
REMOTE_DIR="/home/$LOGIN/iso"
REMOTE="sftp://$HOST$REMOTE_DIR"

sftp() {
    curl -sS --netrc-file "$NETRC" "$@"
}

put() {
    # put <local file> <remote name>: uploaded beside, then renamed into place.
    sftp -T "$1" "$REMOTE/$2.part"
    sftp -Q "rm $REMOTE_DIR/$2" "$REMOTE/" -o /dev/null 2>/dev/null || true
    sftp -Q "rename $REMOTE_DIR/$2.part $REMOTE_DIR/$2" "$REMOTE/" -o /dev/null
    echo "    $2"
}

if ! sftp -l "$REMOTE/" >/dev/null 2>&1; then
    echo "$0: cannot list $REMOTE_DIR on $HOST with $NETRC" >&2
    exit 1
fi

echo "==> Sending the images to $HOST, the sums last"
for file in $FILES "$NAME.SHA256SUMS" "$NAME.SHA256SUMS.sign"; do
    put "$OUT/$file" "$file"
done

# The names without a version: this build's for its kind, the other kind's
# as they were.
mkdir -p "$CHECK"
rm -f "$CHECK/htaccess"
sftp -o "$CHECK/htaccess" "$REMOTE/.htaccess" 2>/dev/null || : > "$CHECK/htaccess"
{
    echo "# Written by ci/publish-image.sh: the names without a version, for the"
    echo "# newest release (kidux-…) and the newest development build (kidux-dev-…)."
    # The other kind's lines, as they were.
    awk -v dev="$dev" '$1 == "Redirect" {
        mine = dev ? ($3 ~ /^\/kidux-dev[-.]/) : ($3 ~ /^\/SHA256SUMS/ || ($3 ~ /^\/kidux-/ && $3 !~ /^\/kidux-dev[-.]/))
        if (!mine) print
    }' "$CHECK/htaccess"
    for file in $FILES; do
        echo "Redirect 302 /$ALIAS-${file#"$NAME"-} /$file"
    done
    if [ "$dev" = 1 ]; then
        echo "Redirect 302 /$ALIAS.SHA256SUMS /$NAME.SHA256SUMS"
        echo "Redirect 302 /$ALIAS.SHA256SUMS.sign /$NAME.SHA256SUMS.sign"
    else
        echo "Redirect 302 /SHA256SUMS /$NAME.SHA256SUMS"
        echo "Redirect 302 /SHA256SUMS.sign /$NAME.SHA256SUMS.sign"
    fi
} > "$CHECK/htaccess.new"
put "$CHECK/htaccess.new" .htaccess

echo "==> Removing what neither the newest release nor the newest development build holds"
kept="$(grep '^Redirect' "$CHECK/htaccess.new" | awk '{ print substr($4, 2) }')"
sftp -l "$REMOTE/" | while read -r file; do
    case "$file" in
        kidux-*) ;;
        *) continue ;;
    esac
    if ! printf '%s\n' "$kept" | grep -qxF "$file"; then
        sftp -Q "rm $REMOTE_DIR/$file" "$REMOTE/" -o /dev/null
        echo "    $file"
    fi
done

echo "==> Checking what the world sees at $PUBLIC_URL"
curl -fsS -o "$CHECK/SHA256SUMS" "$PUBLIC_URL/$NAME.SHA256SUMS"
curl -fsS -o "$CHECK/SHA256SUMS.sign" "$PUBLIC_URL/$NAME.SHA256SUMS.sign"
cmp -s "$CHECK/SHA256SUMS" "$OUT/$NAME.SHA256SUMS" \
    || { echo "$0: the published sums are not the ones just sent" >&2; exit 1; }
gpgv --keyring "$CHECK_KEYRING" "$CHECK/SHA256SUMS.sign" "$CHECK/SHA256SUMS" >/dev/null 2>&1 \
    || { echo "$0: the published sums' signature is not good" >&2; exit 1; }
for file in $FILES; do
    size="$(stat -c %s "$OUT/$file")"
    published="$(curl -fsSI "$PUBLIC_URL/$file" | tr -d '\r' | awk 'tolower($1) == "content-length:" { print $2 }' | tail -1)"
    [ "$published" = "$size" ] \
        || { echo "$0: $PUBLIC_URL/$file has $published bytes, not $size" >&2; exit 1; }
    for range in "0-1048575" "$((size - 1048576))-$((size - 1))"; do
        curl -fsS -r "$range" -o "$CHECK/part" "$PUBLIC_URL/$file"
        start="${range%-*}"
        tail -c +"$((start + 1))" "$OUT/$file" | head -c 1048576 | cmp -s - "$CHECK/part" \
            || { echo "$0: $PUBLIC_URL/$file differs from $file in bytes $range" >&2; exit 1; }
    done
    alias="$ALIAS-${file#"$NAME"-}"
    target="$(curl -fsS -o /dev/null -w '%{redirect_url}' "$PUBLIC_URL/$alias" | sed 's/%7[Ee]/~/g')"
    case "$target" in
        */"$file") ;;
        *) echo "$0: $PUBLIC_URL/$alias leads to '$target', not $file" >&2; exit 1 ;;
    esac
    echo "    $file: $size bytes, its ends identical; $alias leads to it"
done
rm -f "$CHECK/part"
echo "    the sums identical, and signed"
