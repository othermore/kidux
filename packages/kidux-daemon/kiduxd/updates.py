"""Updates: apt, run where neither the daemon's walls nor its own restart can hurt it.

daemon.md section 13, plan step 9.8. The daemon never runs apt itself. Its
unit has no network and a read-only system, and an update may replace and
restart the daemon half-way through. So each job runs in a transient system
unit of its own, `kidux-update.service`, running `/usr/libexec/kidux-update`,
which writes apt's progress and its verdict to a status file. The daemon
reads that file and turns it into signals, and picks it up again after a
restart of its own.

The same runner installs and removes one module's package for the panel
(daemon.md section 9): `kidux-update install <package>` and `remove
<package>`, the package made by the daemon from a module id it checked.

The file is lines apt writes on its status descriptor, `dlstatus:` while
downloading and `pmstatus:` while installing, plus the script's own lines,
all starting `kidux:`:

    kidux:job:<check|apply|install|remove>
    kidux:module:<package>
    kidux:checked:<count>:<package,package,...>
    kidux:done:<updated|up-to-date|restart-needed|installed|removed>
    kidux:failed:<one line saying why>
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Protocol

from .catalogue import PREFIX
from .errors import Busy

UNIT = "kidux-update.service"
SCRIPT = "/usr/libexec/kidux-update"
STATUS = Path(os.environ.get("KIDUX_UPDATE_STATUS", "/run/kidux/update.status"))

JOBS = {"check": "checking", "apply": "applying", "install": "installing",
        "remove": "removing"}
#: The jobs that install or remove one module, and their audit lines.
MODULE_JOBS = {"installing": "module installed", "removing": "module removed"}

#: How much of an installation's bar the downloads take; the rest is dpkg.
DOWNLOAD_SHARE = 0.3


class Runner(Protocol):
    """What the job needs from systemd."""

    def start_update(self, kind: str, package: str = "") -> None: ...
    def update_active(self) -> bool: ...


@dataclass
class Reading:
    """What a status file says so far."""

    job: str = "idle"
    fraction: float = 0.0
    package: str = ""
    verdict: tuple | None = None
    #: The module package an install or remove job is about.
    module: str = ""


def read(text: str, reading: Reading | None = None) -> Reading:
    """Every complete line of `text`, applied to `reading`."""
    reading = reading or Reading()
    for line in text.splitlines():
        head, _, rest = line.partition(":")
        if head == "kidux":
            what, _, value = rest.partition(":")
            if what == "job":
                reading.job = JOBS.get(value, "idle")
            elif what == "module":
                reading.module = value
            elif what == "checked":
                _count, _, names = value.partition(":")
                reading.verdict = ("checked", "", [n for n in names.split(",") if n])
            elif what == "done":
                reading.verdict = (value, "", [])
            elif what == "failed":
                reading.verdict = ("failed", value, [])
        elif head in ("dlstatus", "pmstatus"):
            # dlstatus:<package>:<percent>:<text> and the same for pmstatus.
            parts = rest.split(":", 2)
            if len(parts) < 2:
                continue
            try:
                percent = float(parts[1]) / 100
            except ValueError:
                continue
            percent = min(1.0, max(0.0, percent))
            if reading.job in ("applying", "installing", "removing"):
                percent = (percent * DOWNLOAD_SHARE if head == "dlstatus"
                           else DOWNLOAD_SHARE + percent * (1 - DOWNLOAD_SHARE))
            reading.fraction = max(reading.fraction, percent)
            reading.package = parts[0]
    return reading


@dataclass
class Last:
    """The last job's outcome, for a panel that asks after the signals."""

    outcome: str = ""
    detail: str = ""
    packages: list[str] = field(default_factory=list)


class Updates:
    def __init__(
        self,
        runner: Runner,
        *,
        status: Path = STATUS,
        emit: Callable[[str, str, str, tuple], None] = lambda *signal: None,
        audit: Callable[..., None] = lambda *a, **k: None,
    ) -> None:
        self._runner = runner
        self._status = status
        self._emit = emit
        self._audit = audit
        self._offset = 0
        self._partial = ""
        self.reading = Reading()
        self.last = Last()

    @property
    def job(self) -> str:
        return self.reading.job

    def running(self) -> bool:
        return self.reading.job != "idle"

    def start(self, kind: str, package: str = "") -> None:
        if self.running() or self._runner.update_active():
            raise Busy("an update is already running")
        self._status.unlink(missing_ok=True)
        self._offset, self._partial = 0, ""
        self._runner.start_update(kind, package)
        self.reading = Reading(job=JOBS[kind], package=package, module=package)
        self.last = Last()

    def state(self) -> tuple:
        return (self.reading.job, float(self.reading.fraction), self.reading.package,
                self.last.outcome, self.last.detail, list(self.last.packages))

    def _new_text(self) -> str:
        try:
            with open(self._status, encoding="utf-8", errors="replace") as handle:
                handle.seek(self._offset)
                text = handle.read()
                self._offset = handle.tell()
        except OSError:
            return ""
        text = self._partial + text
        complete, _, self._partial = text.rpartition("\n")
        return complete + "\n" if complete else ""

    def poll(self) -> bool:
        """Read what the job has written since last time. True while it runs."""
        if not self.running():
            return False
        before = (round(self.reading.fraction, 2), self.reading.package)
        job, module = self.reading.job, self.reading.module
        self.reading = read(self._new_text(), self.reading)
        self.reading.job = self.reading.job if self.reading.job != "idle" else job
        self.reading.module = self.reading.module or module
        if (round(self.reading.fraction, 2), self.reading.package) != before:
            self._emit("System1", "UpdateProgress", "(ds)",
                       (float(self.reading.fraction), self.reading.package))
        if self.reading.verdict is None and not self._runner.update_active():
            # One more look: the unit may have written its last line and gone.
            self.reading = read(self._new_text(), self.reading)
            if self.reading.verdict is None:
                self.reading.verdict = ("failed", "the update stopped before it finished", [])
        if self.reading.verdict is not None:
            self._finish()
            return False
        return True

    def resume(self) -> bool:
        """After the daemon starts: watch a job still running, or report one
        that finished while the daemon was away. True if one is running."""
        if not self._status.exists():
            return False
        self._offset, self._partial = 0, ""
        self.reading = read(self._new_text())
        if self.reading.job == "idle":
            self._status.unlink(missing_ok=True)
            return False
        if self.reading.verdict is None and self._runner.update_active():
            return True
        self.poll()  # the verdict, emitted once; or "stopped" if there is none
        return False

    def _finish(self) -> None:
        outcome, detail, packages = self.reading.verdict
        job = self.reading.job
        if job == "checking":
            if outcome == "checked":
                self._emit("System1", "UpdatesChecked", "(uass)", (len(packages), packages, ""))
                self.last = Last("checked", "", list(packages))
            else:
                self._emit("System1", "UpdatesChecked", "(uass)", (0, [], detail))
                self.last = Last("failed", detail, [])
            self._audit("update check", "ok" if outcome == "checked" else "failed",
                        count=len(packages), detail=detail)
        elif job in MODULE_JOBS:
            self._emit("System1", "UpdateFinished", "(ss)", (outcome, detail))
            self.last = Last(outcome, detail, [])
            module = self.reading.module
            self._audit(MODULE_JOBS[job], "failed" if outcome == "failed" else "ok",
                        module=module[len(PREFIX):] if module.startswith(PREFIX) else module,
                        detail=detail)
            # Every launcher and panel reads its modules again.
            self._emit("Modules1", "ModulesChanged", "(s)", ("",))
        else:
            self._emit("System1", "UpdateFinished", "(ss)", (outcome, detail))
            self.last = Last(outcome, detail, [])
            self._audit("update finished", "failed" if outcome == "failed" else "ok",
                        result=outcome, detail=detail)
        self.reading = Reading()
        self._status.unlink(missing_ok=True)
