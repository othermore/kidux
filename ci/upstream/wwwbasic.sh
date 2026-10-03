#!/bin/sh
# wwwBASIC, for kidux-module-basic (D84).
#
# Run by ci/build-upstream.sh kidux-module-basic, in an empty directory.
# wwwBASIC is one JavaScript file with nothing to build: its repository
# keeps it as a script (wwwbasic.js, which node's require() reads, for the
# module's tests) and as a module (wwwbasic.mjs, which the module's page
# imports, and which gives the page its bindings). Both are taken as they
# are at the commit, with the licence, the README and wwwBASIC's own tests.

set -eu

epoch="$(sh "$UPSTREAM_FETCH" git "$UPSTREAM_REPOSITORY" "$UPSTREAM_COMMIT" src)"
out="$PWD/out"
mkdir -p "$out/test"
cp src/wwwbasic.js src/wwwbasic.mjs src/LICENSE src/README.md "$out/"
cp src/test/*.js "$out/test/"
echo "==> $(find "$out" -type f | wc -l) files"
sh "$UPSTREAM_PACK" "$out" "$UPSTREAM_PACKAGE-$UPSTREAM_VERSION" \
    "$UPSTREAM_OUT/$UPSTREAM_TARBALL" "$epoch"
