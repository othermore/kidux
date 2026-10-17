"""A module's guide beside it: which guide the pane shows, what it
remembers, and the missions (launcher.md, section 5; D103).

The policy, with no GTK in it, so that its test is the specification; the
pane itself is `guide.py`. The pane follows the module on screen, which
the desk says at every change, by one rule for each of the child's modes:

- without windows, one module fills the screen at a time: the pane shows
  the guide of the module on screen, and goes away when it has none or
  home is on screen;
- with windows, several are in view at once: the pane stays while any open
  module has a guide, shows the guide of the module in use, keeps the last
  one shown while a module without one or home is in use, and goes away
  when the last open module with a guide closes. The child may also pick a
  guide by hand, which pins it, and pin or unpin the one shown: a pinned
  guide stays whatever window is in use, until it is unpinned or its
  module closes. The pin is the session's alone.

What the child left in each module's guide, folded or not and the lesson
they were in, is remembered in a file of the launcher's own in the child's
home, read at start and written when it changes.
"""

import json
import logging
import os
import shutil
import tempfile
from pathlib import Path

log = logging.getLogger("kidux.launcher")


def state_file(home: str) -> Path:
    return Path(home) / ".local" / "share" / "kidux" / "launcher.json"


class Guides:
    def __init__(self, *, windows: bool, path: Path) -> None:
        self._windows = windows
        self._path = path
        #: The module whose guide the pane shows, or None: no pane.
        self.shown: str | None = None
        #: With windows, the guide the child pinned, or None.
        self.pinned: str | None = None
        #: The open modules that have a guide, in the order they were opened.
        self.open: list[str] = []
        self._remembered = self._read()

    # --- which guide -------------------------------------------------------

    def follow(self, opened: list[str], current: str | None, has_guide) -> str | None:
        """The desk changed: `opened` the open modules in the order they
        were opened, `current` the one on screen or in use (None for home),
        `has_guide(id)` whether a module has a guide. Returns the module
        whose guide the pane shows now, or None."""
        self.open = [module for module in opened if has_guide(module)]
        if not self._windows:
            self.pinned = None
            self.shown = current if current in self.open else None
            return self.shown
        if not self.open:
            self.pinned = self.shown = None
        elif self.pinned in self.open:
            self.shown = self.pinned
        else:
            self.pinned = None
            if current in self.open:
                self.shown = current
            elif self.shown not in self.open:
                self.shown = self.open[-1]
        return self.shown

    def pick(self, module_id: str) -> str | None:
        """The child picked a guide from the pane's list: shown and pinned."""
        if module_id in self.open:
            self.shown = module_id
            if self._windows:
                self.pinned = module_id
        return self.shown

    def pin(self, on: bool) -> None:
        """The pane's pin: the guide shown kept, or let follow again."""
        self.pinned = self.shown if on and self._windows else None

    # --- what is remembered ------------------------------------------------

    def folded(self, module_id: str) -> bool:
        return bool(self._remembered.get(module_id, {}).get("folded", False))

    def lesson(self, module_id: str) -> int | None:
        """The number of the lesson the child was in, None for the list."""
        number = self._remembered.get(module_id, {}).get("lesson")
        return number if isinstance(number, int) and not isinstance(number, bool) else None

    def seen(self, module_id: str) -> bool:
        """Whether the guide was ever shown, so that its missions are copied."""
        return module_id in self._remembered

    def remember(self, module_id: str, *, folded: bool | None = None,
                 lesson: int | None | str = "same") -> None:
        entry = dict(self._remembered.get(module_id, {}))
        if folded is not None:
            entry["folded"] = folded
        if lesson != "same":
            entry["lesson"] = lesson
        entry.setdefault("folded", False)
        entry.setdefault("lesson", None)
        if self._remembered.get(module_id) != entry:
            self._remembered[module_id] = entry
            self._write()

    def _read(self) -> dict:
        try:
            document = json.loads(self._path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            return {}
        except (OSError, ValueError) as error:
            log.warning("the guides' state %s does not read: %s", self._path, error)
            return {}
        guides = document.get("guides") if isinstance(document, dict) else None
        if not isinstance(guides, dict):
            log.warning("the guides' state %s has no guides", self._path)
            return {}
        return {key: value for key, value in guides.items() if isinstance(value, dict)}

    def _write(self) -> None:
        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile("w", dir=self._path.parent, delete=False,
                                             prefix=f".{self._path.name}.",
                                             encoding="utf-8") as handle:
                json.dump({"guides": self._remembered}, handle, indent=1, sort_keys=True)
            os.replace(handle.name, self._path)
        except OSError as error:
            log.warning("could not keep the guides' state: %s", error)


def copy_missions(missions: list[str], folder: Path) -> list[Path]:
    """The guide's missions, files of the program's, copied into `folder`,
    the child's Missions of <name> in their Documents, each under its own
    name; a file already there is never overwritten, since it may be the
    child's work. Returns where each mission is now."""
    copies = []
    for mission in missions:
        target = folder / Path(mission).name
        if not target.exists():
            try:
                folder.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(mission, target)
            except OSError as error:
                log.warning("could not copy the mission %s: %s", mission, error)
                continue
        copies.append(target)
    return copies
