#!/usr/bin/python3
"""Find the version of each of PhET's simulations the Simulations module
serves, and write it into sims.toml with its SHA-256 (phase-4f-plan.md,
4.30).

    ci/upstream/simulations-versions.py            fill in what sims.toml leaves empty
    ci/upstream/simulations-versions.py --again    look again at every simulation
    ci/upstream/simulations-versions.py --sums     the sums of the versions written, again

Run by hand, when the list changes; its result is committed, and the build
(ci/upstream/simulations.sh) only takes what sims.toml says. For each
simulation it is the newest version PhET serves whose file was built
before sims.toml's cutoff and does not name the Creative Commons
NonCommercial licence: the historical versions, which PhET's agreement for
them keeps under CC BY 4.0. A file built in 2026 names CC BY 4.0 itself; an
older one names no licence and links to PhET's licensing page, where that
agreement is. It starts from the
version PhET's metadata says is current and tries the versions below it,
asking only whether each is there, and reads a file only when it is,
with curl as ci/upstream/fetch.sh reads it: the site's front, Cloudflare,
adds a script of its own analytics to what some programs are sent, and
the sums are of the file the build gets. A file that loads any script
from elsewhere is refused, here and in the build.
The files it takes are kept in build/upstream/simulations/, to be looked
at; the build fetches its own.
"""

import hashlib
import json
import re
import subprocess
import sys
import tomllib
import urllib.error
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
LIST = REPO / "packages" / "kidux-module-simulations" / "sims.toml"
KEPT = REPO / "build" / "upstream" / "simulations"
METADATA = ("https://phet.colorado.edu/services/metadata/1.3/simulations"
            "?format=json&type=html&locale=en&summary")
SITE = "https://phet.colorado.edu/sims/html"
AGENT = {"User-Agent": "Kidux (https://kidux.org)"}
#: How far below the current version to look: patches of a minor, minors of
#: a major, and the major before.
PATCHES = 60
MINORS = 10

BUILT = re.compile(r"buildTimestamp = '(\d{4}-\d{2}-\d{2}) ")
#: A script loaded from another server, such as Cloudflare's analytics.
FOREIGN_SCRIPT = re.compile(r"<script[^>]*\ssrc=[\"']?(https?:)?//", re.I)
CC_BY_NC = "creativecommons.org/licenses/by-nc/"


def url(sim: str, version: str) -> str:
    return f"{SITE}/{sim}/{version}/{sim}_all.html"


def there(address: str) -> bool:
    request = urllib.request.Request(address, method="HEAD", headers=AGENT)
    try:
        with urllib.request.urlopen(request, timeout=30) as answer:
            return answer.status == 200
    except urllib.error.HTTPError:
        return False


def fetched(address: str) -> bytes:
    """A file as ci/upstream/fetch.sh fetches it, the same bytes."""
    return subprocess.run(["curl", "-fsSL", "--retry", "3", "--retry-all-errors",
                           "--connect-timeout", "30", address],
                          capture_output=True, check=True).stdout


def judged(data: bytes, cutoff: str) -> str:
    """Why a file will not do, or "" when it will."""
    text = data.decode("utf-8", errors="replace")
    built = BUILT.search(text)
    if not built:
        return "no buildTimestamp"
    if built.group(1) >= cutoff:
        return f"built {built.group(1)}"
    if CC_BY_NC in text:
        return "names CC BY-NC"
    if FOREIGN_SCRIPT.search(text):
        return "loads a script from elsewhere"
    return ""


def candidates(current: str):
    """The versions at and below the current one, newest first."""
    major, minor, patch = (int(part) for part in current.split("."))
    yield from (f"{major}.{minor}.{p}" for p in range(patch, -1, -1))
    for m in range(minor - 1, max(-1, minor - 1 - MINORS), -1):
        yield from (f"{major}.{m}.{p}" for p in range(PATCHES, -1, -1))
    if major > 1:
        for m in range(MINORS, -1, -1):
            yield from (f"{major - 1}.{m}.{p}" for p in range(PATCHES, -1, -1))


def find(sim: str, current: str, cutoff: str) -> tuple[str, str]:
    for version in candidates(current):
        if not there(url(sim, version)):
            continue
        data = fetched(url(sim, version))
        why = judged(data, cutoff)
        print(f"    {sim} {version}: {why or 'taken'}", flush=True)
        if not why:
            KEPT.mkdir(parents=True, exist_ok=True)
            (KEPT / f"{sim}_{version}_all.html").write_bytes(data)
            return version, hashlib.sha256(data).hexdigest()
    raise SystemExit(f"{sim}: no version from {current} down was built before {cutoff} "
                     "without CC BY-NC")


def current_versions() -> dict[str, str]:
    metadata = json.loads(fetched(METADATA))
    found = {}
    for project in metadata["projects"]:
        version = project.get("version", {}).get("string", "")
        for simulation in project.get("simulations", []):
            found[simulation["name"]] = version
    return found


def written(text: str, sim: str, version: str, sha256: str) -> str:
    """sims.toml with one simulation's version and sum in place."""
    section = re.compile(rf'(^\[sims\.{re.escape(sim)}\]\n(?:(?!^\[).*\n)*?)'
                         r'version = ".*"\nsha256 = ".*"', re.M)
    new, count = section.subn(rf'\g<1>version = "{version}"\nsha256 = "{sha256}"', text)
    if count != 1:
        raise SystemExit(f"sims.toml has no version and sha256 lines for {sim}")
    return new


def main(args: list[str]) -> int:
    again = args[1:] == ["--again"]
    listed = tomllib.loads(LIST.read_text())
    cutoff = listed["cutoff"]
    if args[1:] == ["--sums"]:
        text = LIST.read_text()
        for sim, entry in listed["sims"].items():
            data = fetched(url(sim, entry["version"]))
            why = judged(data, cutoff)
            if why:
                raise SystemExit(f"{sim} {entry['version']}: {why}")
            KEPT.mkdir(parents=True, exist_ok=True)
            (KEPT / f"{sim}_{entry['version']}_all.html").write_bytes(data)
            text = written(text, sim, entry["version"], hashlib.sha256(data).hexdigest())
            print(f"    {sim} {entry['version']}", flush=True)
        LIST.write_text(text)
        return 0
    current = current_versions()
    text = LIST.read_text()
    for sim, entry in listed["sims"].items():
        if entry.get("version") and entry.get("sha256") and not again:
            continue
        if sim not in current:
            raise SystemExit(f"{sim}: PhET's metadata has no such simulation")
        print(f"==> {sim}, current {current[sim]}", flush=True)
        version, sha256 = find(sim, current[sim], cutoff)
        text = written(text, sim, version, sha256)
        LIST.write_text(text)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
