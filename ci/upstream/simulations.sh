#!/bin/sh
# PhET's simulations, as the Simulations module serves them
# (phase-4e-plan.md, 4.30; D68).
#
# Run by ci/build-upstream.sh kidux-module-simulations, in an empty
# directory. There is no repository to build: the simulations are PhET's
# own built files, one HTML file each with every language in it. Each is
# fetched, through ci/upstream/fetch.sh like everything else, at the
# version packages/kidux-module-simulations/sims.toml names, and refused
# unless its SHA-256 is the one written there, it was built before the
# list's cutoff, it does not name the Creative Commons NonCommercial
# licence, and it loads no script from another server, such as the
# analytics Cloudflare, in front of PhET's site, adds for some programs.
# These are the historical versions, which PhET's agreement keeps under
# CC BY 4.0 (ci/upstream/simulations-versions.py chooses them). They are
# packed under sims/, untouched, with the attribution the licence asks for
# in LICENSE, and the tarball is dated by the newest of their builds,
# which kept/time records for its source tarball.

set -eu

REPO="$(cd "$(dirname "$UPSTREAM_FETCH")/../.." && pwd)"
LIST="$REPO/packages/$UPSTREAM_PACKAGE/sims.toml"
SITE="https://phet.colorado.edu/sims/html"
top="$PWD"

python3 - "$LIST" > "$top/list" <<'PYTHON'
import sys
import tomllib

with open(sys.argv[1], "rb") as file:
    listed = tomllib.load(file)
print(listed["cutoff"])
for sim, entry in sorted(listed["sims"].items()):
    if not entry.get("version") or not entry.get("sha256"):
        sys.exit(f"sims.toml names no version or sum for {sim}: "
                 "run ci/upstream/simulations-versions.py first")
    print(sim, entry["version"], entry["sha256"])
PYTHON
cutoff="$(head -1 "$top/list")"

mkdir -p "$top/site/sims"
tail -n +2 "$top/list" | while read -r sim version sum; do
    file="$top/site/sims/${sim}_all.html"
    sh "$UPSTREAM_FETCH" url "$SITE/$sim/$version/${sim}_all.html" "$file"
    [ "$(sha256sum "$file" | cut -d' ' -f1)" = "$sum" ] || {
        echo "$sim $version: not the file sims.toml names" >&2
        exit 1
    }
    built="$(grep -o "buildTimestamp = '[0-9-]* [0-9:]* UTC'" "$file" | head -1 \
             | sed "s/^buildTimestamp = '//; s/'\$//")"
    day="$(printf '%s' "$built" | cut -c1-10)"
    [ -n "$built" ] && [ "$day" != "$cutoff" ] \
        && [ "$(printf '%s\n%s\n' "$day" "$cutoff" | sort | head -1)" = "$day" ] || {
        echo "$sim $version: built ${built:-at no time it says}, not before $cutoff" >&2
        exit 1
    }
    if grep -q "creativecommons.org/licenses/by-nc/" "$file"; then
        echo "$sim $version: under CC BY-NC, which this module never ships" >&2
        exit 1
    fi
    if grep -Eiq "<script[^>]*[[:space:]]src=[\"']?(https?:)?//" "$file"; then
        echo "$sim $version: loads a script from elsewhere" >&2
        exit 1
    fi
    echo "$built" >> "$top/built"
    echo "==> $sim $version, built $built"
done

epoch="$(date -u -d "$(sort "$top/built" | tail -1)" +%s)"
if [ -n "${UPSTREAM_KEEP:-}" ]; then
    echo "$epoch" > "$UPSTREAM_KEEP/time"
fi

attribution="$(python3 -c 'import sys, tomllib; print(tomllib.load(open(sys.argv[1], "rb"))["attribution"])' "$LIST")"
cat > "$top/site/LICENSE" <<EOF
$attribution

The simulations in sims/ are PhET Interactive Simulations' own files,
unchanged, each in the version published before $cutoff, which PhET's
agreement for its historical collection of HTML simulations publishes
under the Creative Commons Attribution 4.0 International licence:
https://creativecommons.org/licenses/by/4.0/
https://phet.colorado.edu/en/licensing/html

PhET is a trademark of the Regents of the University of Colorado. Kidux
is not connected with PhET Interactive Simulations. Each simulation's own
About dialog names its authors and the libraries inside it, each under
its own licence.
EOF

python3 "$UPSTREAM_CHECK_SITE" "$top/site" /simulations/
echo "==> $(find "$top/site/sims" -type f | wc -l) simulations, $(du -sh "$top/site" | cut -f1)"
sh "$UPSTREAM_PACK" "$top/site" "$UPSTREAM_PACKAGE-$UPSTREAM_VERSION" \
    "$UPSTREAM_OUT/$UPSTREAM_TARBALL" "$epoch"
