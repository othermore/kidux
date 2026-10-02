"""Children: their accounts and the files that describe them (daemon.md section 6).

Creating a child touches the machine in a fixed order, and a failure at any
step undoes the steps before it, so the machine is never left with half a
child: an account with no profile that the sign-in screen cannot draw, or a
profile with no account that nobody can sign in as.
"""

import re
import shutil
from pathlib import Path

from kidux import avatars, paths, state
from kidux.log import get_logger

from .accounts import check_password_text
from .errors import InvalidArgument, SessionActive
from .locker import wait_for
from .logind import Logind, has_manager, has_session

_log = get_logger("children")

KEYBOARD = re.compile(r"\A[a-z][a-z0-9_+:-]{0,31}\Z")
MAX_DISPLAY_NAME = 64
#: `windows`: whether the child's modules open in windows they move and
#: resize, several at once, rather than filling the screen (D46).
PROFILE_KEYS = ("display_name", "language", "keyboard", "avatar", "age", "windows")

#: A new child can use nothing until an adult says how much. The first-run
#: wizard and the panel always ask; this is only what a child is before that.
NEW_ACCESS = {"mode": "manual", "daily_minutes": 60, "granted_seconds": 0}


def shipped_languages(locales_file: Path | None = None) -> set[str]:
    """The locales kidux-base generates, which are the languages a child may have."""
    path = locales_file or (paths.DATA_ROOT / "locales")
    try:
        lines = path.read_text().splitlines()
    except OSError:
        return {"en_US.UTF-8"}
    return {
        line.split()[0]
        for line in lines
        if line.strip() and not line.lstrip().startswith("#")
    }


class Children:
    def __init__(self, accounts, logind: Logind, languages: set[str] | None = None) -> None:
        self._accounts = accounts
        self._logind = logind
        self._languages = languages

    @property
    def languages(self) -> set[str]:
        return self._languages if self._languages is not None else shipped_languages()

    # --- validation ----------------------------------------------------------

    def _check_display_name(self, value) -> str:
        if not isinstance(value, str) or not value.strip():
            raise InvalidArgument("a child needs a name to be shown")
        if len(value) > MAX_DISPLAY_NAME or any(ord(c) < 32 for c in value):
            raise InvalidArgument("that name cannot be shown")
        return value.strip()

    def _check_language(self, value) -> str:
        if value not in self.languages:
            raise InvalidArgument(f"{value!r} is not a language this computer has")
        return value

    def _check_keyboard(self, value) -> str:
        if not isinstance(value, str) or not KEYBOARD.match(value):
            raise InvalidArgument(f"{value!r} is not a keyboard layout")
        return value

    def _check_avatar(self, value) -> str:
        if not isinstance(value, str) or not avatars.exists(value):
            raise InvalidArgument(f"{value!r} is not one of the pictures on this computer")
        return value

    def _check_age(self, value) -> int:
        if not isinstance(value, int) or isinstance(value, bool) or not 1 <= value <= 18:
            raise InvalidArgument("an age is a whole number from 1 to 18")
        return value

    def _check_windows(self, value) -> bool:
        if not isinstance(value, bool):
            raise InvalidArgument("windows is on or off")
        return value

    # The machine's settings take a language and a keyboard by the same rules.
    check_language = _check_language
    check_keyboard = _check_keyboard

    # --- reading -------------------------------------------------------------

    def usernames(self) -> list[str]:
        return self._accounts.members(paths.CHILDREN_GROUP)

    def profile(self, username: str) -> dict:
        document = state.read(paths.child_profile(username), "profile", default={})
        return {key: document[key] for key in PROFILE_KEYS if key in document}

    def access(self, username: str) -> dict:
        return state.read(paths.child_access(username), "access", default=NEW_ACCESS)

    def list(self) -> list[dict]:
        """What the sign-in screen draws its rows from, sorted by name."""
        entries = []
        for username in self.usernames():
            profile = self.profile(username)
            entry = {
                "username": username,
                "display_name": profile.get("display_name", username),
                "language": profile.get("language", ""),
                "keyboard": profile.get("keyboard", ""),
                "avatar": avatars.resolve(profile.get("avatar"))
                if avatars.available()
                else profile.get("avatar", ""),
                "mode": self.access(username).get("mode", "manual"),
                "windows": bool(profile.get("windows", False)),
            }
            if "age" in profile:
                entry["age"] = profile["age"]
            entries.append(entry)
        return sorted(entries, key=lambda e: (e["display_name"].casefold(), e["username"]))

    # --- changing ------------------------------------------------------------

    def create(
        self,
        username: str,
        display_name: str,
        language: str,
        keyboard: str,
        avatar: str,
        password: str,
    ) -> None:
        profile = {
            "display_name": self._check_display_name(display_name),
            "language": self._check_language(language),
            "keyboard": self._check_keyboard(keyboard),
            "avatar": self._check_avatar(avatar),
        }
        check_password_text(password)

        try:
            self._accounts.create_child(username, profile["display_name"])
            self._accounts.set_password(username, password)
            state.write(paths.child_profile(username), profile, "profile")
            state.write(paths.child_access(username), NEW_ACCESS, "access")
            state.write(
                paths.child_usage(username),
                {"last_day": "", "seconds_used_today": 0},
                "usage",
            )
            state.write(paths.child_modules(username), {"enabled": []}, "modules")
        except BaseException:
            self._undo_create(username)
            raise

    def _undo_create(self, username: str) -> None:
        """Remove whatever of a half-created child exists, keeping the first error.

        adduser can fail after creating the account, when a group is added, so
        the account is checked for rather than assumed either way.
        """
        try:
            if self._accounts.exists(username):
                self._accounts.delete(username, keep_home=False)
        except Exception:
            _log.exception("could not remove the half-created account %s", username)
        shutil.rmtree(paths.child_dir(username), ignore_errors=True)

    def delete(self, username: str, keep_home: bool) -> None:
        uid = self._accounts.uid_of(username)
        if uid is not None and has_session(self._logind, uid):
            raise SessionActive(f"{username} is signed in; they have to log out first")
        if uid is not None and has_manager(self._logind, uid):
            # The child's user manager outlives their last session by a few
            # seconds, and deluser refuses a user with a process: it is ended
            # first, and given a moment to go.
            self._logind.terminate_user(uid)
            wait_for(lambda: not has_manager(self._logind, uid), 10.0)
        self._accounts.delete(username, keep_home)
        shutil.rmtree(paths.child_dir(username), ignore_errors=True)

    def set_profile(self, username: str, changes: dict) -> dict:
        unknown = set(changes) - set(PROFILE_KEYS)
        if unknown:
            raise InvalidArgument(f"not part of a profile: {', '.join(sorted(unknown))}")

        checks = {
            "display_name": self._check_display_name,
            "language": self._check_language,
            "keyboard": self._check_keyboard,
            "avatar": self._check_avatar,
            "age": self._check_age,
            "windows": self._check_windows,
        }
        validated = {key: checks[key](value) for key, value in changes.items()}

        profile = self.profile(username)
        if "display_name" in validated and validated["display_name"] != profile.get(
            "display_name"
        ):
            self._accounts.set_display_name(username, validated["display_name"])

        profile.update(validated)
        state.write(paths.child_profile(username), profile, "profile")
        return validated

    def set_password(self, username: str, password: str) -> None:
        self._accounts.set_password(username, password)
