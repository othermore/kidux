"""What the launcher asks kidux-daemon: its own time, its modules, a lock.

The three things a child may ask for (polkit's `self` action, D27). Signals
are subscribed on the bus name, so they arrive again by themselves after the
daemon restarts.
"""

from gi.repository import Gio

from kidux import client as kidux_client
from kidux import paths
from kidux.client import DaemonError, DaemonUnavailableError

__all__ = ["DaemonError", "DaemonUnavailableError", "SystemDaemon"]


class SystemDaemon:
    def __init__(self, username: str) -> None:
        self._username = username
        self._client = kidux_client.Client()

    def usage(self) -> tuple[int, int]:
        return self._client.usage(self._username)

    def modules(self) -> list[str]:
        """The ids of the modules enabled for this child, in the daemon's order."""
        return [str(entry.get("id")) for entry in self._client.list_modules(self._username)
                if entry.get("enabled")]

    def module_settings(self, module_id: str) -> dict:
        """What an adult set in a module for this child (D90), never a
        secret."""
        return self._client.my_module_settings(module_id)

    def lock(self) -> None:
        self._client.request_lock()

    def lock_for(self, reason: str) -> None:
        """Lock the session for `reason`, `lid` or `idle` (D67)."""
        self._client.request_lock_for(reason)

    def subscribe(self, *, warning, changed) -> bool:
        """`warning(seconds_left)` on TimeWarning; `changed()` on anything that
        changes what the launcher shows: a lock, an unlock, the modules."""
        try:
            connection = self._client.connection
        except DaemonUnavailableError:
            return False

        def mine(handler):
            def on_signal(_c, _s, _p, _i, _n, parameters):
                values = parameters.unpack()
                if values and values[0] == self._username:
                    handler(*values[1:])
            return on_signal

        for interface, name, handler in (
            ("Access1", "TimeWarning", lambda seconds: warning(seconds)),
            ("Access1", "Locked", lambda _reason: changed()),
            ("Access1", "Unlocked", lambda: changed()),
            ("Modules1", "ModulesChanged", lambda: changed()),
        ):
            connection.signal_subscribe(
                paths.BUS_NAME, f"{paths.BUS_NAME}.{interface}", name, paths.OBJECT_PATH,
                None, Gio.DBusSignalFlags.NONE, mine(handler))
        return True
