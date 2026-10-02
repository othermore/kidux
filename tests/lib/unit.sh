#!/bin/sh
# Each package's unit tests, from the working tree, in seconds.
#
#   tests/run unit                   every package
#   tests/run unit kidux-greeter     just the ones named
#
# The quick loop's first step (tests/README.md, "The quick loop"): what the
# package's build runs in its chroot, pyflakes and pytest, run here without
# building, with the tree's kidux-common ahead of any installed one. The
# tests never read the machine's own state, so a machine that runs Kidux
# gives the same answers as the build's chroot; the build stays the one
# that counts. Prints a PASS or FAIL line per package; the exit status is
# the number that failed.

set -u

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$REPO_ROOT"

if [ "$#" -eq 0 ]; then
    set -- $(for dir in packages/*/debian; do basename "$(dirname "$dir")"; done)
fi

failed=0
summary=""
for package in "$@"; do
    dir="packages/$package"
    if [ ! -d "$dir/debian" ]; then
        echo "$0: no such package: $package" >&2
        exit 2
    fi
    echo "==> $package"
    ok=1
    # Every Python file and script the package ships or tests with, as its
    # build's pyflakes and sh -n see them.
    python_files="$(find "$dir" -path "$dir/debian" -prune -o -name '*.py' -print \
                    | grep -v '/__pycache__/')"
    for script in $(find "$dir/bin" "$dir/lib" -type f 2>/dev/null); do
        case "$(head -c 32 "$script")" in
            "#!/usr/bin/python3"*) python_files="$python_files $script" ;;
            "#!/bin/sh"*) sh -n "$script" || ok=0 ;;
        esac
    done
    if [ -n "$python_files" ]; then
        # shellcheck disable=SC2086
        pyflakes3 $python_files || ok=0
    fi
    if [ -d "$dir/tests" ]; then
        (cd "$dir" && KIDUX_SOURCE_ROOT="$PWD" \
             PYTHONPATH="$PWD:$REPO_ROOT/packages/kidux-common${PYTHONPATH:+:$PYTHONPATH}" \
             python3 -B -m pytest -q -p no:cacheprovider tests) || ok=0
    fi
    if [ "$ok" -eq 1 ]; then
        summary="$summary
PASS  $package"
    else
        summary="$summary
FAIL  $package"
        failed=$((failed + 1))
    fi
done

echo
echo "==> Unit tests$summary"
exit "$failed"
