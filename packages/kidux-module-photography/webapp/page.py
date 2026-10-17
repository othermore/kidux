#!/usr/bin/python3
"""Makes the web page of kidux-module-photography, when the package is built.

    python3 webapp/page.py <locale dir> <content dir> <drawings dir> <pictures dir> <template> <page>

The page is a guide, one chapter at a time (docs/dev/photography.md). Every
language's words and every chapter of it are written into it here, so that
it needs nothing but its script, its style and its photographs to run, and
it picks the language its address names, `?lang=es`, or English. The words
are translated through the module's own catalogue, compiled into
<locale dir>/<lang>/LC_MESSAGES/kidux-module-photography.mo.

A chapter is a Markdown file, content/<lang>/NN-name.md, its first line the
heading, read with seven conventions and no others:

- a quotation is the mascot speaking: the penguin chick beside a speech
  bubble, in a pose when its first word is [think], [point], [cheer] or
  [oops];
- the lines between `::: try` and `:::` are *Try it*, what the child does
  with the camera now;
- the lines between `::: camera` and `:::` are the box of the camera the
  guide is written with, the Olympus XZ-2, which says first that other
  cameras have the same under other names;
- the lines between `::: adult` and `:::` are the box for the adult, shut
  until it is opened;
- the lines between `::: compare` and `:::` hold two to four pictures,
  photographs or drawings, shown side by side, each with its words under
  it;
- a drawing, ![words](name.svg), is a drawing from the drawings directory,
  put into the page as it is, with its words for those who cannot see it;
- a photograph, ![caption](name.jpg), is a picture from the pictures
  directory, with its caption under it and its credit from
  pictures/pictures.toml after the caption; with the title "thirds",
  ![caption](name.jpg "thirds"), the rule of thirds' grid is drawn over it.
"""

import gettext
import html
import json
import re
import struct
import sys
import tomllib
from pathlib import Path

import markdown


def N_(message: str) -> str:
    return message


DOMAIN = "kidux-module-photography"
#: The camera the guide is written with; a name, the same in every language.
CAMERA = "Olympus XZ-2"
WORDS = {
    "title": N_("Photography"),
    "back": N_("Back"),
    "next": N_("Next"),
    "contents": N_("Chapters"),
    "try": N_("Try it"),
    # The heading of the camera's box: {camera} is its name, Olympus XZ-2.
    "camera": N_("On the {camera}"),
    "others": N_("Other cameras have the same thing under other names; chapter 3 says how to find it."),
    "adult": N_("For the adult"),
    # Under a photograph: who took it, and under what licence.
    "credit": N_("Photo: {author}, {licence}"),
    # The same, under a photograph the guide changed: cropped, given more
    # or less light, made grey. Its licence asks for the change to be said.
    "creditEdited": N_("Photo: {author}, {licence}, edited"),
    "kidux": N_("Photo: Kidux"),
    # Under a picture generated for the guide, which no camera took.
    "generated": N_("Picture made by a computer"),
    "publicDomain": N_("public domain"),
}

POSES = ("think", "point", "cheer", "oops")
BOXES = ("try", "camera", "adult", "compare")
BOX = re.compile(r"^::: (?P<kind>" + "|".join(BOXES) + r")[ \t]*\n(?P<body>.*?)\n:::[ \t]*$",
                 re.M | re.S)
QUOTE = re.compile(r"(?:^>[^\n]*(?:\n|$))+", re.M)
DRAWING = re.compile(r'<img alt="(?P<alt>[^"]*)" src="(?P<name>[a-z0-9-]+\.svg)" ?/?>')
PHOTO = re.compile(r'<img alt="(?P<alt>[^"]*)" src="(?P<name>[a-z0-9-]+\.jpg)"'
                   r'(?: title="(?P<title>[^"]*)")? ?/?>')

#: How a licence is written under a photograph; public domain is a phrase,
#: and is translated.
LICENCES = {
    "CC0-1.0": "CC0",
    "CC-BY-2.0": "CC BY 2.0",
    "CC-BY-3.0": "CC BY 3.0",
    "CC-BY-4.0": "CC BY 4.0",
    "CC-BY-SA-2.0": "CC BY-SA 2.0",
    "CC-BY-SA-3.0": "CC BY-SA 3.0",
    "CC-BY-SA-4.0": "CC BY-SA 4.0",
}


def body(path: Path) -> str:
    """A chapter's Markdown, without the front matter a translation carries."""
    text = path.read_text(encoding="utf-8")
    if text.startswith("---\n"):
        text = text.split("\n---\n", 1)[1]
    return text.strip() + "\n"


def credits(pictures: Path) -> dict:
    """pictures.toml: one table a photograph, by its file's name."""
    listed = pictures / "pictures.toml"
    if not listed.is_file():
        return {}
    with listed.open("rb") as file:
        return tomllib.load(file)


def credit(entry: dict, words: dict) -> str:
    """What is written under a photograph, after its caption."""
    if entry.get("author") == "generated":
        return words["generated"]
    if entry.get("licence") == "BUSL-1.1":
        return words["kidux"]
    licence = entry.get("licence", "")
    shown = words["publicDomain"] if licence == "public-domain" else LICENCES.get(licence, licence)
    form = words["creditEdited"] if entry.get("made") else words["credit"]
    return form.format(author=entry.get("author", ""), licence=shown)


def drawing(drawings: Path, name: str, alt: str) -> str:
    svg = (drawings / name).read_text(encoding="utf-8")
    svg = re.sub(r"<\?xml[^>]*\?>\s*", "", svg)
    svg = re.sub(r"<!--.*?-->\s*", "", svg, flags=re.S)
    svg = svg.replace("<svg ", f'<svg role="img" aria-label="{html.escape(alt)}" ', 1)
    return svg.strip()


def jpeg_size(path: Path) -> tuple[int, int]:
    """A JPEG's width and height, from its frame header."""
    data = path.read_bytes()
    at = 2
    while at + 9 < len(data):
        marker, length = data[at + 1], struct.unpack(">H", data[at + 2:at + 4])[0]
        if 0xC0 <= marker <= 0xCF and marker not in (0xC4, 0xC8, 0xCC):
            height, width = struct.unpack(">HH", data[at + 5:at + 9])
            return width, height
        at += 2 + length
    raise ValueError(f"{path.name} has no frame header")


def photo(name: str, alt: str, title: str | None, entry: dict, words: dict,
          size: tuple[int, int] | None = None) -> str:
    """A photograph's figure. Its size is written into it, so that the page
    keeps its room before it has loaded, which a picture loaded only when
    it comes into view needs to come into view at all."""
    caption = html.unescape(alt)
    classes = "photo thirds" if title == "thirds" else "photo"
    sized = f' width="{size[0]}" height="{size[1]}"' if size else ""
    return (f'<figure class="{classes}"><div class="frame">'
            f'<img src="pictures/{name}" alt="{html.escape(caption)}"{sized} loading="lazy"></div>'
            f'<figcaption>{html.escape(caption)}'
            f'<span class="credit">{html.escape(credit(entry, words))}</span></figcaption></figure>')


def chapter(text: str, drawings: Path, words: dict, pictures: dict | None = None,
            number: int | None = None, folder: Path | None = None) -> tuple[str, str]:
    """A chapter's heading, and its HTML for the page; with its number,
    from its file's name, before the heading, so that a child remembers
    where they were."""
    pictures = pictures or {}
    kept: list[str] = []

    def keep(fragment: str) -> str:
        kept.append(fragment)
        return f"\n\nKEPT{len(kept) - 1}KEPT\n\n"

    def box(found: re.Match) -> str:
        kind, inner = found["kind"], render(found["body"])
        if kind == "adult":
            return keep(f'<details class="adult"><summary>{html.escape(words["adult"])}'
                        f'</summary>{inner}</details>')
        if kind == "try":
            return keep(f'<section class="try"><h3>{html.escape(words["try"])}</h3>{inner}</section>')
        if kind == "camera":
            heading = words["camera"].format(camera=CAMERA)
            return keep(f'<section class="camera"><h3>{html.escape(heading)}</h3>'
                        f'<p class="others">{html.escape(words["others"])}</p>{inner}</section>')
        # Side by side, a drawing has its words under it too, since the
        # pictures are told apart by them.
        inner = DRAWING.sub(lambda found: f'<figure class="drawing">'
                            f'{drawing(drawings, found["name"], html.unescape(found["alt"]))}'
                            f'<figcaption>{found["alt"]}</figcaption></figure>', inner)
        return keep(f'<div class="compare">{inner}</div>')

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
    if number is not None:
        heading = f"{number}. {heading}"
    rest = lines[1] if len(lines) > 1 else ""
    rest = BOX.sub(box, rest)
    rest = QUOTE.sub(quote, rest)
    out = render(rest)
    out = re.sub(r"<p>KEPT(\d+)KEPT</p>", lambda found: kept[int(found[1])], out)
    while re.search(r"KEPT\d+KEPT", out):
        out = re.sub(r"KEPT(\d+)KEPT", lambda found: kept[int(found[1])], out)
    out = DRAWING.sub(lambda found: f'<figure class="drawing">'
                      f'{drawing(drawings, found["name"], html.unescape(found["alt"]))}</figure>', out)
    def sized(name: str) -> tuple[int, int] | None:
        return jpeg_size(folder / name) if folder is not None and (folder / name).is_file() else None

    out = PHOTO.sub(lambda found: photo(found["name"], found["alt"], found["title"],
                                        pictures.get(found["name"], {}), words,
                                        sized(found["name"])), out)
    out = re.sub(r"<p>((?:<figure .*?</figure>\s*)+)</p>", r"\1", out, flags=re.S)
    return heading, f"<h1>{html.escape(heading)}</h1>\n{out}"


def pages(locale: Path, content: Path, drawings: Path, pictures: Path) -> dict:
    """Every language's words and chapters, by language."""
    found = {}
    listed = credits(pictures)
    for directory in sorted(path for path in content.iterdir() if path.is_dir()):
        lang = directory.name
        translations = gettext.translation(DOMAIN, str(locale), languages=[lang], fallback=True)
        words = {key: translations.gettext(text) for key, text in WORDS.items()}
        chapters = []
        for path in sorted(directory.glob("*.md")):
            heading, html_ = chapter(body(path), drawings, words, listed,
                                     int(path.stem.split("-", 1)[0]), pictures)
            chapters.append({"slug": path.stem, "title": heading, "html": html_})
        found[lang] = {"lang": lang, "words": words, "chapters": chapters}
    return found


def main(args: list[str]) -> int:
    locale, content, drawings, pictures, template, output = map(Path, args[1:7])
    text = template.read_text(encoding="utf-8")
    data = json.dumps(pages(locale, content, drawings, pictures), ensure_ascii=False,
                      sort_keys=True)
    output.write_text(text.replace("@PAGES@", data.replace("</", "<\\/")), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
