"""BASIC as the launcher and the panel will find it: its manifest read by
the one reader (D34), its version, and its words complete."""

import shutil
import subprocess
import tomllib
from pathlib import Path

from kidux import modules

PACKAGE = Path(__file__).resolve().parents[1]


def test_the_manifest_reads_as_the_launcher_reads_it(tmp_path):
    (tmp_path / "basic").mkdir()
    for name in ("module.toml", "icon.svg"):
        shutil.copy(PACKAGE / name, tmp_path / "basic" / name)

    basic = modules.read("basic", root=tmp_path)

    assert basic is not None
    assert basic.launch == {"webapp": "basic"}
    assert basic.i18n_domain == "kidux-module-basic"
    assert (basic.min_age, basic.max_age, basic.memory_max) == (8, 14, "2G")
    assert basic.recommended_before == ("scratch",)


def test_the_manifests_version_is_the_packages_and_starts_with_wwwbasic_s():
    changelog = (PACKAGE / "debian" / "changelog").read_text().split("\n", 1)[0]
    version = changelog.split("(", 1)[1].split(")", 1)[0]
    with (PACKAGE / "upstream.toml").open("rb") as file:
        upstream = tomllib.load(file)["upstream"]

    assert f'version = "{version}"' in (PACKAGE / "module.toml").read_text()
    assert version.startswith(upstream["version"])


def test_the_catalogue_is_complete():
    untranslated = subprocess.run(
        ["msgattrib", "--untranslated", "--only-fuzzy", "--no-obsolete",
         str(PACKAGE / "po" / "es.po")], capture_output=True, text=True, check=True).stdout
    assert [line for line in untranslated.splitlines() if line.startswith('msgid "')
            and line != 'msgid ""'] == []
