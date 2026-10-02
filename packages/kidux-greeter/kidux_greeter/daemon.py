"""What the sign-in and lock screens ask kidux-daemon, behind a protocol.

`flow.py` only ever talks to `Daemon`, so its tests hand it a fake. The real
one goes through `kidux.client.Client`, as `_greetd`, which polkit's `screens`
action allows (docs/dev/daemon.md, section 2).
"""

from typing import Protocol

from gi.repository import Gio, GLib

from kidux import client as kidux_client
from kidux import paths
from kidux.client import DaemonError, DaemonUnavailableError

__all__ = ["Busy", "Daemon", "DaemonError", "DaemonUnavailableError", "Invalid", "NoTimeLeft",
           "NotUnlocked", "SessionActive", "SystemDaemon"]

ERROR = "org.kidux.Daemon1.Error."
NO_TIME_LEFT = ERROR + "NoTimeLeft"


class NoTimeLeft(Exception):
    pass


class NotUnlocked(DaemonError):
    """The panel's token is gone: closed, expired, or never given."""


class SessionActive(DaemonError):
    """The child is signed in, so their account cannot be removed now."""


class Invalid(DaemonError):
    """The daemon refused a value: a name, a password, a setting."""


class Busy(DaemonError):
    """An update job, or a module's install or removal, is already running."""


def _kind(error: DaemonError) -> DaemonError:
    """The same error, as the kind a screen reacts to differently."""
    text = str(error)
    for name, kind in (("NotUnlocked", NotUnlocked), ("SessionActive", SessionActive),
                       ("InvalidArgument", Invalid), ("NoSuchChild", Invalid), ("Busy", Busy)):
        if ERROR + name in text:
            return kind(text)
    return error


class Daemon(Protocol):
    def config(self) -> dict: ...
    def password_is_set(self) -> bool: ...
    def children(self) -> list[dict]: ...
    def check_access(self, username: str) -> tuple[str, int]: ...
    def usage(self, username: str) -> tuple[int, int]: ...
    def authorise_session(self, adult_password: str, username: str, minutes: int) -> bool: ...
    def grant_extra_time(self, adult_password: str, username: str, minutes: int) -> bool: ...
    def unlock_for_saving(self, adult_password: str, minutes: int) -> bool: ...
    def continue_session(self, username: str, password: str) -> bool: ...
    def end_session(self, username: str, password: str) -> bool: ...
    def unlock_panel(self, adult_password: str) -> str | None: ...
    def lock_panel(self, token: str) -> None: ...
    def version(self) -> str: ...
    def set_config(self, token: str, changes: dict) -> None: ...
    def set_adult_password(self, token: str, password: str) -> None: ...
    def recovery_password(self, token: str) -> str: ...
    def create_child(self, token: str, username: str, display_name: str, language: str,
                     keyboard: str, avatar: str, password: str) -> None: ...
    def delete_child(self, token: str, username: str, keep_home: bool) -> None: ...
    def set_profile(self, token: str, username: str, changes: dict) -> None: ...
    def set_child_password(self, token: str, username: str, password: str) -> None: ...
    def policy(self, username: str) -> dict: ...
    def set_policy(self, token: str, username: str, mode: str, daily_minutes: int,
                   days: list[bool] | None = None) -> None: ...
    def grant(self, token: str, username: str, minutes: int) -> None: ...
    def set_time_left(self, token: str, username: str, minutes: int) -> None: ...
    def shutdown(self) -> None: ...
    def reboot(self) -> None: ...
    def check_updates(self, token: str) -> None: ...
    def apply_updates(self, token: str) -> None: ...
    def update_state(self) -> tuple: ...
    def modules(self, username: str) -> list[dict]: ...
    def set_module(self, token: str, username: str, module_id: str, enabled: bool) -> None: ...
    def available_modules(self) -> list[dict]: ...
    def install_module(self, token: str, module_id: str) -> None: ...
    def remove_module(self, token: str, module_id: str) -> None: ...
    def network(self, token: str) -> tuple: ...
    def versions(self) -> dict: ...
    def check_network(self, token: str) -> None: ...
    def connect_wifi(self, token: str, ssid: str, password: str) -> None: ...
    def forget_wifi(self, token: str, ssid: str) -> None: ...


class SystemDaemon:
    def __init__(self) -> None:
        self._client = kidux_client.Client()

    def _call(self, interface, method, signature=None, args=None, reply=None):
        result = self._client.call(
            interface,
            method,
            GLib.Variant(signature, args) if signature else None,
            GLib.VariantType(reply) if reply else None,
        )
        return result.unpack() if result is not None else None

    def config(self) -> dict:
        return self._call("", "GetConfig", reply="(a{sv})")[0]

    def password_is_set(self) -> bool:
        return self._client.is_password_set()

    def children(self) -> list[dict]:
        return self._client.list_children()

    def check_access(self, username):
        return self._client.check_access(username)

    def usage(self, username):
        return self._client.usage(username)

    def authorise_session(self, adult_password, username, minutes):
        return self._call("Access1", "AuthoriseSession", "(ssu)",
                          (adult_password, username, minutes), "(b)")[0]

    def grant_extra_time(self, adult_password, username, minutes):
        return self._call("Access1", "GrantExtraTime", "(ssu)",
                          (adult_password, username, minutes), "(b)")[0]

    def unlock_for_saving(self, adult_password, minutes):
        return self._call("Access1", "UnlockForSaving", "(su)",
                          (adult_password, minutes), "(b)")[0]

    def continue_session(self, username, password):
        try:
            return self._call("Access1", "ContinueSession", "(ss)",
                              (username, password), "(b)")[0]
        except DaemonError as error:
            if NO_TIME_LEFT in str(error):
                raise NoTimeLeft() from error
            raise

    def end_session(self, username, password):
        return self._call("Access1", "EndSession", "(ss)", (username, password), "(b)")[0]

    def unlock_panel(self, adult_password):
        try:
            return self._client.unlock(adult_password)
        except DaemonError:
            return None

    def lock_panel(self, token):
        self._client.lock(token)

    # --- the wizard and the panel ----------------------------------------------
    #
    # Each raises NotUnlocked, SessionActive or Invalid when that is what the
    # daemon said, so the panel can answer each one in its own words.

    def _manage(self, method, *args):
        try:
            return getattr(self._client, method)(*args)
        except DaemonUnavailableError:
            raise
        except DaemonError as error:
            raise _kind(error) from error

    def version(self):
        return self._client.ping()

    def set_config(self, token, changes):
        self._manage("set_config", token, changes)

    def set_adult_password(self, token, password):
        self._manage("set_adult_password", token, password)

    def recovery_password(self, token):
        return self._manage("recovery_password", token)

    def create_child(self, token, username, display_name, language, keyboard, avatar, password):
        self._manage("create_child", token, username, display_name, language, keyboard,
                     avatar, password)

    def delete_child(self, token, username, keep_home):
        self._manage("delete_child", token, username, keep_home)

    def set_profile(self, token, username, changes):
        self._manage("set_profile", token, username, changes)

    def set_child_password(self, token, username, password):
        self._manage("set_child_password", token, username, password)

    def policy(self, username):
        return self._manage("policy", username)

    def set_policy(self, token, username, mode, daily_minutes, days=None):
        self._manage("set_policy", token, username, mode, daily_minutes, days)

    def grant(self, token, username, minutes):
        self._manage("grant", token, username, minutes)

    def set_time_left(self, token, username, minutes):
        self._manage("set_time_left", token, username, minutes)

    def check_updates(self, token):
        self._manage("check_updates", token)

    def apply_updates(self, token):
        self._manage("apply_updates", token)

    def update_state(self):
        return self._manage("update_state")

    def modules(self, username):
        return self._manage("list_modules", username)

    def set_module(self, token, username, module_id, enabled):
        self._manage("set_module_enabled", token, username, module_id, enabled)

    def available_modules(self):
        return self._manage("available_modules")

    def install_module(self, token, module_id):
        self._manage("install_module", token, module_id)

    def remove_module(self, token, module_id):
        self._manage("remove_module", token, module_id)

    def network(self, token):
        return self._manage("network", token)

    def versions(self):
        return self._manage("versions")

    def check_network(self, token):
        self._manage("check_network", token)

    def connect_wifi(self, token, ssid, password):
        self._manage("connect_wifi", token, ssid, password)

    def forget_wifi(self, token, ssid):
        self._manage("forget_wifi", token, ssid)

    def shutdown(self):
        self._client.shutdown()

    def reboot(self):
        self._client.reboot()

    # --- signals -------------------------------------------------------------

    def subscribe(self, on_attention, on_children_changed) -> bool:
        """Call back when the power button is pressed with nobody signed in
        (D16), and when a child is added, changed or removed.

        The callbacks run on the main loop of the thread that subscribed.
        False if the bus cannot be reached, in which case the screen works on
        without them.
        """
        try:
            connection = self._client.connection
        except DaemonUnavailableError:
            return False
        for interface, name, callback in (
            (paths.BUS_NAME, "AttentionRequested", on_attention),
            (f"{paths.BUS_NAME}.Children1", "ChildrenChanged", on_children_changed),
        ):
            connection.signal_subscribe(
                paths.BUS_NAME, interface, name, paths.OBJECT_PATH, None,
                Gio.DBusSignalFlags.NONE,
                lambda *_args, callback=callback: callback(),
            )
        return True
