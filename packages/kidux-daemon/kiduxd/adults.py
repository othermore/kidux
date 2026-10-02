"""The adult password, and the GRUB recovery password kept beside it.

The adult password is free-form text with no rule beyond "not empty" (D5), and
no lock-out: every attempt is audited instead (D15). It is stored as an
argon2id hash, with the library's own parameters, and rehashed after a
successful check whenever those parameters have moved on, so the cost can be
raised in a later release without anybody having to do anything.

The GRUB recovery password is stored in clear on purpose: it is what an adult
reads off the panel when the machine will not boot, and a hash cannot be read
off a panel. adults.toml is root:kidux-admin 0640, which is exactly the set of
people who may see it.
"""

import argon2

from kidux import paths, state

from .errors import InvalidArgument


class AdultPassword:
    def __init__(self, hasher: argon2.PasswordHasher | None = None) -> None:
        self._hasher = hasher or argon2.PasswordHasher()

    def _read(self) -> dict:
        return state.read(paths.ADULTS_FILE, "adults", default={})

    def _write(self, document: dict) -> None:
        document = {k: v for k, v in document.items() if k != "schema_version"}
        state.write(paths.ADULTS_FILE, document, "adults")

    def is_set(self) -> bool:
        return bool(self._read().get("password_hash"))

    def verify(self, password: str) -> bool:
        """True if `password` is the adult password. False if none is set."""
        document = self._read()
        stored = document.get("password_hash")
        if not stored or not password:
            return False

        try:
            self._hasher.verify(stored, password)
        except argon2.exceptions.VerificationError:
            return False
        except argon2.exceptions.InvalidHashError:
            return False

        if self._hasher.check_needs_rehash(stored):
            document["password_hash"] = self._hasher.hash(password)
            self._write(document)

        return True

    def set(self, password: str) -> None:
        if not password:
            raise InvalidArgument("the adult password cannot be empty")
        document = self._read()
        document["password_hash"] = self._hasher.hash(password)
        self._write(document)

    def grub(self) -> tuple[str | None, str | None]:
        """The GRUB recovery password and its PBKDF2 hash, if first boot made them."""
        document = self._read()
        return document.get("grub_password"), document.get("grub_password_hash")

    def set_grub(self, password: str, password_hash: str) -> None:
        document = self._read()
        document["grub_password"] = password
        document["grub_password_hash"] = password_hash
        self._write(document)
