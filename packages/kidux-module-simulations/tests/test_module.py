"""Simulations as the launcher and the panel will find it: its manifest read
by the one reader (D34), its list of PhET's simulations whole, its page
built with every group and title in each language, and its words
complete."""

import json
import re
import shutil
import subprocess
import tomllib
from pathlib import Path

from kidux import modules

PACKAGE = Path(__file__).resolve().parents[1]
LISTED = tomllib.loads((PACKAGE / "sims.toml").read_text())


def test_the_manifest_reads_as_the_launcher_reads_it(tmp_path):
    (tmp_path / "simulations").mkdir()
    for name in ("module.toml", "icon.svg"):
        shutil.copy(PACKAGE / name, tmp_path / "simulations" / name)

    simulations = modules.read("simulations", root=tmp_path)

    assert simulations is not None
    assert simulations.name == "Simulations"
    assert simulations.launch == {"webapp": "simulations"}
    assert simulations.hosts == ()
    assert (simulations.min_age, simulations.max_age) == (6, 14)


def test_every_simulation_is_in_one_group_with_its_titles_its_version_and_its_sum():
    grouped = [sim for group in LISTED["groups"] for sim in group["sims"]]

    assert sorted(grouped) == sorted(LISTED["sims"])
    assert len(grouped) == len(set(grouped))
    for sim, entry in LISTED["sims"].items():
        assert set(entry["title"]) >= {"en", "es"}, sim
        assert re.fullmatch(r"\d+\.\d+\.\d+", entry["version"]), sim
        assert re.fullmatch(r"[0-9a-f]{64}", entry["sha256"]), sim
    for group in LISTED["groups"]:
        assert re.fullmatch(r"\d+-\d+", group["ages"]), group["id"]
    assert LISTED["cutoff"] == "2026-03-29"
    assert "licensed under CC BY 4.0" in LISTED["attribution"]


def built(tmp_path) -> dict:
    """The page, built as debian/rules builds it, and the data written into it."""
    locale = tmp_path / "locale"
    for po in (PACKAGE / "po").glob("*.po"):
        target = locale / po.stem / "LC_MESSAGES"
        target.mkdir(parents=True)
        subprocess.run(["msgfmt", "--check", "-o",
                        str(target / "kidux-module-simulations.mo"), str(po)], check=True)
    page = tmp_path / "index.html"
    subprocess.run(["python3", "-B", str(PACKAGE / "webapp" / "page.py"), str(locale),
                    str(PACKAGE / "sims.toml"), str(PACKAGE / "webapp" / "index.html.in"),
                    str(page)], check=True)
    text = page.read_text()
    assert "@PAGES@" not in text
    return json.loads(re.search(r"const PAGES = (\{.*?\});\n", text).group(1)
                      .replace("<\\/", "</"))


def test_the_page_lists_every_group_and_title_in_each_language(tmp_path):
    pages = built(tmp_path)

    assert set(pages) == {"en", "es"}
    assert [g["name"] for g in pages["es"]["groups"]][:2] == ["Números y formas", "Más números"]
    assert pages["es"]["groups"][0]["ages"] == "De 6 a 10 años"
    assert pages["en"]["groups"][0]["ages"] == "Ages 6 to 10"
    assert pages["es"]["groups"][0]["sims"][0] == {"id": "make-a-ten", "title": "Haz un Diez"}
    assert pages["en"]["words"]["back"] == "Simulations"
    assert pages["es"]["words"]["title"] == "Simulaciones"
    assert "Universidad de Colorado Boulder" in pages["es"]["words"]["attribution"]
    for lang in pages:
        assert sum(len(g["sims"]) for g in pages[lang]["groups"]) == len(LISTED["sims"])


def test_the_page_opens_a_simulation_in_the_child_s_language_from_its_own_file():
    template = (PACKAGE / "webapp" / "index.html.in").read_text()

    assert '"sims/" + sim.id + "_all.html?locale="' in template
    assert "http" not in template.split("<script>", 1)[1]


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
