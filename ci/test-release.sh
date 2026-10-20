#!/bin/sh
# Everything that has to be true before a release, in one command; and the
# release itself.
#
#   ci/test-release.sh [label]               the battery, on ~dev builds
#   ci/test-release.sh <label> --release     the release: the versions themselves
#   ci/test-release.sh <label> --only <stage>
#
# Two things that are not tests, then every test there is. Build: every
# package, with its own unit tests and lintian, into a directory of the
# run's own, build/releases/<label>/packages/; a package whose version the
# archive's testing suite does not hold yet, one changed in the work, as a
# development build of that version, <version>~dev.<time> (ci/devbuild.py),
# never as the version itself. Publish: the result into the local archive's
# testing suite, which is what the VMs and the MacBook install from. Then
# every test. That is the battery, run as often as the work needs.
#
# --release is run once, on a clean tree, when the battery has passed on
# the same commit, or on one from which this differs only outside the
# packages' sources, which it checks in build/releases/*/commit, the owner
# has tried the work and said yes, and any further review the owner asked
# for is done (D93): it builds the versions themselves, which the
# reproducibility stage of the battery left in the build cache, publishes
# them into testing in place of the development builds, runs every test
# on them, and writes the guide's pictures, which only a release run does,
# since a development build's version shows on the screens. The push, the
# promotion to stable and the public archive follow, each on the owner's
# word. Then
# Kidux's image, built from the testing suite as it now stands
# (ci/build-image.sh), since it carries the packages; then
# tests/run, kind by kind: the project's checks first and alone, since they
# are quick; then reproducibility, the packages' and the image's, the
# acceptance VM, the session VMs, one set up in Spanish and one in English,
# which use every screen by keyboard and photograph it (tests/README.md),
# and the image's installation on a VM, all at once; and when the
# installation passed, the trial images, made from the disk it left
# (ci/build-trial-image.py; docs/dev/image.md). They share nothing but the
# archive, which nothing writes to until they are done, and the base image,
# which the VMs only read. The rebuilds run at a lower priority than the
# VMs, whose tests wait on screens.
# The VMs start from Debian with Kidux's Debian dependencies installed
# (tests/lib/warm-image.sh); KIDUX_VM_COLD=1, for a release, starts them
# from the stock image.
#
# Then the pictures: all of them are kept in build/releases/<label>/screens/,
# compared with the previous run's in a report that says what changed
# (build/releases/<label>/report/index.html), and, when everything passed,
# the ones the user guide shows (tests/lib/doc-screenshots.txt) are copied to
# docs/images/es/ and docs/images/en/, each from the run in that language, so
# the guide never shows a screen that no longer exists.
# Whether a changed picture is right is for a person to judge from the report;
# `git diff --stat docs/images` says which of the guide's changed.
#
# The label defaults to the current commit. The tests are skipped if the build
# or the publishing failed, because they would test something that was not
# built; each kind of test runs even if another failed. Every stage's line
# says when it started and how many minutes it took, and the verdicts are
# kept in build/releases/<label>/verdicts, with a `release` mark for a
# release run. The exit status is the number of stages that failed.
#
# --only reruns one test stage (project, reproducible, acceptance, session,
# session-en or install)
# of a run that already built and published, for a stage that failed for a
# reason outside the code: a mirror down, a machine that did not come up. It
# builds nothing, so what it tests is byte for byte what the rest of the run
# tested, and it refuses if the archive or the packages' sources have changed
# since. Its verdict replaces that stage's in the same report, marked as a
# rerun; a session rerun takes the pictures again.

set -u

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"
LABEL="${1:-$(git describe --always --dirty)}"
RELEASES="$REPO_ROOT/build/releases"
#: What the packages are built from: a commit that differs from a tested one
#: only outside these builds the same bytes.
SOURCES="packages tests/lib/seed ci/build-all.sh ci/build-package.sh ci/devbuild.py ci/publish-local.sh"
ONLY=""
RELEASE=""
if [ "${2:-}" = --release ] && [ "$#" -eq 2 ]; then
    RELEASE=yes
    if [ -n "$(git status --porcelain)" ]; then
        echo "$0: a release is built from a commit, and the tree has changes not committed:" >&2
        git status --short >&2
        exit 2
    fi
    # A release publishes its versions to test them, and a published
    # version never changes (D93): so the battery, on ~dev builds of this
    # commit, must have passed first. A battery of an earlier commit counts
    # when nothing the packages are built from has changed since, as after
    # a test's own fault was fixed and that test rerun alone (--only): the
    # bytes it tested are the bytes this builds.
    commit="$(git rev-parse HEAD)"
    green=""
    for run in "$RELEASES"/*/; do
        [ -f "$run/commit" ] && [ ! -f "$run/release" ] && [ -s "$run/verdicts" ] \
            && ! grep -q '^FAIL' "$run/verdicts" || continue
        tested="$(cat "$run/commit")"
        git merge-base --is-ancestor "$tested" "$commit" 2>/dev/null || continue
        git diff --quiet "$tested" "$commit" -- $SOURCES || continue
        green="$run"
    done
    if [ -z "$green" ]; then
        echo "$0: no battery has passed of commit $commit, or of one it differs from only" >&2
        echo "outside the packages' sources; run $0 <label> first, whole" >&2
        exit 2
    fi
    echo "==> Releasing commit $commit, which $(basename "$green") passed" \
         "$([ "$(cat "$green/commit")" = "$commit" ] || echo "as $(cat "$green/commit" | cut -c1-7)")"
elif [ "${2:-}" = --only ]; then
    ONLY="${3:-}"
    case "$ONLY" in
        project|reproducible|acceptance|session|session-en|install) ;;
        *) echo "usage: $0 <label> --only project|reproducible|acceptance|session|session-en|install" >&2
           exit 2 ;;
    esac
elif [ "$#" -gt 1 ]; then
    echo "usage: $0 [label] | $0 <label> --release | $0 <label> --only <stage>" >&2
    exit 2
fi
OUT="$RELEASES/$LABEL"
PACKAGES_DIR="$OUT/packages"
VERDICTS="$OUT/verdicts"
PREVIOUS="$(ls -1dt "$RELEASES"/*/ 2>/dev/null | grep -v "/$LABEL/\$" | head -1)"
mkdir -p "$OUT/logs"

background=""
RERUN=""

published() {
    # What a run's tests test: the archive's testing suite, the sources its
    # packages were built from, and the seed both machines are set up with.
    curl -fsS "${KIDUX_ARCHIVE_URL:-http://kidux.local/apt}/dists/testing/main/binary-amd64/Packages"         | sha256sum | cut -d' ' -f1
    # packages/ below its top, where each build leaves its .dsc and tarball.
    { find packages -mindepth 2 -type f ! -path '*/__pycache__/*' ! -path '*/.pytest_cache/*' -print0
      find tests/lib/seed -type f ! -path '*/__pycache__/*' -print0
    } | sort -z | xargs -0 sha256sum | sha256sum | cut -d' ' -f1
}

slug() {
    echo "$1" | tr -d ' :'
}

minutes() {
    # minutes <start> <end>, both in seconds, to one decimal
    awk -v s="$1" -v e="$2" 'BEGIN { printf "%.1f", (e - s) / 60 }'
}

record() {
    # record <name> <status> <start> <end>: its line in the verdicts,
    # replacing an earlier one of the same stage
    if [ "$2" -eq 0 ]; then
        line="PASS  $1 ($(minutes "$3" "$4") min$RERUN)"
    else
        line="FAIL  $1 ($(minutes "$3" "$4") min$RERUN, $(echo "$OUT/logs/$(slug "$1").log" | sed "s|^$REPO_ROOT/||"))"
    fi
    touch "$VERDICTS"
    grep -v "^[A-Z]*  $1 (" "$VERDICTS" > "$VERDICTS.new" || true
    echo "$line" >> "$VERDICTS.new"
    mv "$VERDICTS.new" "$VERDICTS"
    echo "==> $1: $([ "$2" -eq 0 ] && echo PASS || echo FAIL) at $(date -d "@$4" +%T), $(minutes "$3" "$4") min"
}

stage() {
    # stage <name> <command...>: run it, log it, remember how it went
    name="$1"; shift
    echo "==> $name, from $(date +%T)"
    start="$(date +%s)"
    "$@" > "$OUT/logs/$(slug "$name").log" 2>&1
    status=$?
    record "$name" "$status" "$start" "$(date +%s)"
    return "$status"
}

stage_start() {
    # stage_start <name> <command...>: the same, in the background; its
    # status and times go to a file that stages_wait reads
    name="$1"; shift
    echo "==> $name, from $(date +%T)"
    done_file="$OUT/logs/$(slug "$name").done"
    rm -f "$done_file"
    (
        start="$(date +%s)"
        "$@" > "$OUT/logs/$(slug "$name").log" 2>&1
        echo "$? $start $(date +%s)" > "$done_file"
    ) &
    background="$background
$name"
}

stages_wait() {
    # every stage started in the background, in the order they started
    wait
    saved_ifs="$IFS"
    IFS='
'
    for name in $background; do
        IFS="$saved_ifs"
        done_file="$OUT/logs/$(slug "$name").done"
        if [ -s "$done_file" ]; then
            read -r status start end < "$done_file"
        else
            status=1; start=0; end=0
        fi
        rm -f "$done_file"
        record "$name" "$status" "$start" "$end"
    done
    IFS="$saved_ifs"
    background=""
}

pictures() {
    # The pictures of the session runs, the installations and the trial
    # images into the report, compared with the previous run's; the guide's
    # own copied to docs/images/<language>/ when every stage of a release
    # run passed. The Spanish session run's are session-NN-<screen>.png, the
    # English one's session-en-NN-<screen>.png; the installations' are
    # install-NN- and install-en-NN-, the trial images' trial-es-NN- and
    # trial-en-NN-.
    rm -rf "$OUT/screens"
    mkdir -p "$OUT/screens"
    cp build/vm/session-[0-9]*.png build/vm/session-en-[0-9]*.png \
        build/vm/install-[0-9]*.png build/vm/install-en-[0-9]*.png \
        build/vm/trial-es-[0-9]*.png build/vm/trial-en-[0-9]*.png "$OUT/screens/" 2>/dev/null
    if [ -n "$PREVIOUS" ] && [ -d "$PREVIOUS/screens" ]; then
        echo "==> Comparing the screens with $(basename "$PREVIOUS")"
        ./tests/lib/screenshot-diff.py "$PREVIOUS/screens" "$OUT/screens" "$OUT/report" \
            | tee "$OUT/logs/screens.log"
    fi

    if [ ! -f "$OUT/release" ]; then
        echo "==> A development run: the guide's pictures are left as they are (D93)"
    elif ! grep -q '^FAIL' "$VERDICTS"; then
        echo "==> Updating the user guide's pictures"
        for language in es en; do
            # The session run, the installation and the trial image in
            # that language; a screen is found in the one that takes it.
            runs="session install trial-es"
            [ "$language" = es ] || runs="session-$language install-$language trial-$language"
            mkdir -p "docs/images/$language"
            grep -v '^#' tests/lib/doc-screenshots.txt | while read -r screen file; do
                [ -n "$screen" ] || continue
                picture="$(for run in $runs; do
                    ls "$OUT"/screens/"$run"-[0-9]*-"$screen".png 2>/dev/null
                done | head -1)"
                if [ -n "$picture" ]; then
                    cp "$picture" "docs/images/$language/$file"
                else
                    echo "     no picture of $screen in the $language run" >&2
                fi
            done
        done
        git status --short docs/images
    fi
}

if [ -n "$ONLY" ]; then
    if [ ! -s "$OUT/published" ] || [ "$(published)" != "$(cat "$OUT/published")" ]; then
        echo "$0: the archive or the packages' sources are no longer what $LABEL built and" >&2
        echo "published, so a rerun would not test the same thing; run it whole." >&2
        exit 2
    fi
    RERUN=", rerun"
    if [ "$ONLY" = reproducible ]; then
        stage "test: $ONLY" nice -n 10 ./tests/run "$ONLY"
    else
        stage "test: $ONLY" ./tests/run "$ONLY"
    fi
    case "$ONLY" in session*|install) pictures ;; esac
else
    rm -f "$VERDICTS" "$OUT/published" "$OUT/release"
    rm -rf "$PACKAGES_DIR"
    git rev-parse HEAD > "$OUT/commit"
    if [ -n "$RELEASE" ]; then
        touch "$OUT/release"
        stamp=""
        dev=""
    else
        stamp="$(date +%Y%m%d%H%M%S)"
        dev=1
    fi
    if stage build env KIDUX_BUILD_DIR="$PACKAGES_DIR" KIDUX_DEV_STAMP="$stamp" ./ci/build-all.sh \
            && stage publish env KIDUX_BUILD_DIR="$PACKAGES_DIR" KIDUX_DEV_BUILD="$dev" \
                ./ci/publish-local.sh; then
        published > "$OUT/published"
        stage image ./ci/build-image.sh testing
        stage "test: project" ./tests/run project
        stage_start "test: reproducible" nice -n 10 ./tests/run reproducible
        stage_start "test: reproducible image" nice -n 10 ./tests/run reproducible image
        stage_start "test: acceptance" ./tests/run acceptance
        stage_start "test: session" ./tests/run session
        stage_start "test: session-en" ./tests/run session-en
        if grep -q '^PASS  image (' "$VERDICTS"; then
            stage_start "test: install" ./tests/run install
        fi
        stages_wait
        if grep -q '^PASS  test: install (' "$VERDICTS"; then
            stage "trial images" ./ci/build-trial-image.py
        fi
        pictures
    fi
fi

failed="$(grep -c '^FAIL' "$VERDICTS" 2>/dev/null)"
echo
echo "==> $([ -f "$OUT/release" ] && echo Release || echo Battery) $LABEL"
for name in build publish image "test: project" "test: reproducible" "test: reproducible image" \
        "test: acceptance" "test: session" "test: session-en" "test: install" "trial images"; do
    grep "^[A-Z]*  $name (" "$VERDICTS" 2>/dev/null
done
[ "${failed:-0}" -eq 0 ] && echo "==> Everything passed." || echo "==> $failed stages failed."
exit "${failed:-0}"
