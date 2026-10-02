"""The daemon on a real bus: the protocol, the errors, and the tokens' binding.

A private system bus from python3-dbusmock, dbusmock's polkitd template in
front of it, and the daemon's own code in a subprocess with only adduser and
logind stood in for. This is where the D-Bus types, the error names and "a
token from another connection" are proven, because those only exist on a bus.
"""

import os
import subprocess
import sys
from pathlib import Path

import pytest
from gi.repository import Gio, GLib

dbusmock = pytest.importorskip("dbusmock")

from kidux import paths  # noqa: E402
from kiduxd import VERSION  # noqa: E402
from kiduxd.adults import AdultPassword  # noqa: E402

ADULT_PASSWORD = "a family secret"
HERE = Path(__file__).resolve().parent


@pytest.fixture(scope="module")
def system_bus():
    dbusmock.DBusTestCase.start_system_bus()
    yield os.environ["DBUS_SYSTEM_BUS_ADDRESS"]
    dbusmock.DBusTestCase.tearDownClass()


@pytest.fixture
def polkit(system_bus):
    process, mock = dbusmock.DBusTestCase.spawn_server_template(
        "polkitd", {}, stdout=subprocess.DEVNULL
    )
    mock.AllowUnknown(True, dbus_interface=dbusmock.MOCK_IFACE)
    yield mock
    process.terminate()
    process.wait()


@pytest.fixture
def daemon(polkit, fast_hasher, tmp_path):
    AdultPassword(fast_hasher).set(ADULT_PASSWORD)
    log_file = (tmp_path / "daemon.log").open("w")
    process = subprocess.Popen(
        [sys.executable, str(HERE / "fake_daemon.py")],
        stdout=log_file,
        stderr=subprocess.STDOUT,
        env=os.environ.copy(),
    )
    try:
        dbusmock.DBusTestCase.wait_for_bus_object(
            paths.BUS_NAME, paths.OBJECT_PATH, system_bus=True, timeout=100
        )
        yield process
    finally:
        process.terminate()
        process.wait()
        log_file.close()


def connect(address: str) -> Gio.DBusConnection:
    """A connection of its own, as the panel or a second process would have."""
    return Gio.DBusConnection.new_for_address_sync(
        address,
        Gio.DBusConnectionFlags.AUTHENTICATION_CLIENT
        | Gio.DBusConnectionFlags.MESSAGE_BUS_CONNECTION,
        None,
        None,
    )


def call(connection, interface, method, signature=None, args=None, reply=None):
    full = paths.BUS_NAME if interface == "Daemon1" else f"{paths.BUS_NAME}.{interface}"
    result = connection.call_sync(
        paths.BUS_NAME,
        paths.OBJECT_PATH,
        full,
        method,
        GLib.Variant(signature, args) if signature else None,
        GLib.VariantType(reply) if reply else None,
        Gio.DBusCallFlags.NONE,
        10_000,
        None,
    )
    return result.unpack() if result is not None else None


def error_name(error: GLib.Error) -> str:
    return Gio.DBusError.get_remote_error(error)


def unlock(connection) -> str:
    return call(connection, "Parental1", "Unlock", "(s)", (ADULT_PASSWORD,), "(s)")[0]


def create(connection, token, username="marta"):
    call(
        connection,
        "Children1",
        "Create",
        "(sssssss)",
        (token, username, "Marta", "es_ES.UTF-8", "es", "owl", "marta's password"),
    )


def test_ping(system_bus, daemon):
    assert call(connect(system_bus), "Daemon1", "Ping", reply="(s)") == (VERSION,)


def test_the_version_property(system_bus, daemon):
    connection = connect(system_bus)
    reply = connection.call_sync(
        paths.BUS_NAME, paths.OBJECT_PATH, "org.freedesktop.DBus.Properties", "Get",
        GLib.Variant("(ss)", (paths.BUS_NAME, "Version")), GLib.VariantType("(v)"),
        Gio.DBusCallFlags.NONE, 5_000, None,
    )
    assert reply.unpack()[0] == VERSION


def test_get_config_is_a_dictionary_of_variants(system_bus, daemon):
    (config,) = call(connect(system_bus), "Daemon1", "GetConfig", reply="(a{sv})")

    assert config["reset_hour"] == 4
    assert config["setup_complete"] is False
    assert isinstance(config["display_scale"], float)


def test_create_a_child_over_the_bus(system_bus, daemon):
    connection = connect(system_bus)
    token = unlock(connection)
    create(connection, token)

    (children,) = call(connection, "Children1", "List", reply="(aa{sv})")
    names = {entry["username"]: entry for entry in children}
    assert names["marta"]["display_name"] == "Marta"
    assert names["marta"]["avatar"] == "owl"
    assert names["marta"]["mode"] == "manual"


def test_a_token_is_useless_on_another_connection(system_bus, daemon):
    token = unlock(connect(system_bus))

    with pytest.raises(GLib.Error) as raised:
        create(connect(system_bus), token)

    assert error_name(raised.value) == "org.kidux.Daemon1.Error.NotUnlocked"


def test_closing_the_panel_locks_it(system_bus, daemon):
    connection = connect(system_bus)
    unlock(connection)
    connection.close_sync(None)

    # The daemon hears NameOwnerChanged and audits the lock; give it a moment.
    for _ in range(50):
        if paths.AUDIT_LOG.exists() and "connection closed" in paths.AUDIT_LOG.read_text():
            break
        subprocess.run(["sleep", "0.1"])
    assert "connection closed" in paths.AUDIT_LOG.read_text()


def test_a_wrong_password_has_its_own_error(system_bus, daemon):
    with pytest.raises(GLib.Error) as raised:
        call(connect(system_bus), "Parental1", "Unlock", "(s)", ("a guess",), "(s)")

    assert error_name(raised.value) == "org.kidux.Daemon1.Error.WrongPassword"
    assert "a guess" not in str(raised.value)


def test_polkit_saying_no_is_access_denied(system_bus, daemon, polkit):
    polkit.AllowUnknown(False, dbus_interface=dbusmock.MOCK_IFACE)

    with pytest.raises(GLib.Error) as raised:
        call(connect(system_bus), "Children1", "List", reply="(aa{sv})")

    assert error_name(raised.value) == "org.freedesktop.DBus.Error.AccessDenied"


def test_polkit_saying_no_still_lets_anyone_ping(system_bus, daemon, polkit):
    polkit.AllowUnknown(False, dbus_interface=dbusmock.MOCK_IFACE)

    assert call(connect(system_bus), "Daemon1", "Ping", reply="(s)") == (VERSION,)


def test_the_administrator_cannot_be_deleted_over_the_bus(system_bus, daemon):
    connection = connect(system_bus)
    token = unlock(connection)

    with pytest.raises(GLib.Error) as raised:
        call(connection, "Children1", "Delete", "(ssb)", (token, "admin", False))

    assert error_name(raised.value) == "org.kidux.Daemon1.Error.NoSuchChild"


def test_the_client_speaks_every_call_the_panel_makes(system_bus, daemon):
    # kidux.client and the daemon are two packages; this is where they are
    # proven to agree on every argument and reply the panel and the wizard use.
    from kidux.client import Client

    panel = Client()
    token = panel.unlock(ADULT_PASSWORD)

    panel.set_config(token, {"default_language": "es_ES.UTF-8", "display_scale": 1.5})
    config = panel.config()
    assert (config["default_language"], config["display_scale"]) == ("es_ES.UTF-8", 1.5)
    assert config["language_chosen"] is True
    panel.set_config(token, {"chromium_flags": ["--disable-gpu-compositing"]})
    assert panel.config()["chromium_flags"] == ["--disable-gpu-compositing"]

    panel.create_child(token, "marta", "Marta", "es_ES.UTF-8", "es", "owl", "a password")
    panel.set_profile(token, "marta", {"display_name": "Martita", "age": 7})
    panel.set_policy(token, "marta", "daily", 45, [False] * 7)
    assert panel.policy("marta")["days"] == [False] * 7
    assert panel.check_access("marta") == ("day_off", 0)
    panel.set_policy(token, "marta", "daily", 45, [True] * 7)
    panel.grant(token, "marta", 15)
    assert panel.policy("marta") == {"mode": "daily", "daily_minutes": 45, "granted_seconds": 900,
                                     "days": [True] * 7}
    assert panel.check_access("marta") == ("allowed", 3600)
    assert panel.usage("marta") == (0, 3600)
    panel.set_time_left(token, "marta", 5)
    assert panel.usage("marta") == (0, 300)

    assert isinstance(panel.recovery_password(token), str)
    panel.set_child_password(token, "marta", "another one")
    panel.delete_child(token, "marta", False)
    assert "marta" not in {c["username"] for c in panel.list_children()}
    panel.lock(token)
