"""ScratchJr as the launcher and the panel will find it: its manifest read by
the one reader (D34), its words complete, and the app built from the
commit upstream.toml names (D68)."""

import shutil
import subprocess
import tomllib
from pathlib import Path

from kidux import modules

PACKAGE = Path(__file__).resolve().parents[1]


def test_the_manifest_reads_as_the_launcher_reads_it(tmp_path):
    (tmp_path / "scratchjr").mkdir()
    for name in ("module.toml", "icon.svg"):
        shutil.copy(PACKAGE / name, tmp_path / "scratchjr" / name)

    scratchjr = modules.read("scratchjr", root=tmp_path)

    assert scratchjr is not None
    assert scratchjr.name == "ScratchJr"
    assert scratchjr.launch == {"exec": "/usr/libexec/kidux-module-scratchjr"}
    assert scratchjr.i18n_domain == "kidux-module-scratchjr"
    assert (scratchjr.min_age, scratchjr.max_age, scratchjr.memory_max) == (5, 7, "2G")


def test_the_manifests_version_is_the_packages_and_starts_with_the_app_s():
    changelog = (PACKAGE / "debian" / "changelog").read_text().split("\n", 1)[0]
    version = changelog.split("(", 1)[1].split(")", 1)[0]
    with (PACKAGE / "upstream.toml").open("rb") as file:
        upstream = tomllib.load(file)["upstream"]

    assert f'version = "{version}"' in (PACKAGE / "module.toml").read_text()
    assert version.startswith(upstream["version"])


def test_the_built_app_is_there_when_the_package_is_built():
    # The build stages the tarball into upstream/ (ci/build-package.sh);
    # a checkout of the repository has none, and nothing to check.
    site = PACKAGE / "upstream"
    if site.is_dir():
        assert (site / "ScratchJr").is_file()
        assert (site / "LICENSE.scratchjr").is_file()


def started(tmp_path, *args, flags=None, **environment) -> str:
    """The command the starter runs, printed by a stand-in for ScratchJr,
    with `flags` as the machine's Chromium options' file."""
    script = tmp_path / "kidux-module-scratchjr"
    script.write_text((PACKAGE / "bin" / "kidux-module-scratchjr").read_text()
                      .replace('APP=/usr/lib/kidux-module-scratchjr/ScratchJr', 'APP=echo'))
    options = tmp_path / "chromium-flags"
    if flags is None:
        options.unlink(missing_ok=True)
    else:
        options.write_text(flags)
    return subprocess.run(["sh", str(script), *args], check=True, capture_output=True,
                          text=True,
                          env={"PATH": "/usr/bin:/bin", "KIDUX_CHROMIUM_FLAGS": str(options),
                               **environment}).stdout.strip()


def test_scratchjr_is_told_the_childs_language(tmp_path):
    assert started(tmp_path, LANG="es_ES.UTF-8") == "--lang=es-ES"
    assert started(tmp_path, LANG="en_US.UTF-8", LC_MESSAGES="pt_BR.UTF-8") == "--lang=pt-BR"
    assert started(tmp_path, LANG="C.UTF-8") == ""


def test_it_draws_with_the_machines_chromium_options(tmp_path):
    # D52: the options the adult panel writes, one a line, a line that is
    # not an option left out, before what the starter itself was given.
    flags = "--disable-gpu-compositing\n  --use-gl=angle  \nnot an option\n\n--last"
    assert started(tmp_path, "--given", flags=flags, LANG="es_ES.UTF-8") == \
        "--lang=es-ES --disable-gpu-compositing --use-gl=angle --last --given"
    assert started(tmp_path, "--given", LANG="C") == "--given"


def test_the_catalogue_is_complete_and_holds_the_manifests_words():
    catalogue = PACKAGE / "po" / "es.po"
    untranslated = subprocess.run(
        ["msgattrib", "--untranslated", "--only-fuzzy", "--no-obsolete", str(catalogue)],
        capture_output=True, text=True, check=True).stdout
    text = catalogue.read_text()

    assert [line for line in untranslated.splitlines() if line.startswith('msgid "')
            and line != 'msgid ""'] == []
    for words in ("ScratchJr", "Stories and games with blocks, without a word to read"):
        assert words in text
