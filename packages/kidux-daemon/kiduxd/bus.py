"""The D-Bus side of the daemon: values in, values out, errors across.

Nothing here decides anything. It unpacks a call, asks the bus who is calling,
hands both to `Service.dispatch`, and packs whatever comes back according to
the introspection XML. A `DaemonError` becomes its D-Bus error; anything else
becomes `Failed` with the details in the journal and none on the wire.
"""

import threading
from importlib import resources

from gi.repository import Gio, GLib

from kidux import paths
from kidux.log import get_logger

from . import VERSION
from .errors import DaemonError, Failed
from .gate import Caller
from .service import Later, Service

_log = get_logger("bus")

DBUS = "org.freedesktop.DBus"


def introspection_xml() -> str:
    return resources.files("kiduxd").joinpath("org.kidux.Daemon1.xml").read_text()


def short_interface(name: str) -> str:
    """'org.kidux.Daemon1.Children1' -> 'Children1'; the daemon's own -> 'Daemon1'."""
    if name == paths.BUS_NAME:
        return "Daemon1"
    return name[len(paths.BUS_NAME) + 1 :]


def to_variant_value(value) -> GLib.Variant:
    """A Python value as the variant inside an a{sv}."""
    if isinstance(value, GLib.Variant):
        return value
    if isinstance(value, bool):
        return GLib.Variant("b", value)
    if isinstance(value, int):
        return GLib.Variant("i", value)
    if isinstance(value, float):
        return GLib.Variant("d", value)
    if isinstance(value, str):
        return GLib.Variant("s", value)
    if isinstance(value, (list, tuple)) and value and all(isinstance(v, bool) for v in value):
        return GLib.Variant("ab", list(value))
    if isinstance(value, (list, tuple)) and all(isinstance(v, str) for v in value):
        return GLib.Variant("as", list(value))
    raise TypeError(f"no D-Bus type for {type(value).__name__}")


def pack(signature: str, value):
    """A Python result as the Python structure GLib.Variant wants for `signature`."""
    if signature == "a{sv}":
        return {key: to_variant_value(v) for key, v in value.items()}
    if signature == "aa{sv}":
        return [pack("a{sv}", entry) for entry in value]
    return value


class BusObject:
    def __init__(self, connection: Gio.DBusConnection, service: Service) -> None:
        self._connection = connection
        self._service = service
        self._node = Gio.DBusNodeInfo.new_for_xml(introspection_xml())
        self._registrations: list[int] = []
        self._subscription = 0

    def register(self) -> None:
        for interface in self._node.interfaces:
            self._registrations.append(
                self._connection.register_object(
                    paths.OBJECT_PATH,
                    interface,
                    self._on_method_call,
                    self._on_get_property,
                    None,
                )
            )
        self._subscription = self._connection.signal_subscribe(
            DBUS,
            DBUS,
            "NameOwnerChanged",
            "/org/freedesktop/DBus",
            None,
            Gio.DBusSignalFlags.NONE,
            self._on_name_owner_changed,
        )

    def emit(self, interface: str, signal: str, signature: str, args: tuple) -> None:
        full = paths.BUS_NAME if interface == "Daemon1" else f"{paths.BUS_NAME}.{interface}"
        self._connection.emit_signal(
            None,
            paths.OBJECT_PATH,
            full,
            signal,
            GLib.Variant(signature, args) if args else None,
        )

    # --- incoming ------------------------------------------------------------

    def _caller_uid(self, sender: str) -> int:
        reply = self._connection.call_sync(
            DBUS,
            "/org/freedesktop/DBus",
            DBUS,
            "GetConnectionUnixUser",
            GLib.Variant("(s)", (sender,)),
            GLib.VariantType("(u)"),
            Gio.DBusCallFlags.NONE,
            5_000,
            None,
        )
        return reply.unpack()[0]

    def _on_method_call(
        self, connection, sender, object_path, interface_name, method_name, parameters, invocation
    ) -> None:
        interface = short_interface(interface_name)
        try:
            caller = Caller(sender, self._caller_uid(sender))
            result = self._service.dispatch(caller, interface, method_name, *parameters.unpack())
        except DaemonError as error:
            invocation.return_dbus_error(error.dbus_name, str(error))
            return
        except Exception:
            _log.exception("%s.%s failed", interface, method_name)
            invocation.return_dbus_error(Failed().dbus_name, "internal error")
            return

        method = self._node.lookup_interface(interface_name).lookup_method(method_name)
        out = [arg.signature for arg in method.out_args]
        if isinstance(result, Later):
            self._answer_later(invocation, interface, method_name, out, result)
            return
        self._answer(invocation, out, result)

    def _answer_later(self, invocation, interface, method_name, out, later: Later) -> None:
        """Run `later`'s work in a thread, and answer from the main loop."""
        def work() -> None:
            try:
                value = later.work()
            except DaemonError as error:
                name, text = error.dbus_name, str(error)
                GLib.idle_add(lambda: invocation.return_dbus_error(name, text) and False)
                return
            except Exception:
                _log.exception("%s.%s failed", interface, method_name)
                GLib.idle_add(lambda: invocation.return_dbus_error(Failed().dbus_name,
                                                                   "internal error") and False)
                return
            GLib.idle_add(lambda: self._answer(invocation, out, value) and False)

        threading.Thread(target=work, name=f"{interface}.{method_name}", daemon=True).start()

    def _answer(self, invocation, out, result) -> None:
        if not out:
            invocation.return_value(None)
        elif len(out) == 1:
            invocation.return_value(GLib.Variant(f"({out[0]})", (pack(out[0], result),)))
        else:
            packed = tuple(pack(sig, value) for sig, value in zip(out, result))
            invocation.return_value(GLib.Variant(f"({''.join(out)})", packed))

    def _on_get_property(self, connection, sender, object_path, interface_name, property_name):
        if property_name == "Version":
            return GLib.Variant("s", VERSION)
        return None

    def _on_name_owner_changed(
        self, connection, sender, path, interface, signal, parameters
    ) -> None:
        name, old_owner, new_owner = parameters.unpack()
        if name.startswith(":") and old_owner and not new_owner:
            self._service.connection_closed(name)
