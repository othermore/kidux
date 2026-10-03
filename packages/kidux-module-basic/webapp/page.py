#!/usr/bin/python3
"""Makes the web page of kidux-module-basic, when the package is built.

    python3 webapp/page.py <locale dir> <content dir> <drawings dir> <template> <page>

The page is the machine on the left and the guide on the right (D84). Every
language's words and every chapter of its guide are written into it here,
so that it needs nothing but its scripts to run, and it picks the language
its address names, `?lang=es`, or English. The words are translated through
the module's own catalogue, compiled into
<locale dir>/<lang>/LC_MESSAGES/kidux-module-basic.mo.

A chapter is a Markdown file, content/<lang>/NN-name.md, its first line the
heading, read with four conventions and no others (docs/dev/basic.md):

- a fenced block marked `basic` is a listing, shown as the screen prints
  it, with a button that types it into the editor; after `basic`,
  `keys=…` names, separated by commas, the keys the module's tests give it
  when it reads (`Enter` for the Enter key), and `forever` says it never
  ends by itself; neither is shown;
- a quotation is the mascot speaking: the penguin chick beside a speech
  bubble, in a pose when its first word is [think], [point], [cheer] or
  [oops];
- the lines between `::: adult` and `:::` are the box for the adult, shut
  until it is opened;
- a picture, ![words](name.svg), is a drawing from the drawings directory,
  put into the page as it is, with its words for those who cannot see it.
"""

import gettext
import html
import json
import re
import sys
from pathlib import Path

import markdown


def N_(message: str) -> str:
    return message


DOMAIN = "kidux-module-basic"
WORDS = {
    "run": N_("Run"),
    "runKeys": N_("Run the program (Ctrl+Enter)"),
    "stop": N_("Stop"),
    "stopKeys": N_("Stop the program (Escape)"),
    "new": N_("New"),
    "save": N_("Save"),
    "open": N_("Open"),
    "editor": N_("The program"),
    "screen": N_("The screen"),
    "yes": N_("Yes"),
    "no": N_("No"),
    "sure": N_("The program in the editor will be lost. Go on?"),
    # The name of the file Save makes, without its .bas.
    "file": N_("program"),
    "running": N_("The program is running. Escape stops it."),
    "ended": N_("The program has ended."),
    "stopped": N_("You stopped the program."),
    "typed": N_("The program is in the editor. Press Run to see it."),
    "jump": N_("Line {number} jumps to line {target}, and the program has no line {target}."),
    "syntax": N_("BASIC does not understand line {number}."),
    "syntaxLine": N_("BASIC does not understand line {line} of the editor."),
    "syntaxEnd": N_("Something is missing at the end of the program: a NEXT for a FOR, perhaps, or a closing quote."),
    "noData": N_("A READ found no more DATA to read."),
    "inside": N_("The program stopped at a mistake BASIC cannot name. Look for a RETURN without its GOSUB, or a NEXT without its FOR."),
    "other": N_("The program stopped: {message}"),
    "back": N_("Back"),
    "next": N_("Next"),
    "contents": N_("Chapters"),
    "typeIn": N_("Type it in for me"),
    "adult": N_("For the adult"),
}

POSES = ("think", "point", "cheer", "oops")
LISTING = re.compile(r"^```basic(?P<info>[^\n]*)\n(?P<code>.*?)\n```[ \t]*$", re.M | re.S)
ADULT = re.compile(r"^::: adult[ \t]*\n(?P<body>.*?)\n:::[ \t]*$", re.M | re.S)
QUOTE = re.compile(r"(?:^>[^\n]*(?:\n|$))+", re.M)
DRAWING = re.compile(r'<img alt="(?P<alt>[^"]*)" src="(?P<name>[a-z0-9-]+\.svg)" ?/?>')


def body(path: Path) -> str:
    """A chapter's Markdown, without the front matter a translation carries."""
    text = path.read_text(encoding="utf-8")
    if text.startswith("---\n"):
        text = text.split("\n---\n", 1)[1]
    return text.strip() + "\n"


def listings(text: str) -> list[dict]:
    """Every listing of a chapter, {"code", "keys", "forever"}, as the
    tests read them."""
    found = []
    for listing in LISTING.finditer(text):
        info = listing["info"].split()
        keys = next((word[5:] for word in info if word.startswith("keys=")), "")
        found.append({"code": listing["code"], "keys": [key for key in keys.split(",") if key],
                      "forever": "forever" in info})
    return found


def drawing(drawings: Path, name: str, alt: str) -> str:
    svg = (drawings / name).read_text(encoding="utf-8")
    svg = re.sub(r"<\?xml[^>]*\?>\s*", "", svg)
    svg = re.sub(r"<!--.*?-->\s*", "", svg, flags=re.S)
    svg = svg.replace("<svg ", f'<svg role="img" aria-label="{html.escape(alt)}" ', 1)
    return svg.strip()


def chapter(text: str, drawings: Path, words: dict) -> tuple[str, str]:
    """A chapter's heading, and its HTML for the page."""
    kept: list[str] = []

    def keep(fragment: str) -> str:
        kept.append(fragment)
        return f"\n\nKEPT{len(kept) - 1}KEPT\n\n"

    def listing(found: re.Match) -> str:
        code = html.escape(found["code"])
        return keep(f'<div class="listing"><pre>{code}\n</pre>'
                    f'<button type="button" class="type-in">{html.escape(words["typeIn"])}</button></div>')

    def adult(found: re.Match) -> str:
        inner = render(found["body"])
        return keep(f'<details class="adult"><summary>{html.escape(words["adult"])}</summary>{inner}</details>')

    def quote(found: re.Match) -> str:
        said = "\n".join(re.sub(r"^> ?", "", line) for line in found[0].rstrip("\n").split("\n"))
        pose = ""
        first = re.match(r"\[(\w+)\]\s*", said)
        if first and first[1] in POSES:
            pose, said = f"-{first[1]}", said[first.end():]
        mascot = drawing(drawings, f"mascot{pose}.svg", "")
        mascot = mascot.replace('role="img" aria-label=""', 'aria-hidden="true"')
        return keep(f'<div class="bubble">{mascot}<div class="says">{render(said)}</div></div>')

    def render(fragment: str) -> str:
        return markdown.markdown(fragment, output_format="html")

    lines = text.split("\n", 1)
    if not lines[0].startswith("# "):
        raise ValueError(f"a chapter begins with its heading, '# …': {lines[0]!r}")
    heading = lines[0][2:].strip()
    rest = lines[1] if len(lines) > 1 else ""
    rest = LISTING.sub(listing, rest)
    rest = ADULT.sub(adult, rest)
    rest = QUOTE.sub(quote, rest)
    out = render(rest)
    out = re.sub(r"<p>KEPT(\d+)KEPT</p>", lambda found: kept[int(found[1])], out)
    while re.search(r"KEPT\d+KEPT", out):
        out = re.sub(r"KEPT(\d+)KEPT", lambda found: kept[int(found[1])], out)
    out = DRAWING.sub(lambda found: f'<figure class="drawing">{drawing(drawings, found["name"], html.unescape(found["alt"]))}</figure>', out)
    out = re.sub(r"<p>(<figure .*?</figure>)</p>", r"\1", out, flags=re.S)
    return heading, f"<h1>{html.escape(heading)}</h1>\n{out}"


def pages(locale: Path, content: Path, drawings: Path) -> dict:
    """Every language's words and chapters, by language."""
    found = {}
    for directory in sorted(path for path in content.iterdir() if path.is_dir()):
        lang = directory.name
        translations = gettext.translation(DOMAIN, str(locale), languages=[lang], fallback=True)
        words = {key: translations.gettext(text) for key, text in WORDS.items()}
        chapters = []
        for path in sorted(directory.glob("*.md")):
            heading, html_ = chapter(body(path), drawings, words)
            chapters.append({"slug": path.stem, "title": heading, "html": html_})
        found[lang] = {"lang": lang, "words": words, "chapters": chapters}
    return found


def main(args: list[str]) -> int:
    locale, content, drawings, template, output = map(Path, args[1:6])
    text = template.read_text(encoding="utf-8")
    data = json.dumps(pages(locale, content, drawings), ensure_ascii=False, sort_keys=True)
    output.write_text(text.replace("@PAGES@", data.replace("</", "<\\/")), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
