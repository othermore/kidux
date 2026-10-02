"""Tux Typing as the launcher and the panel will find it: its manifest read
by the one reader (D34), its words complete, and its starter giving it the
child's language and a home of the module's own."""

import shutil
import subprocess
from pathlib import Path

from kidux import modules

PACKAGE = Path(__file__).resolve().parents[1]


def test_the_manifest_reads_as_the_launcher_reads_it(tmp_path):
    (tmp_path / "tuxtype").mkdir()
    for name in ("module.toml", "icon.svg"):
        shutil.copy(PACKAGE / name, tmp_path / "tuxtype" / name)

    tuxtype = modules.read("tuxtype", root=tmp_path)

    assert tuxtype is not None
    assert tuxtype.name == "Tux Typing"
    assert tuxtype.launch == {"exec": "/usr/libexec/kidux-module-tuxtype"}
    assert tuxtype.i18n_domain == "kidux-module-tuxtype"
    assert (tuxtype.min_age, tuxtype.max_age, tuxtype.memory_max) == (6, 12, "1G")
    assert tuxtype.recommended_before == ("gcompris",)
    assert tuxtype.icon == str(tmp_path / "tuxtype" / "icon.svg")


def started(tmp_path, **environment) -> str:
    """What the starter runs: its HOME, its SDL video driver and Tux
    Typing's arguments, printed by a stand-in instead of Tux Typing itself,
    in a session that asks SDL for Wayland."""
    script = tmp_path / "kidux-module-tuxtype"
    script.write_text((PACKAGE / "bin" / "kidux-module-tuxtype").read_text()
                      .replace("exec /usr/games/tuxtype",
                               'exec echo "$HOME" "${SDL_VIDEODRIVER-unset}"'))
    return subprocess.run(["sh", str(script)], check=True, capture_output=True, text=True,
                          env={"HOME": str(tmp_path / "home"), "PATH": "/usr/bin:/bin",
                               "SDL_VIDEODRIVER": "wayland",
                               **environment}).stdout.strip()


def test_a_spanish_speaking_child_gets_the_spanish_words(tmp_path):
    data = tmp_path / "data"
    assert started(tmp_path, LANG="es_ES.UTF-8", XDG_DATA_HOME=str(data)) \
        == f"{data} unset --window --theme espanol"
    assert data.is_dir()


def test_an_english_speaking_child_gets_tux_typing_s_own(tmp_path):
    data = tmp_path / "data"
    assert started(tmp_path, LANG="en_US.UTF-8", XDG_DATA_HOME=str(data)) \
        == f"{data} unset --window"


def test_the_manifests_version_is_the_packages():
    changelog = (PACKAGE / "debian" / "changelog").read_text().split("\n", 1)[0]
    version = changelog.split("(", 1)[1].split(")", 1)[0]

    assert f'version = "{version}"' in (PACKAGE / "module.toml").read_text()


def test_the_catalogue_is_complete_and_holds_the_manifests_words():
    catalogue = PACKAGE / "po" / "es.po"
    untranslated = subprocess.run(
        ["msgattrib", "--untranslated", "--only-fuzzy", "--no-obsolete", str(catalogue)],
        capture_output=True, text=True, check=True).stdout
    text = catalogue.read_text()

    assert [line for line in untranslated.splitlines() if line.startswith('msgid "')
            and line != 'msgid ""'] == []
    for words in ("Tux Typing", "Learn to type: catch the falling letters and words"):
        assert words in text
