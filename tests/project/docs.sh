#!/bin/sh
# The user documentation is the same in both languages, shows only
# pictures that exist or that the release writes, and says on the modules'
# pages what their descriptions in the panel leave out.
#
#   tests/project/docs.sh
#
# docs/en/ and docs/es/ hold the same files, by name (CLAUDE.md: the same
# file names, always in sync). A picture a document shows is in
# docs/images/<lang>/, or is one the release run writes there
# (tests/lib/doc-screenshots.txt), so that a document never shows a
# picture nothing makes.

set -u

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$REPO_ROOT"
failed=0

en="$(cd docs/en && find . -name '*.md' | sort)"
es="$(cd docs/es && find . -name '*.md' | sort)"
if [ "$en" != "$es" ]; then
    echo "FAIL  docs/en and docs/es hold different files:" >&2
    printf '%s\n' "$en" | sed 's/^/  en: /' >&2
    printf '%s\n' "$es" | sed 's/^/  es: /' >&2
    failed=$((failed + 1))
else
    echo "PASS  docs/en and docs/es hold the same files"
fi

written="$(grep -v '^#' tests/lib/doc-screenshots.txt | awk 'NF == 2 { print $2 }')"
for lang in en es; do
    missing=""
    readme=README.md
    [ "$lang" = es ] && readme=README.es.md
    for doc in $readme $(find docs/$lang -name '*.md'); do
        for picture in $(grep -o "images/$lang/[a-z0-9-]*\.png" "$doc" | sed "s|.*/||" | sort -u); do
            [ -f "docs/images/$lang/$picture" ] && continue
            echo "$written" | grep -qx "$picture" && continue
            missing="$missing $doc:$picture"
        done
    done
    if [ -n "$missing" ]; then
        echo "FAIL  pictures shown in $lang that nothing makes:$missing" >&2
        failed=$((failed + 1))
    else
        echo "PASS  every picture the $lang documents show exists or is written by the release"
    fi
done

# A door to someone else's site says on its page in the guide that Kidux is
# not affiliated with the site's owner, which its description in the panel
# leaves out (D125). Each page says it in its own words; they share the
# negation and the word for affiliation, in one sentence with the owner's
# name.
for door in codecombat:CodeCombat "expedition-code:Expedition Code" gmail:Google simulations:PhET; do
    module="${door%%:*}"
    owner="${door#*:}"
    for lang in en es; do
        page="docs/$lang/modules/$module.md"
        if [ "$lang" = en ]; then
            said="Kidux (is not|has no) [^.|]*affiliat[^.|]*$owner"
        else
            said="Kidux no [^.|]*afilia[^.|]*$owner"
        fi
        if grep -Eq "$said" "$page"; then
            echo "PASS  $page says Kidux is not affiliated with $owner"
        else
            echo "FAIL  $page does not say Kidux is not affiliated with $owner" >&2
            failed=$((failed + 1))
        fi
    done
done

# Kydux's page says the game is played without Kidux too, at its own address
# (D120), which its description in the panel leaves out.
for page in "docs/en/modules/kydux.md:Without Kidux" "docs/es/modules/kydux.md:Sin Kidux"; do
    file="${page%%:*}"
    row="${page#*:}"
    if grep -Eq "^\| \*\*$row\*\* \|.*kydux\.kidux\.org" "$file"; then
        echo "PASS  $file says the game is played without Kidux, at kydux.kidux.org"
    else
        echo "FAIL  $file does not say the game is played without Kidux, at kydux.kidux.org" >&2
        failed=$((failed + 1))
    fi
done

exit $failed
