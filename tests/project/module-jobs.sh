#!/bin/sh
# kidux-update, which runs as root with a package name the daemon made,
# refuses anything that is not a module's package before it runs apt.
#
#   tests/project/module-jobs.sh
#
# Only names it must refuse are tried: a good one would run apt here.

set -u

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
SCRIPT="$REPO_ROOT/packages/kidux-daemon/bin/kidux-update"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT
failed=0

newline='kidux-module-hello
bash'
for name in "" "../hello" "hello" "kidux-module-" "kidux-module-Hello" "kidux-module-9lives" \
            "kidux-module-hello;reboot" "kidux-module-hello world" "kidux-module-hello/../x" \
            "kidux-module-$(printf 'a%.0s' $(seq 33))" "$newline" "kidux-base"; do
    for kind in install remove; do
        status="$WORK/status"
        rm -f "$status"
        KIDUX_UPDATE_STATUS="$status" sh "$SCRIPT" "$kind" "$name" >/dev/null 2>&1
        if [ "$(tail -n 1 "$status")" != "kidux:failed:not a module" ] \
           || grep -q '^kidux:module:' "$status"; then
            echo "FAIL  kidux-update $kind took $(printf '%s' "$name" | tr '\n' '|') for a module" >&2
            sed 's/^/      /' "$status" >&2
            failed=$((failed + 1))
        fi
    done
done

[ "$failed" -eq 0 ] && echo "PASS  kidux-update refuses every name that is not a module's package"
exit "$failed"
