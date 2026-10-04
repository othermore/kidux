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
    # Allowed, so that kidux-webapp can drive a module's Chromium through its
    # pipe (D91); the tools themselves stay closed, since every address but
    # the server's and the modules' hosts is blocked, devtools:// among them.
    assert policy["DeveloperToolsAvailability"] == 1
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


class FakePipe:
    """Chromium's pipe as the sign-in uses it: every command kept, and the
    events it waits for there at once."""

    def page(self):
        return "page"

    def call(self, method, params=None, session=""):
        self.calls.append((method, params or {}, session))
        if method == "Runtime.evaluate" and params.get("expression") == "typeof window.kidux":
            # The page is there, unless the test says it is still coming.
            return {"result": {"value": self.pages.pop(0) if self.pages else "object"}}
        return {}

    def __init__(self):
        self.calls, self.events = [], []
        #: What the page's button answers each time it is waited for.
        self.answers = []
        #: What `typeof window.kidux` answers, each time it is asked, until
        #: the page is there.
        self.pages = []

    def event(self, method):
        self.calls.append(("wait", {"for": method}, ""))
        payload = self.answers.pop(0) if self.answers else ""
        return {"method": method, "params": {"payload": payload}}

    def drain(self):
        self.calls.append(("drain", {}, ""))


class FakeProcess:
    def wait(self):
        return 0


SIGNING = modules.Module(id="combat", name="Combat", launch={"web": "https://example.org/"},
                         hosts=("example.org",),
                         sign_in=modules.SignIn("https://example.org/auth", (("a", "{email}"),),
                                                ("sess",), start="https://example.org/play"))


def sign_in(monkeypatch, client, module=SIGNING, answers=()):
    pipe = FakePipe()
    pipe.answers = list(answers)
    monkeypatch.setattr(webapp.browser, "start", lambda command: (FakeProcess(), pipe))
    assert webapp.drive(module, ["chromium"], "es", client) == 0
    return [(method, params) for method, params, _session in pipe.calls]


def test_the_page_is_waited_for_before_it_is_told_anything(monkeypatch):
    cookie = {"name": "sess", "value": "v", "domain": "example.org", "path": "/"}
    client = type("C", (), {"sign_in_module": lambda self, module_id: [cookie]})()
    pipe = FakePipe()
    pipe.pages = ["undefined", "undefined"]
    monkeypatch.setattr(webapp.browser, "start", lambda command: (FakeProcess(), pipe))
    monkeypatch.setattr(webapp.time, "sleep", lambda seconds: None)

    assert webapp.drive(SIGNING, ["chromium"], "es", client) == 0

    asked = [index for index, (method, params, _session) in enumerate(pipe.calls)
             if method == "Runtime.evaluate" and params.get("expression") == "typeof window.kidux"]
    told = next(index for index, (method, params, _session) in enumerate(pipe.calls)
                if method == "Runtime.evaluate" and "show(" in params.get("expression", ""))
    assert len(asked) == 3 and asked[-1] < told


def test_a_signing_module_opens_on_its_own_page_first():
    assert webapp.argv(SIGNING, CHILD)[-1] == "--app=http://127.0.0.1:8123/combat/?lang=es"


def test_signed_in_the_window_gets_the_cookies_and_goes_to_the_site_then_its_start(monkeypatch):
    cookie = {"name": "sess", "value": "v", "domain": "example.org", "path": "/"}
    client = type("C", (), {"sign_in_module": lambda self, module_id: [cookie]})()

    calls = sign_in(monkeypatch, client)

    assert ("Storage.setCookies", {"cookies": [cookie]}) in calls
    navigations = [params["url"] for method, params in calls if method == "Page.navigate"]
    assert navigations == ["https://example.org/", "https://example.org/play"]
    assert calls.index(("Storage.setCookies", {"cookies": [cookie]})) < calls.index(
        ("Page.navigate", {"url": "https://example.org/"}))
    # Then it keeps the pipe, reading, until the window is closed.
    assert calls[-1] == ("drain", {})


def test_a_refused_account_is_said_on_the_page_and_tried_again_when_asked(monkeypatch):
    answers = [RuntimeError("GDBus.Error:org.kidux.Daemon1.Error.SignInRefused: 401"), []]

    class Client:
        def sign_in_module(self, module_id):
            answer = answers.pop(0)
            if isinstance(answer, Exception):
                raise answer
            return answer

    calls = sign_in(monkeypatch, Client())

    shown = [params["expression"] for method, params in calls
             if method == "Runtime.evaluate" and "show(" in params["expression"]]
    assert 'window.kidux.show("refused")' in shown[1]
    assert ("wait", {"for": "Runtime.bindingCalled"}) in calls
    assert answers == []


def test_no_account_set_is_said_and_the_child_may_sign_in_by_hand(monkeypatch, tmp_path):
    class Client:
        def sign_in_module(self, module_id):
            raise RuntimeError("GDBus.Error:org.kidux.Daemon1.Error.SignInNotSet: none")

    by_hand = tmp_path / "by-hand.js"
    by_hand.write_text("document.querySelector('.login').click();\n")
    module = SIGNING.__class__(**{**SIGNING.__dict__, "sign_in": modules.SignIn(
        **{**SIGNING.sign_in.__dict__, "manual": str(by_hand)})})

    calls = sign_in(monkeypatch, Client(), module, answers=["", "manual"])

    shown = [params["expression"] for method, params in calls if method == "Runtime.evaluate"]
    assert sum('window.kidux.show("notset")' in said for said in shown) == 2
    # The first answer tries again; the second goes to the site, and runs
    # the module's script there once the site has loaded.
    assert [params["url"] for method, params in calls if method == "Page.navigate"] == [
        "https://example.org/"]
    loaded = calls.index(("wait", {"for": "Page.loadEventFired"}))
    ran = next(index for index, (method, params) in enumerate(calls)
               if method == "Runtime.evaluate" and ".login" in params["expression"])
    assert calls.index(("Page.navigate", {"url": "https://example.org/"})) < loaded < ran
    assert 'window.KIDUX = {"lang": "es"}' in calls[ran][1]["expression"]
    assert not any(method == "Storage.setCookies" for method, _params in calls)


def test_a_page_script_runs_in_every_page_in_a_world_of_its_own(monkeypatch, tmp_path):
    script = tmp_path / "bar.js"
    script.write_text("document.title;\n")
    wiki = modules.Module(id="wiki", name="Wiki", launch={"web": "https://{lang}.example.org/"},
                          hosts=("example.org",), page_script=str(script))

    calls = sign_in(monkeypatch, None, wiki)

    added = [params for method, params in calls
             if method == "Page.addScriptToEvaluateOnNewDocument"]
    assert added == [{"source": 'window.KIDUX = {"lang": "es"};\ndocument.title;\n',
                      "worldName": "kidux", "runImmediately": True}]
    assert not any(method == "Page.navigate" for method, _params in calls)
    assert calls[-1] == ("drain", {})
    assert webapp.argv(wiki, CHILD)[-1] == "--app=https://es.example.org/"


def test_a_signing_module_s_page_script_waits_for_its_site(monkeypatch, tmp_path):
    script = tmp_path / "bar.js"
    script.write_text("1;\n")
    module = SIGNING.__class__(**{**SIGNING.__dict__, "page_script": str(script)})
    client = type("C", (), {"sign_in_module": lambda self, module_id: []})()

    calls = sign_in(monkeypatch, client, module)

    added = calls.index(next(c for c in calls if c[0] == "Page.addScriptToEvaluateOnNewDocument"))
    assert calls[added][1]["runImmediately"] is False
    assert added < calls.index(("Page.navigate", {"url": "https://example.org/"}))

