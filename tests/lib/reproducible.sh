#!/bin/sh
# Build a package twice and refuse it if the two results differ.
#
#   tests/run reproducible kidux-base
#   tests/run reproducible                 every package
#
# "Everything that ends up on a user's machine must be reproducible from this
# repository" is a project rule, and a rule nobody checks is a wish. This is the
# check.
#
# It matters beyond tidiness. A version number is a promise about specific
# bytes: the archive refuses to replace a published version with different
# content, and promoting from testing to stable only means anything if the bits
# a family installs are the bits that were tested. Two builds of one source that
# disagree break both.
#
# The usual cause is a timestamp. dpkg clamps every file's modification time to
# SOURCE_DATE_EPOCH, which it takes from the newest debian/changelog entry — but
# only clamps times that are *newer* than it. A changelog dated in the future
# therefore clamps nothing, and each build stamps its own wall clock into the
# package. Always take a changelog date from `date -R`.

set -eu

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
BUILD_DIR="$REPO_ROOT/build"
WORK="$BUILD_DIR/reproducible"

if [ "$#" -gt 0 ]; then
    packages="$*"
else
    packages="$(ls "$REPO_ROOT/packages" | sort)"
fi

rm -rf "$WORK"
mkdir -p "$WORK/first" "$WORK/second"

failures=0

FIRST="kidux-archive-keyring kidux-common"

# A package whose build key (ci/build-key.py) was shown to build identically
# twice less than a week ago is not built twice again: its source, its build
# scripts and what it builds against are what they were. The others are,
# with the build cache out of the way, and with the two packages every
# other builds against whenever any other is.
proven_mark() {
    echo "$REPO_ROOT/build/cache/$1/$("$REPO_ROOT/ci/build-key.py" "$1")/reproducible"
}
to_build=""
for package in $packages; do
    [ -d "$REPO_ROOT/packages/$package/debian" ] || continue
    mark="$(proven_mark "$package")"
    if [ -f "$mark" ] && [ -n "$(find "$mark" -mtime -7)" ]; then
        echo "PASS  $package builds identically twice, shown for this source on $(date -r "$mark" -I)"
    else
        to_build="$to_build $package"
    fi
done
if [ -n "$to_build" ]; then
    for package in $FIRST; do
        case " $to_build " in *" $package "*) ;; *) to_build="$package $to_build" ;; esac
    done
fi
packages="$to_build"
export KIDUX_BUILD_CACHE=0

# Each round builds every package once, as ci/build-all.sh does: the keyring
# and kidux-common first, since the others need python3-kidux to build, then
# the rest at once. The two rounds cannot overlap, since both build from the
# same source directories.
for round in first second; do
    echo "==> Building every package, $round round"
    rest=""
    for package in $packages; do
        [ -d "$REPO_ROOT/packages/$package/debian" ] || continue
        case " $FIRST " in
            *" $package "*)
                KIDUX_BUILD_DIR="$WORK/$round" "$REPO_ROOT/ci/build-package.sh" "$package"                     >"$WORK/$round-$package.log" 2>&1                     || echo "$package" >> "$WORK/$round.failed"
                ;;
            *) rest="$rest $package" ;;
        esac
    done
    if [ -n "$rest" ]; then
        # shellcheck disable=SC2086
        "$REPO_ROOT/ci/build-parallel.sh" "$WORK/$round" $rest > "$WORK/$round-rest.log" 2>&1
        for package in $rest; do
            tail -n 1 "$WORK/$round/logs/$package.log" | grep -q "built into"                 || echo "$package" >> "$WORK/$round.failed"
        done
    fi
done

for package in $packages; do
    [ -d "$REPO_ROOT/packages/$package/debian" ] || continue
    if grep -qx "$package" "$WORK/first.failed" "$WORK/second.failed" 2>/dev/null; then
        echo "FAIL  $package did not build" >&2
        for log in "$WORK/first-$package.log" "$WORK/first/logs/$package.log"                    "$WORK/second-$package.log" "$WORK/second/logs/$package.log"; do
            [ -f "$log" ] && tail -n 20 "$log" | sed 's/^/      /' >&2
        done
        failures=$((failures + 1))
        continue
    fi

    version="$(dpkg-parsechangelog -l "$REPO_ROOT/packages/$package/debian/changelog" -S Version)"
    changes="$WORK/first/${package}_${version}_amd64.changes"
    differences=0
    for name in $(awk '/^Files:/ { files = 1; next } /^[^ ]/ { files = 0 }
                        files && $NF ~ /\.deb$/ { print $NF }' "$changes"); do
        first="$WORK/first/$name"
        second="$WORK/second/$name"

        if [ ! -e "$second" ]; then
            echo "FAIL  $name was built once but not twice" >&2
            differences=$((differences + 1))
            continue
        fi

        if ! cmp -s "$first" "$second"; then
            echo "FAIL  $name differs between two builds of the same source" >&2
            # The contents are usually identical and only the metadata moves,
            # so say which, rather than leaving someone to unpack both.
            ar p "$first" data.tar.xz 2>/dev/null | tar tv > "$WORK/first.list" 2>/dev/null || true
            ar p "$second" data.tar.xz 2>/dev/null | tar tv > "$WORK/second.list" 2>/dev/null || true
            diff "$WORK/first.list" "$WORK/second.list" | head -10 | sed 's/^/      /' >&2 || true
            differences=$((differences + 1))
        fi
    done

    if [ "$differences" -eq 0 ]; then
        echo "PASS  $package builds identically twice"
        # Into the build cache, as ci/build-package.sh keeps a build: the
        # release's build of this source is then these bytes, the ones
        # shown to build identically, and takes no time.
        mark="$(proven_mark "$package")"
        cache="$(dirname "$mark")"
        mkdir -p "$cache"
        names="$(basename "$changes")
$(awk '/^Files:/ { files = 1; next } /^[^ ]/ { files = 0 } files { print $NF }' "$changes")"
        for name in $names; do
            cp -p "$WORK/first/$name" "$cache/$name"
        done
        printf '%s\n' $names > "$cache/files"
        touch "$mark"
    else
        failures=$((failures + differences))
    fi
done

echo
if [ "$failures" -eq 0 ]; then
    echo "==> Every package builds reproducibly."
    rm -rf "$WORK"
    exit 0
fi

echo "==> $failures reproducibility problems. Left in $WORK for inspection." >&2
exit 1
