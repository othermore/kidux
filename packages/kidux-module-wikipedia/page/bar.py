#!/usr/bin/python3
"""Makes Wikipedia's bar of Back and Forward, when the package is built.

    python3 page/bar.py <locale dir> <po dir> <template> <script>

An application window has no buttons to go back, and a child does not know
Alt+Left (phase-4c-plan.md, 4.18). The manifest names the script this
writes as its `page_script`, which kidux-webapp runs in every page the
window shows. Every language's words are written into it here, English
and each of po/*.po, translated through the module's own catalogue,
compiled into <locale dir>/<lang>/LC_MESSAGES/kidux-module-wikipedia.mo.
"""

import gettext
import json
import sys
from pathlib import Path


def N_(message: str) -> str:
    return message


DOMAIN = "kidux-module-wikipedia"
WORDS = {
    "back": N_("Back"),
    "forward": N_("Forward"),
    "bar": N_("Go back and forward"),
}


def words(locale: Path, po: Path) -> dict:
    """Every language's words, by language: English, and each catalogue's."""
    languages = ["en", *sorted(path.stem for path in po.glob("*.po"))]
    found = {}
    for lang in languages:
        translations = gettext.translation(DOMAIN, str(locale), languages=[lang], fallback=True)
        found[lang] = {key: translations.gettext(text) for key, text in WORDS.items()}
    return found


def main(args: list[str]) -> int:
    locale, po, template, output = map(Path, args[1:5])
    text = template.read_text(encoding="utf-8")
    data = json.dumps(words(locale, po), ensure_ascii=False, sort_keys=True)
    output.write_text(text.replace("@WORDS@", data), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
