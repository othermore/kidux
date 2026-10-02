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
