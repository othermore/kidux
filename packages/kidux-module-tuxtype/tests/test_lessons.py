"""Kidux's typing lessons, built as Tux Typing's themes (lessons/build.py)."""

import importlib.util
import os
import tomllib
from pathlib import Path

import pytest

PACKAGE = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("lessons", PACKAGE / "lessons" / "build.py")
lessons = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lessons)


def test_each_language_gets_a_theme_of_twelve_lessons_named_as_the_list_shows_them(tmp_path):
    lessons.build(tmp_path)

    spanish = sorted(p.name for p in (tmp_path / "kidux-es" / "scripts").iterdir())
    english = sorted(p.name for p in (tmp_path / "kidux-en" / "scripts").iterdir())
    assert len(spanish) == len(english) == 12
    assert spanish[0] == "Lección 01 - a s d f.xml"
    assert spanish[1] == "Lección 02 - j k l ñ.xml"
    assert spanish[-1] == "Lección 12 - x z y punto.xml"
    assert english[-1] == "Lesson 12 - x z and stop.xml"


def test_a_theme_takes_its_words_from_tux_typing_s_and_says_its_locale(tmp_path):
    lessons.build(tmp_path)

    spanish, english = tmp_path / "kidux-es", tmp_path / "kidux-en"
    assert os.readlink(spanish / "words") == "../espanol/words"
    assert os.readlink(spanish / "images") == "../espanol/images"
    assert os.readlink(english / "words") == "../../words"
    assert os.readlink(english / "keyboard.lst") == "../../keyboard.lst"
    assert (spanish / "settings.txt").read_text() == "theme_locale_name=es_ES.UTF-8\n"
    # The Spanish keyboard's own table, ñ and all.
    table = (spanish / "keyboard.lst").read_text(encoding="utf-8").splitlines()
    assert {"9|ñ", "9|Ñ", "5| ", "7|,", "8|."} <= set(table)


def test_a_lesson_has_the_shape_tux_typing_s_reader_runs(tmp_path):
    lessons.build(tmp_path)

    first = (tmp_path / "kidux-es" / "scripts" / "Lección 01 - a s d f.xml").read_text()
    lines = first.splitlines()
    assert lines[0].startswith('<script title="Lección 1: a s d f"')
    assert lines[-1] == "</script>"
    # Enter on the first page; P before each of the two practices, each
    # followed by an empty page; Enter on the last.
    assert first.count("<waitforinput/>") == 2
    assert first.count("<waitforchar/>") == 2
    assert "      <prac>asdf fdsa as df sa fd</prac>" in lines
    assert "      <prac>da das fa dada sasa</prac>" in lines
    assert first.count("      <page>\n      </page>") == 2
    # Every text says where it goes, or Tux Typing puts it on the top edge.
    assert all('y="' in line for line in lines if "<text " in line)
    assert "Sigue con la lección 2." in first
    last = (tmp_path / "kidux-es" / "scripts" / "Lección 12 - x z y punto.xml").read_text()
    assert "Has terminado todas las lecciones." in last


def problems(**changes) -> list:
    source = tomllib.loads((PACKAGE / "lessons" / "es.toml").read_text(encoding="utf-8"))
    source["lesson"][0].update(changes)
    return lessons.check(source, "es.toml")


def test_the_lessons_as_they_are_break_none_of_the_rules():
    for name in ("es.toml", "en.toml"):
        source = tomllib.loads((PACKAGE / "lessons" / name).read_text(encoding="utf-8"))
        assert lessons.check(source, name) == []


@pytest.mark.parametrize("change, said", [
    ({"drill": "asdf fdsa as df sa fd asdf fdsa as df"}, "longer than 36"),
    ({"words": "kilo"}, "not learnt yet"),
    ({"intro": ["Pon los dedos de la mano izquierda sobre la fila del medio"]}, "longer than 44"),
    ({"words": "da & fa"}, "markup"),
])
def test_a_lesson_that_tux_typing_could_not_show_well_fails_the_build(change, said):
    assert any(said in problem for problem in problems(**change)), problems(**change)


def test_a_practice_key_missing_from_the_keyboard_table_fails_the_build():
    # A key the table lacks makes the practice draw a second keyboard.
    source = tomllib.loads((PACKAGE / "lessons" / "es.toml").read_text(encoding="utf-8"))
    source["lesson"][0]["keys"] = "a s d f ¿"
    source["lesson"][0]["drill"] = "asdf ¿"
    assert any("keyboard table lacks" in p for p in lessons.check(source, "es.toml"))
