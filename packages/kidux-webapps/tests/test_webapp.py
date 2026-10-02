"""kidux-webapp: Chromium's command line, the ids it refuses, and the policy
every Chromium on the machine is held by."""

import json
from pathlib import Path

import pytest

from test_server import load

webapp = load("kidux-webapp")

CHILD = {"LANG": "es_ES.UTF-8", "HOME": "/home/leo",
         "XDG_CONFIG_HOME": "/home/leo/.config/kidux/hello-web"}
POLICY = Path(__file__).parent.parent / "policies" / "kidux.json"


def test_the_policy_allows_the_server_and_closes_every_other_door():
    policy = json.loads(POLICY.read_text())

    assert policy["URLBlocklist"] == ["*"]
    assert policy["DeveloperToolsAvailability"] == 2
    assert policy["IncognitoModeAvailability"] == 1
    assert policy["ExtensionInstallBlocklist"] == ["*"]
    assert not policy["PrintingEnabled"]
    assert not policy["DefaultSearchProviderEnabled"]
    assert not policy["TranslateEnabled"]


def test_the_policy_allows_the_hosts_the_editors_libraries_come_from_and_no_other():
    policy = json.loads(POLICY.read_text())

    assert policy["URLAllowlist"] == [
        "127.0.0.1:8123",
        "assets.scratch.mit.edu",
        "cdn.assets.scratch.mit.edu",
        "cdn2.scratch.mit.edu",
        "cdn.scratch.mit.edu",
        "trampoline.turbowarp.org",
        "blob:*",
    ]


def test_the_policy_lets_a_child_keep_and_open_their_work():
    policy = json.loads(POLICY.read_text())

    # Downloads are how Scratch saves a project, each asking where in a file
    # dialog; only dangerous files are refused. The file dialog is how it
    # opens one too.
    assert policy["DownloadRestrictions"] == 1
    assert policy["AllowFileSelectionDialogs"]
    assert policy["PromptForDownloadLocation"]


def test_chromium_opens_the_application_as_an_app_window_in_the_childs_language():
    assert webapp.argv("hello-web", CHILD) == [
        "/usr/bin/chromium",
        "--ozone-platform=wayland",
        "--no-first-run",
        "--no-default-browser-check",
        "--disable-session-crashed-bubble",
        "--password-store=basic",
        "--enable-unsafe-swiftshader",
        "--user-data-dir=/home/leo/.config/kidux/hello-web/chromium",
        "--lang=es",
        "--app=http://127.0.0.1:8123/hello-web/?lang=es",
    ]


@pytest.mark.parametrize("bad", ["", "Hello", "../hello", "hello/../x", "hello web",
                                 "hello?x=1", "hello#x", "@evil.example", "a" * 33,
                                 "hello\n"])
def test_anything_but_an_id_is_refused(bad):
    with pytest.raises(ValueError):
        webapp.argv(bad, CHILD)


@pytest.mark.parametrize("environ,lang", [
    ({"LANG": "es_ES.UTF-8"}, "es"),
    ({"LANG": "en_GB.UTF-8", "LC_ALL": "es_ES.UTF-8"}, "es"),
    ({"LANG": "C.UTF-8"}, "en"),
    ({}, "en"),
])
def test_the_language_is_the_sessions(environ, lang):
    assert webapp.language(environ) == lang


def test_a_bad_id_starts_nothing(capsys):
    assert webapp.main(["kidux-webapp", "../etc"]) == 2
    assert "not a web application's id" in capsys.readouterr().err


def test_the_machine_s_flags_come_after_kidux_s_own():
    command = webapp.argv("hello-web", CHILD, ["--disable-gpu-compositing"])

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
    monkeypatch.setenv("LANG", "es_ES.UTF-8")

    assert webapp.main(["kidux-webapp", "--print", "hello-web"]) == 0
    printed = capsys.readouterr().out
    assert printed.startswith("/usr/bin/chromium ") and printed.rstrip().endswith(
        "'--app=http://127.0.0.1:8123/hello-web/?lang=es' --disable-gpu")
