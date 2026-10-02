"""Reading and writing the files under /home/.kidux.

Three rules, and every one of them exists because of something that happens on
a real family's machine.

**Atomic writes.** A child pulls the plug. Whatever was being written must
either be the old file or the new one, never half of each. Losing a child's
settings to a power cut would be bad; losing the record of how much time they
have used today would mean the daily limit quietly resets, which a child will
find within a week.

**Schema versions.** Kidux is meant to be upgraded for years on a machine
nobody administers. Every file says which layout it is in. An older file is
migrated on sight; a *newer* one is refused outright, because it was written by
a version of Kidux that knew something this one does not, and guessing would
corrupt it.

**No partial reads.** A file that does not parse is an error, never an empty
dictionary. Treating a corrupt access policy as "no policy" would hand a child
unlimited time.
"""

import grp
import os
import tempfile
import tomllib
from pathlib import Path
from typing import Any

import tomli_w

from . import paths

#: Current layout of each kind of file. Bump one of these when its contents
#: change shape, and add the migration that gets there from the version before.
SCHEMA_VERSIONS = {
    "config": 1,
    "adults": 1,
    "profile": 1,
    "access": 1,
    "usage": 1,
    "modules": 1,
}

#: Migrations from one schema version to the next, per kind. A migration takes
#: the parsed document and returns it in the following version's shape.
#: Keyed by (kind, version_it_upgrades_from).
_MIGRATIONS: dict[tuple[str, int], Any] = {}


class StateError(Exception):
    """Something is wrong with a state file."""


class SchemaTooNewError(StateError):
    """The file was written by a newer Kidux than the one reading it.

    The daemon refuses to start rather than guess. An adult is told to finish
    the upgrade that was interrupted, which is a far better outcome than a
    silently mangled file.
    """


class CorruptStateError(StateError):
    """The file exists but is not readable as the document it claims to be."""


def read(path: Path, kind: str, *, default: dict | None = None) -> dict:
    """Read one state file, migrating it forward if it is old.

    `default` is returned only when the file does not exist at all — a child
    who has never had a module enabled, say. A file that exists and cannot be
    read is an error, never a default.
    """
    _check_kind(kind)

    if not path.exists():
        if default is None:
            raise FileNotFoundError(path)
        return dict(default)

    try:
        with open(path, "rb") as handle:
            document = tomllib.load(handle)
    except tomllib.TOMLDecodeError as error:
        raise CorruptStateError(f"{path} is not valid TOML: {error}") from error
    except OSError as error:
        raise StateError(f"cannot read {path}: {error}") from error

    return _migrate(document, kind, path)


def write(path: Path, document: dict, kind: str, *, mode: int = 0o640) -> None:
    """Write one state file atomically, stamped with the current schema.

    The default mode keeps the file readable by the owner and the group — root
    and kidux-admin — and closed to everyone else, which means to every child.
    """
    _check_kind(kind)

    stamped = {"schema_version": SCHEMA_VERSIONS[kind], **document}

    path.parent.mkdir(parents=True, exist_ok=True)
    own_directories(path.parent)

    # The temporary file has to live in the same directory as its target:
    # os.replace is only atomic within one filesystem.
    handle = tempfile.NamedTemporaryFile(
        mode="wb",
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
        delete=False,
    )
    try:
        with handle:
            tomli_w.dump(stamped, handle)
            handle.flush()
            # Without this the rename can land before the contents do, and a
            # power cut leaves a correctly named, empty file.
            os.fsync(handle.fileno())
        os.chmod(handle.name, mode)
        give_to_administrators(handle.name)
        os.replace(handle.name, path)
    except BaseException:
        try:
            os.unlink(handle.name)
        except OSError:
            pass
        raise

    _fsync_directory(path.parent)


def give_to_administrators(path: str | Path) -> None:
    """Make a file of the family's state root:kidux-admin.

    A file made by root belongs to group root, which would close it to the
    administrators the directory is meant to be readable by. Only root can
    give a file away, so under a test or a developer's account this is a
    no-op, and a machine without the group yet is left alone.
    """
    if os.geteuid() != 0:
        return
    try:
        gid = grp.getgrnam(paths.ADMIN_GROUP).gr_gid
    except KeyError:
        return
    try:
        os.chown(path, 0, gid)
    except OSError:
        pass


def own_directories(directory: Path) -> None:
    """Every directory of the state below its root: root:kidux-admin, 0750.

    Closed to every child, open to administrators, whoever made them.
    """
    root = paths.STATE_ROOT
    current = directory
    while current != root and root in current.parents:
        give_to_administrators(current)
        if os.geteuid() == 0:
            try:
                os.chmod(current, 0o750)
            except OSError:
                pass
        current = current.parent


def _fsync_directory(directory: Path) -> None:
    """Make the rename itself durable, not just the file's contents."""
    fd = os.open(directory, os.O_RDONLY)
    try:
        os.fsync(fd)
    except OSError:
        # Some filesystems refuse to fsync a directory. The rename is still
        # atomic; only its durability across a power cut is weakened, and
        # there is nothing further we can do about it here.
        pass
    finally:
        os.close(fd)


def _check_kind(kind: str) -> None:
    if kind not in SCHEMA_VERSIONS:
        raise ValueError(f"unknown kind of state file: {kind!r}")


def _migrate(document: dict, kind: str, path: Path) -> dict:
    current = SCHEMA_VERSIONS[kind]
    version = document.get("schema_version")

    if version is None:
        raise CorruptStateError(f"{path} has no schema_version")
    if not isinstance(version, int):
        raise CorruptStateError(f"{path} has a non-numeric schema_version")

    if version > current:
        raise SchemaTooNewError(
            f"{path} is schema version {version}, and this Kidux understands "
            f"up to {current}. It was written by a newer version."
        )

    while version < current:
        migration = _MIGRATIONS.get((kind, version))
        if migration is None:
            raise StateError(
                f"{path} is schema version {version} and there is no migration "
                f"from it to {version + 1}"
            )
        document = migration(document)
        version += 1
        document["schema_version"] = version

    return document
