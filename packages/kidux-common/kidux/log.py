"""Logging, and the audit trail that is not the same thing.

Two separate things, kept apart on purpose.

**Logging** is for whoever is fixing Kidux. It goes to the journal, it is in
English, and it may say anything useful.

**The audit trail** is for the adult who owns the machine. It is a permanent,
append-only record of every privileged action and every attempt at the adult
password. It exists because Kidux deliberately has no lock-out on that password
(D15): anyone at the keyboard may try as often as they like, so the only
protection an adult has is being able to see, afterwards, that someone did.

The audit trail never records a password, not even a wrong one. A child who
mistypes their own password into the adult prompt would otherwise have it
written to a file in clear, and a wrong guess is often somebody's real password
somewhere else.
"""

import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Any

from . import paths

_LOGGER_NAME = "kidux"

#: Argument names that must never reach the audit trail whatever a caller does.
_NEVER_RECORD = frozenset(
    {"password", "adult_password", "child_password", "new_password", "token"}
)


def get_logger(component: str) -> logging.Logger:
    """The logger for one Kidux program: daemon, greeter, launcher, panel."""
    return logging.getLogger(f"{_LOGGER_NAME}.{component}")


def setup(component: str, *, debug: bool = False) -> logging.Logger:
    """Set up logging for a program, once, at start-up.

    Output goes to stderr, which systemd hands to the journal. That keeps this
    working identically when a developer runs the program from a terminal.
    """
    root = logging.getLogger(_LOGGER_NAME)

    if not root.handlers:
        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(
            logging.Formatter("%(name)s: %(levelname)s: %(message)s")
        )
        root.addHandler(handler)

    root.setLevel(logging.DEBUG if debug else logging.INFO)
    return get_logger(component)


def audit(action: str, outcome: str, **fields: Any) -> None:
    """Record one privileged action in the audit trail.

    `outcome` is what actually happened, in one word: "ok", "denied",
    "failed". It is separate from `action` so that a reader can find every
    refused attempt without knowing what to look for.

    Writing is best-effort by design. The audit trail is only writable by root,
    so a program that is not the daemon simply cannot write to it, and the
    daemon must not fall over because a disk filled up in the middle of a
    child's session. A failure to record is logged and swallowed.
    """
    entry = {
        "time": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "action": action,
        "outcome": outcome,
    }

    for name, value in fields.items():
        if name in _NEVER_RECORD:
            # Not an error: it is easier to call audit() with the whole set of
            # arguments than to remember which ones are secret. Dropping them
            # here is what makes that safe.
            continue
        entry[name] = value

    line = json.dumps(entry, ensure_ascii=False, sort_keys=True)

    try:
        _append(paths.AUDIT_LOG, line)
    except OSError as error:
        get_logger("audit").warning(
            "could not write to the audit trail: %s", error
        )


def _append(path: Path, line: str) -> None:
    from . import state

    path.parent.mkdir(parents=True, exist_ok=True)
    state.own_directories(path.parent)

    # O_APPEND so that concurrent writers cannot interleave: the daemon is one
    # process today, but the trail has to stay readable if that ever changes.
    fd = os.open(
        path,
        os.O_WRONLY | os.O_CREAT | os.O_APPEND,
        0o640,
    )
    try:
        # The trail is the administrators' to read (D15): root:kidux-admin.
        state.give_to_administrators(path)
        os.write(fd, (line + "\n").encode("utf-8"))
        os.fsync(fd)
    finally:
        os.close(fd)
