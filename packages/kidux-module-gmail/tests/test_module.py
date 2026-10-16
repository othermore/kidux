"""Gmail as the launcher, the panel and Chromium's policy will find it: a door
to Gmail's website (D85), its manifest read by the one reader (D34), with
its hosts and its setting, and its words complete."""

import shutil
import subprocess
from pathlib import Path

from kidux import modules

PACKAGE = Path(__file__).resolve().parents[1]


def read(tmp_path) -> modules.Module:
    (tmp_path / "gmail").mkdir()
    for name in ("module.toml", "icon.svg"):
        shutil.copy(PACKAGE / name, tmp_path / "gmail" / name)
    found = modules.read("gmail", root=tmp_path)
    assert found is not None
    return found


def test_the_manifest_reads_as_a_door_to_gmail(tmp_path):
    gmail = read(tmp_path)

    assert gmail.name == "Gmail"
    assert gmail.launch["web"].startswith("https://accounts.google.com/ServiceLogin?service=mail&")
    assert "&Email={email}&hl={lang}" in gmail.launch["web"]
    assert gmail.app_ids == ("chrome-accounts.google.com__*",)
    assert modules.claims(gmail, "chrome-accounts.google.com__ServiceLogin-Default")
    assert (gmail.min_age, gmail.max_age, gmail.memory_max) == (8, 0, "3G")
    assert [(s.key, s.kind) for s in gmail.settings] == [("email", "text")]


def test_its_hosts_are_gmail_s_and_the_accounts_host_of_every_country(tmp_path):
    hosts = set(read(tmp_path).hosts)

    assert {"mail.google.com", "accounts.google.com", "ssl.gstatic.com",
            "mail-attachment.googleusercontent.com", "accounts.google.es",
            "accounts.google.co.uk", "accounts.google.com.mx"} <= hosts
    assert len([host for host in hosts if host.startswith("accounts.google.")]) == 187
    # Never Google whole, Search or the other services: only the names Gmail
    # was seen to need.
    for closed in ("google.com", "www.google.com", "google.es", "googleusercontent.com",
                   "play.google.com", "drive.google.com", "docs.google.com", "youtube.com"):
        assert closed not in hosts, closed
    gmail_s = {"mail.google.com", "apis.google.com", "contacts.google.com", "ogs.google.com",
               "clients6.google.com", "ssl.gstatic.com", "www.gstatic.com", "fonts.gstatic.com",
               "fonts.googleapis.com", "lh3.google.com", "lh3.googleusercontent.com",
               "mail-attachment.googleusercontent.com", "ci3.googleusercontent.com",
               "ci4.googleusercontent.com", "ci5.googleusercontent.com",
               "ci6.googleusercontent.com"}
    assert {host for host in hosts - gmail_s if not host.startswith("accounts.google.")} == set()


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
    for words in ('msgid "Gmail"', 'msgid "Email address"'):
        assert words in text
