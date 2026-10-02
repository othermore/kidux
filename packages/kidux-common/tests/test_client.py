"""Tests for the D-Bus client, against a stand-in daemon.

The real daemon arrives in step 9.3. These run against a mock on a private
system bus, which is enough to prove the thing worth proving now: that the
client speaks the protocol written down in the phase 1 plan, section 7. If the
client and the daemon disagree about an argument or a return type, the mistake
is found here rather than on a screen a child is sitting in front of.

The private bus matters. Nothing here touches the machine's real system bus,
so the tests run the same on a developer's laptop, in the build chroot and in
CI, and cannot be affected by a daemon that happens to be installed.
"""

import subprocess

import pytest

dbus = pytest.importorskip("dbus")
dbusmock = pytest.importorskip("dbusmock")

from kidux import client, paths  # noqa: E402  (after the skip checks)

MOCK_INTERFACE = "org.freedesktop.DBus.Mock"


@pytest.fixture(scope="module")
def system_bus():
    dbusmock.DBusTestCase.start_system_bus()
    yield
    # tearDownClass is what stops the buses start_system_bus started.
    dbusmock.DBusTestCase.tearDownClass()


@pytest.fixture
def daemon(system_bus):
    """A stand-in for org.kidux.Daemon1 with the methods each test needs."""
    process = dbusmock.DBusTestCase.spawn_server(
        paths.BUS_NAME,
        paths.OBJECT_PATH,
        paths.BUS_NAME,
        system_bus=True,
        stdout=subprocess.PIPE,
    )

    connection = dbusmock.DBusTestCase.get_dbus(system_bus=True)
    mock = dbus.Interface(
        connection.get_object(paths.BUS_NAME, paths.OBJECT_PATH),
        MOCK_INTERFACE,
    )

    yield mock

    process.terminate()
    process.wait()


def add_method(mock, interface, name, in_signature, out_signature, code):
    mock.AddMethod(interface, name, in_signature, out_signature, code)


def test_ping_returns_the_daemon_version(daemon):
    add_method(daemon, paths.BUS_NAME, "Ping", "", "s", "ret = '0.1.0'")

    assert client.Client().ping() == "0.1.0"


def test_is_password_set_on_a_fresh_machine(daemon):
    # False is what sends the first-run wizard to the front instead of the
    # sign-in screen, so getting the type wrong here would hide the wizard.
    add_method(daemon, f"{paths.BUS_NAME}.Parental1", "IsPasswordSet", "", "b", "ret = False")

    assert client.Client().is_password_set() is False


def test_unlock_passes_the_password_and_returns_a_token(daemon):
    add_method(
        daemon,
        f"{paths.BUS_NAME}.Parental1",
        "Unlock",
        "s",
        "s",
        "ret = 'token-for-' + args[0]",
    )

    assert client.Client().unlock("a good password") == "token-for-a good password"


def test_check_access_returns_a_state_and_the_seconds_left(daemon):
    add_method(
        daemon,
        f"{paths.BUS_NAME}.Access1",
        "CheckAccess",
        "s",
        "si",
        "ret = ('allowed', 1800)",
    )

    state, seconds = client.Client().check_access("ana")

    assert state == "allowed"
    assert seconds == 1800


def test_check_access_reports_an_unlimited_child_as_minus_one(daemon):
    # -1 rather than a large number, so a screen can tell "no limit" from "a
    # very long time" without guessing a threshold.
    add_method(
        daemon,
        f"{paths.BUS_NAME}.Access1",
        "CheckAccess",
        "s",
        "si",
        "ret = ('allowed', -1)",
    )

    assert client.Client().check_access("ana")[1] == -1


def test_check_access_reports_a_spent_allowance(daemon):
    # Distinct from a wrong password, which is the whole reason the greeter
    # calls this only after the password has been accepted.
    add_method(
        daemon,
        f"{paths.BUS_NAME}.Access1",
        "CheckAccess",
        "s",
        "si",
        "ret = ('blocked', 0)",
    )

    assert client.Client().check_access("ana")[0] == "blocked"


def test_usage_returns_used_and_available(daemon):
    add_method(
        daemon,
        f"{paths.BUS_NAME}.Access1",
        "Usage",
        "s",
        "ui",
        "ret = (1200, 600)",
    )

    used, available = client.Client().usage("ana")

    assert used == 1200
    assert available == 600


def test_list_children_comes_back_as_dictionaries(daemon):
    add_method(
        daemon,
        f"{paths.BUS_NAME}.Children1",
        "List",
        "",
        "aa{sv}",
        "ret = [{'username': 'ana', 'display_name': 'Ana', 'avatar': 'fox'}]",
    )

    children = client.Client().list_children()

    assert children[0]["username"] == "ana"
    assert children[0]["avatar"] == "fox"


def test_modules_come_back_as_dictionaries(daemon):
    add_method(daemon, f"{paths.BUS_NAME}.Modules1", "List", "s", "aa{sv}",
               "ret = [{'id': 'hello', 'enabled': True}]")

    assert client.Client().list_modules("ana") == [{"id": "hello", "enabled": True}]


def test_a_module_is_switched_with_the_token(daemon):
    add_method(daemon, f"{paths.BUS_NAME}.Modules1", "SetEnabled", "sssb", "", "")

    client.Client().set_module_enabled("token", "ana", "hello", True)

    calls = daemon.GetMethodCalls("SetEnabled")
    assert [list(call[1]) for call in calls] == [["token", "ana", "hello", True]]


def test_lock_takes_no_arguments_and_returns_nothing(daemon):
    # The launcher's Lock button, and what the daemon does by itself when time
    # runs out. A child never needs a password to lock the screen.
    add_method(daemon, f"{paths.BUS_NAME}.Access1", "Lock", "", "", "")

    assert client.Client().request_lock() is None


def test_a_refused_call_raises_permission_denied(daemon):
    add_method(
        daemon,
        f"{paths.BUS_NAME}.Parental1",
        "SetPassword",
        "ss",
        "",
        "raise dbus.exceptions.DBusException("
        "'not authorized', name='org.freedesktop.DBus.Error.AccessDenied')",
    )

    with pytest.raises(client.PermissionDeniedError):
        client.Client().set_adult_password("a token", "a new password")


def test_an_absent_daemon_raises_unavailable(system_bus):
    # No daemon fixture: nothing is on the bus. A screen has to be able to tell
    # this apart from a refusal, because the answer for a family is "wait a
    # moment" rather than "something is broken".
    with pytest.raises(client.DaemonUnavailableError):
        client.Client(timeout_ms=2000).ping()
