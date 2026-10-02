"""The machine's user accounts, as the daemon sees and changes them.

`SystemAccounts` runs adduser, chpasswd, chfn and deluser. The rest of the
daemon only ever talks to the `Accounts` protocol, so the tests can hand it
`FakeAccounts` and never touch /etc/passwd.

A password is only ever written to a command's standard input. It is never an
argument, where any process on the machine could read it from /proc, and it
is never in an error message.
"""

import grp
import pwd
import subprocess
from typing import Protocol

from kidux import paths

from .errors import Failed, InvalidArgument

#: Extra groups every child joins. `video` is for brightnessctl, which the idle
#: handler in the child's session uses to darken the screen.
CHILD_GROUPS = (paths.CHILDREN_GROUP, "video")

CHILD_SHELL = "/usr/sbin/nologin"


class Accounts(Protocol):
    def exists(self, username: str) -> bool: ...
    def uid_of(self, username: str) -> int | None: ...
    def username_of(self, uid: int) -> str | None: ...
    def in_group(self, username: str, group: str) -> bool: ...
    def members(self, group: str) -> list[str]: ...
    def create_child(self, username: str, display_name: str) -> None: ...
    def set_password(self, username: str, password: str) -> None: ...
    def set_display_name(self, username: str, display_name: str) -> None: ...
    def delete(self, username: str, keep_home: bool) -> None: ...
    def add_to_group(self, username: str, group: str) -> None: ...


def check_password_text(password: str) -> None:
    """Refuse what cannot be fed to chpasswd safely: nothing else is refused."""
    if not password:
        raise InvalidArgument("the password cannot be empty")
    if "\n" in password or "\r" in password or "\0" in password:
        raise InvalidArgument("the password cannot contain a line break")


class SystemAccounts:
    def _run(self, *argv: str, stdin: str | None = None) -> None:
        try:
            subprocess.run(
                argv,
                input=stdin,
                text=True,
                capture_output=True,
                check=True,
                env={"PATH": "/usr/sbin:/usr/bin:/sbin:/bin", "LC_ALL": "C.UTF-8"},
            )
        except subprocess.CalledProcessError as error:
            detail = (error.stderr or "").strip().splitlines()
            raise Failed(f"{argv[0]} failed: {detail[-1] if detail else error.returncode}")
        except OSError as error:
            raise Failed(f"{argv[0]} could not run: {error}")

    def exists(self, username: str) -> bool:
        try:
            pwd.getpwnam(username)
        except KeyError:
            return False
        return True

    def uid_of(self, username: str) -> int | None:
        try:
            return pwd.getpwnam(username).pw_uid
        except KeyError:
            return None

    def username_of(self, uid: int) -> str | None:
        try:
            return pwd.getpwuid(uid).pw_name
        except KeyError:
            return None

    def in_group(self, username: str, group: str) -> bool:
        try:
            entry = grp.getgrnam(group)
        except KeyError:
            return False
        if username in entry.gr_mem:
            return True
        try:
            return pwd.getpwnam(username).pw_gid == entry.gr_gid
        except KeyError:
            return False

    def members(self, group: str) -> list[str]:
        try:
            return sorted(grp.getgrnam(group).gr_mem)
        except KeyError:
            return []

    def create_child(self, username: str, display_name: str) -> None:
        self._run(
            "adduser",
            "--quiet",
            "--disabled-password",
            "--comment",
            display_name,
            "--shell",
            CHILD_SHELL,
            username,
        )
        for group in CHILD_GROUPS:
            self.add_to_group(username, group)

    def add_to_group(self, username: str, group: str) -> None:
        self._run("adduser", "--quiet", username, group)

    def set_password(self, username: str, password: str) -> None:
        check_password_text(password)
        self._run("chpasswd", stdin=f"{username}:{password}\n")

    def set_display_name(self, username: str, display_name: str) -> None:
        self._run("chfn", "--full-name", display_name, username)

    def delete(self, username: str, keep_home: bool) -> None:
        argv = ["deluser", "--quiet"]
        if not keep_home:
            argv.append("--remove-home")
        argv.append(username)
        self._run(*argv)


class FakeAccounts:
    """Accounts in memory, for tests. Mirrors what SystemAccounts would do."""

    def __init__(self) -> None:
        self.users: dict[str, dict] = {}
        self.groups: dict[str, set[str]] = {}
        self.next_uid = 2000
        self.fail_on: set[str] = set()

    def add_user(self, username: str, uid: int, groups: tuple[str, ...] = ()) -> None:
        self.users[username] = {"uid": uid, "display_name": username, "password": None}
        for group in groups:
            self.groups.setdefault(group, set()).add(username)

    def _maybe_fail(self, step: str) -> None:
        if step in self.fail_on:
            raise Failed(f"{step} failed")

    def exists(self, username: str) -> bool:
        return username in self.users

    def uid_of(self, username: str) -> int | None:
        user = self.users.get(username)
        return user["uid"] if user else None

    def username_of(self, uid: int) -> str | None:
        for name, user in self.users.items():
            if user["uid"] == uid:
                return name
        return None

    def in_group(self, username: str, group: str) -> bool:
        return username in self.groups.get(group, set())

    def members(self, group: str) -> list[str]:
        return sorted(self.groups.get(group, set()))

    def create_child(self, username: str, display_name: str) -> None:
        self._maybe_fail("adduser")
        self.users[username] = {
            "uid": self.next_uid,
            "display_name": display_name,
            "password": None,
            "home": True,
        }
        self.next_uid += 1
        for group in CHILD_GROUPS:
            self.add_to_group(username, group)

    def add_to_group(self, username: str, group: str) -> None:
        self._maybe_fail(f"group:{group}")
        self.groups.setdefault(group, set()).add(username)

    def set_password(self, username: str, password: str) -> None:
        check_password_text(password)
        self._maybe_fail("chpasswd")
        self.users[username]["password"] = password

    def set_display_name(self, username: str, display_name: str) -> None:
        self._maybe_fail("chfn")
        self.users[username]["display_name"] = display_name

    def delete(self, username: str, keep_home: bool) -> None:
        self._maybe_fail("deluser")
        self.users.pop(username, None)
        for members in self.groups.values():
            members.discard(username)
        self.deleted_keep_home = keep_home

