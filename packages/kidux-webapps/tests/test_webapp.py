"""kidux-webapp: Chromium's command line, the wall around it, the modules
it refuses, and the base of the policy every Chromium on the machine is held
by."""

import json
from pathlib import Path

import pytest

from kidux import modules
from test_server import load

webapp = load("kidux-webapp")

CHILD = {"LANG": "es_ES.UTF-8", "HOME": "/home/leo",
         "XDG_CONFIG_HOME": "/home/leo/.config/kidux/hello-web"}
POLICY = Path(__file__).parent.parent / "policies" / "kidux.json"
HELLO = modules.Module(id="hello-web", name="Hello", launch={"webapp": "hello-web"})
COMBAT = modules.Module(id="codecombat", name="CodeCombat", launch={"web": "https://codecombat.com/"},
                        hosts=("cdn.example.org", "codecombat.com"))
WIKI = modules.Module(id="wikipedia", name="Wikipedia", launch={"web": "https://{lang}.wikipedia.org/"},
                      hosts=("wikipedia.org",))


def test_the_policy_allows_the_server_and_closes_every_other_door():
    policy = json.loads(POLICY.read_text())

    assert policy["URLBlocklist"] == ["*"]
    assert policy["DeveloperToolsAvailability"] == 2
    assert policy["IncognitoModeAvailability"] == 1
    assert policy["ExtensionInstallBlocklist"] == ["*"]
    assert not policy["PrintingEnabled"]
    assert not policy["DefaultSearchProviderEnabled"]
    assert not policy["TranslateEnabled"]


def test_the_base_policy_allows_the_server_and_no_module_s_host():
    # The modules' hosts are added by kidux-chromium-policy (test_policy.py).
    assert json.loads(POLICY.read_text())["URLAllowlist"] == ["127.0.0.1:8123", "blob:*"]


def test_the_policy_lets_a_child_keep_and_open_their_work():
    policy = json.loads(POLICY.read_text())

    # Downloads are how Scratch saves a project, each asking where in a file
    # dialog; only dangerous files are refused. The file dialog is how it
    # opens one too.
    assert policy["DownloadRestrictions"] == 1
    assert policy["AllowFileSelectionDialogs"]
    assert policy["PromptForDownloadLocation"]


def test_chromium_opens_the_application_as_an_app_window_in_the_childs_language():
    assert webapp.argv(HELLO, CHILD) == [
        "/usr/bin/chromium",
        "--ozone-platform=wayland",
        "--no-first-run",
        "--no-default-browser-check",
        "--disable-session-crashed-bubble",
        "--password-store=basic",
        "--enable-unsafe-swiftshader",
        "--proxy-server=127.0.0.1:1",
        "--proxy-bypass-list=127.0.0.1",
        "--user-data-dir=/home/leo/.config/kidux/hello-web/chromium",
        "--lang=es",
        "--app=http://127.0.0.1:8123/hello-web/?lang=es",
    ]


def test_a_website_s_chromium_reaches_its_hosts_and_nothing_else():
    command = webapp.argv(COMBAT, CHILD)

    assert "--proxy-server=127.0.0.1:1" in command
    assert ("--proxy-bypass-list=127.0.0.1;cdn.example.org;*.cdn.example.org;"
            "codecombat.com;*.codecombat.com") in command
    assert command[-1] == "--app=https://codecombat.com/"
    # WebGL in software is for the server's own applications only (D85).
    assert "--enable-unsafe-swiftshader" not in command
    assert command.index("--proxy-server=127.0.0.1:1") < command.index("--app=https://codecombat.com/")


def test_a_website_opens_in_the_child_s_language():
    assert webapp.argv(WIKI, CHILD)[-1] == "--app=https://es.wikipedia.org/"
    assert webapp.argv(WIKI, {"LANG": "en_GB.UTF-8"})[-1] == "--app=https://en.wikipedia.org/"


def test_a_module_that_is_not_made_of_web_pages_is_refused():
    program = modules.Module(id="hello", name="Hello", launch={"exec": "/usr/libexec/hello"})
    with pytest.raises(ValueError):
        webapp.argv(program, CHILD)


@pytest.mark.parametrize("environ,lang", [
    ({"LANG": "es_ES.UTF-8"}, "es"),
    ({"LANG": "en_GB.UTF-8", "LC_ALL": "es_ES.UTF-8"}, "es"),
    ({"LANG": "C.UTF-8"}, "en"),
    ({}, "en"),
])
def test_the_language_is_the_sessions(environ, lang):
    assert webapp.language(environ) == lang


@pytest.mark.parametrize("bad", ["", "Hello", "../hello", "hello/../x", "hello web",
                                 "hello?x=1", "@evil.example", "a" * 33, "nothing-here"])
def test_anything_but_an_installed_module_starts_nothing(bad, tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(webapp.modules.paths, "MODULES_DIR", tmp_path)
    monkeypatch.setattr(webapp.os, "execv", lambda *_a: pytest.fail("it ran Chromium"))

    assert webapp.main(["kidux-webapp", bad]) == 2
    assert "not an installed module" in capsys.readouterr().err


def test_the_machine_s_flags_come_after_kidux_s_own():
    command = webapp.argv(HELLO, CHILD, ["--disable-gpu-compositing"])

    assert command[-2:] == ["--app=http://127.0.0.1:8123/hello-web/?lang=es",
                            "--disable-gpu-compositing"]


def test_the_machine_s_flags_are_read_one_a_line(tmp_path, capsys):
    path = tmp_path / "chromium-flags"
    path.write_text("--disable-gpu-compositing\n\n  --use-gl=angle  \nnot a flag\n")

    assert webapp.machine_flags(path) == ["--disable-gpu-compositing", "--use-gl=angle"]
    assert "not a flag" in capsys.readouterr().err


def test_no_file_is_no_flags(tmp_path):
    assert webapp.machine_flags(tmp_path / "nothing") == []


def test_print_shows_the_command_line_and_runs_nothing(tmp_path, monkeypatch, capsys):
    path = tmp_path / "chromium-flags"
    path.write_text("--disable-gpu\n")
    monkeypatch.setattr(webapp.paths, "CHROMIUM_FLAGS", path)
    monkeypatch.setattr(webapp.os, "execv", lambda *_a: pytest.fail("it ran Chromium"))
    monkeypatch.setattr(webapp.modules.paths, "MODULES_DIR", tmp_path / "modules")
    (tmp_path / "modules" / "hello-web").mkdir(parents=True)
    (tmp_path / "modules" / "hello-web" / "module.toml").write_text(
        'id = "hello-web"\nname = "Hello"\nlaunch = { webapp = "hello-web" }\n')
    monkeypatch.setenv("LANG", "es_ES.UTF-8")

    assert webapp.main(["kidux-webapp", "--print", "hello-web"]) == 0
    printed = capsys.readouterr().out
    assert printed.startswith("/usr/bin/chromium ") and printed.rstrip().endswith(
        "'--app=http://127.0.0.1:8123/hello-web/?lang=es' --disable-gpu")
    assert "--proxy-server=127.0.0.1:1 --proxy-bypass-list=127.0.0.1 " in printed


def test_an_adult_s_settings_go_to_a_web_application_in_its_address():
    # D90: the launcher puts them in the environment, the page reads them.
    child = {**CHILD, "KIDUX_SETTING_TYPE_IN": "0", "KIDUX_SETTING_BAD KEY": "x"}

    assert webapp.argv(HELLO, child)[-1] == "--app=http://127.0.0.1:8123/hello-web/?lang=es&type_in=0"
    # A website gets nothing of them.
    assert webapp.argv(COMBAT, child)[-1] == "--app=https://codecombat.com/"
