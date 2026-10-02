"""systemd-logind, as the daemon uses it.

logind is the authority on who has a session, and the only thing allowed to
turn the machine off. The daemon asks it rather than keeping its own record,
because a record kept by anything a child's session runs can be killed or
edited by the child.
"""

from dataclasses import dataclass
from typing import Protocol

from gi.repository import Gio, GLib

from .errors import Failed

LOGIND = "org.freedesktop.login1"
MANAGER_PATH = "/org/freedesktop/login1"
MANAGER = "org.freedesktop.login1.Manager"


@dataclass(frozen=True)
class SessionInfo:
    session_id: str
    uid: int
    user: str
    seat: str
    path: str
    #: logind's class: "user" for a session someone is in; "manager" for the
    #: user manager logind starts beside it, which outlives it by a few
    #: seconds (UserStopDelaySec) and is nobody being signed in.
    session_class: str = "user"


class Logind(Protocol):
    def sessions(self) -> list[SessionInfo]: ...
    def terminate_user(self, uid: int) -> None: ...
    def power_off(self) -> None: ...
    def reboot(self) -> None: ...


class SystemLogind:
    def __init__(self, connection: Gio.DBusConnection) -> None:
        self._connection = connection

    def _call(self, method: str, arguments=None, reply_type=None):
        try:
            return self._connection.call_sync(
                LOGIND,
                MANAGER_PATH,
                MANAGER,
                method,
                arguments,
                GLib.VariantType(reply_type) if reply_type else None,
                Gio.DBusCallFlags.NONE,
                10_000,
                None,
            )
        except GLib.Error as error:
            raise Failed(f"logind {method} failed: {error.message}") from error

    def sessions(self) -> list[SessionInfo]:
        reply = self._call("ListSessions", None, "(a(susso))")
        return [SessionInfo(*entry, session_class=self._session_class(entry[4]))
                for entry in reply.unpack()[0]]

    def _session_class(self, session_path: str) -> str:
        try:
            reply = self._connection.call_sync(
                LOGIND, session_path, "org.freedesktop.DBus.Properties", "Get",
                GLib.Variant("(ss)", ("org.freedesktop.login1.Session", "Class")),
                GLib.VariantType("(v)"), Gio.DBusCallFlags.NONE, 10_000, None)
        except GLib.Error:
            return ""
        return str(reply.unpack()[0])

    def terminate_user(self, uid: int) -> None:
        """End every session of this user and their user manager, now."""
        self._call("TerminateUser", GLib.Variant("(u)", (uid,)))

    def power_off(self) -> None:
        self._call("PowerOff", GLib.Variant("(b)", (False,)))

    def reboot(self) -> None:
        self._call("Reboot", GLib.Variant("(b)", (False,)))


class FakeLogind:
    def __init__(self) -> None:
        self.open: list[SessionInfo] = []
        self.terminated: list[int] = []
        self.powered_off = False
        self.rebooted = False

    def sessions(self) -> list[SessionInfo]:
        return list(self.open)

    def terminate_user(self, uid: int) -> None:
        self.terminated.append(uid)
        self.open = [session for session in self.open if session.uid != uid]

    def power_off(self) -> None:
        self.powered_off = True

    def reboot(self) -> None:
        self.rebooted = True


def has_session(logind: Logind, uid: int) -> bool:
    """Whether this user is signed in: a session of class "user"."""
    return any(session.uid == uid and session.session_class == "user"
               for session in logind.sessions())


def has_manager(logind: Logind, uid: int) -> bool:
    """Whether logind still holds anything of this user's: their user manager,
    for the seconds after their last session, or a session of any class."""
    return any(session.uid == uid for session in logind.sessions())


class SessionWatcher:
    """Tells the daemon about sessions appearing and disappearing.

    Every session is described the same way, whether it was already running
    when the daemon started or appeared afterwards: id, object path, uid,
    class, scope unit and virtual terminal.
    """

    def __init__(self, connection: Gio.DBusConnection, on_new, on_removed) -> None:
        self._connection = connection
        self._on_new = on_new
        self._on_removed = on_removed
        self._subscriptions: list[int] = []

    def describe(self, session_path: str) -> dict | None:
        try:
            reply = self._connection.call_sync(
                LOGIND,
                session_path,
                "org.freedesktop.DBus.Properties",
                "GetAll",
                GLib.Variant("(s)", ("org.freedesktop.login1.Session",)),
                GLib.VariantType("(a{sv})"),
                Gio.DBusCallFlags.NONE,
                10_000,
                None,
            )
        except GLib.Error:
            return None
        properties = reply.unpack()[0]
        return {
            "id": properties.get("Id", ""),
            "path": session_path,
            "uid": int(properties.get("User", (0, ""))[0]),
            "class": properties.get("Class", ""),
            "scope": properties.get("Scope", ""),
            "vtnr": int(properties.get("VTNr", 0)),
        }

    def existing(self) -> list[dict]:
        found = []
        for session in SystemLogind(self._connection).sessions():
            description = self.describe(session.path)
            if description is not None:
                found.append(description)
        return found

    def start(self) -> None:
        for signal, handler in (
            ("SessionNew", self._new),
            ("SessionRemoved", self._removed),
        ):
            self._subscriptions.append(
                self._connection.signal_subscribe(
                    LOGIND, MANAGER, signal, MANAGER_PATH, None,
                    Gio.DBusSignalFlags.NONE, handler,
                )
            )

    def _new(self, connection, sender, path, interface, signal, parameters) -> None:
        _session_id, session_path = parameters.unpack()
        description = self.describe(session_path)
        if description is not None:
            self._on_new(description)

    def _removed(self, connection, sender, path, interface, signal, parameters) -> None:
        session_id, _session_path = parameters.unpack()
        self._on_removed(session_id)
