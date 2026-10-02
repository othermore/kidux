#!/usr/bin/python3
"""Makes the web page of kidux-module-hello-web, when the package is built.

    python3 webapp/page.py <locale dir> <content dir> <template> <page>

The page shows hello's page (content/<lang>/hello.md) in the language its
address names, `?lang=es`, or in English: every language's page and words
are written into it here, so that it needs nothing but itself to run. Its
words are translated through the module's own catalogue, compiled into
<locale dir>/<lang>/kidux-module-hello-web.mo.
"""

import gettext
import json
import sys
from pathlib import Path


def N_(message: str) -> str:
    return message


DOMAIN = "kidux-module-hello-web"
WORDS = {
    "done": N_("Done"),
    "save": N_("Save"),
    # The name of the file Save makes, without its .txt.
    "file": N_("hello"),
    "elsewhere": N_("A page on the internet"),
    "closed": N_("This page lives on this computer. The rest of the internet stays closed."),
}


def page(path: Path) -> dict:
    """The heading and the paragraphs of one hello.md, as hello reads it."""
    text = path.read_text(encoding="utf-8")
    if text.startswith("---\n"):
        text = text.split("\n---\n", 1)[1]
    blocks = [" ".join(block.split()) for block in text.strip().split("\n\n")]
    heading = blocks[0].lstrip("#").strip() if blocks and blocks[0].startswith("#") else ""
    return {"heading": heading, "paragraphs": [b for b in blocks[1 if heading else 0:] if b]}


def pages(locale: Path, content: Path) -> dict:
    """Every language's page and words, by language."""
    found = {}
    for directory in sorted(content.iterdir()):
        lang = directory.name
        translations = gettext.translation(DOMAIN, str(locale), languages=[lang], fallback=True)
        found[lang] = dict(page(directory / "hello.md"),
                           words={key: translations.gettext(text) for key, text in WORDS.items()})
    return found


def main(args: list[str]) -> int:
    locale, content, template, output = map(Path, args[1:5])
    text = template.read_text(encoding="utf-8")
    data = json.dumps(pages(locale, content), ensure_ascii=False, sort_keys=True)
    output.write_text(text.replace("@PAGES@", data.replace("</", "<\\/")), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
