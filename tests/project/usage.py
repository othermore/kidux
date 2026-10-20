#!/usr/bin/python3
"""What ci/usage.py counts from the hosting's access log.

    tests/project/usage.py

Lines in the shape the hosting writes them, taken from its log of
2026-10-18 with the addresses replaced by documentation ones: machines with
an identifier and without, an identifier of a test, other apt clients, a
package downloaded, a browser and a crawler, and another site's line; and
in the shape iso.kidux.org's will be, the images downloaded and the trial
images looking for updates.
"""

import datetime
import importlib.util
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("usage", REPO / "ci" / "usage.py")
usage = importlib.util.module_from_spec(spec)
spec.loader.exec_module(usage)

LOG = '''\
192.0.2.1 apt.kidux.org - [18/Oct/2026:19:29:51 +0200] "GET /dists/stable/InRelease HTTP/1.1" 200 1864 "-" "Debian APT-HTTP/1.3 Kidux/51d1002cbf595fe691f73b47438577ce"
192.0.2.1 apt.kidux.org - [18/Oct/2026:19:29:51 +0200] "GET /dists/stable/main/binary-amd64/Packages.gz HTTP/1.1" 200 12045 "-" "Debian APT-HTTP/1.3 Kidux/51d1002cbf595fe691f73b47438577ce"
192.0.2.1 apt.kidux.org - [18/Oct/2026:19:30:07 +0200] "GET /dists/stable/InRelease HTTP/1.1" 200 1864 "-" "Debian APT-HTTP/1.3 Kidux/51d1002cbf595fe691f73b47438577ce"
192.0.2.1 apt.kidux.org - [18/Oct/2026:19:32:20 +0200] "GET /dists/stable/InRelease HTTP/1.1" 200 1864 "-" "Debian APT-HTTP/1.3 Kidux/936c7fdc2dca2272cdfd334fb40e0b88"
198.51.100.7 apt.kidux.org - [18/Oct/2026:19:29:59 +0200] "GET /dists/stable/InRelease HTTP/1.1" 200 1864 "-" "Debian APT-HTTP/1.3 Kidux"
198.51.100.8 apt.kidux.org - [18/Oct/2026:19:31:00 +0200] "GET /dists/stable/InRelease HTTP/1.1" 304 - "-" "Debian APT-HTTP/1.3 Kidux"
198.51.100.8 apt.kidux.org - [18/Oct/2026:19:31:00 +0200] "GET /dists/stable/InRelease HTTP/1.1" 200 1864 "-" "Debian APT-HTTP/1.3 Kidux"
192.0.2.1 apt.kidux.org - [18/Oct/2026:19:27:04 +0200] "GET /dists/stable/InRelease HTTP/1.1" 200 1864 "-" "Debian APT-HTTP/1.3 Kidux/00000000000000000000000000000001"
192.0.2.1 apt.kidux.org - [18/Oct/2026:19:27:04 +0200] "GET /pool/main/k/kidux-module-hello/kidux-module-hello_0.1.9_all.deb HTTP/1.1" 200 6792 "-" "Debian APT-HTTP/1.3 Kidux/00000000000000000000000000000001"
192.0.2.1 apt.kidux.org - [18/Oct/2026:19:21:18 +0200] "GET /dists/stable/InRelease HTTP/1.1" 200 1864 "-" "Debian APT-HTTP/1.3 Kidux/0123456789abcdef0123456789abcdef"
192.0.2.1 apt.kidux.org - [18/Oct/2026:19:27:05 +0200] "GET /dists/stable/InRelease HTTP/1.1" 200 1864 "-" "Debian APT-HTTP/1.3 (3.0.3)"
192.0.2.9 apt.kidux.org - [19/Oct/2026:09:12:40 +0200] "GET /pool/main/k/kidux-module-scratchjr/kidux-module-scratchjr_1.3.2+git20201121.5_amd64.deb HTTP/1.1" 200 119335124 "-" "Debian APT-HTTP/1.3 Kidux/2b8f1c2a9d3e4f5061728394a5b6c7d8"
192.0.2.9 apt.kidux.org - [19/Oct/2026:09:12:30 +0200] "GET /dists/stable/InRelease HTTP/1.1" 200 1864 "-" "Debian APT-HTTP/1.3 Kidux/2b8f1c2a9d3e4f5061728394a5b6c7d8"
203.0.113.4 apt.kidux.org - [18/Oct/2026:17:45:37 +0200] "GET /robots.txt HTTP/1.1" 404 196 "-" "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko; compatible; ClaudeBot/1.0; +claudebot@anthropic.com)"
203.0.113.5 apt.kidux.org - [18/Oct/2026:16:45:45 +0200] "GET /auth HTTP/1.1" 404 196 "-" "\\"Mozilla/5.0 (iPhone; CPU iPhone OS 18_3_2 like Mac OS X) Safari/604.\\""
203.0.113.6 kidux.org - [18/Oct/2026:16:45:45 +0200] "GET /dists/stable/InRelease HTTP/1.1" 200 1864 "-" "Debian APT-HTTP/1.3 Kidux/ffffffffffffffffffffffffffffffff"
'''

failed = 0


def check(name: str, passed: bool, detail: str = "") -> None:
    global failed
    print(("PASS  " if passed else "FAIL  ") + name)
    if not passed:
        failed += 1
        if detail:
            print("      " + detail)


known = {"0123456789abcdef0123456789abcdef"}
days = usage.parse(LOG.splitlines(), known)
first, second = days.get(datetime.date(2026, 10, 18)), days.get(datetime.date(2026, 10, 19))

check("only apt.kidux.org's lines are read here, by the day they were made",
      sorted(days) == [datetime.date(2026, 10, 18), datetime.date(2026, 10, 19)], str(sorted(days)))
usage.INCLUDE_TESTS = True
counted = usage.parse(LOG.splitlines(), known)[datetime.date(2026, 10, 18)]
usage.INCLUDE_TESTS = False
check("with the page's toggle on, the test machines count as any other",
      "00000000000000000000000000000001" in counted["ids"] and not counted["tests"],
      str(counted["ids"]))
check("a machine with an identifier counts once a day however often it looks",
      first["ids"] == {"51d1002cbf595fe691f73b47438577ce", "936c7fdc2dca2272cdfd334fb40e0b88"},
      str(first["ids"]))
check("a machine without one counts by its address, 304 or 200",
      first["anonymous"] == {"198.51.100.7", "198.51.100.8"}, str(first["anonymous"]))
check("tests' identifiers, sixteen zeros first or listed, never count",
      first["tests"] == {"00000000000000000000000000000001", "0123456789abcdef0123456789abcdef"}
      and not any(i.startswith("0" * 16) for i in first["ids"]), str(first["tests"]))
check("another apt is counted apart, and a browser or a crawler as another visitor",
      first["other_apt"] == {"192.0.2.1"} and first["other"] == 2,
      f"{first['other_apt']} {first['other']}")
check("a Kidux machine's download is counted by package and version, not a test's",
      sum(first["downloads"].values()) == 0
      and second["downloads"] == {("kidux-module-scratchjr", "1.3.2+git20201121.5"): 1},
      f"{first['downloads']} {second['downloads']}")
check("every test identifier in ci/usage-test-ids.txt is 32 hexadecimal figures",
      all(len(i) == 32 and all(c in "0123456789abcdef" for c in i) for i in usage.test_ids()),
      str(usage.test_ids()))

# A school: five machines behind one address and two more from a near one;
# three households of one provider's range, a machine each; and a household
# without an identifier.
SCHOOL = "".join(
    f'203.0.113.{10 if i < 5 else 11} apt.kidux.org - [20/Oct/2026:08:{i:02d}:00 +0200] '
    f'"GET /dists/stable/InRelease HTTP/1.1" 200 1864 "-" "Debian APT-HTTP/1.3 Kidux/5c{i:030x}"\n'
    for i in range(7)) + "".join(
    f'198.51.100.{20 + i} apt.kidux.org - [20/Oct/2026:09:00:00 +0200] '
    f'"GET /dists/stable/InRelease HTTP/1.1" 200 1864 "-" "Debian APT-HTTP/1.3 Kidux/ab{i:030x}"\n'
    for i in range(3)) + (
    '192.0.2.50 apt.kidux.org - [20/Oct/2026:10:00:00 +0200] '
    '"GET /dists/stable/InRelease HTTP/1.1" 200 1864 "-" "Debian APT-HTTP/1.3 Kidux"\n')
school = usage.parse(SCHOOL.splitlines(), set())
day = school[datetime.date(2026, 10, 20)]
check("ten machines, each its own identifier, count as ten",
      len(day["ids"]) == 10, str(len(day["ids"])))
per_address, total = usage.estimate(day)
check("the estimate counts an address without id as the median machines per address, "
      "which the school does not pull up",
      per_address == 1.0 and total == 11, f"{per_address} {total}")
found = usage.places(day)
check("the school shows as an address with five machines and a range with seven, "
      "and the three near households as a range of their own",
      found["addresses"] == [("203.0.113.10", 5)]
      and found["ranges"] == [("203.0.113.0/24", 7, 2, 0), ("198.51.100.0/24", 3, 3, 0)],
      str(found))
check("addresses are told apart by how many machines are behind them",
      found["machines_per_address"] == [(1, 3), (2, 1), (5, 1)], str(found["machines_per_address"]))

all_days = usage.parse((LOG + SCHOOL).splitlines(), known)
summary = usage.summary(all_days, None)
check("days, ISO weeks and months each have their table",
      [r["period"] for r in summary["tables"]["day"]] == ["2026-10-18", "2026-10-19", "2026-10-20"]
      and [r["period"] for r in summary["tables"]["week"]] == ["2026-W42", "2026-W43"]
      and [r["period"] for r in summary["tables"]["month"]] == ["2026-10"],
      str({k: [r["period"] for r in v] for k, v in summary["tables"].items()}))
check("the test machines are listed apart, each with its address and requests",
      ("0123456789abcdef0123456789abcdef", "192.0.2.1", 1, 1, "2026-10-18") in summary["test_rows"]
      and ("00000000000000000000000000000001", "192.0.2.1", 1, 2, "2026-10-18") in summary["test_rows"],
      str(summary["test_rows"]))
check("all time counts every machine once, from the first day",
      summary["tables"]["all"][0]["period"] == "since 2026-10-18"
      and summary["tables"]["all"][0]["ids"] == 3 + 10
      and list(summary["tables"])[0] == "all", str(summary["tables"]["all"]))
check("a month counts a machine once however many days it looked",
      summary["tables"]["month"][0]["ids"] == 3 + 10, str(summary["tables"]["month"][0]))

# A machine that moves: two days at home, then a day at another address.
MOVES = "".join(
    f'{address} apt.kidux.org - [{day}/Oct/2026:07:00:00 +0200] '
    f'"GET /dists/stable/InRelease HTTP/1.1" 200 1864 "-" "Debian APT-HTTP/1.3 Kidux/7e{0:030x}"\n'
    for day, address in (("21", "192.0.2.70"), ("22", "192.0.2.70"), ("25", "198.51.100.70"))) + (
    '203.0.113.9 apt.kidux.org - [21/Oct/2026:07:00:00 +0200] "GET / HTTP/1.1" 200 336 "-" '
    '"Mozilla/5.0 (compatible; ExampleBot/1.0)"\n')
with tempfile.TemporaryDirectory() as folder:
    built = usage.build(MOVES.splitlines(), Path(folder) / "usage.sqlite")
    connection = usage.read_only(built)
    moved = {row[0]: row for row in usage.movements(connection)}["7e" + "0" * 30]
    check("a machine's address changes are counted, and the days between them",
          moved[1:] == ("2026-10-21", "2026-10-25", 3, 2, 1, "4.0"), str(moved))
    names, rows = usage.query(connection, "SELECT client, agent, requests FROM requests WHERE client = 'web'")
    check("the database keeps who else came, by user agent",
          rows == [("web", "Mozilla/5.0 (compatible; ExampleBot/1.0)", 1)], str(rows))
    try:
        connection.execute("DELETE FROM requests")
        refused = False
    except Exception:
        refused = True
    check("a query may read the database and never change it", refused)
    connection.close()

# Two machines install Scratch, one upgrades it, and a household without an
# identifier installs it too.
INSTALLS = "".join(
    f'{address} apt.kidux.org - [{day}/Oct/2026:07:00:00 +0200] '
    f'"GET /pool/main/k/kidux-module-scratch/kidux-module-scratch_{version}_all.deb HTTP/1.1" '
    f'200 89556104 "-" "Debian APT-HTTP/1.3 Kidux{identifier}"\n'
    for day, address, identifier, version in (
        ("21", "192.0.2.80", "/8a" + "0" * 30, "15.2.0+build2.3"),
        ("28", "192.0.2.80", "/8a" + "0" * 30, "15.2.0+build2.10"),
        ("22", "192.0.2.81", "/8b" + "0" * 30, "15.2.0+build2.3"),
        ("22", "198.51.100.82", "", "15.2.0+build2.3")))
with tempfile.TemporaryDirectory() as folder:
    connection = usage.read_only(usage.build(INSTALLS.splitlines(), Path(folder) / "usage.sqlite"))
    rows = usage.installed(connection)
    check("a package counts the machines that downloaded it, and those on its newest version, "
          "build2.10 after build2.3",
          rows == [("kidux-module-scratch", 2, 2, 1, "15.2.0+build2.10", 1)], str(rows))
    connection.close()

# The images: a browser that fetches the installer in three parts, and again
# the next day; another address that fetches it whole; a look at its size
# alone, a file that is not there and the sums, none of them a download; and
# a trial image downloaded.
ISO = "kidux-0.2.7-20261020-amd64.iso"
TRIAL = "kidux-0.2.7-20261020-trial-es.qcow2"
IMAGES = "".join(
    f'{address} iso.kidux.org - [{day}/Oct/2026:{hour}:00:00 +0200] "{method} /{file} HTTP/1.1" '
    f'{status} 1000 "-" "Mozilla/5.0"\n'
    for address, day, hour, method, file, status in (
        ("192.0.2.90", "20", "10", "GET", ISO, "206"),
        ("192.0.2.90", "20", "10", "GET", ISO, "206"),
        ("192.0.2.90", "20", "11", "GET", ISO, "206"),
        ("192.0.2.90", "21", "09", "GET", ISO, "206"),
        ("192.0.2.91", "20", "12", "GET", ISO, "200"),
        ("192.0.2.92", "20", "12", "HEAD", ISO, "200"),
        ("192.0.2.93", "20", "12", "GET", "kidux-0.1.0-amd64.iso", "404"),
        ("192.0.2.94", "20", "12", "GET", "SHA256SUMS", "200"),
        ("192.0.2.95", "21", "08", "GET", TRIAL, "200"))) + "".join(
    # Two copies of the Spanish trial image, and one of them again the next
    # day, looking for updates.
    f'{address} apt.kidux.org - [{day}/Oct/2026:{hour}:00:00 +0200] '
    f'"GET /dists/stable/InRelease HTTP/1.1" 200 1864 "-" "Debian APT-HTTP/1.3 Kidux/{"f" * 30}01"\n'
    for address, day, hour in (("192.0.2.95", "21", "09"), ("192.0.2.95", "22", "09"),
                               ("198.51.100.96", "21", "10")))
image_days = usage.parse(IMAGES.splitlines(), set(), set())
check("a download is one address and one file on one day, whole or in parts, "
      "and nothing else is one",
      image_days[datetime.date(2026, 10, 20)]["images"]
      == {(ISO, "192.0.2.90"), (ISO, "192.0.2.91")}
      and image_days[datetime.date(2026, 10, 21)]["images"]
      == {(ISO, "192.0.2.90"), (TRIAL, "192.0.2.95")},
      str({day: numbers["images"] for day, numbers in image_days.items()}))
check("a trial image is no family's machine: it is counted apart, by its address",
      image_days[datetime.date(2026, 10, 21)]["trials"]
      == {("f" * 30 + "01", "192.0.2.95"), ("f" * 30 + "01", "198.51.100.96")}
      and not any(numbers["ids"] or numbers["anonymous"] for numbers in image_days.values()),
      str({day: (n["trials"], n["ids"], n["anonymous"]) for day, n in image_days.items()}))
image_summary = usage.summary(image_days, None)
check("the images' table counts the installer's downloads and the trial image's apart, "
      "and the trials run",
      image_summary["images"]["all"][0] == {"period": "since 2026-10-20", "installer": 3,
                                             "trial": 1, "trials": 2}
      and [(r["period"], r["installer"], r["trial"]) for r in image_summary["images"]["day"]]
      == [("2026-10-20", 2, 0), ("2026-10-21", 1, 1), ("2026-10-22", 0, 0)],
      str(image_summary["images"]))
check("each image is listed with its downloads, first and last day",
      image_summary["image_rows"] == [(ISO, "installer", 3, "2026-10-20", "2026-10-21"),
                                      (TRIAL, "trial", 1, "2026-10-21", "2026-10-21")],
      str(image_summary["image_rows"]))
check("each trial is listed with the image's identifier, its address and its days",
      image_summary["trial_rows"] == [("f" * 30 + "01", "192.0.2.95", 2, "2026-10-21", "2026-10-22"),
                                      ("f" * 30 + "01", "198.51.100.96", 1, "2026-10-21",
                                       "2026-10-21")],
      str(image_summary["trial_rows"]))
check("the images' page lists the downloads by day and file",
      "2026-10-21" in usage.images_view(IMAGES.splitlines()) and TRIAL in usage.images_view(IMAGES.splitlines()))
check("every identifier in ci/usage-trial-ids.txt is 32 hexadecimal figures, "
      "and none is a test's",
      usage.trial_ids()
      and all(len(i) == 32 and all(c in "0123456789abcdef" for c in i)
              and not usage.is_test(i, usage.test_ids()) for i in usage.trial_ids()),
      str(usage.trial_ids()))

# The hosting's log holds every site's lines; only the archive's and the
# images' are kept.
MIXED = (b'198.51.100.1 antonio.mg - [18/Oct/2026:10:00:00 +0200] "GET / HTTP/1.1" 200 1 "-" "x"\n'
         b'198.51.100.2 apt.kidux.org - [18/Oct/2026:10:00:01 +0200] "GET / HTTP/1.1" 200 1 "-" "x"\n'
         b'198.51.100.3 apt2.kidux.org - [18/Oct/2026:10:00:02 +0200] "GET / HTTP/1.1" 200 1 "-" "x"\n'
         b'198.51.100.4 iso.kidux.org - [18/Oct/2026:10:00:03 +0200] "GET / HTTP/1.1" 200 1 "-" "x"\n')
check("today's log is written up to its last line's time, whichever site it is",
      usage.written_up_to(MIXED) == "10:00", usage.written_up_to(MIXED))
check("of the hosting's every site, only apt.kidux.org's and iso.kidux.org's lines are kept",
      usage.only_ours(MIXED) == b"".join(MIXED.splitlines(keepends=True)[i] for i in (1, 3)),
      str(usage.only_ours(MIXED)))

sys.exit(1 if failed else 0)
