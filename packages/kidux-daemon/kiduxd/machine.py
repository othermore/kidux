"""systemd and logind, as the lock needs them (the real `locker.Machine`)."""

import subprocess

from gi.repository import Gio, GLib

from .errors import Busy, Failed
from .locker import LOCK_VT
from .updates import (DAILY, RUNNING, SCRIPT, STATUS, UNIT, UNIT_GONE, UNIT_RUNNING,
                      UNIT_UNKNOWN)

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
#: How long the question about an update's unit waits for systemd: it is
#: asked from the daemon's main loop, which answers the lock, the time and
#: the sign-in, every half second while a job runs, and a job systemd does
#: not answer about is asked about again (D124). A call in flight while
#: systemd re-executes itself fails with NoReply after some 0.4 seconds,
#: and the next one is answered (update-watch-plan.md, section 1). The
#: daily upgrade's questions, asked once at a sign-in or a log-out, wait
#: TIMEOUT_MS: their true answer is worth the wait.
WATCH_TIMEOUT_MS = 1_000
#: The one answer that says a unit is gone, as against not answering.
NO_SUCH_UNIT = "org.freedesktop.systemd1.NoSuchUnit"


def locker_unit(username: str) -> str:
    return f"kidux-locker@{username}.service"


class SystemMachine:
    def __init__(self, connection: Gio.DBusConnection) -> None:
        self._connection = connection

    def _call(self, name, path, interface, method, arguments=None, reply=None,
              timeout_ms=TIMEOUT_MS):
        """The call's answer, or Failed with `remote`, the name of the D-Bus
        error that came back over the bus, from the other side or from the
        bus itself (NoReply when the other side left without answering);
        empty when no error came back over the bus: the call's own timeout,
        the bus gone."""
        try:
            result = self._connection.call_sync(
                name,
                path,
                interface,
                method,
                arguments,
                GLib.VariantType(reply) if reply else None,
                Gio.DBusCallFlags.NONE,
                timeout_ms,
                None,
            )
        except GLib.Error as error:
            failed = Failed(f"{method} failed: {error.message}")
            failed.remote = Gio.DBusError.get_remote_error(error) or ""
            raise failed from error
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

    def _unit_property(self, path: str, interface: str, name: str,
                       timeout_ms: int = TIMEOUT_MS):
        return self._call(SYSTEMD, path, "org.freedesktop.DBus.Properties", "Get",
                          GLib.Variant("(ss)", (f"org.freedesktop.systemd1.{interface}", name)),
                          "(v)", timeout_ms)[0]

    def update_unit(self) -> str:
        """What systemd says of the update's unit: UNIT_RUNNING, UNIT_GONE
        when it has no such unit or the unit has stopped, or UNIT_UNKNOWN
        when it does not answer (D124)."""
        try:
            path = self._call(SYSTEMD, SYSTEMD_PATH, SYSTEMD_MANAGER, "GetUnit",
                              GLib.Variant("(s)", (UNIT,)), "(o)", WATCH_TIMEOUT_MS)[0]
            state = self._unit_property(path, "Unit", "ActiveState", WATCH_TIMEOUT_MS)
        except Failed as error:
            return UNIT_GONE if getattr(error, "remote", "") == NO_SUCH_UNIT else UNIT_UNKNOWN
        return UNIT_RUNNING if state in RUNNING else UNIT_GONE

    def daily_upgrade_state(self) -> tuple[str, str] | None:
        """Debian's daily upgrade's state and its last run's result, `exec-condition`
        for one its condition skipped; empty where systemd has no such unit;
        None when systemd does not answer within TIMEOUT_MS, which a child's
        sign-in takes as an upgrade that may be running (D124)."""
        try:
            path = self._call(SYSTEMD, SYSTEMD_PATH, SYSTEMD_MANAGER, "LoadUnit",
                              GLib.Variant("(s)", (DAILY,)), "(o)")[0]
            if self._unit_property(path, "Unit", "LoadState") != "loaded":
                return ("", "")
            return (self._unit_property(path, "Unit", "ActiveState"),
                    self._unit_property(path, "Service", "Result"))
        except Failed:
            return None

    def start_daily_upgrade(self) -> None:
        self._call(SYSTEMD, SYSTEMD_PATH, SYSTEMD_MANAGER, "StartUnit",
                   GLib.Variant("(ss)", (DAILY, "replace")), "(o)")
