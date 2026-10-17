"""Step as the launcher and the panel will find it: its manifest read by the
one reader (D34), its words complete, and its starter switching off KDE's
actions a child has no business in, once, before it starts Step."""

import shutil
import subprocess
from pathlib import Path

from kidux import modules

PACKAGE = Path(__file__).resolve().parents[1]
RESTRICTIONS = ("[KDE Action Restrictions][$i]\nghns=false\nshell_access=false\n"
                "action/help_report_bug=false\naction/help_donate=false\n")


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
                      .replace("exec /usr/bin/step", "exec echo step"))
    return subprocess.run(["sh", str(script), *environment.pop("args", [])], check=True,
                          capture_output=True, text=True,
                          env={"HOME": str(tmp_path / "home"), "PATH": "/usr/bin:/bin",
                               **environment}).stdout.strip()


def test_the_first_start_switches_off_what_a_child_has_no_business_in(tmp_path):
    config = tmp_path / "config"

    assert started(tmp_path, XDG_CONFIG_HOME=str(config), args=["a.step"]) == "step a.step"
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
    for words in ("Step", "A physics playground: put springs, weights and forces"):
        assert words in text
