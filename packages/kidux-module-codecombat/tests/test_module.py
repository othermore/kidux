"""CodeCombat as the launcher and the panel will find it: a door to the
CodeCombat website (D86), its manifest read by the one reader (D34), its
words complete."""

import shutil
import subprocess
from pathlib import Path

from kidux import modules

PACKAGE = Path(__file__).resolve().parents[1]


def test_the_manifest_reads_as_a_door_to_the_website(tmp_path):
    (tmp_path / "codecombat").mkdir()
    for name in ("module.toml", "icon.svg"):
        shutil.copy(PACKAGE / name, tmp_path / "codecombat" / name)

    combat = modules.read("codecombat", root=tmp_path)

    assert combat is not None
    assert combat.launch == {"web": "https://codecombat.com/"}
    assert "codecombat.com" in combat.hosts
    assert combat.app_ids == ("chrome-codecombat.com__*",)
    assert (combat.min_age, combat.max_age, combat.memory_max) == (9, 16, "3G")


def test_the_manifests_version_is_the_packages():
    changelog = (PACKAGE / "debian" / "changelog").read_text().split("\n", 1)[0]
    version = changelog.split("(", 1)[1].split(")", 1)[0]

    assert f'version = "{version}"' in (PACKAGE / "module.toml").read_text()


def test_its_words_say_it_is_not_connected_with_codecombat():
    manifest = (PACKAGE / "module.toml").read_text()
    spanish = (PACKAGE / "po" / "es.po").read_text()

    assert "Kidux is not connected with CodeCombat" in manifest
    assert "Kidux no tiene ninguna relación con CodeCombat" in spanish.replace('"\n"', "")


def test_the_catalogue_is_complete():
    untranslated = subprocess.run(
        ["msgattrib", "--untranslated", "--only-fuzzy", "--no-obsolete",
         str(PACKAGE / "po" / "es.po")], capture_output=True, text=True, check=True).stdout
    assert [line for line in untranslated.splitlines() if line.startswith('msgid "')
            and line != 'msgid ""'] == []
