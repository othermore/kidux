#!/bin/sh
# Serve the archive at http://kidux.local/apt without nginx, for CI.
#
#   ci/serve-archive.sh [root]      as root: port 80
#
# The development machine serves /srv/kidux-apt with nginx
# (ci/setup-dev-host.sh). A CI container has no nginx and needs none: the
# test machines only fetch static files. /srv/www holds a link apt ->
# /srv/kidux-apt, which ci/setup-ci-host.sh makes, so the paths are the same.
# Runs in the background and says where; stop it by killing that pid.

set -eu

ROOT="${1:-/srv/www}"
LOG="${KIDUX_SERVE_LOG:-/tmp/kidux-serve-archive.log}"

python3 -m http.server 80 --bind 0.0.0.0 --directory "$ROOT" >"$LOG" 2>&1 &
echo "$!" > /tmp/kidux-serve-archive.pid
for _ in $(seq 50); do
    if curl -fsS -o /dev/null http://127.0.0.1/apt/ 2>/dev/null \
       || curl -fsS -o /dev/null http://127.0.0.1/ 2>/dev/null; then
        echo "==> Serving $ROOT on port 80 (pid $(cat /tmp/kidux-serve-archive.pid))"
        exit 0
    fi
    sleep 0.2
done
echo "$0: the server did not start; see $LOG" >&2
exit 1
