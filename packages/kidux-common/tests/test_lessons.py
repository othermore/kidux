"""A module's guide as the launcher's pane reads it (kidux.lessons, D103):
each block from its lines, the lessons in order, the child's language with
English where it has none, and what cannot be used left out."""

from pathlib import Path

from kidux import lessons

LESSON = """# Points and lines

Kig is a sheet where everything **can move**, a *point* first.

![Two points](images/two.svg)

@mission missions/middle.kig

1. Press **Point** on the left,
   then click twice.
2. Drag A.

- one choice
- another

> [think] The line turns
> to follow A.

## A triangle

::: try
Make a **square**.

1. Then drag it.
:::
"""


def guide(tmp_path: Path) -> Path:
    content = tmp_path / "content"
    for lang in ("en", "es"):
        (content / lang / "missions").mkdir(parents=True)
    (content / "images").mkdir()
    (content / "images" / "two.svg").write_text("<svg/>")
    (content / "en" / "missions" / "middle.kig").write_text("kig")
    (content / "es" / "missions" / "middle.kig").write_text("kig es")
    (content / "en" / "01-points.md").write_text(LESSON)
    (content / "en" / "02-circles.md").write_text("# Circles\n\nRound.\n")
    (content / "en" / "10-last.md").write_text("# Last\n")
    (content / "es" / "01-points.md").write_text(LESSON.replace("# Points and lines",
                                                                 "# Puntos y rectas"))
    (content / "en" / "notes.txt").write_text("not a lesson")
    return content


def test_each_block_comes_from_its_lines(tmp_path):
    content = guide(tmp_path)
    first = lessons.read(content, "en_US.UTF-8")[0]

    assert (first.number, first.slug, first.title) == (1, "points", "Points and lines")
    assert first.blocks[0] == ("paragraph", (("", "Kig is a sheet where everything "),
                                             ("bold", "can move"), ("", ", a "),
                                             ("italic", "point"), ("", " first.")))
    assert first.blocks[1] == ("image", str((content / "images" / "two.svg").resolve()),
                               "Two points")
    assert first.blocks[2] == ("mission", str((content / "en" / "missions" / "middle.kig")
                                              .resolve()))
    assert first.blocks[3] == ("steps", [(("", "Press "), ("bold", "Point"),
                                          ("", " on the left, then click twice.")),
                                         (("", "Drag A."),)])
    assert first.blocks[4] == ("bullets", [(("", "one choice"),), (("", "another"),)])
    assert first.blocks[5] == ("mascot", "think", (("", "The line turns to follow A."),))
    assert first.blocks[6] == ("heading", 2, "A triangle")
    assert first.blocks[7] == ("try", (("paragraph", (("", "Make a "), ("bold", "square"),
                                                      ("", "."))),
                                       ("steps", [(("", "Then drag it."),)])))


def test_the_lessons_come_in_their_numbers_order_and_nothing_else(tmp_path):
    found = lessons.read(guide(tmp_path), "en")

    assert [(lesson.number, lesson.title) for lesson in found] == [
        (1, "Points and lines"), (2, "Circles"), (10, "Last")]


def test_the_child_s_language_first_and_english_where_it_has_none(tmp_path):
    content = guide(tmp_path)
    found = lessons.read(content, "es_ES.UTF-8")

    assert [lesson.title for lesson in found] == ["Puntos y rectas", "Circles", "Last"]
    # A mission is the lesson's language's own.
    assert ("mission", str((content / "es" / "missions" / "middle.kig").resolve())) \
        in found[0].blocks
    assert lessons.missions(found) == [str((content / "es" / "missions" / "middle.kig")
                                           .resolve())]


def test_what_cannot_be_used_is_left_out_and_the_rest_stays(tmp_path):
    content = guide(tmp_path)
    (content / "en" / "03-untitled.md").write_text("No title here.\n")
    (content / "en" / "missions" / "middle.kig").unlink()
    (content / "images" / "two.svg").unlink()

    found = lessons.read(content, "en")

    assert [lesson.number for lesson in found] == [1, 2, 10]
    kinds = [block[0] for block in found[0].blocks]
    assert "image" not in kinds and "mission" not in kinds
    assert lessons.read(tmp_path / "nowhere", "en") == []


def test_a_mission_or_a_picture_cannot_lead_out_of_the_guide(tmp_path):
    content = guide(tmp_path)
    (tmp_path / "outside.kig").write_text("x")
    (content / "en" / "04-out.md").write_text(
        "# Out\n\n@mission ../../outside.kig\n\n![x](../outside.kig)\n")

    out = next(lesson for lesson in lessons.read(content, "en") if lesson.number == 4)

    assert out.blocks == ()


def test_a_language_from_a_locale():
    assert [lessons.language_of(locale) for locale in ("es_ES.UTF-8", "en", "", "pt_BR")] == [
        "es", "en", "en", "pt"]
