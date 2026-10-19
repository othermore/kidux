#!/usr/bin/python3
"""How many machines follow the public archive, from the hosting's access logs.

    ci/usage.py fetch [--since YYYY-MM-DD]   keep every day's log not kept yet, up to yesterday
    ci/usage.py report [--days N] [--today] [--html] [FILE…]
                                             the numbers, from the logs kept (or the files
                                             given); with --today, today's so far too; with
                                             --html, as a page rather than as text

The archive is served by the project's web hosting at https://apt.kidux.org
(D109), whose web server writes one access log a day, on
https://logs.cluster131.hosting.ovh.net/<space>/ behind the logs user's
password. `fetch` downloads each day it has not kept, as gzip, into
~/.local/share/kidux/usage/ (KIDUX_USAGE_DIR names another folder), so that
the history does not depend on how long the hosting keeps it; the logs
user's line is in the same netrc file as the SFTP one,
~/.config/kidux/apt-hosting.netrc (`machine logs.cluster131.hosting.ovh.net
login <user> password <password>`), and nothing here prints or passes it.

`report` counts, for each day, the machines that looked for updates, that
is, fetched dists/stable/InRelease, as apt does once a day:

- with an identifier: the distinct identifiers after `Kidux/` in
  `Debian APT-HTTP/1.3 Kidux/<32 hex>`, one per machine whose adult shares
  usage statistics (statistics.py of kidux-daemon);
- without one: the distinct addresses that sent `Debian APT-HTTP/1.3 Kidux`
  alone, a household behind one address counting once;
- other apt clients, and the packages Kidux machines downloaded, by version.

Identifiers made by tests never count: those that begin with sixteen zeros,
and those listed in ci/usage-test-ids.txt. Only lines of apt.kidux.org are
read, whatever else the space's log holds.

It runs on the release machine and on the hosting itself, whose Python is
3.7 (Debian 10), behind the page https://apt.kidux.org/usage/ that
ci/publish-usage.sh puts there; so it keeps to what Python 3.7 has.
"""

from __future__ import annotations

import argparse
import datetime
import gzip
import html
import netrc
import os
import re
import sys
import urllib.error
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path

HOST = "logs.cluster131.hosting.ovh.net"
SPACE = "kidux.org"
SITE = "apt.kidux.org"
NETRC = Path(os.environ.get("KIDUX_APT_HOSTING", Path.home() / ".config/kidux/apt-hosting.netrc"))
KEPT = Path(os.environ.get("KIDUX_USAGE_DIR", Path.home() / ".local/share/kidux/usage"))
TEST_IDS = Path(__file__).resolve().parent / "usage-test-ids.txt"
#: The first day the archive was at apt.kidux.org.
FIRST_DAY = datetime.date(2026, 10, 18)

#: An access log line: address, site, the time, the request, status, size,
#: referrer and user agent. A user agent may hold quotes of its own.
LINE = re.compile(r'^(?P<address>\S+) (?P<site>\S+) \S+ \[(?P<time>[^\]]+)\] '
                  r'"(?P<method>\S+) (?P<path>\S+)[^"]*" (?P<status>\d{3}) \S+ '
                  r'"[^"]*" "(?P<agent>.*)"$')
KIDUX = "Debian APT-HTTP/1.3 Kidux"
IDENTIFIED = re.compile(r"^Debian APT-HTTP/1\.3 Kidux/([0-9a-f]{32})$")
PACKAGE = re.compile(r"^/pool/main/[^/]+/[^/]+/([^_/]+)_([^_/]+)_[^_/]+\.deb$")


def test_ids() -> set[str]:
    if not TEST_IDS.exists():
        return set()
    return {line.split("#")[0].strip() for line in TEST_IDS.read_text().splitlines()} - {""}


def is_test(identifier: str, known: set[str]) -> bool:
    return identifier.startswith("0" * 16) or identifier in known


def parse(lines, known: set[str] | None = None) -> dict:
    """The day's numbers, by day, from access log lines (text)."""
    known = test_ids() if known is None else known
    days = defaultdict(lambda: {"ids": set(), "anonymous": set(), "other_apt": set(),
                                "downloads": Counter(), "tests": set(), "other": 0})
    for line in lines:
        found = LINE.match(line.rstrip("\n"))
        if not found or found["site"] != SITE:
            continue
        day = datetime.datetime.strptime(found["time"], "%d/%b/%Y:%H:%M:%S %z").date()
        numbers = days[day]
        agent, path, ok = found["agent"], found["path"], found["status"] in ("200", "304")
        identified = IDENTIFIED.match(agent)
        if not agent.startswith("Debian APT-HTTP/"):
            numbers["other"] += 1
            continue
        if identified and is_test(identified[1], known):
            numbers["tests"].add(identified[1])
            continue
        if path == "/dists/stable/InRelease" and ok:
            if identified:
                numbers["ids"].add(identified[1])
            elif agent == KIDUX:
                numbers["anonymous"].add(found["address"])
            else:
                numbers["other_apt"].add(found["address"])
        package = PACKAGE.match(path)
        if package and ok and agent.startswith(KIDUX):
            numbers["downloads"][(package[1], package[2])] += 1
    return dict(days)


def kept_files() -> list[Path]:
    return sorted(KEPT.glob(f"{SPACE}-*.log.gz"), key=lambda p: day_of(p))


def day_of(path: Path) -> datetime.date:
    stamp = re.search(r"(\d{4}-\d{2}-\d{2})", path.name)[1]
    return datetime.date.fromisoformat(stamp)


def read(path: Path) -> list[str]:
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="utf-8", errors="replace") as handle:
        return handle.readlines()


def summary(numbers: dict, days: int | None) -> dict:
    """The rows of the report and its totals, from parse()'s days."""
    shown = sorted(numbers)
    if days:
        shown = shown[-days:]
    rows, every_id, downloads, tests = [], set(), Counter(), set()
    for day in shown:
        n = numbers[day]
        every_id |= n["ids"]
        downloads.update(n["downloads"])
        tests |= n["tests"]
        rows.append({"day": day, "machines": len(n["ids"]) + len(n["anonymous"]),
                     "ids": len(n["ids"]), "anonymous": len(n["anonymous"]),
                     "other_apt": len(n["other_apt"]),
                     "downloads": sum(n["downloads"].values()), "other": n["other"]})
    return {"rows": rows, "machines_with_id": len(every_id), "tests": len(tests),
            "downloads": sorted(downloads.items())}


COLUMNS = (("machines", "machines"), ("ids", "by id"), ("anonymous", "no id"),
           ("other_apt", "other apt"), ("downloads", "downloads"), ("other", "others"))
LEGEND = ("machines: by id plus no id, the machines that looked for updates that day. "
          "no id: distinct addresses of Kidux machines without an identifier. "
          "others: requests that were not apt's, browsers and crawlers.")


def as_text(report: dict, today: datetime.date | None) -> str:
    out = [f"{'day':<12}" + "".join(f"{title:>11}" for _, title in COLUMNS)]
    for row in report["rows"]:
        mark = " (so far)" if row["day"] == today else ""
        out.append(f"{row['day'].isoformat():<12}"
                   + "".join(f"{row[key]:>11}" for key, _ in COLUMNS) + mark)
    out += ["", f"Machines with an identifier over these {len(report['rows'])} days: "
                f"{report['machines_with_id']}"]
    if report["tests"]:
        out.append(f"Identifiers of tests, not counted: {report['tests']}")
    if report["downloads"]:
        out.append("Packages Kidux machines downloaded:")
        out += [f"  {package} {version}: {count}" for (package, version), count in report["downloads"]]
    out += ["", LEGEND]
    return "\n".join(out)


def as_html(report: dict, today: datetime.date | None) -> str:
    """The report as a page of its own, with nothing it fetches."""
    def cell(value) -> str:
        return f"<td>{html.escape(str(value))}</td>"
    head = "".join(f"<th>{html.escape(title)}</th>" for _, title in COLUMNS)
    body = "".join(
        f"<tr><td>{row['day'].isoformat()}{' <small>so far</small>' if row['day'] == today else ''}</td>"
        + "".join(cell(row[key]) for key, _ in COLUMNS) + "</tr>"
        for row in reversed(report["rows"]))
    downloads = "".join(f"<li>{html.escape(package)} {html.escape(version)}: {count}</li>"
                        for (package, version), count in report["downloads"])
    made = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex">
<title>Kidux machines</title>
<style>
body {{ background: #fdf6f0; color: #24313f; font: 16px/1.5 system-ui, sans-serif;
       margin: 0 auto; max-width: 860px; padding: 16px; }}
h1 {{ font-size: 1.4em; }}
table {{ border-collapse: collapse; width: 100%; }}
th, td {{ padding: 6px 8px; text-align: right; border-bottom: 1px solid #e6d9cc; }}
th:first-child, td:first-child {{ text-align: left; }}
.wide {{ overflow-x: auto; }}
p.note {{ color: #5b6672; font-size: 0.9em; }}
</style></head><body>
<h1>Kidux machines that follow apt.kidux.org</h1>
<p><strong>{report["machines_with_id"]}</strong> machines with an identifier over these
{len(report["rows"])} days{f"; {report['tests']} identifiers of tests not counted" if report["tests"] else ""}.</p>
<div class="wide"><table><thead><tr><th>day</th>{head}</tr></thead><tbody>{body}</tbody></table></div>
{f"<h2>Packages Kidux machines downloaded</h2><ul>{downloads}</ul>" if downloads else ""}
<p class="note">{html.escape(LEGEND)}</p>
<p class="note">Made {made} from the hosting's access logs (ci/usage.py).</p>
</body></html>
"""


def report(files: list[Path], days: int | None, today: bool = False, page: bool = False) -> int:
    lines = []
    for path in files:
        lines += read(path)
    day = None
    if today:
        login, password = credentials()
        day = datetime.date.today()
        body = download(day, login, password)
        if body:
            lines += body.decode("utf-8", "replace").splitlines()
    numbers = parse(lines)
    if not numbers:
        print("No requests of apt.kidux.org in what was read.")
        return 0
    result = summary(numbers, days)
    print(as_html(result, day) if page else as_text(result, day))
    return 0


def credentials() -> tuple[str, str]:
    try:
        entry = netrc.netrc(NETRC).authenticators(HOST)
    except (FileNotFoundError, netrc.NetrcParseError) as error:
        sys.exit(f"{sys.argv[0]}: cannot read {NETRC}: {error}")
    if not entry:
        sys.exit(f"{sys.argv[0]}: {NETRC} has no line for {HOST}: "
                 f"machine {HOST} login <logs user> password <password>")
    return entry[0], entry[2]


def download(day: datetime.date, login: str, password: str) -> bytes | None:
    """The day's log, or None when the hosting has none for it."""
    stamp = day.strftime("%d-%m-%Y")
    candidates = [f"https://{HOST}/{SPACE}/osl/{SPACE}-{stamp}.log",
                  f"https://{HOST}/{SPACE}/osl/{SPACE}-{stamp}.log.gz",
                  f"https://{HOST}/{SPACE}/logs/logs-{day:%m-%Y}/{SPACE}-{stamp}.log.gz"]
    manager = urllib.request.HTTPPasswordMgrWithDefaultRealm()
    manager.add_password(None, f"https://{HOST}/", login, password)
    opener = urllib.request.build_opener(urllib.request.HTTPBasicAuthHandler(manager))
    for url in candidates:
        try:
            with opener.open(url, timeout=60) as answer:
                body = answer.read()
                kind = answer.headers.get("Content-Type", "")
        except urllib.error.HTTPError as error:
            if error.code in (401, 403):
                sys.exit(f"{sys.argv[0]}: the logs user may not open {url} ({error.code})")
            continue
        if "html" in kind:
            # A page instead of a log: a login form, or a listing.
            continue
        if url.endswith(".gz"):
            body = gzip.decompress(body)
        return body
    return None


def fetch(since: datetime.date) -> int:
    login, password = credentials()
    KEPT.mkdir(parents=True, exist_ok=True, mode=0o700)
    kept = {day_of(p) for p in kept_files()}
    day, yesterday, missing = since, datetime.date.today() - datetime.timedelta(days=1), []
    while day <= yesterday:
        if day not in kept:
            body = download(day, login, password)
            if body is None:
                missing.append(day)
            else:
                target = KEPT / f"{SPACE}-{day.isoformat()}.log.gz"
                # Written aside and renamed, so that a report read meanwhile
                # never finds half a day.
                partial = target.with_name(target.name + ".partial")
                with gzip.open(partial, "wb") as handle:
                    handle.write(body)
                partial.chmod(0o600)
                partial.replace(target)
                lines = body.count(b"\n")
                print(f"kept {target.name}, {lines} lines")
        day += datetime.timedelta(days=1)
    for day in missing:
        print(f"no log for {day.isoformat()} on the hosting", file=sys.stderr)
    return 0


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = parser.add_subparsers(dest="command", required=True)
    fetching = commands.add_parser("fetch")
    fetching.add_argument("--since", type=datetime.date.fromisoformat, default=FIRST_DAY)
    reporting = commands.add_parser("report")
    reporting.add_argument("--days", type=int)
    reporting.add_argument("--today", action="store_true")
    reporting.add_argument("--html", action="store_true")
    reporting.add_argument("files", nargs="*", type=Path)
    asked = parser.parse_args(argv[1:])
    if asked.command == "fetch":
        return fetch(asked.since)
    return report(asked.files or kept_files(), asked.days, asked.today, asked.html)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
