"""First boot: the state directory, the recovery password, the administrators.

Run once per machine by kidux-firstboot.service, on the first boot after
kidux-daemon is installed (daemon.md section 12). That includes the first boot
of a fresh install from an image, where the administrator's account did not
exist when the packages were built (D18) — which is why this is a boot unit
and not part of the package's postinst.

config.toml is written last, because its existence is what marks first boot
as done: a first boot interrupted halfway runs again from the start.
"""

import grp
import os
import pwd
import secrets
import shutil
import string
import subprocess
from pathlib import Path
from typing import Callable

from kidux import log, paths

from .adults import AdultPassword
from .children import shipped_languages
from .config import DEFAULTS, Config

RECOVERY_ALPHABET = string.ascii_lowercase + string.digits
RECOVERY_LENGTH = 16

Runner = Callable[..., subprocess.CompletedProcess]


def _read_shell_assignments(path: Path) -> dict[str, str]:
    """KEY=value lines from /etc/default/*, quotes stripped. Missing file: {}."""
    values = {}
    try:
        lines = path.read_text().splitlines()
    except OSError:
        return values
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        values[key.strip()] = value.strip().strip("\"'")
    return values


def default_language(locale_file: Path, languages: set[str]) -> str:
    language = _read_shell_assignments(locale_file).get("LANG", "")
    return language if language in languages else DEFAULTS["default_language"]


def default_keyboard(keyboard_file: Path) -> str:
    layout = _read_shell_assignments(keyboard_file).get("XKBLAYOUT", "")
    # A machine can list several layouts; the first is the one that is used.
    first = layout.split(",")[0].strip()
    return first or DEFAULTS["default_keyboard"]


def recovery_password() -> str:
    return "".join(secrets.choice(RECOVERY_ALPHABET) for _ in range(RECOVERY_LENGTH))


def grub_hash(password: str, run: Runner) -> str | None:
    """The PBKDF2 hash GRUB wants, from GRUB's own tool, or None without GRUB."""
    if shutil.which("grub-mkpasswd-pbkdf2") is None:
        return None
    result = run(
        ["grub-mkpasswd-pbkdf2"],
        input=f"{password}\n{password}\n",
        text=True,
        capture_output=True,
        check=True,
    )
    for word in result.stdout.split():
        if word.startswith("grub.pbkdf2."):
            return word
    return None


def _prepare_state_root(chown: bool) -> None:
    for directory in (paths.STATE_ROOT, paths.CHILDREN_DIR, paths.STATE_DIR):
        directory.mkdir(parents=True, exist_ok=True)
        os.chmod(directory, 0o750)
        if chown:
            os.chown(directory, 0, grp.getgrnam(paths.ADMIN_GROUP).gr_gid)


def run(
    *,
    locale_file: Path = Path("/etc/default/locale"),
    keyboard_file: Path = Path("/etc/default/keyboard"),
    run_command: Runner = subprocess.run,
    chown: bool = True,
    languages: set[str] | None = None,
    administrators: Callable[[], list[str]] | None = None,
) -> bool:
    """Do first boot, unless it has been done. True if it ran."""
    if paths.CONFIG_FILE.exists():
        return False

    _prepare_state_root(chown)

    # The recovery password has to exist before the session hardening that
    # relies on it takes effect, so it is made here, before anything else.
    adults = AdultPassword()
    password, existing_hash = adults.grub()
    if not existing_hash:
        password = recovery_password()
        hashed = grub_hash(password, run_command)
        if hashed:
            adults.set_grub(password, hashed)
            if shutil.which("update-grub"):
                run_command(["update-grub"], capture_output=True, check=False)
            log.audit("recovery password", "ok")
        else:
            log.audit("recovery password", "skipped", reason="no GRUB on this machine")

    # Every administrator becomes an adult of the family's state directory.
    # Only sudo members: the daemon never puts a child in sudo, so no child
    # can arrive here.
    for member in (administrators or sudo_members)():
        run_command(
            ["gpasswd", "--add", member, paths.ADMIN_GROUP],
            capture_output=True,
            check=False,
        )
        log.audit("administrator added", "ok", user=member)

    known = languages if languages is not None else shipped_languages()
    config = Config(
        **{
            **DEFAULTS,
            "default_language": default_language(locale_file, known),
            "default_keyboard": default_keyboard(keyboard_file),
        }
    )
    config.save()
    log.audit("first boot", "ok")
    return True


def sudo_members() -> list[str]:
    try:
        members = grp.getgrnam("sudo").gr_mem
    except KeyError:
        return []
    humans = []
    for name in members:
        try:
            if pwd.getpwnam(name).pw_uid >= 1000:
                humans.append(name)
        except KeyError:
            continue
    return sorted(humans)


def main() -> int:
    log.setup("firstboot")
    ran = run()
    print("kidux-firstboot: done" if ran else "kidux-firstboot: already done")
    return 0
