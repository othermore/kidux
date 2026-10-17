"""Kalzium as the launcher and the panel will find it: its manifest read by the
one reader (D34), its words complete, and its starter switching off KDE's
actions a child has no business in, once, before it starts Kalzium."""

import shutil
import subprocess
from pathlib import Path

from kidux import modules

PACKAGE = Path(__file__).resolve().parents[1]
RESTRICTIONS = ("[KDE Action Restrictions][$i]\nghns=false\nshell_access=false\n"
                "action/help_report_bug=false\naction/help_donate=false\n")


def test_the_manifest_reads_as_the_launcher_reads_it(tmp_path):
    (tmp_path / "kalzium").mkdir()
    for name in ("module.toml", "icon.svg"):
        shutil.copy(PACKAGE / name, tmp_path / "kalzium" / name)

    kalzium = modules.read("kalzium", root=tmp_path)

    assert kalzium is not None
    assert kalzium.name == "Kalzium"
    assert kalzium.launch == {"exec": "/usr/libexec/kidux-module-kalzium"}
    assert kalzium.i18n_domain == "kidux-module-kalzium"
    assert (kalzium.min_age, kalzium.max_age, kalzium.memory_max) == (10, 16, "1G")
    assert kalzium.recommended_before == ()
    assert kalzium.icon == str(tmp_path / "kalzium" / "icon.svg")


def started(tmp_path, **environment) -> str:
    """What the starter runs, printed by a stand-in instead of Kalzium itself."""
    script = tmp_path / "kidux-module-kalzium"
    script.write_text((PACKAGE / "bin" / "kidux-module-kalzium").read_text()
                      .replace("exec /usr/bin/kalzium", "exec echo kalzium"))
    return subprocess.run(["sh", str(script), *environment.pop("args", [])], check=True,
                          capture_output=True, text=True,
                          env={"HOME": str(tmp_path / "home"), "PATH": "/usr/bin:/bin",
                               **environment}).stdout.strip()


def test_the_first_start_switches_off_what_a_child_has_no_business_in(tmp_path):
    config = tmp_path / "config"

    assert started(tmp_path, XDG_CONFIG_HOME=str(config), args=["a.cml"]) == "kalzium a.cml"
    assert (config / "kdeglobals").read_text() == RESTRICTIONS


def test_a_kdeglobals_already_there_is_never_touched(tmp_path):
    config = tmp_path / "config"
    config.mkdir()
    (config / "kdeglobals").write_text("[General]\nmine=yes\n")

    started(tmp_path, XDG_CONFIG_HOME=str(config))

    assert (config / "kdeglobals").read_text() == "[General]\nmine=yes\n"


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
    for words in ("Kalzium", "The periodic table: every element, what it is like"):
        assert words in text
