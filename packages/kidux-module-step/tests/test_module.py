"""Step as the launcher and the panel will find it: its manifest read by the
one reader (D34), its words complete, and its starter giving the program
the module's restrictions on KDE's actions before it starts Step."""

import shutil
import subprocess
from pathlib import Path

from kidux import modules

PACKAGE = Path(__file__).resolve().parents[1]
MODULE = "step"
KDE = f"/usr/share/kidux/modules/{MODULE}/kde"


def test_the_manifest_reads_as_the_launcher_reads_it(tmp_path):
    (tmp_path / "step").mkdir()
    for name in ("module.toml", "icon.svg"):
        shutil.copy(PACKAGE / name, tmp_path / "step" / name)

    step = modules.read("step", root=tmp_path)

    assert step is not None
    assert step.name == "Step"
    assert step.launch == {"exec": "/usr/libexec/kidux-module-step"}
    assert step.i18n_domain == "kidux-module-step"
    assert (step.min_age, step.max_age, step.memory_max) == (10, 16, "2G")
    assert step.recommended_before == ("simulations",)
    assert step.icon == str(tmp_path / "step" / "icon.svg")


def started(tmp_path, **environment) -> str:
    """What the starter runs, printed by a stand-in instead of Step itself."""
    script = tmp_path / "kidux-module-step"
    script.write_text((PACKAGE / "bin" / "kidux-module-step").read_text()
                      .replace("exec /usr/bin/step", 'exec echo "$XDG_CONFIG_DIRS"'))
    return subprocess.run(["sh", str(script), *environment.pop("args", [])], check=True,
                          capture_output=True, text=True,
                          env={"HOME": str(tmp_path / "home"), "PATH": "/usr/bin:/bin",
                               **environment}).stdout.strip()


def test_the_starter_gives_the_program_the_modules_restrictions_first(tmp_path):
    assert started(tmp_path, args=["a.step"]) == f"{KDE}:/etc/xdg a.step"
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
    for words in ("Step", "A physics playground: put springs, weights and forces"):
        assert words in text
