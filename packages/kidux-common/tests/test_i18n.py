"""Tests for translation.

The acceptance for step 9.2 is that this works:

    LANG=es_ES.UTF-8 python3 -c "from kidux.i18n import _; print(_('Adult'))"

and prints "Adulto". These tests are that, plus the ways it could quietly stop
being true.
"""

import importlib
import os
import subprocess
import sys
from pathlib import Path

import pytest

from kidux import i18n, vocabulary


def shared_terms() -> dict[str, str]:
    """The vocabulary's terms, and only those.

    `vars()` also returns what the module imported, and `N_` passes `isupper()`
    because its only cased letter is a capital. Filtering on the value's type
    is what keeps a helper from being mistaken for a word on a screen.
    """
    return {
        name: value
        for name, value in vars(vocabulary).items()
        if name.isupper() and not name.startswith("_") and isinstance(value, str)
    }


@pytest.fixture
def compiled_catalogues(tmp_path, catalogues):
    """Compile the committed catalogues into a throwaway locale directory.

    Against the real es.po, not a fixture: a test that passes on an invented
    catalogue would say nothing about whether a Spanish child sees Spanish.
    """
    for po in sorted(catalogues.glob("*.po")):
        language = po.stem
        destination = tmp_path / language / "LC_MESSAGES"
        destination.mkdir(parents=True)
        subprocess.run(
            ["msgfmt", "--check", "-o", str(destination / "kidux.mo"), str(po)],
            check=True,
        )
    return tmp_path


def test_spanish_translates_the_shared_vocabulary(compiled_catalogues, monkeypatch):
    monkeypatch.setenv("KIDUX_LOCALE_ROOT", str(compiled_catalogues))
    monkeypatch.setenv("LANGUAGE", "es")

    importlib.reload(i18n)

    assert i18n._(vocabulary.ADULT) == "Adulto"
    assert i18n._(vocabulary.LOG_OUT) == "Salir"
    assert i18n._(vocabulary.TIME_IS_UP) == "Se ha acabado el tiempo"


def test_english_is_the_source_language_and_needs_no_catalogue(monkeypatch, tmp_path):
    # An empty locale directory: nothing to fall back to. English must still
    # come out, because an untranslated string already is English.
    monkeypatch.setenv("KIDUX_LOCALE_ROOT", str(tmp_path))
    monkeypatch.setenv("LANGUAGE", "en")

    importlib.reload(i18n)

    assert i18n._(vocabulary.ADULT) == "Adult"


def test_a_missing_catalogue_falls_back_instead_of_crashing(monkeypatch, tmp_path):
    # A packaging bug, but it must not take down a screen a child is looking
    # at. English on screen beats a traceback.
    monkeypatch.setenv("KIDUX_LOCALE_ROOT", str(tmp_path))
    monkeypatch.setenv("LANGUAGE", "de")

    importlib.reload(i18n)

    assert i18n._(vocabulary.ADULT) == "Adult"


def test_the_acceptance_command_from_the_plan(compiled_catalogues):
    # Run as its own process, exactly as the plan writes it, because importing
    # is the thing being tested and a reload inside this process would not
    # prove that a fresh interpreter gets it right.
    environment = {
        **os.environ,
        "KIDUX_LOCALE_ROOT": str(compiled_catalogues),
        "LANGUAGE": "es",
        "LANG": "es_ES.UTF-8",
        "PYTHONPATH": str(Path(__file__).resolve().parents[1]),
    }

    result = subprocess.run(
        [sys.executable, "-c", "from kidux.i18n import _; print(_('Adult'))"],
        capture_output=True,
        text=True,
        env=environment,
        check=True,
    )

    assert result.stdout.strip() == "Adulto"


def test_N_marks_without_translating():
    # N_ has to be transparent: it exists so xgettext can see a string that is
    # defined before anything knows what language the screen will be in.
    assert i18n.N_("Adult") == "Adult"


def test_every_vocabulary_term_is_a_non_empty_string():
    terms = shared_terms()

    # Named explicitly, so that a filter which quietly matched nothing could
    # not make the next two tests pass by checking no words at all.
    assert {"ADULT", "LOCK", "LOG_OUT", "TIME_LEFT"} <= set(terms)

    for name, value in terms.items():
        assert value.strip(), f"{name} is empty"


def test_the_vocabulary_says_adult_and_never_parent():
    # D8: mothers, fathers, grandparents and teachers all use the same machine.
    for name, value in shared_terms().items():
        assert "parent" not in value.lower(), f"{name} says 'parent'"


def test_the_vocabulary_says_password_and_never_pin():
    # D5: it is free-form text, and calling it a PIN would tell an adult to
    # choose digits.
    for name, value in shared_terms().items():
        assert " pin" not in f" {value.lower()}", f"{name} says 'PIN'"


def test_translations_for_one_language_at_run_time(compiled_catalogues, monkeypatch):
    # The sign-in screen switches language when a child is tapped, whatever
    # language the program itself started in.
    monkeypatch.setenv("KIDUX_LOCALE_ROOT", str(compiled_catalogues))
    monkeypatch.setenv("LANGUAGE", "en")
    importlib.reload(i18n)

    assert i18n.translations("es_ES.UTF-8").gettext(vocabulary.ADULT) == "Adulto"
    assert i18n.translations("en_US.UTF-8").gettext(vocabulary.ADULT) == "Adult"
    assert i18n._(vocabulary.ADULT) == "Adult"


def test_translations_for_an_unknown_language_gives_english(compiled_catalogues, monkeypatch):
    monkeypatch.setenv("KIDUX_LOCALE_ROOT", str(compiled_catalogues))

    assert i18n.translations("xx_YY.UTF-8").gettext(vocabulary.ADULT) == "Adult"
    assert i18n.translations("").gettext(vocabulary.ADULT) == "Adult"
