#!/bin/sh
# Build a program that is not in trixie into the tarball its package is
# built from, and keep everything the build fetched in a source tarball
# beside it (D68, D71, docs/dev/packaging.md "Programs built at development
# time").
#
#   ci/build-upstream.sh <package>                  build it into build/upstream/
#   ci/build-upstream.sh <package> --publish        and put both in a GitHub release
#   ci/build-upstream.sh <package> --from-source [<source tarball>]
#                                                   build it again from its source
#                                                   tarball alone, without the network
#
# packages/<package>/upstream.toml names the repository, the commit, the
# version, the Node.js release the build needs and the build script. The
# script runs here, on the development machine, in a fresh
# build/upstream/work/<package>/, with the Node.js release of
# ci/upstream/node.sh first in its PATH, a home of its own, and these in
# its environment:
#
#   UPSTREAM_PACKAGE, UPSTREAM_REPOSITORY, UPSTREAM_COMMIT, UPSTREAM_VERSION
#   UPSTREAM_OUT          where the tarball goes
#   UPSTREAM_TARBALL      its file name, <package>_<version>.orig.tar.xz
#   UPSTREAM_FETCH        ci/upstream/fetch.sh, through which it fetches
#                         every repository and file it needs
#   UPSTREAM_KEEP         a directory for what else the source tarball must
#                         hold, such as a lock file npm wrote (a build)
#   UPSTREAM_KEPT         the same directory, read back (a build from source)
#
# and writes the tarball: one top-level directory, <package>-<version>/,
# made with ci/upstream/pack.sh so that the same tree gives the same bytes.
# Its SHA-256 is written into upstream.toml the first time; a later build
# whose sum differs is an error, since a version's bytes never change and a
# new build is a new version.
#
# The source tarball, <package>_<version>.source.tar.xz, holds what the
# build fetched: every repository's tree at its commit and every file
# (ci/upstream/fetch.sh), npm's cache of every package it installed, its
# cache directory (XDG_CACHE_HOME), where Electron's downloads go, the
# Node.js release, the lock files the script kept, and the scripts of this
# repository that build it. It is made by the
# first build of a version, and its SHA-256 recorded as source_sha256; npm's
# cache holds the times it was filled, so a later build's copy differs, and
# the recorded one, published, is the version's source. --from-source takes
# it, from build/upstream/ or its release, builds with npm offline in a
# network namespace of its own, where nothing but the loopback answers, and
# checks that the tarball is the recorded one.
#
# The log is build/upstream/<package>.log; the work directory stays after a
# failed build, to be looked at. Nothing here installs anything on the
# machine. What a build needs that the machine has not, it downloads under
# build/, checked; packaging.md lists what the development machine has to
# have.

set -eu

PACKAGE="${1:?usage: ci/build-upstream.sh <package> [--publish | --from-source [<tarball>]]}"
MODE="${2:-}"
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"
field() { python3 ci/upstream/upstream.py "$PACKAGE" "$1"; }

[ -f "packages/$PACKAGE/upstream.toml" ] || {
    echo "$0: packages/$PACKAGE has no upstream.toml" >&2
    exit 2
}
case "$MODE" in
    ""|--publish|--from-source) ;;
    *) echo "$0: no such option: $MODE" >&2; exit 2 ;;
esac

for tool in git curl xz tar python3 make unshare; do
    command -v "$tool" >/dev/null || {
        echo "$0: $tool is missing; packaging.md lists what this machine needs" >&2
        exit 2
    }
done

REPOSITORY="$(field repository)"
COMMIT="$(field commit)"
VERSION="$(field version)"
NODE="$(field node)"
BUILD="$(field build)"
RECORDED="$(field sha256)"
RECORDED_SOURCE="$(field source_sha256)"
TARBALL="$(field tarball)"
SOURCE="$(field source)"
OUT="$REPO_ROOT/build/upstream"
WORK="$OUT/work/$PACKAGE"
LOG="$OUT/$PACKAGE.log"
SOURCES="$OUT/sources/$PACKAGE"
# The build's home and caches, beside its work directory, not in it.
AROUND="$OUT/work/$PACKAGE.around"
FROM=""

mkdir -p "$OUT"
rm -rf "$WORK" "$AROUND" "$SOURCES"
mkdir -p "$WORK" "$AROUND/home"

if [ "$MODE" = --from-source ]; then
    ARCHIVE="${3:-}"
    [ -n "$ARCHIVE" ] || ARCHIVE="$(ci/fetch-upstream.sh "$PACKAGE" --source)"
    FROM="$OUT/from/$PACKAGE"
    rm -rf "$FROM"
    mkdir -p "$FROM"
    tar -xJf "$ARCHIVE" -C "$FROM" --strip-components=1
    # The build writes into npm's cache and Electron's even when it only
    # reads them: it works on copies.
    cp -a "$FROM/npm-cache" "$AROUND/npm-cache" 2>/dev/null || mkdir -p "$AROUND/npm-cache"
    cp -a "$FROM/cache" "$AROUND/cache" 2>/dev/null || mkdir -p "$AROUND/cache"
    BUILT="$OUT/from-source"
    mkdir -p "$BUILT"
    set -- UPSTREAM_FROM="$FROM" UPSTREAM_KEPT="$FROM/kept" \
        npm_config_cache="$AROUND/npm-cache" npm_config_offline=true \
        XDG_CACHE_HOME="$AROUND/cache" electron_config_cache="$AROUND/cache/electron"
    NETWORK="unshare --user --map-current-user --net"
    export NODE_FROM="$FROM/node"
else
    mkdir -p "$SOURCES/kept"
    BUILT="$OUT"
    set -- UPSTREAM_SOURCES="$SOURCES" UPSTREAM_KEEP="$SOURCES/kept" \
        npm_config_cache="$SOURCES/npm-cache" \
        XDG_CACHE_HOME="$SOURCES/cache" electron_config_cache="$SOURCES/cache/electron"
    NETWORK=""
fi
rm -f "$BUILT/$TARBALL"

PATH_FOR_BUILD="$PATH"
if [ -n "$NODE" ]; then
    if [ -n "$FROM" ]; then
        NODE_HOME="$(ci/upstream/node.sh "$NODE")"
    else
        NODE_HOME="$(ci/upstream/node.sh "$NODE" --keep "$SOURCES/node")"
    fi
    PATH_FOR_BUILD="$NODE_HOME/bin:$PATH"
fi

echo "==> Building $PACKAGE $VERSION from ${FROM:+its source tarball, }$REPOSITORY at $COMMIT (log: ${LOG#"$REPO_ROOT"/})"
# Test browsers and drivers some packages download when installed are not
# part of any build here, and are not fetched.
if ! ( cd "$WORK" && $NETWORK env PATH="$PATH_FOR_BUILD" HOME="$AROUND/home" \
        "$@" \
        PUPPETEER_SKIP_DOWNLOAD=1 CHROMEDRIVER_SKIP_DOWNLOAD=true CYPRESS_INSTALL_BINARY=0 \
        PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1 npm_config_update_notifier=false \
        UPSTREAM_PACKAGE="$PACKAGE" UPSTREAM_REPOSITORY="$REPOSITORY" \
        UPSTREAM_COMMIT="$COMMIT" UPSTREAM_VERSION="$VERSION" \
        UPSTREAM_OUT="$BUILT" UPSTREAM_TARBALL="$TARBALL" \
        UPSTREAM_FETCH="$REPO_ROOT/ci/upstream/fetch.sh" \
        UPSTREAM_PACK="$REPO_ROOT/ci/upstream/pack.sh" \
        UPSTREAM_CHECK_SITE="$REPO_ROOT/ci/upstream/check-site.py" \
        sh "$REPO_ROOT/$BUILD" ) > "$LOG" 2>&1; then
    echo "$0: the build failed; the end of its log:" >&2
    tail -n 40 "$LOG" | sed 's/^/      /' >&2
    exit 1
fi
[ -s "$BUILT/$TARBALL" ] || {
    echo "$0: the build wrote no $TARBALL" >&2
    exit 1
}

SUM="$(sha256sum "$BUILT/$TARBALL" | cut -d' ' -f1)"
echo "==> $TARBALL: $(du -h "$BUILT/$TARBALL" | cut -f1), sha256 $SUM"
if [ -z "$RECORDED" ] && [ -z "$FROM" ]; then
    python3 ci/upstream/upstream.py "$PACKAGE" set-sha256 "$SUM"
    echo "    written into packages/$PACKAGE/upstream.toml"
elif [ "$RECORDED" != "$SUM" ]; then
    echo "$0: upstream.toml records $RECORDED for this version; a new build is a new version" >&2
    exit 1
fi

if [ -n "$FROM" ]; then
    echo "==> Built again from its source tarball alone, the same bytes"
    rm -rf "$WORK" "$AROUND" "$FROM" "$BUILT"
    exit 0
fi
rm -rf "$WORK" "$AROUND"

# The source tarball: made by the first build of the version, kept after.
if [ -z "$RECORDED_SOURCE" ]; then
    rm -rf "$SOURCES/npm-cache/_logs" "$SOURCES/npm-cache/_update-notifier-last-checked"
    mkdir -p "$SOURCES/kidux/ci/upstream" "$SOURCES/kidux/packages/$PACKAGE"
    cp ci/build-upstream.sh ci/fetch-upstream.sh "$SOURCES/kidux/ci/"
    cp ci/upstream/* "$SOURCES/kidux/ci/upstream/"
    cp "packages/$PACKAGE/upstream.toml" "$SOURCES/kidux/packages/$PACKAGE/"
    cat > "$SOURCES/README.txt" <<EOF
The source of $TARBALL: $PACKAGE $VERSION, built by Kidux from
$REPOSITORY at $COMMIT.

git/        every repository the build fetched, at its commit, without its
            history, each with its commit's time beside it
url/        every other file it fetched
npm-cache/  npm's cache of every package it installed, as npm downloaded it
cache/      the build's cache directory: Electron's downloads, when it has
            Electron
node/       the Node.js release it ran with, and nodejs.org's sums
kept/       what else the build script kept, such as npm's lock file
kidux/      the scripts of Kidux's repository that build it, and the
            package's upstream.toml, which records the built tarball's sum

In a checkout of Kidux's repository at the commit that published this:

    ci/build-upstream.sh $PACKAGE --from-source <this file>

builds it again from this alone, without the network, and checks that the
result is the same bytes. Each program is under its own licence, in its
tree under git/ and in its packages under npm-cache/.
EOF
    time="$(cat "$SOURCES"/git/*-"$COMMIT".time)"
    sh ci/upstream/pack.sh "$SOURCES" "$PACKAGE-$VERSION-source" "$OUT/$SOURCE" "$time"
    SOURCE_SUM="$(sha256sum "$OUT/$SOURCE" | cut -d' ' -f1)"
    python3 ci/upstream/upstream.py "$PACKAGE" set-source-sha256 "$SOURCE_SUM"
    echo "==> $SOURCE: $(du -h "$OUT/$SOURCE" | cut -f1), sha256 $SOURCE_SUM"
    echo "    written into packages/$PACKAGE/upstream.toml"
else
    echo "==> The source tarball recorded for this version stands; this build's copy is not kept"
    SOURCE_SUM="$RECORDED_SOURCE"
fi
rm -rf "$SOURCES"

if [ "$MODE" = --publish ]; then
    TAG="upstream/$PACKAGE/$VERSION"
    if ! gh release view "$TAG" >/dev/null 2>&1; then
        gh release create "$TAG" --title "$PACKAGE upstream $VERSION" \
            --notes "$REPOSITORY at $COMMIT, node ${NODE:-none}. $TARBALL sha256 $SUM; its source, $SOURCE, sha256 $SOURCE_SUM." \
            "$OUT/$TARBALL"
        echo "==> Published as the release $TAG"
    fi
    assets="$(gh release view "$TAG" --json assets --jq '.assets[].name')"
    for pair in "$TARBALL $SUM" "$SOURCE $SOURCE_SUM"; do
        name="${pair% *}"
        sum="${pair#* }"
        if printf '%s\n' "$assets" | grep -qxF "$name"; then
            rm -rf "$OUT/published"
            gh release download "$TAG" --pattern "$name" --dir "$OUT/published"
            [ "$(sha256sum "$OUT/published/$name" | cut -d' ' -f1)" = "$sum" ] || {
                echo "$0: the release $TAG holds other bytes for $name" >&2
                exit 1
            }
            rm -rf "$OUT/published"
            echo "==> The release $TAG already holds $name"
        else
            [ -f "$OUT/$name" ] || {
                echo "$0: $name is not in build/upstream/ to publish" >&2
                exit 1
            }
            gh release upload "$TAG" "$OUT/$name"
            echo "==> $name added to the release $TAG"
        fi
    done
fi
