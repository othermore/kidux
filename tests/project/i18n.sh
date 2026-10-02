#!/bin/sh
# Refuse a change that would put an untranslated string in front of a child.
#
#   tests/project/i18n.sh
#
# Kidux ships in Spanish and English from the first day, and that only stays
# true if it is impossible to forget. This is what makes forgetting fail loudly
# instead of shipping a Spanish child an English screen.
#
# Four things are checked, for Kidux's own domain and for every learning
# module's (ci/i18n-extract.sh):
#
#   1. The catalogue template matches the source. Adding a string without
#      running ci/i18n-extract.sh fails here.
#   2. Every catalogue is complete: nothing untranslated, nothing left fuzzy.
#      A fuzzy entry is gettext saying "this is probably wrong", and probably
#      wrong is not good enough for a screen a child reads.
#   3. Every catalogue compiles.
#   4. No user-visible string reaches a widget without passing through _().

set -eu

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
PO_DIR="$REPO_ROOT/packages/kidux-common/po"
POT="$PO_DIR/kidux.pot"

failures=0

fail() {
    echo "FAIL  $1" >&2
    failures=$((failures + 1))
}

pass() {
    echo "PASS  $1"
}

# --- 1. is the template up to date? ------------------------------------------

tmpdir="$(mktemp -d)"
trap 'rm -rf "$tmpdir"' EXIT

# The creation date changes on every run and means nothing, so it is the one
# line the comparison ignores.
strip_date() {
    grep -v '^"POT-Creation-Date:' "$1" > "$2"
}

if [ ! -f "$POT" ]; then
    fail "no catalogue template at $POT; run ci/i18n-extract.sh"
elif ! "$REPO_ROOT/ci/i18n-extract.sh" "$tmpdir/regenerated.pot" >/dev/null 2>&1; then
    fail "could not extract strings from the source"
else
    strip_date "$POT" "$tmpdir/committed.stripped"
    strip_date "$tmpdir/regenerated.pot" "$tmpdir/regenerated.stripped"

    if cmp -s "$tmpdir/committed.stripped" "$tmpdir/regenerated.stripped"; then
        pass "the catalogue template matches the source"
    else
        fail "the catalogue template is out of date; run ci/i18n-extract.sh and commit the result"
        diff "$tmpdir/committed.stripped" "$tmpdir/regenerated.stripped" | head -20 >&2
    fi

    for module in "$REPO_ROOT"/packages/kidux-module-*; do
        [ -d "$module/po" ] || continue
        domain="$(basename "$module")"
        if [ ! -f "$module/po/$domain.pot" ]; then
            fail "no catalogue template for $domain; run ci/i18n-extract.sh"
            continue
        fi
        strip_date "$module/po/$domain.pot" "$tmpdir/committed.stripped"
        strip_date "$tmpdir/$domain.pot" "$tmpdir/regenerated.stripped"
        if cmp -s "$tmpdir/committed.stripped" "$tmpdir/regenerated.stripped"; then
            pass "$domain's template matches its source"
        else
            fail "$domain's template is out of date; run ci/i18n-extract.sh and commit the result"
            diff "$tmpdir/committed.stripped" "$tmpdir/regenerated.stripped" | head -20 >&2
        fi
    done
fi

# --- 2 and 3. are the catalogues complete and usable? ------------------------

found_catalogue=0
for po in "$PO_DIR"/*.po "$REPO_ROOT"/packages/kidux-module-*/po/*.po; do
    [ -e "$po" ] || continue
    case "$po" in
        "$PO_DIR"/*) found_catalogue=1; language="$(basename "$po" .po)" ;;
        *) language="$(basename "$(dirname "$(dirname "$po")")"): $(basename "$po" .po)" ;;
    esac

    untranslated="$(msgattrib --untranslated --no-obsolete "$po" | grep -c '^msgid "' || true)"
    # msgattrib always emits the header entry, whose msgid is the empty string.
    untranslated=$((untranslated > 0 ? untranslated - 1 : 0))

    fuzzy="$(msgattrib --only-fuzzy --no-obsolete "$po" | grep -c '^msgid "' || true)"
    fuzzy=$((fuzzy > 0 ? fuzzy - 1 : 0))

    if [ "$untranslated" -eq 0 ] && [ "$fuzzy" -eq 0 ]; then
        pass "$language is fully translated"
    else
        fail "$language has $untranslated untranslated and $fuzzy fuzzy entries"
        msgattrib --untranslated --only-fuzzy --no-obsolete "$po" \
            | grep '^msgid "' | grep -v '^msgid ""$' | head -10 >&2
    fi

    if msgfmt --check --output-file=/dev/null "$po" 2>/dev/null; then
        pass "$language compiles"
    else
        fail "$language does not compile"
        msgfmt --check --output-file=/dev/null "$po" >&2 2>&1 || true
    fi
done

if [ "$found_catalogue" -eq 0 ]; then
    fail "no catalogues found in $PO_DIR"
fi

# --- 4. did a string reach a widget without being translated? ----------------

# Only literals matter. A variable passed to set_label may well hold something
# that was translated where it was built, and this cannot tell; a literal in
# the call is unambiguous, and unambiguous is what a check that blocks a commit
# has to be.
setters='set_label|set_title|set_text|set_subtitle|set_tooltip_text|set_placeholder_text|add_button'

# A module's programs live in its bin/ without a .py suffix, and are read too.
offenders="$(find "$REPO_ROOT/packages" \
        -path '*/debian' -prune -o \( -name '*.py' -o -path '*/kidux-module-*/bin/*' \) -type f -print \
    | sort \
    | xargs grep -nE "\.($setters)\([\"']" 2>/dev/null \
    | grep -v ':[0-9]*: *#' \
    || true)"

if [ -z "$offenders" ]; then
    pass "no literal strings go straight into a widget"
else
    fail "these put a literal string into a widget without _():"
    echo "$offenders" | sed 's|^'"$REPO_ROOT"'/||' | head -20 >&2
fi

# --- verdict -----------------------------------------------------------------

echo
if [ "$failures" -eq 0 ]; then
    echo "==> Translations are in order."
    exit 0
fi

echo "==> $failures translation problems." >&2
exit 1
