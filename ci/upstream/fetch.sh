#!/bin/sh
# What an upstream build fetches, kept for its source tarball (D68, D71).
#
#   fetch.sh git <repository> <commit> <directory>    prints the commit's time
#   fetch.sh url <url> <file>
#
# Every build script fetches through this, never with git or curl itself,
# so that everything a build took from the network ends up in the source
# tarball ci/build-upstream.sh publishes beside the built one. A build that
# records (UPSTREAM_SOURCES set) fetches from the network and keeps a copy:
# a repository is checked out at the commit into the directory, with the
# one commit's history, and its tree, without that history, is kept under
# git/<name>-<commit>/ with the commit's time beside it; a file is kept
# under url/. A build from a source tarball (UPSTREAM_FROM set, the tarball
# unpacked) takes the same things from it, and reaches nothing: a
# repository's tree comes without .git, which no build here reads.

set -eu

KIND="${1:?usage: fetch.sh git <repository> <commit> <directory> | url <url> <file>}"
shift

slug() {
    printf '%s' "$1" | sed 's,^https://,,; s,\.git$,,; s,[^A-Za-z0-9._-],_,g'
}

case "$KIND" in
git)
    repository="$1"; commit="$2"; directory="$3"
    name="$(slug "$repository")-$commit"
    mkdir -p "$directory"
    if [ -n "${UPSTREAM_FROM:-}" ]; then
        kept="$UPSTREAM_FROM/git/$name"
        [ -d "$kept" ] || { echo "fetch.sh: the source tarball has no $name" >&2; exit 1; }
        cp -a "$kept/." "$directory/"
        cat "$kept.time"
        exit 0
    fi
    git -C "$directory" init -q
    git -C "$directory" fetch -q --depth 1 "$repository" "$commit"
    git -C "$directory" -c advice.detachedHead=false checkout -q FETCH_HEAD
    [ "$(git -C "$directory" rev-parse HEAD)" = "$commit" ] || {
        echo "fetch.sh: $repository gave another commit than $commit" >&2
        exit 1
    }
    time="$(git -C "$directory" log -1 --format=%ct)"
    if [ -n "${UPSTREAM_SOURCES:-}" ]; then
        mkdir -p "$UPSTREAM_SOURCES/git/$name"
        tar -C "$directory" --exclude=./.git -cf - . | tar -xf - -C "$UPSTREAM_SOURCES/git/$name"
        echo "$time" > "$UPSTREAM_SOURCES/git/$name.time"
    fi
    echo "$time"
    ;;
url)
    url="$1"; file="$2"
    name="$(slug "$url")"
    mkdir -p "$(dirname "$file")"
    if [ -n "${UPSTREAM_FROM:-}" ]; then
        [ -f "$UPSTREAM_FROM/url/$name" ] || { echo "fetch.sh: the source tarball has no $url" >&2; exit 1; }
        cp "$UPSTREAM_FROM/url/$name" "$file"
        exit 0
    fi
    curl -fsSL --retry 3 --retry-all-errors --connect-timeout 30 -o "$file" "$url"
    if [ -n "${UPSTREAM_SOURCES:-}" ]; then
        mkdir -p "$UPSTREAM_SOURCES/url"
        cp "$file" "$UPSTREAM_SOURCES/url/$name"
    fi
    ;;
*)
    echo "fetch.sh: no such kind: $KIND" >&2
    exit 2
    ;;
esac
