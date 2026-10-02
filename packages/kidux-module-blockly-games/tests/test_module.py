"""Blockly Games as the launcher and the panel will find it: its manifest read by
the one reader (D34), its words complete, and the editor built from the
commit upstream.toml names (D68)."""

import shutil
import subprocess
import tomllib
from pathlib import Path

from kidux import modules

PACKAGE = Path(__file__).resolve().parents[1]


def test_the_manifest_reads_as_the_launcher_reads_it(tmp_path):
    (tmp_path / "blockly-games").mkdir()
    for name in ("module.toml", "icon.svg"):
        shutil.copy(PACKAGE / name, tmp_path / "blockly-games" / name)

    games = modules.read("blockly-games", root=tmp_path)

    assert games is not None
    assert games.name == "Blockly Games"
    assert games.launch == {"webapp": "blockly-games"}
    assert games.i18n_domain == "kidux-module-blockly-games"
    assert (games.min_age, games.max_age, games.memory_max) == (6, 12, "2G")


def test_the_manifests_version_is_the_packages_and_starts_with_the_editor_s():
    changelog = (PACKAGE / "debian" / "changelog").read_text().split("\n", 1)[0]
    version = changelog.split("(", 1)[1].split(")", 1)[0]
    with (PACKAGE / "upstream.toml").open("rb") as file:
        upstream = tomllib.load(file)["upstream"]

    assert f'version = "{version}"' in (PACKAGE / "module.toml").read_text()
    assert version.startswith(upstream["version"])


def test_the_built_games_are_there_when_the_package_is_built():
    # The build stages the tarball into upstream/ (ci/build-package.sh);
    # a checkout of the repository has none, and nothing to check.
    site = PACKAGE / "upstream"
    if site.is_dir():
        assert (site / "index.html").is_file()
        assert (site / "LICENSE").is_file()
        assert (site / "third-party" / "soundfonts" / "README.txt").is_file()
        assert (site / "maze" / "generated" / "msg" / "es.js").is_file()


def test_the_catalogue_is_complete_and_holds_the_manifests_words():
    catalogue = PACKAGE / "po" / "es.po"
    untranslated = subprocess.run(
        ["msgattrib", "--untranslated", "--only-fuzzy", "--no-obsolete", str(catalogue)],
        capture_output=True, text=True, check=True).stdout
    text = catalogue.read_text()

    assert [line for line in untranslated.splitlines() if line.startswith('msgid "')
            and line != 'msgid ""'] == []
    for words in ("Blockly Games", "Puzzles with blocks: a maze, a bird, a turtle"):
        assert words in text
