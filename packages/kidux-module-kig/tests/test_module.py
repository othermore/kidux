"""Kig as the launcher and the panel will find it: its manifest read by the
one reader (D34), its words complete, and its starter giving the program
the module's restrictions on KDE's actions before it starts Kig."""

import shutil
import subprocess
from pathlib import Path

from kidux import lessons, modules

PACKAGE = Path(__file__).resolve().parents[1]
MODULE = "kig"
KDE = f"/usr/share/kidux/modules/{MODULE}/kde"


def test_the_manifest_reads_as_the_launcher_reads_it(tmp_path):
    (tmp_path / "kig").mkdir()
    for name in ("module.toml", "icon.svg"):
        shutil.copy(PACKAGE / name, tmp_path / "kig" / name)

    kig = modules.read("kig", root=tmp_path)

    assert kig is not None
    assert kig.name == "Kig"
    assert kig.launch == {"exec": "/usr/libexec/kidux-module-kig"}
    assert kig.i18n_domain == "kidux-module-kig"
    assert (kig.min_age, kig.max_age, kig.memory_max) == (10, 14, "1G")
    assert kig.recommended_before == ("gcompris",)
    assert kig.icon == str(tmp_path / "kig" / "icon.svg")


def started(tmp_path, **environment) -> str:
    """What the starter runs, printed by a stand-in instead of Kig itself."""
    script = tmp_path / "kidux-module-kig"
    script.write_text((PACKAGE / "bin" / "kidux-module-kig").read_text()
                      .replace("exec /usr/bin/kig", 'exec echo "$XDG_CONFIG_DIRS"'))
    return subprocess.run(["sh", str(script), *environment.pop("args", [])], check=True,
                          capture_output=True, text=True,
                          env={"HOME": str(tmp_path / "home"), "PATH": "/usr/bin:/bin",
                               **environment}).stdout.strip()


def test_the_starter_gives_the_program_the_modules_restrictions_first(tmp_path):
    assert started(tmp_path, args=["a.kig"]) == f"{KDE}:/etc/xdg a.kig"
    assert started(tmp_path, XDG_CONFIG_DIRS="/x:/y") == f"{KDE}:/x:/y"


def test_the_restrictions_switch_off_what_a_child_has_no_business_in():
    lines = (PACKAGE / "kde" / "kdeglobals").read_text().splitlines()

    assert "[KDE Action Restrictions][$i]" in lines
    for key in ("ghns", "shell_access", "action/help_contents", "action/help_report_bug",
                "action/help_donate", "action/switch_application_language",
                "action/fullscreen"):
        assert f"{key}=false" in lines, key
    assert not [line for line in lines if "=true" in line]


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
    for words in ("Kig", "Geometry you can move: points, lines, circles and shapes"):
        assert words in text


def test_the_guide_has_six_lessons_in_both_languages_with_their_missions_and_pictures(tmp_path):
    shutil.copytree(PACKAGE, tmp_path / "kig", ignore=shutil.ignore_patterns("debian", "tests"))
    kig = modules.read("kig", root=tmp_path)

    assert kig.guide == str(tmp_path / "kig" / "content")
    english = lessons.read(kig.guide, "en_US.UTF-8")
    spanish = lessons.read(kig.guide, "es_ES.UTF-8")
    assert [lesson.number for lesson in english] == [1, 2, 3, 4, 5, 6]
    assert [lesson.title for lesson in spanish][:2] == ["Puntos y rectas", "El medio de un segmento"]
    assert all(english[i].title != spanish[i].title for i in range(6))
    for found in (english, spanish):
        kinds = [{block[0] for block in lesson.blocks} for lesson in found]
        assert all("image" in k for k in kinds[:6]), kinds
        assert ["mission" in k for k in kinds] == [False, True, True, True, True, False]
    assert [Path(m).name for m in lessons.missions(spanish)] == [
        "medio.kig", "dos-circunferencias.kig", "paralelas.kig", "triangulo.kig"]
    for mission in lessons.missions(english) + lessons.missions(spanish):
        assert "<KigDocument" in Path(mission).read_text()
