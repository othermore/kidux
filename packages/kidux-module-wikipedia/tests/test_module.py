"""Wikipedia as the launcher and the panel will find it: a door to the
encyclopedia in the child's language (D87), its manifest read by the one
reader (D34), its words complete."""

import json
import shutil
import subprocess
import sys
from pathlib import Path

from kidux import modules

PACKAGE = Path(__file__).resolve().parents[1]


def built_bar(tmp_path) -> str:
    """The bar as the package builds it, every catalogue compiled first."""
    locale = tmp_path / "locale"
    for po in (PACKAGE / "po").glob("*.po"):
        mo = locale / po.stem / "LC_MESSAGES" / "kidux-module-wikipedia.mo"
        mo.parent.mkdir(parents=True)
        subprocess.run(["msgfmt", "--check", "-o", str(mo), str(po)], check=True)
    subprocess.run([sys.executable, str(PACKAGE / "page" / "bar.py"), str(locale),
                    str(PACKAGE / "po"), str(PACKAGE / "page" / "bar.js.in"),
                    str(tmp_path / "bar.js")], check=True)
    return (tmp_path / "bar.js").read_text()


def test_the_manifest_reads_as_a_door_to_the_encyclopedia(tmp_path):
    (tmp_path / "wikipedia").mkdir()
    for name in ("module.toml", "icon.svg"):
        shutil.copy(PACKAGE / name, tmp_path / "wikipedia" / name)
    (tmp_path / "wikipedia" / "bar.js").write_text(built_bar(tmp_path))

    wiki = modules.read("wikipedia", root=tmp_path)

    assert wiki is not None
    assert wiki.launch == {"web": "https://{lang}.wikipedia.org/"}
    assert {"wikipedia.org", "wikimedia.org", "wiktionary.org"} <= set(wiki.hosts)
    assert wiki.app_ids == ("chrome-*.wikipedia.org__*",)
    assert modules.claims(wiki, "chrome-es.wikipedia.org__-Default")
    assert (wiki.min_age, wiki.max_age, wiki.memory_max) == (8, 0, "2G")
    assert wiki.page_script == str(tmp_path / "wikipedia" / "bar.js")


def test_the_bar_says_back_and_forward_in_every_language(tmp_path):
    bar = built_bar(tmp_path)

    assert "@WORDS@" not in bar
    words = json.loads(bar.split("const WORDS = ", 1)[1].split(";\n", 1)[0])
    assert words["en"] == {"back": "Back", "forward": "Forward", "bar": "Go back and forward"}
    assert words["es"]["back"] == "Atrás" and words["es"]["forward"] == "Adelante"
    assert set(words) == {"en", *(po.stem for po in (PACKAGE / "po").glob("*.po"))}
    assert "history.back()" in bar and "navigation.canGoBack" in bar


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
