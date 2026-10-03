"""Wikipedia as the launcher and the panel will find it: a door to the
encyclopedia in the child's language (D87), its manifest read by the one
reader (D34), its words complete."""

import shutil
import subprocess
from pathlib import Path

from kidux import modules

PACKAGE = Path(__file__).resolve().parents[1]


def test_the_manifest_reads_as_a_door_to_the_encyclopedia(tmp_path):
    (tmp_path / "wikipedia").mkdir()
    for name in ("module.toml", "icon.svg"):
        shutil.copy(PACKAGE / name, tmp_path / "wikipedia" / name)

    wiki = modules.read("wikipedia", root=tmp_path)

    assert wiki is not None
    assert wiki.launch == {"web": "https://{lang}.wikipedia.org/"}
    assert {"wikipedia.org", "wikimedia.org", "wiktionary.org"} <= set(wiki.hosts)
    assert wiki.app_ids == ("chrome-*.wikipedia.org__*",)
    assert modules.claims(wiki, "chrome-es.wikipedia.org__-Default")
    assert (wiki.min_age, wiki.max_age, wiki.memory_max) == (8, 0, "2G")


def test_the_manifests_version_is_the_packages():
    changelog = (PACKAGE / "debian" / "changelog").read_text().split("\n", 1)[0]
    version = changelog.split("(", 1)[1].split(")", 1)[0]

    assert f'version = "{version}"' in (PACKAGE / "module.toml").read_text()


def test_the_catalogue_is_complete():
    untranslated = subprocess.run(
        ["msgattrib", "--untranslated", "--only-fuzzy", "--no-obsolete",
         str(PACKAGE / "po" / "es.po")], capture_output=True, text=True, check=True).stdout
    assert [line for line in untranslated.splitlines() if line.startswith('msgid "')
            and line != 'msgid ""'] == []
