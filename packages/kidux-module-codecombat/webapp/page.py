#!/usr/bin/python3
"""Makes CodeCombat's Connecting… page, when the package is built.

    python3 webapp/page.py <locale dir> <po dir> <template> <page>

The window opens on this page first, served by kidux-webapps, while
kidux-webapp has the daemon sign the child in (phase-4c-plan.md, 4.17); it
says so, and says what went wrong when something does, with *Try again*.
kidux-webapp tells it which by calling `kidux.show(state)` in it; with no
account set, the page offers to sign in by hand. Every
language's words are written into it here, English and each of po/*.po,
translated through the module's own catalogue, compiled into
<locale dir>/<lang>/LC_MESSAGES/kidux-module-codecombat.mo.
"""

import gettext
import json
import sys
from pathlib import Path


def N_(message: str) -> str:
    return message


DOMAIN = "kidux-module-codecombat"
WORDS = {
    "connecting": N_("Connecting to CodeCombat…"),
    "refused": N_("I could not sign in to CodeCombat: the email or the password is not right. "
                  "Ask an adult to check your account."),
    "unreachable": N_("CodeCombat does not answer. Check that the internet works, "
                      "or try again in a while."),
    "again": N_("Try again"),
    "notset": N_("No CodeCombat account is set for you yet. The easiest is for an adult to "
                 "put it in CodeCombat's Settings on the adult panel. Until then, you can "
                 "sign in yourself:"),
    "byhand": N_("Sign in myself"),
}


def pages(locale: Path, po: Path) -> dict:
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
    data = json.dumps(pages(locale, po), ensure_ascii=False, sort_keys=True)
    output.write_text(text.replace("@WORDS@", data.replace("</", "<\\/")), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
