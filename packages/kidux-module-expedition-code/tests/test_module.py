"""Expedition Code as the launcher, the panel and Chromium's policy will find
it: a door to the Expedition Code website (D85, D121), its manifest read by
the one reader (D34), with the site's own hosts and none of the sites it
embeds or counts with, and its words complete."""

import shutil
import subprocess
from pathlib import Path

from kidux import modules

PACKAGE = Path(__file__).resolve().parents[1]
#: Its pages, its backend and its fonts.
HOSTS = {"expeditioncode.com", "spotted-shepherd-639.convex.cloud",
         "fonts.googleapis.com", "fonts.gstatic.com"}


def read(tmp_path) -> modules.Module:
    (tmp_path / "expedition-code").mkdir()
    for name in ("module.toml", "icon.svg"):
        shutil.copy(PACKAGE / name, tmp_path / "expedition-code" / name)
    found = modules.read("expedition-code", root=tmp_path)
    assert found is not None
    return found


def test_the_manifest_reads_as_a_door_to_the_website(tmp_path):
    expedition = read(tmp_path)

    assert expedition.name == "Expedition Code"
    assert expedition.launch == {"web": "https://www.expeditioncode.com/"}
    assert expedition.app_ids == ("chrome-www.expeditioncode.com__*",)
    assert modules.claims(expedition, "chrome-www.expeditioncode.com__-Default")
    assert (expedition.min_age, expedition.max_age, expedition.memory_max) == (9, 0, "2G")
    assert expedition.recommended_before == ("scratch",)
    assert expedition.settings == () and expedition.sign_in is None


def test_its_hosts_are_the_site_s_own_and_never_a_site_to_browse_or_its_counting(tmp_path):
    hosts = set(read(tmp_path).hosts)

    assert hosts == HOSTS
    # A host stands for every name under it (D85): YouTube, Google and
    # PostHog stay out whole, and Convex is named by the site's own backend,
    # never as the whole of Convex's cloud (D122).
    for closed in ("youtube.com", "google.com", "posthog.com"):
        assert not any(host == closed or host.endswith("." + closed) for host in hosts), closed
    assert "convex.cloud" not in hosts


def test_its_words_say_the_language_and_that_kidux_is_not_connected_with_it():
    manifest = (PACKAGE / "module.toml").read_text()
    spanish = (PACKAGE / "po" / "es.po").read_text().replace('"\n"', "")

    assert "In English only" in manifest and "Solo en inglés" in spanish
    assert "Kidux is not connected with Expedition Code" in manifest
    assert "Kidux no tiene ninguna relación con Expedition Code" in spanish


def test_it_brings_the_font_its_avatars_are_drawn_with():
    control = (PACKAGE / "debian" / "control").read_text()

    assert "fonts-noto-color-emoji," in control.split("Depends:", 2)[2].split("Description:", 1)[0]


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
