#!/bin/sh
# Refuse anything under packages/, image/, ci/ or tests/ that names the machine it was
# written on.
#
#   tests/project/no-local-identity.sh
#
# Kidux has to work on machines nobody here has ever seen (D18): it depends on
# groups, never on names, and nothing it ships may carry a developer's user
# name, home directory, host address or e-mail. A path like /home/someone left
# in a script works perfectly on the machine that wrote it and nowhere else,
# which is exactly the kind of bug nobody here would ever notice.
#
# What counts as local is read from the machine running the check, so the same
# script works for anyone. The maintainer's address is identity on purpose,
# not by accident, where a package or a catalogue names who to write to:
# debian/changelog, debian/control, debian/copyright and gettext's headers.

set -eu

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$REPO_ROOT"

user="$(id -un)"
home="${HOME:-/home/$user}"
email="$(git config user.email 2>/dev/null || true)"
# In CI the machine running this is nobody's: the author of the change being
# checked is who it must not name, and git knows their address.
author="$(git log -1 --format=%ae 2>/dev/null || true)"
addresses="$(hostname -I 2>/dev/null || true)"

patterns=""
add() {
    [ -n "$1" ] || return 0
    patterns="$patterns
$1"
}
add "$home"
add "/home/$user"
add "$email"
[ "$author" = "$email" ] || add "$author"
for address in $addresses; do
    case "$address" in
        127.*|::1|10.0.2.*) ;;   # loopback and QEMU's user network are everyone's
        *) add "$address" ;;
    esac
done

patterns="$(printf '%s\n' "$patterns" | sed '/^$/d' | sort -u)"
if [ -z "$patterns" ]; then
    echo "==> Nothing local to look for."
    exit 0
fi

found="$(git ls-files packages image ci tests 2>/dev/null \
    | grep -v -E '^packages/[^/]+/debian/(changelog|control|copyright)$' \
    | grep -v '^tests/project/no-local-identity.sh$' \
    | xargs -r grep -n -F -I "$(printf '%s\n' "$patterns")" 2>/dev/null || true)"

# A user name on its own is too short to search for without false alarms, so
# it is only looked for where it would be a path or an owner.
by_name="$(git ls-files packages image ci tests 2>/dev/null \
    | grep -v -E '^packages/[^/]+/debian/(changelog|control|copyright)$' \
    | grep -v '^tests/project/no-local-identity.sh$' \
    | xargs -r grep -n -E -I "(/home/$user\\b|\\b$user:|User=$user\\b|-u $user\\b)" 2>/dev/null || true)"

# The maintainer's address is also the contact for translations, on purpose:
# gettext's bug-report and last-translator headers, and the flag that writes
# them.
all="$(printf '%s\n%s\n' "$found" "$by_name" \
    | grep -v -E 'Report-Msgid-Bugs-To|Last-Translator|--msgid-bugs-address' \
    | sed '/^$/d' | sort -u)"

if [ -z "$all" ]; then
    echo "PASS  nothing under packages/, image/, ci/ or tests/ names this machine"
    exit 0
fi

echo "FAIL  these name the machine they were written on:" >&2
printf '%s\n' "$all" | sed 's/^/      /' >&2
exit 1
