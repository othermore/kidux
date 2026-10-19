#!/usr/bin/python3
"""How many machines follow the public archive, from the hosting's access logs.

    ci/usage.py fetch [--since YYYY-MM-DD]   keep every day's log not kept yet, up to yesterday
    ci/usage.py report [--days N] [--today] [--html] [FILE…]
                                             the numbers, from the logs kept (or the files
                                             given); with --today, today's so far too; with
                                             --html, as a page rather than as text
    ci/usage.py page [--view V] [--value X] [--today]
                                             a page of https://apt.kidux.org/usage/: the
                                             summary, the machines (ids) or one (id), the
                                             addresses or one (address), a query of the
                                             database (sql, KIDUX_USAGE_SQL), or the database's
                                             table as CSV (csv)

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
- other apt clients, and the packages Kidux machines downloaded, by version;

and the same by week and by month, with an estimate of the machines in all:
the machines with an identifier show how many machines usually come from
one address, the median, and each address without one counts as that many.
Last, the places many machines come from, an address or a range of near
ones (a /24, or an IPv6 /48), which may be a school or a centre.

Identifiers made by tests never count: those that begin with sixteen zeros,
and those listed in ci/usage-test-ids.txt. Only lines of apt.kidux.org are
read, whatever else the space's log holds.

To explore, every view but the summary first makes a database again from
the logs kept, usage.sqlite beside them: a row a day, address, identifier,
client, kind of request, package and user agent, with how many requests
(SCHEMA says it), which a query reads and cannot change.

It runs on the release machine and on the hosting itself, whose Python is
3.7 (Debian 10), behind the page https://apt.kidux.org/usage/ that
ci/publish-usage.sh puts there; so it keeps to what Python 3.7 has.
"""

from __future__ import annotations

import argparse
import datetime
import gzip
import html
import ipaddress
import netrc
import os
import csv
import re
import sqlite3
import statistics
import sys
import urllib.error
import urllib.request
from urllib.parse import quote
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


def records(lines, known: set[str] | None = None):
    """Each line of apt.kidux.org, simplified: the day, the address, the
    identifier if any, who asked (`kidux`, a Kidux machine, with or without
    an identifier; `test`, a test machine's identifier; `apt`, another apt;
    `web`, a browser or a crawler), what (`index`, InRelease; `lists`, the
    other indexes; `package`, a .deb, with its name and version; `other`;
    `error`, an answer that was not 200 or 304), and the user agent of a
    client that is not Kidux's. What the database holds, a request a row."""
    known = test_ids() if known is None else known
    for line in lines:
        found = LINE.match(line.rstrip("\n"))
        if not found or found["site"] != SITE:
            continue
        agent, path = found["agent"], found["path"]
        identified = IDENTIFIED.match(agent)
        identifier = identified[1] if identified else None
        if not agent.startswith("Debian APT-HTTP/"):
            client = "web"
        elif identifier and is_test(identifier, known):
            client = "test"
        elif identifier or agent == KIDUX:
            client = "kidux"
        else:
            client = "apt"
        package = PACKAGE.match(path)
        if found["status"] not in ("200", "304"):
            kind = "error"
        elif path == "/dists/stable/InRelease":
            kind = "index"
        elif package:
            kind = "package"
        elif path.startswith("/dists/"):
            kind = "lists"
        else:
            kind = "other"
        yield {"day": datetime.datetime.strptime(found["time"], "%d/%b/%Y:%H:%M:%S %z").date(),
               "address": found["address"], "identifier": identifier, "client": client,
               "kind": kind, "package": package[1] if package else None,
               "version": package[2] if package else None,
               "agent": agent if client in ("apt", "web") else None}


def parse(lines, known: set[str] | None = None) -> dict:
    """The day's numbers, by day, from access log lines (text)."""
    days = defaultdict(lambda: {"ids": set(), "pairs": set(), "anonymous": set(),
                                "other_apt": set(), "downloads": Counter(), "tests": set(),
                                "other": 0})
    for record in records(lines, known):
        numbers, client, kind = days[record["day"]], record["client"], record["kind"]
        if client == "web":
            numbers["other"] += 1
            continue
        if client == "test":
            numbers["tests"].add(record["identifier"])
            continue
        if kind == "index":
            if client == "kidux" and record["identifier"]:
                numbers["ids"].add(record["identifier"])
                numbers["pairs"].add((record["identifier"], record["address"]))
            elif client == "kidux":
                numbers["anonymous"].add(record["address"])
            else:
                numbers["other_apt"].add(record["address"])
        if kind == "package" and client == "kidux":
            numbers["downloads"][(record["package"], record["version"])] += 1
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


#: How many of each period the report shows, the latest last.
SHOWN = {"day": 14, "week": 8, "month": 12}
#: A place shows when this many machines with an identifier come from it.
MANY = 3
#: The places are looked for over the last this many days.
PLACES_DAYS = 30


def period_of(day: datetime.date, kind: str) -> str:
    if kind == "day":
        return day.isoformat()
    if kind == "week":
        year, week, _ = day.isocalendar()
        return f"{year}-W{week:02d}"
    return f"{day:%Y-%m}"


def merged(numbers: dict, days: list) -> dict:
    """One period's numbers, from its days'."""
    out = {"ids": set(), "pairs": set(), "anonymous": set(), "other_apt": set(),
           "downloads": Counter(), "tests": set(), "other": 0}
    for day in days:
        n = numbers[day]
        for key in ("ids", "pairs", "anonymous", "other_apt", "tests"):
            out[key] |= n[key]
        out["downloads"].update(n["downloads"])
        out["other"] += n["other"]
    return out


def estimate(n: dict) -> tuple[float, float]:
    """Machines behind an address, as the machines with an identifier show
    it, and the machines estimated in all: those with an identifier, and
    each address without one taken to hide as many. The median, not the
    mean, so that a school's thirty machines behind one address do not make
    every household count as several."""
    behind = Counter(address for _, address in n["pairs"])
    per_address = max(1.0, float(statistics.median(behind.values()))) if behind else 1.0
    return per_address, len(n["ids"]) + len(n["anonymous"]) * per_address


def network(address: str) -> str:
    """The range an address is in: its /24, or for IPv6 its /48."""
    try:
        ip = ipaddress.ip_address(address)
    except ValueError:
        return address
    size = 24 if ip.version == 4 else 48
    return str(ipaddress.ip_network(f"{address}/{size}", strict=False))


def places(n: dict) -> dict:
    """Addresses and ranges many machines come from: schools, clubs, offices."""
    by_address, by_range, range_addresses = defaultdict(set), defaultdict(set), defaultdict(set)
    for identifier, address in n["pairs"]:
        by_address[address].add(identifier)
        by_range[network(address)].add(identifier)
        range_addresses[network(address)].add(address)
    anonymous_in = Counter(network(address) for address in n["anonymous"])
    addresses = sorted(((a, len(m)) for a, m in by_address.items() if len(m) >= MANY),
                       key=lambda item: -item[1])
    ranges = sorted(((r, len(m), len(range_addresses[r]), anonymous_in[r])
                     for r, m in by_range.items()
                     if len(m) >= MANY and len(range_addresses[r]) > 1),
                    key=lambda item: -item[1])
    machines_per_address = Counter(len(m) for m in by_address.values())
    return {"addresses": addresses, "ranges": ranges,
            "machines_per_address": sorted(machines_per_address.items())}


def summary(numbers: dict, days: int | None) -> dict:
    """Every table of the report, from parse()'s days."""
    every = sorted(numbers)
    if days:
        every = every[-days:]
    tables = {}
    for kind in ("day", "week", "month"):
        grouped = defaultdict(list)
        for day in every:
            grouped[period_of(day, kind)].append(day)
        rows = []
        for period in sorted(grouped)[-SHOWN[kind]:]:
            n = merged(numbers, grouped[period])
            per_address, total = estimate(n)
            rows.append({"period": period, "ids": len(n["ids"]), "anonymous": len(n["anonymous"]),
                         "per_address": per_address, "estimate": round(total),
                         "other_apt": len(n["other_apt"]),
                         "downloads": sum(n["downloads"].values()), "other": n["other"]})
        tables[kind] = rows
    recent = [day for day in every if day > every[-1] - datetime.timedelta(days=PLACES_DAYS)]
    window = merged(numbers, recent)
    whole = merged(numbers, every)
    return {"tables": tables, "places": places(window), "tests": len(whole["tests"]),
            "downloads": sorted(whole["downloads"].items()), "first": every[0], "last": every[-1]}


COLUMNS = (("period", ""), ("ids", "with id"), ("anonymous", "addresses without id"),
           ("per_address", "machines per address"), ("estimate", "estimated machines"),
           ("other_apt", "other apt"), ("downloads", "downloads"), ("other", "others"))
#: The same columns, in the few letters a terminal has room for.
SHORT = {"ids": "with id", "anonymous": "no-id addr", "per_address": "per addr",
         "estimate": "estimate", "other_apt": "other apt", "downloads": "downloads",
         "other": "others"}
TITLES = {"day": "Machines by day", "week": "Machines by week", "month": "Machines by month"}
LEGEND = ("with id: distinct machines that looked for updates and share usage statistics. "
          "addresses without id: distinct addresses of Kidux machines that do not. "
          "machines per address: how many machines with an identifier usually come from one "
          "address, the median. estimated machines: those with an identifier, and each address without "
          "one counted as that many. Over a week or a month an address that changes counts "
          "more than once, so the day's estimate is the steadiest. others: requests that were "
          "not apt's, browsers and crawlers.")


def shown(row: dict, key: str, today: str | None):
    value = row[key]
    if key == "per_address":
        return f"{value:.2f}"
    if key == "period" and value == today:
        return f"{value} (so far)"
    return value


def as_text(report: dict, today: datetime.date | None) -> str:
    mark = today.isoformat() if today else None
    out = []
    for kind, rows in report["tables"].items():
        out.append(TITLES[kind])
        out.append(f"{'':<14}" + "".join(f"{SHORT[key]:>12}" for key, _ in COLUMNS[1:]))
        for row in rows:
            out.append(f"{shown(row, 'period', mark):<14}"
                       + "".join(f"{shown(row, key, mark):>12}" for key, _ in COLUMNS[1:]))
        out.append("")
    p = report["places"]
    out.append(f"Places with {MANY} machines or more, over the last {PLACES_DAYS} days")
    if not p["addresses"] and not p["ranges"]:
        out.append("  none")
    for address, machines in p["addresses"]:
        out.append(f"  address {address}: {machines} machines")
    for network_, machines, addresses, anonymous in p["ranges"]:
        out.append(f"  range {network_}: {machines} machines from {addresses} addresses"
                   f"{f', and {anonymous} addresses without id' if anonymous else ''}")
    out.append("Addresses by the machines with an identifier behind them: "
               + ", ".join(f"{machines} machine{'s' if machines > 1 else ''}: {count}"
                           for machines, count in p["machines_per_address"]))
    if report["tests"]:
        out.append(f"\nIdentifiers of tests, not counted: {report['tests']}")
    if report["downloads"]:
        out.append("\nPackages Kidux machines downloaded:")
        out += [f"  {package} {version}: {count}" for (package, version), count in report["downloads"]]
    out += ["", LEGEND]
    return "\n".join(out)


def as_html(report: dict, today: datetime.date | None) -> str:
    """The report as the body of a page, which shell() frames."""
    mark = today.isoformat() if today else None
    e = html.escape
    sections = []
    for kind, rows in report["tables"].items():
        head = "".join(f"<th>{e(title)}</th>" for _, title in COLUMNS)
        body = "".join("<tr>" + "".join(f"<td>{e(str(shown(row, key, mark)))}</td>"
                                         for key, _ in COLUMNS) + "</tr>"
                       for row in reversed(rows))
        sections.append(f"<h2>{e(TITLES[kind])}</h2><div class=\"wide\"><table><thead><tr>"
                        f"{head}</tr></thead><tbody>{body}</tbody></table></div>")
    p = report["places"]
    items = [f"<li>address {e(a)}: <strong>{m}</strong> machines</li>" for a, m in p["addresses"]]
    items += [f"<li>range {e(r)}: <strong>{m}</strong> machines from {a} addresses"
              f"{f', and {n} addresses without id' if n else ''}</li>"
              for r, m, a, n in p["ranges"]]
    spread = ", ".join(f"{m} machine{'s' if m > 1 else ''}: {c}" for m, c in p["machines_per_address"])
    sections.append(f"<h2>Places with {MANY} machines or more, over the last {PLACES_DAYS} days</h2>"
                    f"<ul>{''.join(items) or '<li>none</li>'}</ul>"
                    f"<p class=\"note\">Addresses by the machines with an identifier behind them: "
                    f"{e(spread) or 'none'}.</p>")
    if report["downloads"]:
        downloads = "".join(f"<li>{e(package)} {e(version)}: {count}</li>"
                            for (package, version), count in report["downloads"])
        sections.append(f"<h2>Packages Kidux machines downloaded</h2><ul>{downloads}</ul>")
    tests = f" {report['tests']} identifiers of tests are not counted." if report["tests"] else ""
    made = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    return (f"<p>From {report['first'].isoformat()} to {report['last'].isoformat()}.{e(tests)}</p>"
            + "".join(sections)
            + f"<p class=\"note\">{e(LEGEND)}</p>"
            + f"<p class=\"note\">Made {made} from the hosting's access logs (ci/usage.py).</p>")


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
    print(shell(TITLE, as_html(result, day)) if page else as_text(result, day))
    return 0


# --- The database, to explore ------------------------------------------------

DATABASE = "usage.sqlite"
TITLE = "Kidux machines that follow apt.kidux.org"
SCHEMA = """
CREATE TABLE requests (
    day TEXT NOT NULL,          -- YYYY-MM-DD, the hosting's own day
    address TEXT NOT NULL,      -- the address the request came from
    identifier TEXT,            -- a Kidux machine's, when it shares usage statistics
    client TEXT NOT NULL,       -- kidux, test, apt or web
    kind TEXT NOT NULL,         -- index, lists, package, other or error
    package TEXT, version TEXT, -- a package's, for kind package
    agent TEXT,                 -- the user agent, for clients apt and web
    requests INTEGER NOT NULL   -- how many such requests that day
);
CREATE VIEW machines AS         -- a Kidux machine with an identifier, a day and an address
    SELECT day, identifier, address, SUM(requests) AS requests FROM requests
    WHERE client = 'kidux' AND identifier IS NOT NULL GROUP BY day, identifier, address;
CREATE VIEW anonymous AS        -- an address of Kidux machines without an identifier, a day
    SELECT day, address, SUM(requests) AS requests FROM requests
    WHERE client = 'kidux' AND identifier IS NULL GROUP BY day, address;
"""
COLUMNS_OF_REQUESTS = ("day", "address", "identifier", "client", "kind", "package", "version",
                       "agent")
EXAMPLES = (
    ("Addresses with more than one machine",
     "SELECT address, COUNT(DISTINCT identifier) AS machines FROM machines\n"
     "GROUP BY address HAVING machines > 1 ORDER BY machines DESC"),
    ("Machines seen at more than one address",
     "SELECT identifier, COUNT(DISTINCT address) AS addresses, COUNT(DISTINCT day) AS days\n"
     "FROM machines GROUP BY identifier HAVING addresses > 1 ORDER BY addresses DESC"),
    ("Machines new each day",
     "SELECT first, COUNT(*) AS machines FROM\n"
     "(SELECT identifier, MIN(day) AS first FROM machines GROUP BY identifier)\n"
     "GROUP BY first ORDER BY first"),
    ("Packages downloaded by Kidux machines",
     "SELECT package, version, SUM(requests) AS downloads FROM requests\n"
     "WHERE client = 'kidux' AND kind = 'package' GROUP BY package, version\n"
     "ORDER BY downloads DESC"),
    ("Who else comes, by user agent",
     "SELECT client, agent, SUM(requests) AS requests FROM requests\n"
     "WHERE client IN ('apt', 'web') GROUP BY client, agent ORDER BY requests DESC"),
)
MOST_ROWS = 2000


def build(lines, path: Path) -> Path:
    """The database of these lines, made again whole: the kept logs are what
    it is made from, so it is never out of step with them."""
    counted = Counter(tuple(r[key] for key in COLUMNS_OF_REQUESTS[1:])
                      + (r["day"].isoformat(),) for r in records(lines))
    partial = path.with_name(path.name + ".partial")
    if partial.exists():
        partial.unlink()
    connection = sqlite3.connect(str(partial))
    with connection:
        connection.executescript(SCHEMA)
        connection.executemany(
            "INSERT INTO requests (address, identifier, client, kind, package, version, agent, "
            "day, requests) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [key + (count,) for key, count in counted.items()])
    connection.close()
    partial.chmod(0o600)
    partial.replace(path)
    return path


def read_only(path: Path) -> sqlite3.Connection:
    """The database, opened so that a query may read it and nothing more."""
    connection = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    allowed = {sqlite3.SQLITE_SELECT, sqlite3.SQLITE_READ, sqlite3.SQLITE_FUNCTION}

    def authorizer(action, *_):
        return sqlite3.SQLITE_OK if action in allowed else sqlite3.SQLITE_DENY
    connection.set_authorizer(authorizer)
    steps = {"n": 0}

    def progress():
        steps["n"] += 1
        return 1 if steps["n"] > 20000 else 0   # about a few seconds' work, then stop
    connection.set_progress_handler(progress, 1000)
    return connection


def query(connection: sqlite3.Connection, sql: str, parameters=()) -> tuple[list, list]:
    cursor = connection.execute(sql, parameters)
    names = [column[0] for column in cursor.description or ()]
    return names, cursor.fetchmany(MOST_ROWS)


def link(view: str, value: str, text: str | None = None) -> str:
    return (f'<a href="?view={view}&amp;value={html.escape(quote(value, safe=""))}">'
            f"{html.escape(text if text is not None else value)}</a>")


def table(names: list, rows: list, links: dict | None = None) -> str:
    """Rows as a table; a column named in `links` links each value to a view."""
    links = links or {}
    head = "".join(f"<th>{html.escape(str(name))}</th>" for name in names)
    body = []
    for row in rows:
        cells = []
        for name, value in zip(names, row):
            text = "" if value is None else str(value)
            cells.append(f"<td>{link(links[name], text) if name in links and text else html.escape(text)}</td>")
        body.append("<tr>" + "".join(cells) + "</tr>")
    more = (f"<p class=\"note\">The first {MOST_ROWS} rows only.</p>"
            if len(rows) >= MOST_ROWS else "")
    return (f"<div class=\"wide\"><table><thead><tr>{head}</tr></thead>"
            f"<tbody>{''.join(body)}</tbody></table></div>{more}")


def shell(title: str, body: str) -> str:
    nav = " · ".join(f'<a href="?view={view}">{name}</a>' for view, name in
                     (("summary", "Summary"), ("ids", "Machines"), ("addresses", "Addresses"),
                      ("sql", "Query"), ("csv", "Download the table")))
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex">
<title>Kidux machines</title>
<style>
body {{ background: #fdf6f0; color: #24313f; font: 16px/1.5 system-ui, sans-serif;
       margin: 0 auto; max-width: 1100px; padding: 16px; }}
h1 {{ font-size: 1.4em; }} h2 {{ font-size: 1.1em; margin-top: 1.6em; }}
nav {{ margin-bottom: 1em; }}
a {{ color: #1f5fa8; }}
table {{ border-collapse: collapse; width: 100%; }}
th, td {{ padding: 5px 8px; text-align: left; border-bottom: 1px solid #e6d9cc;
          font-variant-numeric: tabular-nums; }}
th {{ font-weight: 600; font-size: 0.85em; }}
.wide {{ overflow-x: auto; }}
p.note {{ color: #5b6672; font-size: 0.9em; }}
textarea {{ width: 100%; font: 14px/1.4 ui-monospace, monospace; box-sizing: border-box; }}
pre {{ white-space: pre-wrap; }}
</style></head><body>
<nav>{nav}</nav>
<h1>{html.escape(title)}</h1>
{body}
</body></html>
"""


def movements(connection) -> list[tuple]:
    """Every machine with an identifier: its first and last day, the days it
    was seen, its addresses, how many times its address changed from one day
    it was seen to the next, and the days between changes on average. A day
    with two addresses takes the one it asked most from."""
    seen = defaultdict(dict)
    for day, identifier, address, requests in connection.execute(
            "SELECT day, identifier, address, requests FROM machines ORDER BY day"):
        best = seen[identifier].get(day)
        if best is None or requests > best[1]:
            seen[identifier][day] = (address, requests)
    every_address = defaultdict(set)
    for identifier, address in connection.execute("SELECT DISTINCT identifier, address FROM machines"):
        every_address[identifier].add(address)
    rows = []
    for identifier, days in seen.items():
        ordered = sorted(days)
        changes = sum(1 for a, b in zip(ordered, ordered[1:]) if days[a][0] != days[b][0])
        span = (datetime.date.fromisoformat(ordered[-1]) - datetime.date.fromisoformat(ordered[0])).days
        rows.append((identifier, ordered[0], ordered[-1], len(ordered), len(every_address[identifier]),
                     changes, f"{span / changes:.1f}" if changes else ""))
    rows.sort(key=lambda row: (-row[3], row[0]))
    return rows


def machines_view(connection) -> str:
    rows = movements(connection)
    names = ["identifier", "first day", "last day", "days seen", "addresses", "address changes",
             "days between changes"]
    return (f"<p>{len(rows)} machines with an identifier. An address change is a day whose "
            f"address differs from the day before it was seen; the days between changes are "
            f"the days from its first to its last, over its changes.</p>"
            + table(names, rows, {"identifier": "id"}))


def machine_view(connection, identifier: str) -> str:
    names, rows = query(connection, "SELECT day, address, requests FROM machines WHERE identifier = ? "
                        "ORDER BY day", (identifier,))
    rows = [(day, address, network(address), requests) for day, address, requests in rows]
    _, downloads = query(connection, "SELECT day, package, version, requests FROM requests "
                         "WHERE identifier = ? AND kind = 'package' ORDER BY day", (identifier,))
    return (table(["day", "address", "range", "requests"], rows, {"address": "address"})
            + "<h2>Packages it downloaded</h2>"
            + (table(["day", "package", "version", "requests"], downloads) if downloads
               else "<p>None.</p>"))


def addresses_view(connection) -> str:
    _, rows = query(connection, """
        SELECT address, COUNT(DISTINCT identifier), COUNT(DISTINCT day), SUM(requests)
        FROM machines GROUP BY address""")
    _, anonymous = query(connection, "SELECT address, COUNT(DISTINCT day), SUM(requests) "
                         "FROM anonymous GROUP BY address")
    without = {address: (days, requests) for address, days, requests in anonymous}
    merged = {address: [machines, days, requests, 0] for address, machines, days, requests in rows}
    for address, (days, requests) in without.items():
        merged.setdefault(address, [0, 0, 0, 0])[3] = days
    table_rows = sorted(((address, network(address), m, d, r, a) for address, (m, d, r, a) in merged.items()),
                        key=lambda row: (-row[2], -row[5], row[0]))
    names = ["address", "range", "machines with id", "days with id", "requests with id",
             "days without id"]
    return (f"<p>{len(table_rows)} addresses Kidux machines came from.</p>"
            + table(names, table_rows, {"address": "address"}))


def address_view(connection, address: str) -> str:
    _, rows = query(connection, "SELECT day, identifier, requests FROM machines WHERE address = ? "
                    "ORDER BY day, identifier", (address,))
    _, anonymous = query(connection, "SELECT day, requests FROM anonymous WHERE address = ? "
                         "ORDER BY day", (address,))
    near = network(address)
    _, neighbours = query(connection, "SELECT DISTINCT address FROM requests WHERE client = 'kidux'")
    others = sorted(a for (a,) in neighbours if network(a) == near and a != address)
    return (f"<p>Range {html.escape(near)}"
            + (": also " + ", ".join(link("address", a) for a in others) if others else ", no other address of it")
            + ".</p><h2>Machines with an identifier</h2>"
            + (table(["day", "identifier", "requests"], rows, {"identifier": "id"}) if rows else "<p>None.</p>")
            + "<h2>Kidux requests without an identifier</h2>"
            + (table(["day", "requests"], anonymous) if anonymous else "<p>None.</p>"))


def sql_view(connection, sql: str) -> str:
    examples = "".join(f"<li><a href=\"?view=sql&amp;example={i}\">{html.escape(name)}</a></li>"
                       for i, (name, _) in enumerate(EXAMPLES))
    form = (f'<form method="post" action="?view=sql"><textarea name="sql" rows="6">{html.escape(sql)}'
            f'</textarea><p><button type="submit">Run</button></p></form>')
    result = ""
    if sql.strip():
        try:
            names, rows = query(connection, sql)
            result = f"<p>{len(rows)} rows.</p>" + table(names, rows)
        except sqlite3.Error as error:
            result = f"<p><strong>{html.escape(str(error))}</strong></p>"
    schema = html.escape(SCHEMA.strip())
    return (form + result + f"<h2>Examples</h2><ul>{examples}</ul>"
            f"<h2>The tables</h2><pre>{schema}</pre>")


def explore(view: str, value: str, today: bool) -> int:
    """A page of the hosting's usage/: the database made again from the logs
    kept, and today's so far, then the view asked for."""
    lines = []
    for path in kept_files():
        lines += read(path)
    if today:
        login, password = credentials()
        body = download(datetime.date.today(), login, password)
        if body:
            lines += body.decode("utf-8", "replace").splitlines()
    if view == "summary":
        numbers = parse(lines)
        body = (as_html(summary(numbers, None), datetime.date.today() if today else None)
                if numbers else "<p>No requests yet.</p>")
        print(shell(TITLE, body))
        return 0
    path = build(lines, KEPT / DATABASE)
    connection = read_only(path)
    if view == "csv":
        writer = csv.writer(sys.stdout)
        cursor = connection.execute("SELECT * FROM requests ORDER BY day, address")
        writer.writerow([column[0] for column in cursor.description])
        writer.writerows(cursor)
        return 0
    if view == "ids":
        title, body = "Machines with an identifier", machines_view(connection)
    elif view == "id":
        title, body = f"Machine {value}", machine_view(connection, value)
    elif view == "addresses":
        title, body = "Addresses", addresses_view(connection)
    elif view == "address":
        title, body = f"Address {value}", address_view(connection, value)
    elif view == "sql":
        sql = os.environ.get("KIDUX_USAGE_SQL", "")
        if value.isdigit() and int(value) < len(EXAMPLES):
            sql = EXAMPLES[int(value)][1]
        title, body = "Query", sql_view(connection, sql)
    else:
        title, body = "Kidux machines", "<p>No such page.</p>"
    print(shell(title, body))
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
    exploring = commands.add_parser("page")
    exploring.add_argument("--view", default="summary",
                           choices=("summary", "ids", "id", "addresses", "address", "sql", "csv"))
    exploring.add_argument("--value", default="")
    exploring.add_argument("--today", action="store_true")
    asked = parser.parse_args(argv[1:])
    if asked.command == "fetch":
        return fetch(asked.since)
    if asked.command == "page":
        return explore(asked.view, asked.value, asked.today)
    return report(asked.files or kept_files(), asked.days, asked.today, asked.html)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
