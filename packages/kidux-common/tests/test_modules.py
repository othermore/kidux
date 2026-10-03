"""Reading module manifests: good ones read, broken ones skipped, never a crash."""

import gettext

from kidux import modules

GOOD = '''id = "{id}"
version = "1.0.0"
name = "Hello"
description = "Say hello."
min_age = 4
max_age = 8
memory_max = "1G"
launch = {{ exec = "/usr/libexec/kidux-module-{id}" }}
'''


def manifest(root, module_id, text, icon=False):
    (root / module_id).mkdir(parents=True)
    (root / module_id / "module.toml").write_text(text)
    if icon:
        (root / module_id / "icon.svg").write_text("<svg/>")


def test_a_good_manifest_is_read_whole(tmp_path):
    manifest(tmp_path, "hello", GOOD.format(id="hello"), icon=True)

    module = modules.read("hello", tmp_path)

    assert module == modules.Module(
        id="hello", name="Hello", description="Say hello.",
        icon=str(tmp_path / "hello" / "icon.svg"),
        launch={"exec": "/usr/libexec/kidux-module-hello"},
        i18n_domain="kidux-module-hello", min_age=4, max_age=8, memory_max="1G",
        version="1.0.0")


def test_what_a_manifest_leaves_out_has_its_default(tmp_path):
    manifest(tmp_path, "web", 'id = "web"\nname = "Web"\nlaunch = { webapp = "web" }\n')

    module = modules.read("web", tmp_path)

    assert module.icon == ""
    assert module.description == ""
    assert (module.min_age, module.max_age) == (0, 0)
    assert module.memory_max == "2G"
    assert module.i18n_domain == "kidux-module-web"
    assert module.launch == {"webapp": "web"}


def test_broken_manifests_are_skipped_and_logged(tmp_path, caplog):
    manifest(tmp_path, "hello", GOOD.format(id="hello"))
    manifest(tmp_path, "badid", GOOD.format(id="other"))
    manifest(tmp_path, "noname", 'id = "noname"\nlaunch = { exec = "/bin/true" }\n')
    manifest(tmp_path, "stringlaunch", 'id = "stringlaunch"\nname = "X"\nlaunch = "/bin/true"\n')
    manifest(tmp_path, "notoml", "this is = not [toml")
    (tmp_path / "empty").mkdir()
    (tmp_path / "Upper").mkdir()

    assert [m.id for m in modules.installed(tmp_path)] == ["hello"]
    for skipped in ("badid", "noname", "stringlaunch", "notoml", "empty"):
        assert modules.read(skipped, tmp_path) is None
        assert skipped in caplog.text


def test_an_id_that_could_leave_the_directory_is_refused(tmp_path):
    manifest(tmp_path, "hello", GOOD.format(id="hello"))

    for bad in ("../hello", "hello/", "", "Hello", "a" * 33):
        assert modules.read(bad, tmp_path) is None


def test_an_empty_or_missing_directory_has_no_modules(tmp_path):
    assert modules.installed(tmp_path) == []
    assert modules.installed(tmp_path / "missing") == []


def test_the_default_directory_is_the_data_roots(tmp_path, monkeypatch):
    monkeypatch.setattr(modules.paths, "MODULES_DIR", tmp_path)
    manifest(tmp_path, "hello", GOOD.format(id="hello"))

    assert [m.id for m in modules.installed()] == ["hello"]


def test_a_module_without_a_catalogue_shows_its_english(tmp_path, monkeypatch):
    # No catalogue anywhere: not even one a machine running Kidux has installed.
    monkeypatch.setattr(modules.paths, "LOCALE_ROOT", tmp_path / "locale")
    manifest(tmp_path, "hello", GOOD.format(id="hello"))
    module = modules.read("hello", tmp_path)

    assert modules.name_in(module, "es_ES.UTF-8") == "Hello"
    assert modules.description_in(module, "es_ES.UTF-8") == "Say hello."
    assert modules.name_in(module, "") == "Hello"


def test_a_module_with_a_catalogue_is_translated(tmp_path, monkeypatch):
    manifest(tmp_path, "hello", GOOD.format(id="hello"))
    module = modules.read("hello", tmp_path)
    catalogue = {"Hello": "Hola", "Say hello.": "Saluda."}

    class Spanish(gettext.NullTranslations):
        def gettext(self, message):
            return catalogue.get(message, message)

    def translation(domain, localedir=None, languages=None, fallback=False):
        assert domain == "kidux-module-hello"
        return Spanish() if languages and languages[0].startswith("es") else gettext.NullTranslations()

    monkeypatch.setattr(modules.gettext, "translation", translation)

    assert modules.name_in(module, "es_ES.UTF-8") == "Hola"
    assert modules.description_in(module, "es_ES.UTF-8") == "Saluda."
    assert modules.name_in(module, "en_US.UTF-8") == "Hello"


def test_a_module_needs_windows_only_when_its_manifest_says_so(tmp_path):
    manifest(tmp_path, "hello", GOOD.format(id="hello"))
    manifest(tmp_path, "editor", GOOD.format(id="editor") + "needs_windows = true\n")
    manifest(tmp_path, "odd", GOOD.format(id="odd") + 'needs_windows = "yes"\n')

    assert modules.read("hello", tmp_path).needs_windows is False
    assert modules.read("editor", tmp_path).needs_windows is True
    assert modules.read("odd", tmp_path).needs_windows is False


def test_the_modules_best_done_first_are_the_ids_in_the_manifest(tmp_path, caplog):
    # D55: what is not a module id is dropped with a line in the log.
    manifest(tmp_path, "hello", GOOD.format(id="hello"))
    manifest(tmp_path, "later", GOOD.format(id="later")
             + 'recommended_before = ["hello", "Not An Id", 3, "gcompris"]\n')
    manifest(tmp_path, "odd", GOOD.format(id="odd") + 'recommended_before = "hello"\n')

    assert modules.read("hello", tmp_path).recommended_before == ()
    assert modules.read("later", tmp_path).recommended_before == ("hello", "gcompris")
    assert modules.read("odd", tmp_path).recommended_before == ()
    assert "'Not An Id' in recommended_before is not a module id" in caplog.text
    assert "recommended_before is not a list of ids" in caplog.text


def test_a_module_says_what_its_windows_are_called(tmp_path, caplog):
    # D58: the launcher knows a window's module by its app_id.
    manifest(tmp_path, "hello", GOOD.format(id="hello") + 'app_ids = ["org.kidux.modules.Hello"]\n')
    manifest(tmp_path, "odd", GOOD.format(id="odd") + 'app_ids = "org.odd"\n')
    manifest(tmp_path, "web", 'id = "web"\nname = "Web"\nlaunch = { webapp = "web" }\n')

    hello, odd, web = (modules.read(m, tmp_path) for m in ("hello", "odd", "web"))

    assert hello.app_ids == ("org.kidux.modules.Hello",)
    assert modules.claims(hello, "org.kidux.modules.Hello")
    assert not modules.claims(hello, "org.kidux.modules.Hello2")
    assert odd.app_ids == () and "app_ids is not a list of names" in caplog.text
    # A web application's window is Chromium's, named after its address.
    assert modules.claims(web, "chrome-127.0.0.1__web_-Default")
    assert not modules.claims(web, "chrome-127.0.0.1__webby_-Default")


def test_a_module_that_opens_a_website_reads_with_its_window_name(tmp_path):
    # D85: a third kind of launch, an https:// address on the internet.
    manifest(tmp_path, "codecombat",
             'id = "codecombat"\nname = "CodeCombat"\nlaunch = { web = "https://codecombat.com/" }\n')
    manifest(tmp_path, "wikipedia",
             'id = "wikipedia"\nname = "Wikipedia"\nlaunch = { web = "https://{lang}.wikipedia.org/" }\n')

    combat, wiki = modules.read("codecombat", tmp_path), modules.read("wikipedia", tmp_path)

    assert combat.launch == {"web": "https://codecombat.com/"}
    assert combat.app_ids == ("chrome-codecombat.com__*",)
    assert modules.claims(combat, "chrome-codecombat.com__-Default")
    # {lang} in the host stands for any language's.
    assert wiki.app_ids == ("chrome-*.wikipedia.org__*",)
    assert modules.claims(wiki, "chrome-es.wikipedia.org__-Default")
    assert not modules.claims(wiki, "chrome-wikipedia.org.evil.com__-Default")


def test_a_website_that_is_not_https_is_skipped(tmp_path, caplog):
    for name, address in (("plain", "http://example.org/"), ("nohost", "https:///path"),
                          ("number", "3")):
        launch = f'"{address}"' if name != "number" else address
        manifest(tmp_path, name, f'id = "{name}"\nname = "X"\nlaunch = {{ web = {launch} }}\n')

    assert [modules.read(name, tmp_path) for name in ("plain", "nohost", "number")] == [None] * 3
    assert "its website is not an https:// address" in caplog.text


def test_a_module_names_the_hosts_its_pages_may_reach(tmp_path, caplog):
    manifest(tmp_path, "site", GOOD.format(id="site")
             + 'hosts = ["www.example.org", "cdn.example.org", "www.example.org"]\n')
    manifest(tmp_path, "bad", GOOD.format(id="bad") + 'hosts = ["https://example.org"]\n')
    manifest(tmp_path, "star", GOOD.format(id="star") + 'hosts = ["*.example.org"]\n')
    manifest(tmp_path, "none", GOOD.format(id="none"))

    assert modules.read("site", tmp_path).hosts == ("cdn.example.org", "www.example.org")
    assert modules.read("bad", tmp_path).hosts == ()
    assert modules.read("star", tmp_path).hosts == ()
    assert modules.read("none", tmp_path).hosts == ()
    assert caplog.text.count("hosts is not a list of host names") == 2


SETTINGS = '''
[[settings]]
key = "type_in"
kind = "switch"
label = "Type it in for me"
description = "A button types the listing."
default = true

[[settings]]
key = "speed"
kind = "integer"
label = "Speed"
description = "What it does."
default = 3
min = 1
max = 5

[[settings]]
key = "password"
kind = "secret"
label = "Password"
description = "What it does."

[[settings]]
key = "Bad Key"
kind = "switch"
label = "x"
description = "What it does."

[[settings]]
key = "colour"
kind = "colour"
label = "Colour"
description = "What it does."

[[settings]]
key = "quiet"
kind = "switch"
label = "Quiet"

[[settings]]
key = "big"
kind = "integer"
label = "Big"
description = "What it does."
default = 9
max = 5
'''


def test_a_module_declares_its_own_settings_of_the_known_kinds(tmp_path, caplog):
    # D90: no central list of settings; a module says which it has.
    manifest(tmp_path, "basic", GOOD.format(id="basic") + SETTINGS)

    settings = modules.read("basic", tmp_path).settings

    assert [(s.key, s.kind, s.default) for s in settings] == [
        ("type_in", "switch", True), ("speed", "integer", 3), ("password", "secret", "")]
    assert settings[1].minimum == 1 and settings[1].maximum == 5
    assert caplog.text.count("a setting is left out") == 4
    assert "quiet does not say what it does in a description" in caplog.text
    assert modules.read("basic", tmp_path).settings[0].description == "A button types the listing."


def test_a_setting_takes_only_values_of_its_kind_within_its_limits(tmp_path):
    manifest(tmp_path, "basic", GOOD.format(id="basic") + SETTINGS)
    switch, speed, secret = modules.read("basic", tmp_path).settings

    assert switch.value(False) is False
    assert speed.value(5) == 5
    assert secret.value("hunter2") == "hunter2"
    for setting, wrong in ((switch, 1), (switch, "yes"), (speed, 6), (speed, 0), (speed, True),
                           (speed, 2.5), (secret, 3), (secret, "two\nlines")):
        try:
            setting.value(wrong)
        except ValueError:
            continue
        raise AssertionError(f"{setting.key} took {wrong!r}")


def test_a_module_without_settings_has_none(tmp_path, caplog):
    manifest(tmp_path, "hello", GOOD.format(id="hello"))
    manifest(tmp_path, "odd", GOOD.format(id="odd") + 'settings = "type_in"\n')

    assert modules.read("hello", tmp_path).settings == ()
    assert modules.read("odd", tmp_path).settings == ()
    assert "settings is not a list of tables" in caplog.text


SIGN_IN = '''
hosts = ["example.org"]

[sign_in]
url = "https://example.org/auth/login"
body = { username = "{email}", password = "{password}" }
cookies = ["site.sess", "site.sess.sig"]
script = "sign-in.js"
start = "https://example.org/play"
'''


def test_a_website_module_says_how_it_signs_a_child_in(tmp_path):
    manifest(tmp_path, "site", 'id = "site"\nname = "Site"\n'
             'launch = { web = "https://example.org/" }\n' + SIGN_IN)
    (tmp_path / "site" / "sign-in.js").write_text("// the site's first page\n")

    site = modules.read("site", tmp_path)

    assert site.sign_in.url == "https://example.org/auth/login"
    assert dict(site.sign_in.body) == {"username": "{email}", "password": "{password}"}
    assert site.sign_in.cookies == ("site.sess", "site.sess.sig")
    assert site.sign_in.script == str(tmp_path / "site" / "sign-in.js")
    assert site.sign_in.start == "https://example.org/play"
    # Its window opens on its own Connecting… page first.
    assert modules.claims(site, "chrome-127.0.0.1__site_-Default")
    assert modules.claims(site, "chrome-example.org__-Default")


def test_a_sign_in_that_would_send_an_account_elsewhere_is_left_out(tmp_path, caplog):
    for name, change in (("http", ("https://example.org/auth", "http://example.org/auth")),
                         ("away", ("https://example.org/auth", "https://evil.example.com/auth")),
                         ("noscript", ('script = "sign-in.js"', 'script = "../x.js"')),
                         ("cookies", ('cookies = ["site.sess", "site.sess.sig"]', 'cookies = []'))):
        manifest(tmp_path, name, f'id = "{name}"\nname = "X"\n'
                 'launch = { web = "https://example.org/" }\n'
                 + SIGN_IN.replace(*change).replace('script = "sign-in.js"\n', "")
                 if name != "noscript" else
                 f'id = "{name}"\nname = "X"\nlaunch = {{ web = "https://example.org/" }}\n'
                 + SIGN_IN.replace(*change))

        assert modules.read(name, tmp_path).sign_in is None, name
    assert caplog.text.count("its sign_in is left out") == 4
