"""Modules installed and removed from the panel (daemon.md section 9).

What the archive offers is read from apt's and dpkg's own output, a pure
function tested here against samples. Installing and removing go through
the update job of section 13, with a package name the daemon makes from an
id it checks, never while a child has a session.
"""

import pytest

from kiduxd import catalogue
from kiduxd.errors import Busy, InvalidArgument, NotUnlocked, SessionActive
from kiduxd.updates import Updates, read

from test_service import ADMIN, ANA, GREETER
from test_time_and_lock import ADULT, SESSION, Harness, UpdateRunner

#: What `apt-cache search --names-only --full '^kidux-module-'` prints: a
#: record per package, as the archive's index has it.
RECORDS = """\
Package: kidux-module-hello
Version: 0.1.2
Kidux-Name-en: Hello
Kidux-Description-en: A first page to read, and a button to press.
Kidux-Name-es: Hola
Kidux-Description-es: Una primera página para leer, y un botón para pulsar.
Kidux-Ages: 4-8
Description: Kidux learning module: Hello, a first page to read
 Kidux is a Debian derivative for a child's first computer.
Description-md5:

Package: kidux-module-gcompris
Version: 0.1.2
Kidux-Name-en: GCompris
Kidux-Description-en: Over a hundred activities.
Kidux-Ages: 2-
Kidux-Before: hello Not-An-Id hello-web
Description: Kidux learning module: GCompris, over a hundred activities for ages two to ten

Package: kidux-module-older
Description: Kidux learning module: Older, from before the fields

Package: kidux-module-Shouting
Description: Kidux learning module: Shouting, not an id

Package: kidux-module-../x
Description: Kidux learning module: Escape, not an id either

Package: kidux-module-plain
Description: A description without the convention

Package: kidux-archive-keyring
Description: not a module at all
"""
DPKG = """\
kidux-module-hello 0.1.1 installed
kidux-module-plain 2.0 config-files
"""


def test_the_archive_s_modules_are_listed_by_id_in_the_machine_s_language():
    offered = catalogue.available(RECORDS, DPKG, lambda module_id: None, "es")

    assert [m["id"] for m in offered] == ["gcompris", "hello", "older", "plain"]
    gcompris, hello, older, plain = offered
    assert hello == {"id": "hello", "name": "Hola",
                     "description": "Una primera página para leer, y un botón para pulsar.",
                     "installed": True, "version": "0.1.1", "offered_version": "0.1.2",
                     "min_age": 4, "max_age": 8, "before": []}
    # English when the package has no fields in the machine's language, and
    # its short description when it has none at all.
    assert gcompris == {"id": "gcompris", "name": "GCompris",
                        "description": "Over a hundred activities.",
                        "installed": False, "version": "", "offered_version": "0.1.2",
                        "min_age": 2, "max_age": 0, "before": ["hello", "hello-web"]}
    assert (older["name"], older["description"]) == ("Older", "From before the fields")
    # Without the fields, no ages and nothing first.
    assert (older["min_age"], older["max_age"], older["before"]) == (0, 0, [])
    # A record without a version, as an index never has, says none.
    assert older["offered_version"] == ""
    # Removed with its settings left is not installed; a description that
    # does not follow the convention is shown as it is.
    assert (plain["installed"], plain["name"], plain["description"]) == (
        False, "Plain", "A description without the convention")


def test_in_english_on_an_english_machine():
    offered = catalogue.available(RECORDS, DPKG, lambda module_id: None, "en")

    assert [(m["name"], m["description"]) for m in offered][:2] == [
        ("GCompris", "Over a hundred activities."),
        ("Hello", "A first page to read, and a button to press.")]


def test_an_installed_module_is_named_as_its_manifest_says():
    manifest = {"name": "Hola, instalado", "min_age": 5, "max_age": 0, "before": ["intro"]}
    offered = catalogue.available(RECORDS, DPKG, {"hello": manifest}.get, "es")

    assert {key: offered[1][key] for key in manifest} == manifest


@pytest.mark.parametrize("field, bounds", [
    ("4-8", (4, 8)), ("2-", (2, 0)), ("-10", (0, 10)), ("", (0, 0)), ("four", (0, 0)),
    ("4", (0, 0)), ("4-8-9", (0, 0)), (" 4-8 ", (4, 8)),
])
def test_the_ages_field(field, bounds):
    assert catalogue.ages(field) == bounds


def test_the_machine_s_language_from_its_locale():
    assert catalogue.language_of("es_ES.UTF-8") == "es"
    assert catalogue.language_of("en_GB.UTF-8") == "en"
    assert catalogue.language_of("") == "en"


def test_an_empty_archive_offers_nothing():
    assert catalogue.available("", "", lambda module_id: None) == []


def test_a_module_id_makes_its_package():
    assert catalogue.package_of("hello") == "kidux-module-hello"


# --- Install and Remove ----------------------------------------------------------


@pytest.fixture
def h(fast_hasher):
    return Harness(fast_hasher)


@pytest.fixture
def jobs(h, tmp_path):
    runner = UpdateRunner(tmp_path / "update.status")
    h.service.updates = Updates(
        runner, status=runner.status, emit=lambda *signal: h.signals.append(signal),
        audit=lambda action, outcome, **fields: h.audit.append((action, outcome, fields)))
    token = h.call(ADMIN, "Parental1", "Unlock", ADULT)
    return runner, token


@pytest.mark.parametrize("method,kind,job", [("Install", "install", "installing"),
                                             ("Remove", "remove", "removing")])
def test_a_module_is_installed_or_removed_by_its_id(h, jobs, method, kind, job):
    runner, token = jobs

    h.call(ADMIN, "Modules1", method, token, "hello")

    assert (runner.started, runner.packages) == ([kind], ["kidux-module-hello"])
    assert h.call(GREETER, "System1", "UpdateState")[:3] == (job, 0.0, "kidux-module-hello")


@pytest.mark.parametrize("method", ["Install", "Remove"])
@pytest.mark.parametrize("bad", ["../hello", "Hello", "kidux-module-hello", "", "hello world",
                                 "hello\nbash", "a" * 33])
def test_anything_but_a_module_id_is_refused(h, jobs, method, bad):
    runner, token = jobs

    with pytest.raises(InvalidArgument):
        h.call(ADMIN, "Modules1", method, token, bad)
    assert runner.started == []


@pytest.mark.parametrize("method", ["Install", "Remove"])
def test_installing_and_removing_need_a_token(h, jobs, method):
    runner, _token = jobs

    with pytest.raises(NotUnlocked):
        h.call(ADMIN, "Modules1", method, "", "hello")
    assert runner.started == []


@pytest.mark.parametrize("method", ["Install", "Remove"])
def test_nothing_is_installed_or_removed_while_a_child_has_a_session(h, jobs, method):
    runner, token = jobs
    h.service.session_appeared(SESSION)
    h.call(ANA, "Access1", "Lock")

    with pytest.raises(SessionActive):
        h.call(ADMIN, "Modules1", method, token, "hello")
    assert runner.started == []


def test_one_job_at_a_time(h, jobs):
    runner, token = jobs
    h.call(ADMIN, "Modules1", "Install", token, "hello")

    with pytest.raises(Busy):
        h.call(ADMIN, "Modules1", "Remove", token, "hello")
    assert runner.started == ["install"]


def test_no_session_starts_while_a_module_is_installed(h, jobs):
    runner, token = jobs
    h.call(ADMIN, "Modules1", "Install", token, "hello")

    assert h.call(GREETER, "Access1", "CheckAccess", "ana") == ("updating", 0)


def test_a_finished_install_is_announced_audited_and_changes_every_list(h, jobs):
    runner, token = jobs
    h.call(ADMIN, "Modules1", "Install", token, "hello")
    with open(runner.status, "a") as handle:
        handle.write("kidux:module:kidux-module-hello\npmstatus:kidux-module-hello:50:Installing\n"
                     "kidux:done:installed\n")
    runner.active = False

    assert h.service.updates.poll() is False
    assert ("System1", "UpdateFinished", "(ss)", ("installed", "")) in h.signals
    assert ("Modules1", "ModulesChanged", "(s)", ("",)) in h.signals
    assert h.call(GREETER, "System1", "UpdateState")[:4] == ("idle", 0.0, "", "installed")
    assert any(entry[0] == "module installed" and entry[1] == "ok"
               and entry[2].get("module") == "hello" for entry in h.audit)


def test_a_failed_remove_says_why(h, jobs):
    runner, token = jobs
    h.call(ADMIN, "Modules1", "Remove", token, "hello")
    with open(runner.status, "a") as handle:
        handle.write("kidux:failed:E: Unable to locate package kidux-module-hello\n")
    runner.active = False

    h.service.updates.poll()
    assert ("System1", "UpdateFinished", "(ss)",
            ("failed", "E: Unable to locate package kidux-module-hello")) in h.signals
    assert any(entry[0] == "module removed" and entry[1] == "failed" for entry in h.audit)


def test_the_status_file_names_the_module_job():
    reading = read("kidux:job:install\nkidux:module:kidux-module-hello\n"
                   "dlstatus:kidux-module-hello:50:Downloading\n")

    assert (reading.job, reading.module) == ("installing", "kidux-module-hello")
    assert 0 < reading.fraction < 0.3
    assert read("kidux:job:remove\nkidux:done:removed\n").verdict == ("removed", "", [])
