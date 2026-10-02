"""TurboWarp as the launcher and the panel will find it: its manifest read by
the one reader (D34), its words complete, and the editor built from the
commit upstream.toml names (D68)."""

import shutil
import subprocess
import tomllib
from pathlib import Path

from kidux import modules

PACKAGE = Path(__file__).resolve().parents[1]


def test_the_manifest_reads_as_the_launcher_reads_it(tmp_path):
    (tmp_path / "turbowarp").mkdir()
    for name in ("module.toml", "icon.svg"):
        shutil.copy(PACKAGE / name, tmp_path / "turbowarp" / name)

    turbowarp = modules.read("turbowarp", root=tmp_path)

    assert turbowarp is not None
    assert turbowarp.name == "TurboWarp"
    assert turbowarp.launch == {"webapp": "turbowarp"}
    assert turbowarp.i18n_domain == "kidux-module-turbowarp"
    assert (turbowarp.min_age, turbowarp.max_age, turbowarp.memory_max) == (8, 16, "3G")


def test_the_manifests_version_is_the_packages_and_starts_with_the_editor_s():
    changelog = (PACKAGE / "debian" / "changelog").read_text().split("\n", 1)[0]
    version = changelog.split("(", 1)[1].split(")", 1)[0]
    with (PACKAGE / "upstream.toml").open("rb") as file:
        upstream = tomllib.load(file)["upstream"]

    assert f'version = "{version}"' in (PACKAGE / "module.toml").read_text()
    assert version.startswith(upstream["version"])


def test_the_built_editor_is_there_when_the_package_is_built():
    # The build stages the tarball into upstream/ (ci/build-package.sh);
    # a checkout of the repository has none, and nothing to check.
    site = PACKAGE / "upstream"
    if site.is_dir():
        assert (site / "index.html").is_file()
        assert (site / "LICENSE").is_file()
        assert not list(site.rglob("*.map"))


def test_the_catalogue_is_complete_and_holds_the_manifests_words():
    catalogue = PACKAGE / "po" / "es.po"
    untranslated = subprocess.run(
        ["msgattrib", "--untranslated", "--only-fuzzy", "--no-obsolete", str(catalogue)],
        capture_output=True, text=True, check=True).stdout
    text = catalogue.read_text()

    assert [line for line in untranslated.splitlines() if line.startswith('msgid "')
            and line != 'msgid ""'] == []
    for words in ("TurboWarp", "Scratch, made faster: the same blocks and the same projects"):
        assert words in text
