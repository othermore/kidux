#!/bin/sh
# Put the page of the machines that follow the archive on the hosting.
#
#   ci/publish-usage.sh
#
# https://apt.kidux.org/usage/ shows what ci/usage.py counts from the
# hosting's access logs, behind a password (docs/dev/packaging.md, "The
# public archive"). Two places on the hosting, over the same SFTP as the
# archive:
#
#   kidux-usage/      in the account's home, which no site serves: usage.py,
#                     its list of tests' identifiers, the daily task
#                     cron.php, the logs space's address (logs.url), the
#                     logs user's line (logs.netrc), the page's password
#                     (.htpasswd), and logs/, every day's lines of
#                     apt.kidux.org as usage.py keeps them
#   apt/usage/        the page, index.php, and the .htaccess that asks for
#                     the password
#
# What it needs on this machine, outside the repository: the netrc file of
# ci/publish-public.sh, ~/.config/kidux/apt-hosting.netrc, with a line for
# the logs space's host beside the SFTP one; the logs space's address,
# ~/.config/kidux/usage-logs.url; and the page's password as Apache reads
# it, ~/.config/kidux/usage-page.htpasswd. None is printed. Run it again
# whenever ci/usage.py or ci/usage-site/ changes.

set -eu

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
NETRC="${KIDUX_APT_HOSTING:-$HOME/.config/kidux/apt-hosting.netrc}"
HTPASSWD="${KIDUX_USAGE_HTPASSWD:-$HOME/.config/kidux/usage-page.htpasswd}"
LOGS_URL="${KIDUX_USAGE_LOGS:-$HOME/.config/kidux/usage-logs.url}"

for file in "$NETRC" "$HTPASSWD" "$LOGS_URL"; do
    if [ ! -r "$file" ]; then
        echo "$0: $file is missing (docs/dev/packaging.md, \"The public archive\")" >&2
        exit 1
    fi
done
LOGS_HOST="$(sed -n 's|^https://\([^/]*\)/.*|\1|p' "$LOGS_URL" | head -1)"
if ! grep -q "^machine $LOGS_HOST " "$NETRC"; then
    echo "$0: $NETRC has no line for $LOGS_HOST, the logs user's" >&2
    exit 1
fi

HOST="$(awk '$1 == "machine" && $2 != "'"$LOGS_HOST"'" { print $2; exit }' "$NETRC")"
LOGIN="$(awk -v host="$HOST" '$2 == host { for (i = 1; i < NF; i++) if ($i == "login") print $(i + 1) }' "$NETRC" | head -1)"
HOME_DIR="/home/$LOGIN"
PRIVATE="$HOME_DIR/kidux-usage"
REMOTE="sftp://$HOST"

sftp() {
    # sftp <curl arguments>: a call on the hosting with the credentials, quiet.
    curl -sS --netrc-file "$NETRC" "$@"
}
put() {
    # put <local file> <remote path> <mode>
    sftp --ftp-create-dirs -T "$1" "$REMOTE$2"
    sftp -Q "chmod $3 $2" "$REMOTE$HOME_DIR/" -o /dev/null
    echo "    $2"
}

WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT
umask 077
grep "^machine $LOGS_HOST " "$NETRC" > "$WORK/logs.netrc"
sed "s|@PRIVATE@|$PRIVATE|" "$REPO_ROOT/ci/usage-site/htaccess.in" > "$WORK/htaccess"

echo "==> The private folder, which no site serves"
put "$REPO_ROOT/ci/usage.py" "$PRIVATE/usage.py" 600
put "$REPO_ROOT/ci/usage-test-ids.txt" "$PRIVATE/usage-test-ids.txt" 600
put "$REPO_ROOT/ci/usage-site/cron.php" "$PRIVATE/cron.php" 600
put "$WORK/logs.netrc" "$PRIVATE/logs.netrc" 600
put "$LOGS_URL" "$PRIVATE/logs.url" 600
put "$HTPASSWD" "$PRIVATE/.htpasswd" 644
sftp -Q "chmod 711 $PRIVATE" "$REMOTE$HOME_DIR/" -o /dev/null

echo "==> The page, behind its password"
put "$WORK/htaccess" "$HOME_DIR/apt/usage/.htaccess" 644
put "$REPO_ROOT/ci/usage-site/index.php" "$HOME_DIR/apt/usage/index.php" 644

echo "==> Checking that it asks for the password"
status="$(curl -sS -o /dev/null -w '%{http_code}' https://apt.kidux.org/usage/)"
if [ "$status" != 401 ]; then
    echo "$0: https://apt.kidux.org/usage/ answered $status without a password, not 401" >&2
    exit 1
fi
echo "    https://apt.kidux.org/usage/ asks for it (401); open it with the page's user"
