#!/bin/sh
# Every package under packages/ is in ci/build-all.sh's list, once.
#
#   tests/project/build-list.sh
#
# ci/build-all.sh names the packages it builds, in an order chosen by hand.
# A package left out of the list builds nowhere: not in the battery, not in
# the release, and the archive never gets it, while the test machines may
# still find a development build of it that a `tests/run vm push` left in
# testing, and pass.

set -u

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$REPO_ROOT"
failed=0

scratch="$(mktemp -d)"
trap 'rm -rf "$scratch"' EXIT
grep -E '^kidux-[a-z0-9-]+$' ci/build-all.sh | sort > "$scratch/listed"
for dir in packages/*/debian; do basename "$(dirname "$dir")"; done | sort > "$scratch/present"
missing="$(comm -13 "$scratch/listed" "$scratch/present")"
extra="$(comm -23 "$scratch/listed" "$scratch/present")"
twice="$(uniq -d "$scratch/listed")"

if [ -z "$missing" ]; then
    echo "PASS  every package under packages/ is built by ci/build-all.sh"
else
    echo "FAIL  ci/build-all.sh does not build: $(echo "$missing" | tr '\n' ' ')" >&2
    failed=$((failed + 1))
fi
if [ -z "$extra" ] && [ -z "$twice" ]; then
    echo "PASS  and it names nothing that is not a package, and nothing twice"
else
    echo "FAIL  ci/build-all.sh names packages that are not there or twice: $(echo "$extra" "$twice" | tr '\n' ' ')" >&2
    failed=$((failed + 1))
fi

exit $failed
