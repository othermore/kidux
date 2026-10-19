#!/usr/bin/python3
"""Kidux's typing lessons, as a theme of Tux Typing's for each language.

    lessons/build.py OUT    write OUT/kidux-<language>/ for every lessons/<language>.toml

Tux Typing's *Lessons* list the files of its theme's scripts/ folder, by
their names, and runs the one chosen. Debian's lessons are drafts in English
only, and the Spanish theme has none, so Kidux brings a theme of its own for
each language it has lessons in, kidux-<language> (D112), which Kidux's
build of Tux Typing, kidux-tuxtype, runs (D113):

    settings.txt   the theme's locale, for Tux Typing's own words
    keyboard.lst   the language's keyboard table: which finger types each
                   key, and the key of the US keyboard in its place, which
                   is how Tux Typing knows where a key is, to frame it and
                   to label it on the practice's keyboard
    words          the games' word lists: the language's own, from
                   lessons/<word_lists>/, or a link to the base theme's
    images         a link to the base theme's, when there is one
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
keyboard table, with its place, without which the practice draws a second
keyboard where the hands go, or no frame and no label for the key; and no
character Tux Typing's reader would take for markup. A word list has its
name on its first line, then a word a line in capitals, every character in
the table, none longer than WORD_MOST, none twice.
"""

import os
import shutil
import sys
import tomllib
from pathlib import Path

HERE = Path(__file__).resolve().parent
#: The longest line of text a page shows whole, and the longest practice
#: that stays on one line of the practice's screen.
TEXT_MOST = 44
PRACTICE_MOST = 36
#: The longest word the games' falling words have room for.
WORD_MOST = 12
#: Characters Tux Typing's script reader would take for its own.
MARKUP = set('<>&"')


def keyboard_table(lessons: dict) -> dict[str, bool]:
    """The keys the language's keyboard table names, each with whether the
    table gives its place (`finger|key|US key`) or its finger alone. Tux
    Typing reads a line by its characters' positions, the finger first,
    the key third and the US key fifth, so that `9||||` is the bar's."""
    lines = (HERE / lessons["keyboard"]).read_text(encoding="utf-8").splitlines()
    table = {}
    for line in lines:
        if line.startswith("#") or len(line) < 3 or line[1] != "|":
            continue
        table[line[2]] = len(line) >= 5 and line[3] == "|"
    return table


def word_lists(lessons: dict) -> list[Path]:
    """The language's own word lists for the games, if it has any."""
    if not lessons.get("word_lists"):
        return []
    return sorted((HERE / lessons["word_lists"]).glob("*.txt"))


def check_words(path: Path, table: dict[str, bool]) -> list[str]:
    """What is wrong with a word list, if anything."""
    problems = []
    lines = path.read_text(encoding="utf-8").splitlines()
    where = f"{path.parent.name}/{path.name}"
    if len(lines) < 2 or not lines[0].strip():
        return [f"{where}: no name on its first line, or no words"]
    seen = set()
    for word in lines[1:]:
        if word != word.upper() or not word or " " in word:
            problems.append(f"{where}: {word!r} is not one word in capitals")
        if len(word) > WORD_MOST:
            problems.append(f"{where}: {word!r} is longer than {WORD_MOST} characters")
        missing = sorted(set(word) - set(table))
        if missing:
            problems.append(f"{where}: {word!r} has keys the keyboard table lacks: {missing}")
        if word in seen:
            problems.append(f"{where}: {word!r} is there twice")
        seen.add(word)
    return problems


def check(lessons: dict, name: str) -> list[str]:
    """What is wrong with a language's lessons and word lists, if anything."""
    problems = []
    table = keyboard_table(lessons)
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
            missing = sorted(set(practice) - set(table))
            if missing:
                problems.append(f"{where}: {practice!r} has keys the keyboard table lacks: {missing}")
            unplaced = sorted(key for key in set(practice) & set(table)
                              if key != " " and not table[key])
            if unplaced:
                problems.append(f"{where}: {practice!r} has keys the table does not place: {unplaced}")
        for text in texts + [lesson["drill"], lesson["words"]]:
            if set(text) & MARKUP:
                problems.append(f"{where}: {text!r} holds a character Tux Typing reads as markup")
    for key, text in lessons["words"].items():
        if len(text) > TEXT_MOST:
            problems.append(f"{name}, words.{key}: {text!r} is longer than {TEXT_MOST} characters")
    if lessons.get("word_lists") and not word_lists(lessons):
        problems.append(f"{name}: lessons/{lessons['word_lists']}/ has no word lists")
    for path in word_lists(lessons):
        problems += check_words(path, table)
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
        if name.is_dir() and not name.is_symlink():
            shutil.rmtree(name)
        else:
            name.unlink()
    os.symlink(target, name)


def build(out: Path) -> list[Path]:
    made, problems = [], []
    every = sorted(HERE.glob("*.toml"))
    for source in every:
        lessons = tomllib.loads(source.read_text(encoding="utf-8"))
        problems += check(lessons, source.name)
    if problems:
        sys.exit("lessons/build.py:\n  " + "\n  ".join(problems))
    for source in every:
        lessons = tomllib.loads(source.read_text(encoding="utf-8"))
        theme = out / f"kidux-{lessons['language']}"
        (theme / "scripts").mkdir(parents=True, exist_ok=True)
        (theme / "settings.txt").write_text(f"theme_locale_name={lessons['locale']}\n",
                                            encoding="utf-8")
        (theme / "keyboard.lst").write_text(
            (HERE / lessons["keyboard"]).read_text(encoding="utf-8"), encoding="utf-8")
        base = f"../{lessons['base']}" if lessons["base"] else "../.."
        lists = word_lists(lessons)
        if lists:
            words = theme / "words"
            if words.is_symlink():
                words.unlink()
            words.mkdir(exist_ok=True)
            for path in lists:
                (words / path.name).write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
        else:
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
