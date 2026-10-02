#!/usr/bin/python3
"""A family's machine trusts the key stable is signed with, and no other.

    tests/project/archive-keys.py

kidux-archive-keyring installs the one key apt checks Kidux's archive
against. It must be the key the archive signs its stable suite with
(ci/archive/conf/distributions), and it must not be the development key,
which signs the testing suite, has no passphrase and lives on a
development machine: a keyring that held it would let that machine sign
updates for every family (D82). The development key's public part is
ci/archive/development-key.pgp, for the machines that follow testing.

The keys are read here, from the OpenPGP packets, so the check needs no
gpg: a version 4 key's fingerprint is the SHA-1 of its public key packet.
"""

import hashlib
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
KEYRING = REPO / "packages" / "kidux-archive-keyring" / "keyrings" / "kidux-archive-keyring.pgp"
DEVELOPMENT = REPO / "ci" / "archive" / "development-key.pgp"
DISTRIBUTIONS = REPO / "ci" / "archive" / "conf" / "distributions"

failed = 0


def check(name: str, passed: bool, detail: str = "") -> None:
    global failed
    print(("PASS  " if passed else "FAIL  ") + name)
    if not passed:
        failed += 1
        if detail:
            print("      " + detail)


def primary_keys(path: Path) -> list[str]:
    """The fingerprints of the primary keys in a binary OpenPGP keyring."""
    data = path.read_bytes()
    found, at = [], 0
    while at < len(data):
        first = data[at]
        if not first & 0x80:
            raise ValueError(f"{path}: not OpenPGP packets")
        if first & 0x40:                         # new format
            tag = first & 0x3F
            length = data[at + 1]
            if length < 192:
                start = at + 2
            elif length < 224:
                length = ((length - 192) << 8) + data[at + 2] + 192
                start = at + 3
            elif length == 255:
                length = int.from_bytes(data[at + 2:at + 6], "big")
                start = at + 6
            else:
                raise ValueError(f"{path}: a packet of partial length")
        else:                                    # old format
            tag = (first >> 2) & 0x0F
            size = (1, 2, 4)[first & 0x03]
            length = int.from_bytes(data[at + 1:at + 1 + size], "big")
            start = at + 1 + size
        body = data[start:start + length]
        if tag == 6:                             # a public key, not a subkey
            if body[0] != 4:
                raise ValueError(f"{path}: a key of version {body[0]}")
            found.append(hashlib.sha1(b"\x99" + len(body).to_bytes(2, "big") + body)
                         .hexdigest().upper())
        at = start + length
    return found


signs = dict(re.findall(r"^Suite: (\S+)\n(?:(?!^Suite: ).*\n)*?^SignWith: (\S+)$",
                        DISTRIBUTIONS.read_text(), re.MULTILINE))
check("each suite of the archive names the key it is signed with",
      set(signs) == {"testing", "stable"}, str(signs))
shipped = primary_keys(KEYRING)
check("kidux-archive-keyring holds one key, the one stable is signed with",
      shipped == [signs.get("stable")], f"it holds {shipped}; stable is signed with {signs.get('stable')}")
check("and it is not the key testing is signed with, the development one",
      signs.get("testing") not in shipped and signs.get("testing") != signs.get("stable"),
      str(signs))
check("the development key's public part is beside the archive's configuration",
      primary_keys(DEVELOPMENT) == [signs.get("testing")],
      f"{DEVELOPMENT} holds {primary_keys(DEVELOPMENT)}")

sys.exit(failed)
