#!/bin/sh
# The logo, mascot and splash the packages ship are the ones in branding/.
#
#   tests/project/branding.sh
#
# A package's source can only hold what is in its own directory, so
# ci/render-branding.sh copies them in; this fails if a copy was forgotten.

set -u

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
failed=0

same() {
    # same <original> <copy>
    if cmp -s "$REPO_ROOT/$1" "$REPO_ROOT/$2"; then
        echo "PASS  $2 is $1"
    else
        echo "FAIL  $2 differs from $1; run ci/render-branding.sh" >&2
        failed=$((failed + 1))
    fi
}

same branding/svg/logo.svg packages/kidux-common/data/branding/logo.svg
same branding/svg/mascot.svg packages/kidux-common/data/branding/mascot.svg
same branding/png/logo-512.png packages/kidux-session/plymouth/logo.png
same branding/png/mascot-256.png packages/kidux-installer/calamares/branding/kidux/mascot.png
same branding/png/icon-128.png packages/kidux-installer/calamares/branding/kidux/icon.png
same branding/png/logo-512.png packages/kidux-installer/calamares/branding/kidux/logo.png

exit "$failed"
