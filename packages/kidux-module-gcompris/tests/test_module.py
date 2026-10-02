"""GCompris as the launcher and the panel will find it: its manifest read
by the one reader (D34), its words complete."""

import shutil
import subprocess
from pathlib import Path

from kidux import modules

PACKAGE = Path(__file__).resolve().parents[1]


def test_the_manifest_reads_as_the_launcher_reads_it(tmp_path):
    (tmp_path / "gcompris").mkdir()
    for name in ("module.toml", "icon.svg"):
        shutil.copy(PACKAGE / name, tmp_path / "gcompris" / name)

    gcompris = modules.read("gcompris", root=tmp_path)

    assert gcompris is not None
    assert gcompris.name == "GCompris"
    assert gcompris.launch == {"exec": "/usr/libexec/kidux-module-gcompris"}
    assert gcompris.i18n_domain == "kidux-module-gcompris"
    assert (gcompris.min_age, gcompris.max_age, gcompris.memory_max) == (2, 10, "3G")
    assert gcompris.icon == str(tmp_path / "gcompris" / "icon.svg")


def starter(tmp_path) -> Path:
    """The program that starts GCompris, starting `true` instead."""
    script = tmp_path / "kidux-module-gcompris"
    script.write_text((PACKAGE / "bin" / "kidux-module-gcompris").read_text()
                      .replace("exec /usr/games/gcompris-qt", "exec true"))
    return script


def test_the_first_start_has_its_questions_answered(tmp_path):
    config = tmp_path / "config"
    subprocess.run(["sh", str(starter(tmp_path))], check=True,
                   env={"XDG_CONFIG_HOME": str(config), "HOME": str(tmp_path),
                        "PATH": "/usr/bin:/bin"})

    written = (config / "gcompris" / "gcompris-qt.conf").read_text()
    assert "enableAutomaticDownloads=true" in written
    assert "exeCount=1" in written
    assert "lastGCVersionRan=" in written


def test_a_childs_own_configuration_is_never_touched(tmp_path):
    conf = tmp_path / "config" / "gcompris" / "gcompris-qt.conf"
    conf.parent.mkdir(parents=True)
    conf.write_text("[%General]\nenableAutomaticDownloads=false\n")

    subprocess.run(["sh", str(starter(tmp_path))], check=True,
                   env={"XDG_CONFIG_HOME": str(tmp_path / "config"), "HOME": str(tmp_path),
                        "PATH": "/usr/bin:/bin"})

    assert conf.read_text() == "[%General]\nenableAutomaticDownloads=false\n"


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
    for words in ("GCompris", "Over a hundred activities: reading, counting, colours, the "):
        assert words in text
