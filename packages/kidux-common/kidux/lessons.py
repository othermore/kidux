"""A module's guide: its lessons, read for the launcher's pane (D103).

A module whose manifest says `guide = true` has its lessons beside the
manifest, under `content/<lang>/`, one file each, `NN-<slug>.md`, in the
order of their numbers, with the files its lessons open under
`content/<lang>/missions/` and their pictures, shared by the languages,
under `content/images/` (modules.md, section 3). English is the reference:
a lesson missing in the child's language is read in English.

A lesson is Markdown of a small, fixed shape, which this reads into blocks
the launcher draws, and nothing else:

    # Title                       once, first
    ## Heading                    ("heading", 2, text)
    a paragraph                   ("paragraph", runs)
    1. a step                     ("steps", [runs, …])
    - a choice                    ("bullets", [runs, …])
    ![what it shows](images/x)    ("image", path, alt)
    > [think] words               ("mascot", pose, runs)
    @mission missions/x           ("mission", path)
    ::: try … :::                 ("try", [blocks])

A run is (style, text), style "" for plain, "bold" or "italic", from
**bold** and *italic*. A lesson without a title is left out, a picture or
a mission that is not there is left out, each with a line in the log; the
rest of the guide stays.
"""

import logging
import re
from dataclasses import dataclass
from pathlib import Path

log = logging.getLogger("kidux.lessons")

#: A lesson's file: two digits, a hyphen, its name.
LESSON = re.compile(r"^(\d{2})-([a-z0-9-]+)\.md$")
#: The mascot's poses, as the BASIC guide's.
POSES = ("think", "point", "cheer")
#: The language every other is translated from.
SOURCE_LANGUAGE = "en"

_STEP = re.compile(r"^(\d+)\.\s+(.*)$")
_BULLET = re.compile(r"^-\s+(.*)$")
_IMAGE = re.compile(r"^!\[([^\]]*)\]\(([^)\s]+)\)$")
_MASCOT = re.compile(r"^\[(\w+)\]\s*(.*)$", re.S)
_RUN = re.compile(r"(\*\*[^*]+\*\*|\*[^*]+\*)")


@dataclass(frozen=True)
class Lesson:
    number: int
    #: Its file's name, without the number and `.md`: what remembers it.
    slug: str
    title: str
    blocks: tuple


def language_of(locale: str) -> str:
    """`es` from `es_ES.UTF-8`, `en` from nothing."""
    return re.split(r"[_.@]", locale or "", maxsplit=1)[0] or SOURCE_LANGUAGE


def runs(text: str) -> tuple:
    """`text` as runs of plain, bold and italic."""
    found = []
    for part in _RUN.split(" ".join(text.split())):
        if not part:
            continue
        if part.startswith("**") and part.endswith("**") and len(part) > 4:
            found.append(("bold", part[2:-2]))
        elif part.startswith("*") and part.endswith("*") and len(part) > 2:
            found.append(("italic", part[1:-1]))
        else:
            found.append(("", part))
    return tuple(found)


def _items(lines: list[str], pattern: re.Pattern) -> list:
    """The items of a list, each with the lines that continue it."""
    items: list[list[str]] = []
    for line in lines:
        matched = pattern.match(line)
        if matched:
            items.append([matched.group(matched.lastindex)])
        elif items:
            items[-1].append(line.strip())
    return [runs(" ".join(item)) for item in items]


def _group(lines: list[str], content: Path, language: Path, name: str) -> list:
    """The blocks of one group of lines between blank ones."""
    first = lines[0]
    if first.startswith("## "):
        return [("heading", 2, " ".join(first[3:].split()))]
    if first.startswith("@mission "):
        target = (language / first[len("@mission "):].strip()).resolve()
        if not target.is_file() or language.resolve() not in target.parents:
            log.warning("%s: no mission %s", name, first[len("@mission "):].strip())
            return []
        return [("mission", str(target))]
    image = _IMAGE.match(first)
    if image and len(lines) == 1:
        target = (content / image.group(2)).resolve()
        if not target.is_file() or content.resolve() not in target.parents:
            log.warning("%s: no picture %s", name, image.group(2))
            return []
        return [("image", str(target), image.group(1))]
    if first.startswith(">"):
        text = " ".join(line.lstrip(">").strip() for line in lines)
        mascot = _MASCOT.match(text)
        if mascot and mascot.group(1) in POSES:
            return [("mascot", mascot.group(1), runs(mascot.group(2)))]
        return [("mascot", "point", runs(text))]
    if _STEP.match(first):
        return [("steps", _items(lines, _STEP))]
    if _BULLET.match(first):
        return [("bullets", _items(lines, _BULLET))]
    return [("paragraph", runs(" ".join(lines)))]


def parse(text: str, content: Path, language: Path, name: str = "") -> tuple[str, tuple] | None:
    """A lesson's title and blocks, or None when it has no title.
    `content` is the guide's directory, where `images/` is; `language` is
    the lesson's language's, where `missions/` is."""
    lines = text.splitlines()
    while lines and not lines[0].strip():
        lines.pop(0)
    if not lines or not lines[0].startswith("# "):
        log.warning("%s: a lesson starts with its title, # Title", name)
        return None
    title = " ".join(lines[0][2:].split())
    return title, tuple(_blocks(lines[1:], content, language, name))


def _blocks(lines: list[str], content: Path, language: Path, name: str) -> list:
    blocks: list = []
    group: list[str] = []

    def flush():
        if group:
            blocks.extend(_group(group, content, language, name))
            group.clear()

    index = 0
    while index < len(lines):
        line = lines[index]
        if line.strip().startswith("::: try"):
            flush()
            inner: list[str] = []
            index += 1
            while index < len(lines) and lines[index].strip() != ":::":
                inner.append(lines[index])
                index += 1
            blocks.append(("try", tuple(_blocks(inner, content, language, name))))
        elif not line.strip():
            flush()
        else:
            group.append(line.rstrip())
        index += 1
    flush()
    return blocks


def read(content: Path | str, locale: str = "") -> list[Lesson]:
    """The guide under `content`, in the language of `locale`, each lesson
    in English where the language has none; [] when there is no guide."""
    content = Path(content)
    source = content / SOURCE_LANGUAGE
    wanted = content / language_of(locale)
    try:
        names = sorted(entry.name for entry in source.iterdir() if LESSON.match(entry.name))
    except OSError:
        return []
    found = []
    for file_name in names:
        directory = wanted if (wanted / file_name).is_file() else source
        try:
            text = (directory / file_name).read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as error:
            log.warning("%s: %s", file_name, error)
            continue
        parsed = parse(text, content, directory, file_name)
        if parsed is None:
            continue
        number, slug = LESSON.match(file_name).groups()
        found.append(Lesson(number=int(number), slug=slug, title=parsed[0], blocks=parsed[1]))
    return found


def missions(lessons: list[Lesson]) -> list[str]:
    """The mission files the lessons name, each once, in their order."""
    found: list[str] = []

    def walk(blocks):
        for block in blocks:
            if block[0] == "mission" and block[1] not in found:
                found.append(block[1])
            elif block[0] == "try":
                walk(block[1])

    for lesson in lessons:
        walk(lesson.blocks)
    return found
