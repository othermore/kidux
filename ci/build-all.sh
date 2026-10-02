#!/bin/sh
# Build every Kidux package.
#
# The order is explicit rather than computed: there are few packages, each one
# is a deliberate step in the plan, and a wrong guess at build order is a
# confusing failure rather than an obvious one. Two come first, one after the
# other, because the others need them to build: the keyring, and kidux-common,
# whose python3-kidux the daemon, the screens and the modules install to run
# their tests. The rest need nothing from each other, so they build at once,
# each with its log in build/logs/, and the script waits for all of them and
# says how each went.

set -eu

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BUILD_DIR="${KIDUX_BUILD_DIR:-$REPO_ROOT/build}"

# The project-wide checks first. They are quick, and a package that builds
# perfectly while carrying an untranslated string is not a package we want in
# the archive.
"$REPO_ROOT/tests/run" project
echo

FIRST="
kidux-archive-keyring
kidux-common
"

REST="
kidux-daemon
kidux-greeter
kidux-launcher
kidux-module-hello
kidux-module-gcompris
kidux-module-tuxtype
kidux-module-scratch
kidux-module-scratchjr
kidux-module-turbowarp
kidux-module-blockly-games
kidux-webapps
kidux-module-hello-web
kidux-session
kidux-base
"

for package in $FIRST; do
    "$REPO_ROOT/ci/build-package.sh" "$package"
done

"$REPO_ROOT/ci/build-parallel.sh" "$BUILD_DIR" $REST

echo
echo "==> All packages built. Publish them with ci/publish-local.sh"
