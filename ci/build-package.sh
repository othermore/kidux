#!/bin/sh
# Build one Kidux source package.
#
#   ci/build-package.sh kidux-base
#
# Builds in an unshare chroot, so it needs no root and behaves the same on a
# developer's machine and in CI. Results land in build/, which is not in git.

set -eu

PACKAGE="${1:-}"
DIST="${KIDUX_DIST:-trixie}"
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
# A copy of the package's source elsewhere, for a development build
# (tests/lib/vm.py push, or below for the battery); the package's own
# directory otherwise.
SOURCE_DIR="${KIDUX_SOURCE_DIR:-$REPO_ROOT/packages/$PACKAGE}"
BUILD_DIR="${KIDUX_BUILD_DIR:-$REPO_ROOT/build}"
CHROOT_TARBALL="$HOME/.cache/sbuild/$DIST-amd64.tar"

if [ -z "$PACKAGE" ]; then
    echo "usage: $0 <package-name>" >&2
    echo "available:" >&2
    ls "$REPO_ROOT/packages" >&2
    exit 1
fi

if [ ! -d "$SOURCE_DIR/debian" ]; then
    echo "$0: no such package: $PACKAGE" >&2
    exit 1
fi

if [ ! -f "$CHROOT_TARBALL" ]; then
    echo "$0: no build chroot at $CHROOT_TARBALL" >&2
    echo "Create it with:" >&2
    echo "  mmdebstrap --mode=unshare --variant=buildd $DIST $CHROOT_TARBALL" >&2
    exit 1
fi

mkdir -p "$BUILD_DIR"

# The battery's build (ci/test-release.sh, D93): with KIDUX_DEV_STAMP, a
# package whose version the archive's testing suite does not hold yet is
# built as a development build of that version, <version>~dev.<stamp>, from
# a copy of its source (ci/devbuild.py), so that the version itself is
# built for publishing only once the owner has tried it and said yes. One
# the archive holds is built as it is.
if [ -n "${KIDUX_DEV_STAMP:-}" ] && [ -z "${KIDUX_SOURCE_DIR:-}" ] \
        && "$REPO_ROOT/ci/devbuild.py" unpublished "$PACKAGE"; then
    KIDUX_SOURCE_DIR="$BUILD_DIR/dev-src/$PACKAGE"
    rm -rf "$KIDUX_SOURCE_DIR"
    echo "==> $PACKAGE as $("$REPO_ROOT/ci/devbuild.py" copy "$PACKAGE" "$KIDUX_DEV_STAMP" "$KIDUX_SOURCE_DIR")"
    SOURCE_DIR="$KIDUX_SOURCE_DIR"
fi

# The build cache (packaging.md, "The build cache"): a package whose source,
# build scripts, chroot and packages of ours it builds against are what they
# were for a build less than a week old gives that build's files, already
# through lintian, instead of building again. A development build
# (KIDUX_SOURCE_DIR, tests/lib/vm.py push) and KIDUX_BUILD_CACHE=0 build
# whatever the cache holds, and a development build is never kept in it.
CACHE_DAYS=7
CACHED=""
if [ -z "${KIDUX_SOURCE_DIR:-}" ] && [ "${KIDUX_BUILD_CACHE:-1}" != 0 ]; then
    CACHED="$REPO_ROOT/build/cache/$PACKAGE/$("$REPO_ROOT/ci/build-key.py" "$PACKAGE")"
    if [ -f "$CACHED/files" ] && [ -n "$(find "$CACHED/files" -mtime -"$CACHE_DAYS")" ]; then
        while read -r name; do
            cp -p "$CACHED/$name" "$BUILD_DIR/$name"
        done < "$CACHED/files"
        echo "==> $PACKAGE taken from the build cache, built $(date -r "$CACHED/files" -I)"
        echo "==> $PACKAGE built into $BUILD_DIR"
        exit 0
    fi
fi

# A package built from a program that is not in trixie (D68, packaging.md
# "Programs built at development time") is built from a staged copy of its
# source, with the tarball ci/build-upstream.sh made unpacked into upstream/
# inside it, so that nothing of the build reaches packages/. Its source
# package is large, and packed fast.
SOURCE_OPTIONS=""
# dpkg-source's own list of what to leave out of a source package, which a
# bare -I keeps, holds *.so: right for our own sources, and wrong for a
# program built upstream, whose libraries are part of it. Such a package
# leaves out only what a working copy can add to it.
IGNORE="--dpkg-source-opt=-I"
if [ -f "$SOURCE_DIR/upstream.toml" ]; then
    TARBALL="$("$REPO_ROOT/ci/fetch-upstream.sh" "$PACKAGE")"
    STAGED="$BUILD_DIR/staged/$PACKAGE"
    rm -rf "$STAGED"
    mkdir -p "$STAGED/upstream"
    cp -a "$SOURCE_DIR/." "$STAGED/"
    tar -xJf "$TARBALL" -C "$STAGED/upstream" --strip-components=1
    SOURCE_DIR="$STAGED"
    SOURCE_OPTIONS="--dpkg-source-opt=-z1"
    IGNORE="--dpkg-source-opt=-I.git"
fi

# sbuild unpacks each build's chroot under TMPDIR. /tmp here is a tmpfs, in
# memory, that the test machines need too, and a few builds at once, one of
# them a module built from an upstream tarball, filled it; so the chroots go
# on the disk, in /var/tmp/kidux-sbuild/. Not under build/: the chroot's
# root, a user of sbuild's own namespace, has to reach it, and a home
# directory is closed to other users. A build that dies leaves its chroot
# there, owned by that namespace's users; `unshare --map-auto
# --map-root-user rm -rf` removes it.
TMPDIR="${KIDUX_TMPDIR:-/var/tmp/kidux-sbuild}"
mkdir -p "$TMPDIR"
export TMPDIR

echo "==> Building $PACKAGE for $DIST"
cd "$SOURCE_DIR"
# Every file newer than the changelog's date, so that dpkg clamps every file
# time to that date. A file older than it keeps its own time, and then the
# package depends on when a file in this working copy was last written:
# two builds of the same source, from the same commit, differed by the time
# of a copied logo.
find . -exec touch {} +
# Our packages build-depend on each other — the daemon's tests need the
# library — and the chroot only knows Debian. So it is given two more sources:
# every .deb already built in this run, which is what a build of several
# packages at once needs, and the local archive's testing suite, which is what
# a build of one package on its own needs. The archive is reached by address
# rather than as kidux.local because the chroot has no mDNS, and trusted by
# the key testing is signed with, the development one, which no package ships.
# ci/build-parallel.sh names a copy of that directory in KIDUX_EXTRA_PACKAGES,
# so that a build never reads a package another build is still writing.
EXTRA_PACKAGES="${KIDUX_EXTRA_PACKAGES:-$BUILD_DIR}"
set --
if ls "$EXTRA_PACKAGES"/*.deb >/dev/null 2>&1; then
    set -- "$@" --extra-package="$EXTRA_PACKAGES"
fi
if curl -fsS -o /dev/null "http://127.0.0.1/apt/dists/testing/InRelease" 2>/dev/null; then
    set -- "$@" \
        --extra-repository="deb http://127.0.0.1/apt testing main" \
        --extra-repository-key="${KIDUX_ARCHIVE_PUBLIC_KEY:-$REPO_ROOT/ci/archive/development-key.pgp}"
fi

# --no-clean-source because sbuild otherwise runs debian/rules clean on the
# host first, which would mean every build dependency had to be installed
# outside the chroot as well. The chroot is the whole point.
#
# dpkg-source packs the directory as it is, including the __pycache__ and
# .pytest_cache directories any local run of the tests leaves behind. A bare
# -I keeps dpkg-source's own exclusions; the others add these, so the source
# package is the same from a working copy as from a clean checkout.
sbuild \
    "$@" \
    $SOURCE_OPTIONS \
    $IGNORE \
    --dpkg-source-opt=-I__pycache__ \
    --dpkg-source-opt=-I.pytest_cache \
    --chroot-mode=unshare \
    --dist="$DIST" \
    --build-dir="$BUILD_DIR" \
    --no-clean-source \
    --no-run-lintian \
    --no-run-piuparts \
    --no-run-autopkgtest

# Lintian runs here rather than inside sbuild: sbuild reports a lintian failure
# but still exits successfully, so a broken package would sail through CI.
CHANGES="$BUILD_DIR/${PACKAGE}_$(dpkg-parsechangelog -l debian/changelog -S Version)_amd64.changes"

if [ ! -f "$CHANGES" ]; then
    echo "$0: sbuild produced no $CHANGES" >&2
    exit 1
fi

echo "==> Checking $PACKAGE with lintian"
# A development build's version (ci/devbuild.py) carries the time it
# was made, which makes a long module's .buildinfo name longer than
# lintian likes; the version a release builds does not.
LINTIAN_SUPPRESS=""
case "$CHANGES" in
    *~dev.*) LINTIAN_SUPPRESS="--suppress-tags package-has-long-file-name" ;;
esac
if ! lintian --fail-on error,warning --display-info --pedantic $LINTIAN_SUPPRESS "$CHANGES"; then
    echo "$0: lintian rejected $PACKAGE" >&2
    exit 1
fi

if [ -n "$CACHED" ]; then
    # The .changes and every file it lists: what publishing takes.
    rm -rf "$CACHED"
    mkdir -p "$CACHED"
    names="$(basename "$CHANGES")
$(awk '/^Files:/ { files = 1; next } /^[^ ]/ { files = 0 } files { print $NF }' "$CHANGES")"
    for name in $names; do
        cp -p "$BUILD_DIR/$name" "$CACHED/$name"
    done
    printf '%s\n' $names > "$CACHED/files"
fi

echo "==> $PACKAGE built into $BUILD_DIR"
