"""A call whose sender left before the daemon could ask the bus who it was,
as happens when a session ends: answered quietly, never as a failure."""

import logging

from gi.repository import GLib

from kiduxd import bus


class GoneConnection:
    """A bus that no longer knows the sender."""

    def call_sync(self, *args):
        raise GLib.GError.new_literal(
            GLib.quark_from_string("g-dbus-error-quark"),
            "GDBus.Error:org.freedesktop.DBus.Error.NameHasNoOwner: "
            "Could not get UID of name ':1.80': no such name", 3)


class Invocation:
    def __init__(self):
        self.errors = []

    def return_dbus_error(self, name, text):
        self.errors.append(name)


class Service:
    def __init__(self):
        self.asked = []

    def dispatch(self, *args):
        self.asked.append(args)


def test_a_caller_gone_before_it_was_answered_is_no_failure(caplog):
    obj = bus.BusObject.__new__(bus.BusObject)
    obj._connection, obj._service = GoneConnection(), Service()
    invocation = Invocation()

    with caplog.at_level(logging.INFO):
        obj._on_method_call(None, ":1.80", "/org/kidux/Daemon1", "org.kidux.Daemon1",
                            "Ping", GLib.Variant("()", ()), invocation)

    assert obj._service.asked == []
    assert invocation.errors == ["org.kidux.Daemon1.Error.Failed"]
    assert "gone before it was answered" in caplog.text
    assert "Traceback" not in caplog.text and "failed" not in caplog.text
