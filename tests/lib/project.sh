#!/bin/sh
# Every check on the project as a whole: each file in tests/project/.
#
#   tests/run project
#
# Run before committing. ci/build-all.sh runs this first, so that a change
# which builds perfectly but leaves a Spanish child an English screen cannot
# reach the archive. A new check is a new executable file in tests/project/;
# nothing here needs to know its name. The exit status is the number of checks
# that failed.

set -u

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$REPO_ROOT"

failed=0
for check in tests/project/*; do
    [ -x "$check" ] || continue
    echo "==> $check"
    if ! "$check"; then
        failed=$((failed + 1))
    fi
    echo
done

if [ "$failed" -eq 0 ]; then
    echo "==> All project checks passed."
else
    echo "==> $failed project checks failed." >&2
fi
exit "$failed"
