#!/bin/sh
# Every package built from a program that is not in trixie says where it
# comes from, and nothing of its build is in git (D68).
#
#   tests/project/upstream.sh
#
# A packages/<package>/upstream.toml has its fields; its commit is a whole
# git hash; its sha256 and source_sha256 are both empty, before the first
# build, or both whole SHA-256s (D71); the package's changelog version
# starts with its version; its build script is there, parses, and fetches
# nothing itself but through ci/upstream/fetch.sh, so that its source
# tarball holds everything it took. No packages/*/upstream/ is tracked. And
# the check of a built site (ci/upstream/check-site.py) tells a site built
# for its path from one built for the root.

set -u

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$REPO_ROOT"
failed=0

pass() { echo "PASS  $1"; }
fail() { echo "FAIL  $1" >&2; failed=$((failed + 1)); }

for toml in packages/*/upstream.toml; do
    [ -f "$toml" ] || continue
    package="$(basename "$(dirname "$toml")")"
    field() { python3 ci/upstream/upstream.py "$package" "$1" 2>/dev/null; }
    missing=""
    for name in name repository commit version build; do
        [ -n "$(field "$name")" ] || missing="$missing $name"
    done
    if [ -n "$missing" ]; then
        fail "$package: upstream.toml lacks$missing"
        continue
    fi
    commit="$(field commit)"
    sum="$(field sha256)"
    source_sum="$(field source_sha256)"
    version="$(field version)"
    build="$(field build)"
    released="$(sed -n '1s/^[^(]*(\([^)]*\)).*/\1/p' "packages/$package/debian/changelog")"
    if printf '%s' "$commit" | grep -Eqx '[0-9a-f]{40}' \
            && { { [ -z "$sum" ] && [ -z "$source_sum" ]; } \
                 || { printf '%s' "$sum" | grep -Eqx '[0-9a-f]{64}' \
                      && printf '%s' "$source_sum" | grep -Eqx '[0-9a-f]{64}'; }; } \
            && case "$released" in "$version"*) true ;; *) false ;; esac \
            && [ -f "$build" ] && sh -n "$build"; then
        pass "$package: built from $(field name) at ${commit%"${commit#????????????}"}, $version"
    else
        fail "$package: upstream.toml is not whole: commit $commit, sha256 ${sum:-none}, source_sha256 ${source_sum:-none}, version $version against the changelog's $released, build $build"
    fi
    fetching="$(grep -nE '^[[:space:]]*(git|curl|wget|svn)[[:space:]]' "$build" || true)"
    if [ -z "$fetching" ]; then
        pass "$package: its build fetches only through ci/upstream/fetch.sh"
    else
        fail "$package: $build fetches by itself, out of its source tarball: $fetching"
    fi
done

tracked="$(git ls-files 'packages/*/upstream/*' | head -5)"
if [ -z "$tracked" ]; then
    pass "no program built at development time is in git"
else
    fail "these are in git, and belong in a tarball: $tracked"
fi

scratch="$(mktemp -d)"
trap 'rm -rf "$scratch"' EXIT
mkdir -p "$scratch/right/static" "$scratch/wrong/static"
printf '<script src="/scratch/static/main.js"></script><a href="https://example.org/">x</a>\n' \
    > "$scratch/right/index.html"
printf 'fetch("./static/data.json")\n' > "$scratch/right/static/main.js"
printf '<script src="/static/main.js"></script>\n' > "$scratch/wrong/index.html"
mkdir -p "$scratch/rooted"
printf 'var o={};o.p="/";\n' > "$scratch/rooted/main.js"
printf 'var o={};o.p="";var n={};n.p="/scratch/";\n' > "$scratch/right/static/chunk.js"
if ci/upstream/check-site.py "$scratch/right" /scratch/ >/dev/null 2>&1 \
        && ! ci/upstream/check-site.py "$scratch/wrong" /scratch/ >/dev/null 2>&1 \
        && ! ci/upstream/check-site.py "$scratch/rooted" /scratch/ >/dev/null 2>&1; then
    pass "a site built for its path is told from one built for the root, or with a public path at the root"
else
    fail "ci/upstream/check-site.py does not tell a site built for its path from one built for the root"
fi

[ "$failed" -eq 0 ]
