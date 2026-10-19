#!/usr/bin/python3
"""Kidux's typing lessons, as a theme of Tux Typing's for each language.

    lessons/build.py OUT    write OUT/kidux-<language>/ for every lessons/<language>.toml

Tux Typing's *Lessons* list the files of its theme's scripts/ folder, by
their names, and runs the one chosen. Debian's lessons are drafts in English
only, and the Spanish theme has none, so that a Spanish-speaking child's
list opened nothing (D112). Kidux brings a theme of its own
for each language it has lessons in, kidux-<language>:

    settings.txt   the theme's locale, for Tux Typing's own words
    keyboard.lst   which finger types each key, for the practice's hands: the
                   lessons' own (Spanish's, with ñ, the comma and the full
                   stop, which Debian's Spanish theme lacks), or a link to
                   Tux Typing's own
    words, images  links to the base theme's, so that the games keep its words
    scripts/       a lesson a file, named as the list shows it

A lesson is four pages, in the shape Tux Typing's own lessons have, which
its script reader is particular about: the keys and where the fingers go,
Enter to go on; the fingers again over a keyboard, P to practise them; a
line of words made of the keys learnt so far, P again; and well done. Each
practice comes after an empty page, as Tux Typing's own lessons have it.

What Tux Typing's screen can show is checked here and the build fails
otherwise: a line of text at most TEXT_MOST characters, a practice at most
PRACTICE_MOST, so that it stays on one line; every character of a practice a
key learnt in this lesson or an earlier one; every one of them in the
keyboard table, without which the practice draws a second keyboard where the
hands go; and no character Tux Typing's reader would take for markup.
"""

import os
import sys
import tomllib
from pathlib import Path

HERE = Path(__file__).resolve().parent
#: The longest line of text a page shows whole, and the longest practice
#: that stays on one line of the practice's screen.
TEXT_MOST = 44
PRACTICE_MOST = 36
#: Characters Tux Typing's script reader would take for its own.
MARKUP = set('<>&"')


def keyboard_keys(lessons: dict) -> set[str]:
    """The keys the theme's keyboard table names."""
    if lessons["keyboard"]:
        lines = (HERE / lessons["keyboard"]).read_text(encoding="utf-8").splitlines()
    else:
        # Tux Typing's own table, the English keyboard's: what Debian's
        # tuxtype-data installs as /usr/share/tuxtype/keyboard.lst.
        lines = (HERE / "keyboard-tuxtype.lst").read_text(encoding="utf-8").splitlines()
    return {line.split("|", 1)[1] for line in lines
            if "|" in line and not line.startswith("#") and len(line.split("|", 1)[1]) == 1}


def check(lessons: dict, name: str) -> list[str]:
    """What is wrong with a language's lessons, if anything."""
    problems = []
    table = keyboard_keys(lessons)
    learnt = {" "}
    for number, lesson in enumerate(lessons["lesson"], 1):
        where = f"{name}, lesson {number}"
        learnt |= set(lesson["keys"].replace(" ", "")) | {key.upper() for key in lesson["keys"]}
        texts = lesson["intro"] + lesson["fingers"] + [
            lessons["words"]["title"].format(number=number, keys=lesson["keys"])]
        for text in texts:
            if len(text) > TEXT_MOST:
                problems.append(f"{where}: {text!r} is longer than {TEXT_MOST} characters")
        for practice in (lesson["drill"], lesson["words"]):
            if len(practice) > PRACTICE_MOST:
                problems.append(f"{where}: {practice!r} is longer than {PRACTICE_MOST} characters")
            unlearnt = sorted(set(practice) - learnt)
            if unlearnt:
                problems.append(f"{where}: {practice!r} has keys not learnt yet: {unlearnt}")
            missing = sorted(set(practice) - table)
            if missing:
                problems.append(f"{where}: {practice!r} has keys the keyboard table lacks: {missing}")
        for text in texts + [lesson["drill"], lesson["words"]]:
            if set(text) & MARKUP:
                problems.append(f"{where}: {text!r} holds a character Tux Typing reads as markup")
    for key, text in lessons["words"].items():
        if len(text) > TEXT_MOST:
            problems.append(f"{name}, words.{key}: {text!r} is longer than {TEXT_MOST} characters")
    return problems


def text(line: str, y: int) -> str:
    return f'       <text align="center" y="{y}">{line}</text>'


def script(lessons: dict, number: int, lesson: dict, last: bool) -> str:
    """One lesson, in the shape Tux Typing's own lessons have."""
    words = lessons["words"]
    title = words["title"].format(number=number, keys=lesson["keys"])
    ending = words["last"] if last else words["next"].format(next=number + 1)
    lines = [f'<script title="{title}" bgcolor="#3f4f1f">',
             f'       <page title="{title}">',
             text(title, 80),
             *(text(line, 160 + 40 * i) for i, line in enumerate(lesson["intro"])),
             text(words["start"], 360),
             "      <waitforinput/>",
             "       </page>",
             f'       <page title="{lesson["keys"]}" bgcolor="#3f7f3f">',
             *(text(line, 30 + 40 * i) for i, line in enumerate(lesson["fingers"])),
             '       <img src="/keyboard/keyboard.png" x="95" y="140"/>',
             text(words["practise"], 380),
             "      <waitforchar/>",
             f"      <prac>{lesson['drill']}</prac>",
             "      </page>",
             "      <page>",
             "      </page>",
             f'       <page title="{words["now_words"]}" bgcolor="#3f7f3f">',
             text(words["now_words"], 80),
             text(words["practise"], 380),
             "      <waitforchar/>",
             f"      <prac>{lesson['words']}</prac>",
             "      </page>",
             "      <page>",
             "      </page>",
             "      <page>",
             text(words["well_done"], 160),
             text(ending, 220),
             text(words["back"], 300),
             "       <waitforinput/>",
             "     </page>",
             "</script>"]
    return "\n".join(lines) + "\n"


def link(target: str, name: Path) -> None:
    if name.is_symlink() or name.exists():
        name.unlink()
    os.symlink(target, name)


def build(out: Path) -> list[Path]:
    made, problems = [], []
    every = sorted(HERE.glob("*.toml"))
    for source in every:
        lessons = tomllib.loads(source.read_text(encoding="utf-8"))
        problems += check(lessons, source.name)
    counts = {source.name: len(tomllib.loads(source.read_text(encoding="utf-8"))["lesson"])
              for source in every}
    if len(set(counts.values())) > 1:
        problems.append(f"the languages have different numbers of lessons: {counts}")
    if problems:
        sys.exit("lessons/build.py:\n  " + "\n  ".join(problems))
    for source in every:
        lessons = tomllib.loads(source.read_text(encoding="utf-8"))
        theme = out / f"kidux-{lessons['language']}"
        (theme / "scripts").mkdir(parents=True, exist_ok=True)
        (theme / "settings.txt").write_text(f"theme_locale_name={lessons['locale']}\n",
                                            encoding="utf-8")
        if lessons["keyboard"]:
            (theme / "keyboard.lst").write_text(
                (HERE / lessons["keyboard"]).read_text(encoding="utf-8"), encoding="utf-8")
        else:
            link("../../keyboard.lst", theme / "keyboard.lst")
        base = f"../{lessons['base']}" if lessons["base"] else "../.."
        link(f"{base}/words", theme / "words")
        if lessons["base"]:
            link(f"{base}/images", theme / "images")
        count = len(lessons["lesson"])
        for number, lesson in enumerate(lessons["lesson"], 1):
            name = lessons["file"].format(number=number, name=lesson.get("name", lesson["keys"])) + ".xml"
            path = theme / "scripts" / name
            path.write_text(script(lessons, number, lesson, number == count), encoding="utf-8")
            made.append(path)
    return made


if __name__ == "__main__":
    made = build(Path(sys.argv[1]))
    print(f"{len(made)} lessons")
