"""CodeCombat as the launcher and the panel will find it: a door to the
CodeCombat website (D86), its manifest read by the one reader (D34), its
words complete."""

import shutil
import subprocess
from pathlib import Path

from kidux import modules

PACKAGE = Path(__file__).resolve().parents[1]


def test_the_manifest_reads_as_a_door_to_the_website(tmp_path):
    (tmp_path / "codecombat").mkdir()
    for name in ("module.toml", "icon.svg", "sign-in.js", "sign-in-by-hand.js"):
        shutil.copy(PACKAGE / name, tmp_path / "codecombat" / name)

    combat = modules.read("codecombat", root=tmp_path)

    assert combat is not None
    assert combat.launch == {"web": "https://codecombat.com/"}
    assert "codecombat.com" in combat.hosts
    assert combat.app_ids == ("chrome-codecombat.com__*", "chrome-127.0.0.1__codecombat_-*")
    assert (combat.min_age, combat.max_age, combat.memory_max) == (9, 16, "3G")


def test_the_manifests_version_is_the_packages():
    changelog = (PACKAGE / "debian" / "changelog").read_text().split("\n", 1)[0]
    version = changelog.split("(", 1)[1].split(")", 1)[0]

    assert f'version = "{version}"' in (PACKAGE / "module.toml").read_text()


def test_its_words_say_it_is_not_connected_with_codecombat():
    manifest = (PACKAGE / "module.toml").read_text()
    spanish = (PACKAGE / "po" / "es.po").read_text()

    assert "Kidux is not connected with CodeCombat" in manifest
    assert "Kidux no tiene ninguna relación con CodeCombat" in spanish.replace('"\n"', "")


def test_the_catalogue_is_complete():
    untranslated = subprocess.run(
        ["msgattrib", "--untranslated", "--only-fuzzy", "--no-obsolete",
         str(PACKAGE / "po" / "es.po")], capture_output=True, text=True, check=True).stdout
    assert [line for line in untranslated.splitlines() if line.startswith('msgid "')
            and line != 'msgid ""'] == []


def test_an_adult_gives_the_account_and_the_daemon_signs_in_with_it(tmp_path):
    (tmp_path / "codecombat").mkdir()
    for name in ("module.toml", "icon.svg", "sign-in.js", "sign-in-by-hand.js"):
        shutil.copy(PACKAGE / name, tmp_path / "codecombat" / name)

    combat = modules.read("codecombat", root=tmp_path)

    assert [(s.key, s.kind) for s in combat.settings] == [("email", "text"), ("password", "secret")]
    assert all(s.description for s in combat.settings)
    assert combat.sign_in.url == "https://codecombat.com/auth/login"
    assert dict(combat.sign_in.body) == {"username": "{email}", "password": "{password}"}
    assert combat.sign_in.cookies == ("codecombat.sess", "codecombat.sess.sig")
    assert combat.sign_in.start == "https://codecombat.com/play"
    assert combat.sign_in.manual == str(tmp_path / "codecombat" / "sign-in-by-hand.js")
    assert ".login-button" in (PACKAGE / "sign-in-by-hand.js").read_text()
    # Its window opens on its own Connecting… page, served by kidux-webapps.
    assert modules.claims(combat, "chrome-127.0.0.1__codecombat_-Default")


def test_the_connecting_page_holds_every_language_s_words(tmp_path):
    import importlib.util
    import json
    import sys

    locale = tmp_path / "locale" / "es" / "LC_MESSAGES"
    locale.mkdir(parents=True)
    subprocess.run(["msgfmt", "-o", str(locale / "kidux-module-codecombat.mo"),
                    str(PACKAGE / "po" / "es.po")], check=True)
    sys.dont_write_bytecode = True
    spec = importlib.util.spec_from_file_location("page", PACKAGE / "webapp" / "page.py")
    page = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(page)
    output = tmp_path / "index.html"

    page.main(["page.py", str(tmp_path / "locale"), str(PACKAGE / "po"),
               str(PACKAGE / "webapp" / "index.html.in"), str(output)])

    html = output.read_text()
    words = json.loads(html.split("const WORDS = ", 1)[1].split(";\n", 1)[0])
    assert set(words) == {"en", "es"}
    assert words["es"]["connecting"] == "Conectándose a CodeCombat…"
    assert set(words["en"]) == {"connecting", "refused", "unreachable", "again", "notset",
                                "byhand"}
    assert words["es"]["byhand"] == "Entrar yo"
    assert "window.kidux = {" in html and "kiduxTryAgain" in html


def test_the_script_sets_the_account_s_language_through_the_site_s_own_pages():
    script = (PACKAGE / "sign-in.js").read_text()

    assert '"/auth/whoami"' in script and 'method: "PATCH"' in script
    assert "preferredLanguage" in script and "window.KIDUX.lang" in script
