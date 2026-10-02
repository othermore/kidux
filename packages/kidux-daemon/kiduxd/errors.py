"""The errors the daemon answers with, as D-Bus error names.

Each class carries the last component of its D-Bus name. The bus layer turns
an instance into `org.kidux.Daemon1.Error.<name>` with the instance's message.
A message never contains a password.
"""

ERROR_PREFIX = "org.kidux.Daemon1.Error."
ACCESS_DENIED = "org.freedesktop.DBus.Error.AccessDenied"


class DaemonError(Exception):
    """Something the caller asked for could not be done."""

    name = "Failed"

    @property
    def dbus_name(self) -> str:
        return ERROR_PREFIX + self.name


class Failed(DaemonError):
    """Something on the machine failed: adduser, chpasswd, logind."""

    name = "Failed"


class AccessDenied(DaemonError):
    """polkit said no. Carries D-Bus's own name, which clients already know."""

    name = "AccessDenied"

    @property
    def dbus_name(self) -> str:
        return ACCESS_DENIED


class NotAuthorized(DaemonError):
    """The daemon's own checks said no: polkit cannot see arguments."""

    name = "NotAuthorized"


class NotUnlocked(DaemonError):
    """The token is missing, unknown, expired or belongs to another connection."""

    name = "NotUnlocked"


class WrongPassword(DaemonError):
    name = "WrongPassword"


class NoSuchChild(DaemonError):
    name = "NoSuchChild"


class SessionActive(DaemonError):
    """The child has a session; it has to end before this can happen."""

    name = "SessionActive"


class NoTimeLeft(DaemonError):
    name = "NoTimeLeft"


class NoSession(DaemonError):
    name = "NoSession"


class InvalidArgument(DaemonError):
    name = "InvalidArgument"


class Busy(DaemonError):
    """An update job is already running."""

    name = "Busy"
