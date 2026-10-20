#!/bin/sh
# Push main to GitHub, inside the hours Kidux is seen working (D99).
#
#   ci/push.sh                  now, inside the hours: the commits not yet on GitHub are
#                               dated inside them, ending now, then pushed
#   ci/push.sh --later          the same at the next moment the hours allow, by a timer of
#                               the user's systemd; nothing to watch for
#   ci/push.sh --then-publish   the last steps of a release around the push:
#                               ci/promote.sh and ci/publish-image.sh before it,
#                               ci/publish-public.sh after it; with --later, at
#                               the timer's push
#
# Nothing of Kidux's goes to GitHub by any other way: a commit made in the
# day is pushed in the evening with the evening's dates, the author's and the
# committer's alike, the same tree, message and author (ci/hours.py). Only
# commits not yet on origin/main are dated again, and as the very last step
# before the push: a commit once pushed never changes. The timer is a unit of
# the user's systemd, which lives while the user has a session or lingers
# (loginctl enable-linger); the script says so when it does not.

set -eu

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"
HOURS="$REPO_ROOT/ci/hours.py"
LATER=""
PUBLISH=""
for argument in "$@"; do
    case "$argument" in
        --later) LATER=yes ;;
        --then-publish) PUBLISH=yes ;;
        *) echo "usage: $0 [--later] [--then-publish]" >&2; exit 2 ;;
    esac
done

if [ "$(git rev-parse --abbrev-ref HEAD)" != main ]; then
    echo "$0: only main is pushed, and this is $(git rev-parse --abbrev-ref HEAD)" >&2
    exit 2
fi
if [ -n "$(git status --porcelain)" ]; then
    echo "$0: the tree has changes not committed:" >&2
    git status --short >&2
    exit 2
fi

if ! "$HOURS" allowed; then
    if [ -z "$LATER" ]; then
        echo "$0: run it then, or now with --later, which sets a timer" >&2
        exit 2
    fi
    when="$("$HOURS" next --calendar)"
    unit="kidux-push-$(date +%s)"
    systemd-run --user --quiet --collect --unit="$unit" --on-calendar="$when" \
        --working-directory="$REPO_ROOT" "$REPO_ROOT/ci/push.sh" ${PUBLISH:+--then-publish}
    echo "==> The push is set for $when, as $unit: systemctl --user list-timers;"
    echo "    what it did: journalctl --user -u $unit"
    if [ "$(loginctl show-user "$(id -un)" -p Linger --value 2>/dev/null)" != yes ]; then
        echo "    The timer lives only while you have a session on this machine; to keep it"
        echo "    without one: sudo loginctl enable-linger $(id -un)"
    fi
    exit 0
fi

git fetch -q origin
base="$(git rev-parse origin/main)"
old="$(git rev-parse HEAD)"
if ! git merge-base --is-ancestor "$base" "$old"; then
    echo "$0: origin/main is not behind main; pull first" >&2
    exit 2
fi
count="$(git rev-list --count "$base..$old")"

# A release's images go up before the push: the website, which a push of
# site/ publishes at once, and the README link to them by their names
# without a version. Neither the promotion nor the images touch GitHub.
if [ -n "$PUBLISH" ]; then
    "$REPO_ROOT/ci/promote.sh"
    "$REPO_ROOT/ci/publish-image.sh"
fi

if [ "$count" -eq 0 ]; then
    echo "==> Nothing to push: origin/main is main."
else
    new="$("$HOURS" redate "$base" "$old")"
    git update-ref -m "ci/push.sh: dated inside the hours" refs/heads/main "$new" "$old"
    echo "==> $count commit(s) dated inside the hours, $old -> $new"
    git push origin main
    echo "==> Pushed main, $(git rev-parse --short HEAD), at $(date '+%H:%M')"
fi

if [ -n "$PUBLISH" ]; then
    "$REPO_ROOT/ci/publish-public.sh"
fi
