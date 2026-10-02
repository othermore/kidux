#!/bin/sh
# Collect every translatable string in the project and update the catalogues.
#
#   ci/i18n-extract.sh
#
# Run this whenever a user-visible string is added, changed or removed, and
# commit the result alongside the change. tests/project/i18n.sh fails if you did not.
#
# Kidux has one gettext domain for everything it ships, so a word is translated
# once and reads the same on every screen. The catalogues live with
# kidux-common, which is the package that installs them, and this script reaches
# across every package to fill them.
#
# A learning module is the exception: it is a package of its own that an adult
# installs or removes on its own, so it brings its own words. Every
# packages/kidux-module-<id>/po/ is the gettext domain kidux-module-<id>,
# extracted from that package alone: its program, and the name and description
# in its manifest (modules.md, section 3).

set -eu

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PO_DIR="$REPO_ROOT/packages/kidux-common/po"
DOMAIN=kidux

# With an argument, write the template there and merge nothing. That is how
# tests/project/i18n.sh compares what the source says against what was committed,
# without touching the committed file at all. Each module's template then goes
# beside it, as <domain>.pot.
POT="${1:-$PO_DIR/kidux.pot}"
MERGE=yes
if [ "$#" -gt 0 ]; then
    MERGE=no
fi

mkdir -p "$PO_DIR" "$(dirname "$POT")"

# Absolute, because the next thing this does is change directory.
case "$POT" in
    /*) ;;
    *) POT="$(pwd)/$POT" ;;
esac

# Everything is named relative to the repository root, so the file references
# xgettext writes into the template are the same on every machine. With
# absolute paths the template would differ between a developer's home directory
# and CI, and the check that it is up to date would fail for no reason.
cd "$REPO_ROOT"

# Sorted, so that the template does not churn with whatever order the
# filesystem happens to return files in, and every diff is a real change.
# debian/ holds packaging, not interface. tests/ holds strings that only a
# test ever reads, and translating those would fill the catalogue with words no
# child will ever see.
sources="$(find packages \
    -path 'packages/kidux-module-*' -prune -o \
    -path '*/debian' -prune -o \
    -path '*/tests' -prune -o \
    \( -name '*.py' -o -name '*.ui' \) -print | sort)"

if [ -z "$sources" ]; then
    echo "$0: no sources to extract from" >&2
    exit 1
fi

echo "==> Extracting into $POT"
# shellcheck disable=SC2086
xgettext \
    --from-code=UTF-8 \
    --language=Python \
    --keyword=_ \
    --keyword=N_ \
    --keyword=ngettext:1,2 \
    --keyword=pgettext:1c,2 \
    --add-comments=TRANSLATORS \
    --sort-by-file \
    --package-name="$DOMAIN" \
    --copyright-holder="Antonio Morales Garcia" \
    --package-version=0.1.0 \
    --msgid-bugs-address=info@kidux.org \
    --output="$POT" \
    $sources

if [ "$MERGE" = yes ]; then
    for po in "$PO_DIR"/*.po; do
        [ -e "$po" ] || continue
        echo "==> Merging into $(basename "$po")"
        msgmerge --quiet --update --backup=none --sort-by-file "$po" "$POT"
    done
fi

# The modules' own domains. A manifest is TOML, which xgettext cannot read, so
# its name and description are handed to it as the Python they would be; the
# references are left out, since they would name that temporary file.
for module in packages/kidux-module-*; do
    [ -d "$module/po" ] || continue
    domain="$(basename "$module")"
    if [ "$MERGE" = yes ]; then
        module_pot="$module/po/$domain.pot"
    else
        module_pot="$(dirname "$POT")/$domain.pot"
    fi
    words="$(mktemp -d)"
    python3 - "$module/module.toml" > "$words/manifest.py" <<'PYTHON'
import sys
import tomllib

with open(sys.argv[1], "rb") as manifest:
    fields = tomllib.load(manifest)
for field in ("name", "description"):
    if fields.get(field):
        print(f"N_({fields[field]!r})")
PYTHON
    echo "==> Extracting $domain into $module_pot"
    xgettext \
        --from-code=UTF-8 \
        --language=Python \
        --keyword=_ \
        --keyword=N_ \
        --no-location \
        --package-name="$domain" \
        --copyright-holder="Antonio Morales Garcia" \
        --package-version=0.1.0 \
        --msgid-bugs-address=info@kidux.org \
        --output="$module_pot" \
        "$words/manifest.py" $([ -d "$module/bin" ] && find "$module/bin" -maxdepth 1 -type f | sort) \
        $([ -d "$module/webapp" ] && find "$module/webapp" -maxdepth 1 -name '*.py' | sort)
    rm -rf "$words"
    if [ "$MERGE" = yes ]; then
        for po in "$module"/po/*.po; do
            [ -e "$po" ] || continue
            echo "==> Merging into $po"
            msgmerge --quiet --update --backup=none "$po" "$module_pot"
        done
    fi
done

if [ "$MERGE" = no ]; then
    exit 0
fi

echo
echo "==> Done. Translate anything new, then run tests/project/i18n.sh"
