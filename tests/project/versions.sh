#!/bin/sh
# Every version a package states is the one its changelog gives it.
#
#   tests/project/versions.sh
#
# The newest debian/changelog entry is the package's version. A pyproject.toml
# or a VERSION constant that says something else reports a version that was
# never published: the daemon answers Ping with its VERSION.

set -u

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
failed=0

check() {
    # check <package> <file> <stated version> <changelog version>
    if [ "$3" = "$4" ]; then
        echo "PASS  $1: $2 says $4, as its changelog does"
    else
        echo "FAIL  $1: $2 says ${3:-nothing}, its changelog $4" >&2
        failed=$((failed + 1))
    fi
}

for dir in "$REPO_ROOT"/packages/*/; do
    package="$(basename "$dir")"
    [ -f "$dir/debian/changelog" ] || continue
    released="$(sed -n '1s/^[^(]*(\([^)]*\)).*/\1/p' "$dir/debian/changelog")"

    if [ -f "$dir/pyproject.toml" ]; then
        stated="$(sed -n 's/^version = "\(.*\)"$/\1/p' "$dir/pyproject.toml")"
        check "$package" pyproject.toml "$stated" "$released"
    fi

    # A learning module's manifest says its version too (modules.md).
    if [ -f "$dir/module.toml" ]; then
        stated="$(sed -n 's/^version = "\(.*\)"$/\1/p' "$dir/module.toml")"
        check "$package" module.toml "$stated" "$released"
    fi

    for init in "$dir"*/__init__.py; do
        [ -f "$init" ] || continue
        grep -Eq '^(VERSION|__version__) = ' "$init" || continue
        stated="$(sed -En 's/^(VERSION|__version__) = "(.*)"$/\2/p' "$init")"
        check "$package" "${init#"$dir"}" "$stated" "$released"
    done
done

exit "$failed"
