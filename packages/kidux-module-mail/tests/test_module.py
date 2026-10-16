"""Mail as the launcher, the panel and Thunderbird will find it: its manifest
read by the one reader (D34), the user.js its program writes from each kind
of setting, its profile closed to everyone but the child, its policies
whole, and its words complete."""

import importlib.machinery
import importlib.util
import json
import shutil
import stat
import subprocess
from pathlib import Path

from kidux import modules

PACKAGE = Path(__file__).resolve().parents[1]

_loader = importlib.machinery.SourceFileLoader("mail", str(PACKAGE / "bin" / "kidux-module-mail"))
_spec = importlib.util.spec_from_loader("mail", _loader)
mail = importlib.util.module_from_spec(_spec)
_loader.exec_module(mail)

#: An answer of the autoconfiguration database for a provider that signs in
#: with OAuth2, shaped as Mozilla's are.
OAUTH = """<clientConfig version="1.1">
  <emailProvider id="example.com">
    <domain>example.com</domain>
    <incomingServer type="pop3">
      <hostname>pop.example.com</hostname><port>995</port><socketType>SSL</socketType>
      <username>%EMAILADDRESS%</username><authentication>OAuth2</authentication>
    </incomingServer>
    <incomingServer type="imap">
      <hostname>imap.example.com</hostname><port>993</port><socketType>SSL</socketType>
      <username>%EMAILADDRESS%</username>
      <authentication>OAuth2</authentication><authentication>password-cleartext</authentication>
    </incomingServer>
    <outgoingServer type="smtp">
      <hostname>smtp.example.com</hostname><port>465</port><socketType>SSL</socketType>
      <username>%EMAILADDRESS%</username>
      <authentication>OAuth2</authentication><authentication>password-cleartext</authentication>
    </outgoingServer>
  </emailProvider>
</clientConfig>"""

#: One for a provider that takes a password, its user name the address's
#: first part, its outgoing server on STARTTLS.
PASSWORD = """<clientConfig version="1.1">
  <emailProvider id="example.net">
    <domain>example.net</domain>
    <incomingServer type="imap">
      <hostname>mail.example.net</hostname><port>993</port><socketType>SSL</socketType>
      <username>%EMAILLOCALPART%</username><authentication>password-cleartext</authentication>
    </incomingServer>
    <outgoingServer type="smtp">
      <hostname>mail.example.net</hostname><port>587</port><socketType>STARTTLS</socketType>
      <username>%EMAILLOCALPART%</username><authentication>password-cleartext</authentication>
    </outgoingServer>
  </emailProvider>
</clientConfig>"""


def environment(tmp_path, **chosen) -> dict:
    home = tmp_path / "home"
    config = home / ".config" / "kidux" / "mail"
    config.mkdir(parents=True, exist_ok=True)
    (config / "user-dirs.dirs").write_text('XDG_DESKTOP_DIR="$HOME/Escritorio"\n'
                                           'XDG_DOWNLOAD_DIR="$HOME/Descargas"\n')
    return {"HOME": str(home), "XDG_CONFIG_HOME": str(config),
            **{f"KIDUX_SETTING_{key.upper()}": value for key, value in chosen.items()}}


def prefs(text: str) -> dict:
    """user.js's prefs, as a dict."""
    found = {}
    for line in text.splitlines():
        assert line.startswith("user_pref(") and line.endswith(");"), line
        name, value = json.loads("[" + line[len("user_pref("):-2] + "]")
        found[name] = value
    return found


def written(tmp_path, ask=lambda domain: None, **chosen) -> dict:
    environ = environment(tmp_path, **chosen)
    profile = Path(environ["XDG_CONFIG_HOME"]) / "thunderbird"
    profile.mkdir(exist_ok=True)
    picked = mail.settings(environ)
    return prefs(mail.user_js(picked, mail.servers(picked, profile, ask), "Carpetas locales",
                              mail.downloads(environ)))


def test_the_manifest_reads_as_the_launcher_reads_it(tmp_path):
    (tmp_path / "mail").mkdir()
    for name in ("module.toml", "icon.svg"):
        shutil.copy(PACKAGE / name, tmp_path / "mail" / name)

    found = modules.read("mail", root=tmp_path)

    assert found is not None
    assert found.name == "Mail"
    assert found.launch == {"exec": "/usr/libexec/kidux-module-mail"}
    assert found.app_ids == ("thunderbird",)
    assert (found.min_age, found.memory_max) == (8, "2G")
    assert [(s.key, s.kind) for s in found.settings] == [
        ("email", "text"), ("name", "text"), ("imap_host", "text"), ("smtp_host", "text")]


def test_servers_given_make_the_account_with_a_password(tmp_path):
    asked = []
    got = written(tmp_path, ask=asked.append, email="leo@example.org", name="Leo",
                  imap_host="imap.example.org", smtp_host="smtp.example.org:587")

    assert asked == []
    assert got["mail.accountmanager.accounts"] == "account1,account2"
    assert got["mail.identity.id1.useremail"] == "leo@example.org"
    assert got["mail.identity.id1.fullName"] == "Leo"
    assert (got["mail.server.server1.hostname"], got["mail.server.server1.port"],
            got["mail.server.server1.socketType"], got["mail.server.server1.authMethod"]) == \
        ("imap.example.org", 993, mail.TLS, mail.PASSWORD)
    assert got["mail.server.server1.userName"] == "leo@example.org"
    assert got["mail.server.server1.login_at_startup"] is True
    assert got["mail.server.server1.check_new_mail"] is True
    assert (got["mail.smtpserver.smtp1.hostname"], got["mail.smtpserver.smtp1.port"],
            got["mail.smtpserver.smtp1.try_ssl"], got["mail.smtpserver.smtp1.authMethod"]) == \
        ("smtp.example.org", 587, mail.STARTTLS, mail.PASSWORD)


def test_a_provider_the_database_knows_signs_in_with_oauth2(tmp_path):
    got = written(tmp_path, ask={"example.com": OAUTH}.get, email="leo@Example.com", name="Leo")

    assert got["mail.server.server1.hostname"] == "imap.example.com"
    assert got["mail.server.server1.authMethod"] == mail.OAUTH2
    assert got["mail.smtpserver.smtp1.hostname"] == "smtp.example.com"
    assert got["mail.smtpserver.smtp1.authMethod"] == mail.OAUTH2


def test_a_provider_with_a_password_gets_its_own_user_names(tmp_path):
    got = written(tmp_path, ask={"example.net": PASSWORD}.get, email="leo@example.net")

    assert (got["mail.server.server1.userName"], got["mail.server.server1.authMethod"]) == \
        ("leo", mail.PASSWORD)
    assert (got["mail.smtpserver.smtp1.port"], got["mail.smtpserver.smtp1.try_ssl"],
            got["mail.smtpserver.smtp1.username"]) == (587, mail.STARTTLS, "leo")


def test_the_databases_answer_is_kept_and_not_asked_again(tmp_path):
    asked = []

    def ask(domain):
        asked.append(domain)
        return OAUTH

    written(tmp_path, ask=ask, email="leo@example.com")
    got = written(tmp_path, ask=ask, email="leo@example.com")

    assert asked == ["example.com"]
    assert got["mail.server.server1.hostname"] == "imap.example.com"


def test_a_server_given_takes_the_place_of_the_databases(tmp_path):
    got = written(tmp_path, ask={"example.com": OAUTH}.get, email="leo@example.com",
                  imap_host="imap.other.example:143")

    assert (got["mail.server.server1.hostname"], got["mail.server.server1.socketType"],
            got["mail.server.server1.authMethod"]) == ("imap.other.example", mail.STARTTLS,
                                                       mail.PASSWORD)
    assert got["mail.smtpserver.smtp1.hostname"] == "smtp.example.com"


def test_no_address_or_no_servers_is_no_account(tmp_path):
    for chosen in ({}, {"email": "not an address"}, {"email": "leo@unknown.example"},
                   {"email": "leo@example.org", "imap_host": "bad host!"}):
        got = written(tmp_path, **chosen)

        assert got["mail.accountmanager.accounts"] == "account2", chosen
        assert not any(name.startswith(("mail.server.server1.", "mail.smtpserver."))
                       for name in got), chosen


def test_local_folders_and_the_quiet_prefs_are_always_there(tmp_path):
    for chosen in ({}, {"email": "leo@example.org", "imap_host": "imap.example.org",
                        "smtp_host": "smtp.example.org"}):
        got = written(tmp_path, **chosen)

        assert got["mail.accountmanager.localfoldersserver"] == "server2"
        assert (got["mail.server.server2.type"], got["mail.server.server2.name"]) == \
            ("none", "Carpetas locales")
        assert got["mailnews.start_page.enabled"] is False
        assert got["mail.rights.version"] == 1
        assert got["browser.download.dir"] == str(tmp_path / "home" / "Descargas")
        assert got["browser.download.folderList"] == 2


def test_what_an_adult_typed_is_written_as_a_string_and_nothing_more(tmp_path):
    got = written(tmp_path, email="leo@example.org", name='Leo"); user_pref("x", 1);//',
                  imap_host="imap.example.org", smtp_host="smtp.example.org")

    assert got["mail.identity.id1.fullName"] == 'Leo"); user_pref("x", 1);//'
    assert "x" not in got


def test_the_program_writes_user_js_in_a_profile_only_the_child_reads(tmp_path):
    environ = environment(tmp_path, email="leo@example.org", imap_host="imap.example.org",
                          smtp_host="smtp.example.org")
    started = []
    mail.os.execv, real = (lambda path, args: started.append(args)), mail.os.execv
    try:
        mail.main(["kidux-module-mail"], environ)
    finally:
        mail.os.execv = real

    profile = Path(environ["XDG_CONFIG_HOME"]) / "thunderbird"
    assert stat.S_IMODE(profile.stat().st_mode) == 0o700
    assert prefs((profile / "user.js").read_text())["mail.server.server1.hostname"] == \
        "imap.example.org"
    assert started == [[mail.THUNDERBIRD, "--profile", str(profile), "--no-remote"]]


def test_print_writes_user_js_to_standard_output_and_starts_nothing(tmp_path, capsys):
    environ = environment(tmp_path, email="leo@example.org", imap_host="imap.example.org",
                          smtp_host="smtp.example.org")

    assert mail.main(["kidux-module-mail", "--print"], environ) == 0

    assert prefs(capsys.readouterr().out)["mail.identity.id1.useremail"] == "leo@example.org"
    assert not (Path(environ["XDG_CONFIG_HOME"]) / "thunderbird" / "user.js").exists()


def test_the_policies_are_whole():
    policies = json.loads((PACKAGE / "policies" / "policies.json").read_text())["policies"]

    for name in ("DisableAppUpdate", "DisableSafeMode", "DisableDeveloperTools",
                 "DisableTelemetry", "DisableMasterPasswordCreation", "BlockAboutConfig",
                 "BlockAboutAddons", "BlockAboutProfiles", "BlockAboutSupport",
                 "PasswordManagerEnabled", "OfferToSaveLogins"):
        assert policies[name] is True, name
    assert policies["InstallAddonsPermission"] == {"Default": False}
    for scheme in ("http", "https"):
        handler = policies["Handlers"]["schemes"][scheme]
        assert (handler["action"], handler["ask"]) == ("useHelperApp", False)
        assert [h["path"] for h in handler["handlers"]] == ["/usr/bin/true"]
    locked = {name: pref["Value"] for name, pref in policies["Preferences"].items()
              if pref["Status"] == "locked"}
    assert locked == {"browser.download.forbid_open_with": True,
                      "network.protocol-handler.external-default": False,
                      "browser.download.useDownloadDir": True,
                      "browser.download.always_ask_before_handling_new_types": False,
                      "mail.chat.enabled": False,
                      "mail.suppressAlertsForTests": True,
                      "mail.biff.show_alert": False}


def test_the_manifests_version_is_the_packages():
    changelog = (PACKAGE / "debian" / "changelog").read_text().split("\n", 1)[0]
    version = changelog.split("(", 1)[1].split(")", 1)[0]

    assert f'version = "{version}"' in (PACKAGE / "module.toml").read_text()


def test_the_catalogue_is_complete_and_holds_the_programs_words():
    catalogue = PACKAGE / "po" / "es.po"
    untranslated = subprocess.run(
        ["msgattrib", "--untranslated", "--only-fuzzy", "--no-obsolete", str(catalogue)],
        capture_output=True, text=True, check=True).stdout
    text = catalogue.read_text()

    assert [line for line in untranslated.splitlines() if line.startswith('msgid "')
            and line != 'msgid ""'] == []
    for words in ('msgid "Mail"', 'msgid "Local Folders"', 'msgid "Incoming server"'):
        assert words in text
