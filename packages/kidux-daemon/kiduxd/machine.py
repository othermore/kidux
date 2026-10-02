"""systemd and logind, as the lock needs them (the real `locker.Machine`)."""

import subprocess

from gi.repository import Gio, GLib

from .errors import Busy, Failed
from .locker import LOCK_VT
from .updates import SCRIPT, STATUS, UNIT

SYSTEMD = "org.freedesktop.systemd1"
SYSTEMD_PATH = "/org/freedesktop/systemd1"
SYSTEMD_MANAGER = "org.freedesktop.systemd1.Manager"

LOGIND = "org.freedesktop.login1"
LOGIND_PATH = "/org/freedesktop/login1"
LOGIND_MANAGER = "org.freedesktop.login1.Manager"
SESSION = "org.freedesktop.login1.Session"
SEAT = "org.freedesktop.login1.Seat"
SEAT0 = "/org/freedesktop/login1/seat/seat0"

TIMEOUT_MS = 10_000


def locker_unit(username: str) -> str:
    return f"kidux-locker@{username}.service"


class SystemMachine:
    def __init__(self, connection: Gio.DBusConnection) -> None:
        self._connection = connection

    def _call(self, name, path, interface, method, arguments=None, reply=None):
        try:
            result = self._connection.call_sync(
                name,
                path,
                interface,
                method,
                arguments,
                GLib.VariantType(reply) if reply else None,
                Gio.DBusCallFlags.NONE,
                TIMEOUT_MS,
                None,
            )
        except GLib.Error as error:
            raise Failed(f"{method} failed: {error.message}") from error
        return result.unpack() if result is not None else None

    def _session_property(self, session_path: str, name: str):
        value = self._call(
            LOGIND,
            session_path,
            "org.freedesktop.DBus.Properties",
            "Get",
            GLib.Variant("(ss)", (SESSION, name)),
            "(v)",
        )
        return value[0]

    # --- the lock screen's unit ------------------------------------------------

    def start_locker(self, username: str) -> None:
        self._call(
            SYSTEMD, SYSTEMD_PATH, SYSTEMD_MANAGER, "StartUnit",
            GLib.Variant("(ss)", (locker_unit(username), "replace")), "(o)",
        )

    def stop_locker(self, username: str) -> None:
        self._call(
            SYSTEMD, SYSTEMD_PATH, SYSTEMD_MANAGER, "StopUnit",
            GLib.Variant("(ss)", (locker_unit(username), "replace")), "(o)",
        )

    def locker_ready(self) -> bool:
        """True once logind shows a greeter-class session on the lock screen's terminal."""
        sessions = self._call(LOGIND, LOGIND_PATH, LOGIND_MANAGER, "ListSessions",
                              None, "(a(susso))")[0]
        for _id, _uid, _user, _seat, path in sessions:
            try:
                if (
                    self._session_property(path, "Class") == "greeter"
                    and self._session_property(path, "VTNr") == LOCK_VT
                ):
                    return True
            except Failed:
                continue
        return False

    # --- the seat and the session ----------------------------------------------

    def switch_to(self, vt: int) -> None:
        self._call(LOGIND, SEAT0, SEAT, "SwitchTo", GLib.Variant("(u)", (vt,)))

    def session_active(self, session_path: str) -> bool:
        return bool(self._session_property(session_path, "Active"))

    def terminate(self, session_path: str) -> None:
        self._call(LOGIND, session_path, SESSION, "Terminate")

    def stop_scope(self, scope: str) -> None:
        self._call(SYSTEMD, SYSTEMD_PATH, SYSTEMD_MANAGER, "StopUnit",
                   GLib.Variant("(ss)", (scope, "replace")), "(o)")

    def wake_input(self) -> None:
        """A change event on every input device, so that a compositor that
        has just resumed reads its device queue now rather than on the
        child's first key (locker.py, `unlock`)."""
        subprocess.run(["udevadm", "trigger", "--subsystem-match=input", "--action=change"],
                       check=True, timeout=10, capture_output=True)

    def session_closing(self, session_path: str) -> bool:
        """Whether logind is ending this session: its leader has gone, and
        what is left of it is still running. False for one that is gone."""
        try:
            return self._session_property(session_path, "State") == "closing"
        except Failed:
            return False

    # --- freezing --------------------------------------------------------------

    def freeze(self, scope: str) -> None:
        self._call(SYSTEMD, SYSTEMD_PATH, SYSTEMD_MANAGER, "FreezeUnit",
                   GLib.Variant("(s)", (scope,)))

    def thaw(self, scope: str) -> None:
        self._call(SYSTEMD, SYSTEMD_PATH, SYSTEMD_MANAGER, "ThawUnit",
                   GLib.Variant("(s)", (scope,)))

    # --- updates (daemon.md section 13) ----------------------------------------

    def start_update(self, kind: str, package: str = "") -> None:
        """Run `kidux-update <kind> [package]` in a transient unit of its own.

        Outside the daemon's walls, which keep it off the network and the
        system read-only, and outside its cgroup, so that an update that
        restarts the daemon does not take the job down with it. The fixed
        name is what makes two jobs at once impossible.
        """
        properties = [
            ("Description", GLib.Variant("s", "Kidux update")),
            ("ExecStart", GLib.Variant("a(sasb)", [(SCRIPT, [SCRIPT, kind]
                                                    + ([package] if package else []), False)])),
            ("Environment", GLib.Variant("as", [f"KIDUX_UPDATE_STATUS={STATUS}"])),
            ("CollectMode", GLib.Variant("s", "inactive-or-failed")),
        ]
        try:
            self._call(SYSTEMD, SYSTEMD_PATH, SYSTEMD_MANAGER, "StartTransientUnit",
                       GLib.Variant("(ssa(sv)a(sa(sv)))", (UNIT, "fail", properties, [])), "(o)")
        except Failed as error:
            if "exists" in str(error) or "already" in str(error):
                raise Busy("an update is already running") from error
            raise

    def modules_offered(self) -> tuple[str, str]:
        """What apt's lists and dpkg say about the module packages, for
        catalogue.available: read only, from the lists as they are."""
        search = subprocess.run(["apt-cache", "search", "--names-only", "--full",
                                 "^kidux-module-"],
                                capture_output=True, text=True, timeout=60)
        installed = subprocess.run(["dpkg-query", "-W", "-f",
                                    "${Package} ${Version} ${db:Status-Status}\n",
                                    "kidux-module-*"],
                                   capture_output=True, text=True, timeout=60)
        return search.stdout, installed.stdout

    def kidux_packages(self) -> str:
        """What dpkg says about every Kidux package, for the versions the
        screens show: one "package version status" a line."""
        done = subprocess.run(["dpkg-query", "-W", "-f",
                               "${Package} ${Version} ${db:Status-Status}\n",
                               "kidux-*", "python3-kidux"],
                              capture_output=True, text=True, timeout=60)
        return done.stdout

    def update_active(self) -> bool:
        try:
            path = self._call(SYSTEMD, SYSTEMD_PATH, SYSTEMD_MANAGER, "GetUnit",
                              GLib.Variant("(s)", (UNIT,)), "(o)")[0]
            state = self._call(SYSTEMD, path, "org.freedesktop.DBus.Properties", "Get",
                               GLib.Variant("(ss)", ("org.freedesktop.systemd1.Unit",
                                                     "ActiveState")), "(v)")[0]
        except Failed:
            return False
        return state in ("active", "activating", "deactivating", "reloading")
