#!/bin/sh
# Every script in ci/ and tests/ parses, and the Python ones pass pyflakes.
#
#   tests/project/scripts.sh
#
# A test that does not even parse is found here in a second, not an hour into
# a VM run. The package's own code is checked by its build.

set -u

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$REPO_ROOT"
failed=0

# Continuous integration never holds a secret (packaging.md, "Continuous
# integration"): a workflow that names one fails here, before it runs.
# ... and it has to be YAML GitHub can read: a colon followed by a space in a
# plain scalar is a mapping, and a workflow with one never runs at all.
for workflow in $(git ls-files .github/workflows); do
    if grep -n 'secrets\.' "$workflow" >&2; then
        echo "FAIL  $workflow uses a secret" >&2
        failed=$((failed + 1))
    fi
    if ! error="$(perl -MYAML::XS -e 'YAML::XS::LoadFile($ARGV[0])' "$workflow" 2>&1)"; then
        echo "FAIL  $workflow is not YAML a workflow can be read from:" >&2
        printf '%s\n' "$error" | sed 's/^/      /' >&2
        failed=$((failed + 1))
    fi
done

for script in $(git ls-files ci tests | sort); do
    [ -f "$script" ] || continue
    case "$(head -c 64 "$script")" in
        "#!/bin/sh"*|"#!/bin/bash"*) kind=shell ;;
        "#!/usr/bin/python3"*) kind=python ;;
        *) case "$script" in
               *.py) kind=python ;;
               *.sh) kind=shell ;;
               *) continue ;;
           esac ;;
    esac
    if [ "$kind" = shell ]; then
        sh -n "$script" || { echo "FAIL  $script does not parse" >&2; failed=$((failed + 1)); }
    else
        PYTHONPATH=tests/lib pyflakes3 "$script" || { echo "FAIL  $script" >&2; failed=$((failed + 1)); }
    fi
done
find ci tests -name __pycache__ -type d -prune -exec rm -rf {} + 2>/dev/null

[ "$failed" -eq 0 ] && echo "PASS  every script in ci/ and tests/ parses and passes pyflakes"
exit "$failed"
