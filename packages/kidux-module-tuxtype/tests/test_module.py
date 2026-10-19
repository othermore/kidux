"""Tux Typing as the launcher and the panel will find it: its manifest read
by the one reader (D34), its words complete, and its starter giving it the
child's language and a home of the module's own."""

import shutil
import subprocess
import tomllib
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
                      .replace("exec /usr/games/kidux-tuxtype",
                               'exec echo "$HOME" "${SDL_VIDEODRIVER-unset}"'))
    return subprocess.run(["sh", str(script)], check=True, capture_output=True, text=True,
                          env={"HOME": str(tmp_path / "home"), "PATH": "/usr/bin:/bin",
                               "SDL_VIDEODRIVER": "wayland",
                               **environment}).stdout.strip()


def themes(tmp_path) -> str:
    """A themes folder with Kidux's two themes, as the package installs them."""
    folder = tmp_path / "themes"
    for language in ("es", "en"):
        (folder / f"kidux-{language}").mkdir(parents=True, exist_ok=True)
    return str(folder)


def test_a_spanish_speaking_child_gets_kidux_s_spanish_theme(tmp_path):
    data = tmp_path / "data"
    assert started(tmp_path, LANG="es_ES.UTF-8", XDG_DATA_HOME=str(data),
                   KIDUX_TUXTYPE_THEMES=themes(tmp_path)) \
        == f"{data} unset --window --theme kidux-es"
    assert data.is_dir()


def test_an_english_speaking_child_gets_kidux_s_english_theme(tmp_path):
    data = tmp_path / "data"
    assert started(tmp_path, LANG="en_GB.UTF-8", XDG_DATA_HOME=str(data),
                   KIDUX_TUXTYPE_THEMES=themes(tmp_path)) \
        == f"{data} unset --window --theme kidux-en"


def test_a_language_without_lessons_gets_english_s(tmp_path):
    assert started(tmp_path, LANG="de_DE.UTF-8", XDG_DATA_HOME=str(tmp_path / "data"),
                   KIDUX_TUXTYPE_THEMES=themes(tmp_path)).endswith("--theme kidux-en")
    assert started(tmp_path, LANG="C", XDG_DATA_HOME=str(tmp_path / "data"),
                   KIDUX_TUXTYPE_THEMES=themes(tmp_path)).endswith("--theme kidux-en")


def test_the_manifests_version_is_the_packages():
    changelog = (PACKAGE / "debian" / "changelog").read_text().split("\n", 1)[0]
    version = changelog.split("(", 1)[1].split(")", 1)[0]

    assert f'version = "{version}"' in (PACKAGE / "module.toml").read_text()


def test_the_catalogue_is_complete_and_holds_the_manifests_words():
    catalogue = PACKAGE / "po" / "es.po"
    untranslated = subprocess.run(
        ["msgattrib", "--untranslated", "--only-fuzzy", "--no-obsolete", str(catalogue)],
        capture_output=True, text=True, check=True).stdout

    assert [line for line in untranslated.splitlines() if line.startswith('msgid "')
            and line != 'msgid ""'] == []
    # The manifest's own name and description, each a msgid of the catalogue,
    # read whole whatever the catalogue's line wrapping.
    manifest = tomllib.loads((PACKAGE / "module.toml").read_text())
    flat = subprocess.run(["msgcat", "--no-wrap", str(catalogue)],
                          capture_output=True, text=True, check=True).stdout
    for words in (manifest["name"], manifest["description"]):
        escaped = words.replace("\\", "\\\\").replace('"', '\\"')
        assert f'msgid "{escaped}"' in flat
