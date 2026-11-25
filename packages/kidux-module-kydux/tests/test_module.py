"""Kydux as the launcher, the panel and Chromium's policy will find it: a door
to the Kidux family's game (D85, D120), its manifest read by the one reader
(D34), with the game's hosts and its counting's and never kidux.org, and its
words complete."""

import shutil
import subprocess
from pathlib import Path

from kidux import modules

PACKAGE = Path(__file__).resolve().parents[1]
#: The game's own host, and those its counting of visits uses.
HOSTS = {"kydux.kidux.org", "kidux.goatcounter.com", "googletagmanager.com",
         "google-analytics.com", "analytics.google.com"}


def read(tmp_path) -> modules.Module:
    (tmp_path / "kydux").mkdir()
    for name in ("module.toml", "icon.svg"):
        shutil.copy(PACKAGE / name, tmp_path / "kydux" / name)
    found = modules.read("kydux", root=tmp_path)
    assert found is not None
    return found


def test_the_manifest_reads_as_a_door_to_the_game(tmp_path):
    kydux = read(tmp_path)

    assert kydux.name == "Kydux"
    assert kydux.launch == {"web": "https://kydux.kidux.org/?from=kidux"}
    assert kydux.app_ids == ("chrome-kydux.kidux.org__*",)
    assert modules.claims(kydux, "chrome-kydux.kidux.org__-Default")
    assert (kydux.min_age, kydux.max_age, kydux.memory_max) == (8, 0, "2G")
    assert kydux.recommended_before == ()
    assert kydux.settings == () and kydux.sign_in is None and kydux.page_script == ""


def test_its_hosts_are_the_game_s_and_its_counting_s_and_never_kidux_org(tmp_path):
    hosts = set(read(tmp_path).hosts)

    assert hosts == HOSTS
    # A host stands for every name under it (D85): none may be kidux.org, or
    # a name above it, which would open the site, its archive and its
    # installer's download to the child.
    for kidux_s in ("kidux.org", "apt.kidux.org", "iso.kidux.org", "www.kidux.org"):
        assert not any(kidux_s == host or kidux_s.endswith("." + host) for host in hosts), kidux_s


def test_its_words_say_what_a_family_needs():
    # The price, the account and the internet, in both languages (D125); that
    # it is played without Kidux too is on its page in the guide (D120,
    # tests/project/docs.sh).
    manifest = (PACKAGE / "module.toml").read_text()
    spanish = (PACKAGE / "po" / "es.po").read_text().replace('"\n"', "")

    assert "Free, in English and Spanish, with no account. Requires internet." in manifest
    assert "Gratis, en español y en inglés, sin cuenta. Requiere conexión a internet." in spanish


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
