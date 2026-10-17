"""Photography as the launcher and the panel will find it: its manifest read
by the one reader (D34), its version, and its words complete."""

import shutil
import subprocess
from pathlib import Path

from kidux import modules

PACKAGE = Path(__file__).resolve().parents[1]


def test_the_manifest_reads_as_the_launcher_reads_it(tmp_path):
    (tmp_path / "photography").mkdir()
    for name in ("module.toml", "icon.svg"):
        shutil.copy(PACKAGE / name, tmp_path / "photography" / name)

    photography = modules.read("photography", root=tmp_path)

    assert photography is not None
    assert photography.launch == {"webapp": "photography"}
    assert photography.i18n_domain == "kidux-module-photography"
    assert (photography.min_age, photography.max_age) == (8, 12)
    assert photography.hosts == ()
    assert photography.icon.endswith("icon.svg")


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
