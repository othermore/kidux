#!/bin/sh
# The user documentation is the same in both languages, and shows only
# pictures that exist or that the release writes.
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

exit $failed
