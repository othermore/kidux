"""A module's notices: the desktop's notifications, kept for the bubble (D98).

A program tells its user something through freedesktop.org's *Desktop
Notifications*, `org.freedesktop.Notifications` on the session's bus. In a
child's session the launcher owns that name (bubbles.py) and shows each
notice as a bubble in the screen's corner; this is what it keeps of them,
and what it answers, with nothing of GTK or D-Bus, so that it is tested
where there is neither.

A notice goes after `SECONDS`, or stays until it is closed when its program
marks it urgent or never expiring, as an error is. It never makes a sound:
the capabilities say none, and a notice's sound is never read.
"""

import re
from dataclasses import dataclass, field
from pathlib import Path

#: The interface, as the specification gives it.
NAME = "org.freedesktop.Notifications"
PATH = "/org/freedesktop/Notifications"
INTERFACE = """
<node>
  <interface name="org.freedesktop.Notifications">
    <method name="GetCapabilities">
      <arg type="as" name="capabilities" direction="out"/>
    </method>
    <method name="Notify">
      <arg type="s" name="app_name" direction="in"/>
      <arg type="u" name="replaces_id" direction="in"/>
      <arg type="s" name="app_icon" direction="in"/>
      <arg type="s" name="summary" direction="in"/>
      <arg type="s" name="body" direction="in"/>
      <arg type="as" name="actions" direction="in"/>
      <arg type="a{sv}" name="hints" direction="in"/>
      <arg type="i" name="expire_timeout" direction="in"/>
      <arg type="u" name="id" direction="out"/>
    </method>
    <method name="CloseNotification">
      <arg type="u" name="id" direction="in"/>
    </method>
    <method name="GetServerInformation">
      <arg type="s" name="name" direction="out"/>
      <arg type="s" name="vendor" direction="out"/>
      <arg type="s" name="version" direction="out"/>
      <arg type="s" name="spec_version" direction="out"/>
    </method>
    <signal name="NotificationClosed">
      <arg type="u" name="id"/>
      <arg type="u" name="reason"/>
    </signal>
    <signal name="ActionInvoked">
      <arg type="u" name="id"/>
      <arg type="s" name="action_key"/>
    </signal>
  </interface>
</node>
"""

#: What the bubble can show: a text, and actions. No markup, no sound.
CAPABILITIES = ("body", "actions")
SPEC_VERSION = "1.2"

#: How long a notice that is not urgent stays, in seconds.
SECONDS = 8
#: The specification's urgencies, and why a notice was closed.
CRITICAL = 2
EXPIRED, DISMISSED, CLOSED = 1, 2, 3
#: The action a click on the bubble itself does.
DEFAULT = "default"

#: A module's scope, in a process's cgroup: `kidux-module-<id>.scope`.
SCOPE = re.compile(r"/kidux-module-([a-z0-9][a-z0-9-]*)\.scope(?:/|$)")


@dataclass
class Notice:
    id: int
    #: The id of the module whose scope sent it, or "".
    module: str
    app_name: str
    summary: str
    body: str
    #: (key, label) pairs, as the program gave them; DEFAULT is the click.
    actions: tuple = ()
    stays: bool = False
    hints: dict = field(default_factory=dict, repr=False)

    @property
    def buttons(self) -> tuple:
        """The actions shown as buttons: all but the click's."""
        return tuple((key, label) for key, label in self.actions if key != DEFAULT)


def pairs(flat) -> tuple:
    """The specification's actions, a flat list of key, label, key, label…,
    as (key, label) pairs; an odd one left over is dropped."""
    flat = [str(item) for item in flat]
    return tuple(zip(flat[0::2], flat[1::2]))


def stays(hints: dict, expire_timeout: int) -> bool:
    """Whether a notice stays until it is closed: urgent, or never
    expiring (an expire_timeout of 0)."""
    try:
        urgency = int(hints.get("urgency", 1))
    except (TypeError, ValueError):
        urgency = 1
    return urgency == CRITICAL or expire_timeout == 0


def module_of(pid: int, proc: Path = Path("/proc")) -> str:
    """The id of the module whose scope process `pid` runs in, from its
    cgroup; "" for any other process, or one gone."""
    try:
        text = (proc / str(pid) / "cgroup").read_text()
    except (OSError, ValueError):
        return ""
    found = SCOPE.search(text)
    return found.group(1) if found else ""


class Notices:
    """The notices shown, by number. `show(notice)` and `hide(id)` draw and
    take away a bubble; `closed(id, reason)` and `invoked(id, key)` are the
    signals the server sends."""

    def __init__(self, *, show, hide, closed, invoked) -> None:
        self._show, self._hide = show, hide
        self._closed, self._invoked = closed, invoked
        self.shown: dict[int, Notice] = {}
        self._last = 0

    def notify(self, module: str, app_name: str, replaces_id: int, summary: str, body: str,
               actions, hints: dict, expire_timeout: int) -> Notice:
        """A notice from a program; one it asked to replace takes that one's
        number and place."""
        if replaces_id and replaces_id in self.shown:
            number = replaces_id
            self._hide(number)
        else:
            self._last += 1
            number = self._last
        notice = Notice(number, module, app_name, summary, body, pairs(actions),
                        stays(hints, expire_timeout), dict(hints))
        self.shown[number] = notice
        self._show(notice)
        return notice

    def close(self, number: int, reason: int) -> bool:
        """Take a notice away, and say why; False for one not shown."""
        if self.shown.pop(number, None) is None:
            return False
        self._hide(number)
        self._closed(number, reason)
        return True

    def expire(self, number: int) -> None:
        """Its time is up, unless it stays."""
        notice = self.shown.get(number)
        if notice is not None and not notice.stays:
            self.close(number, EXPIRED)

    def act(self, number: int, key: str) -> None:
        """The child pressed one of its actions, or clicked the bubble
        (DEFAULT, when it has one): the program is told, and it goes."""
        notice = self.shown.get(number)
        if notice is None or key not in dict(notice.actions):
            return
        self._invoked(number, key)
        self.close(number, DISMISSED)
