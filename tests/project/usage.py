#!/usr/bin/python3
"""What ci/usage.py counts from the hosting's access log.

    tests/project/usage.py

Lines in the shape the hosting writes them, taken from its log of
2026-10-18 with the addresses replaced by documentation ones: machines with
an identifier and without, an identifier of a test, other apt clients, a
package downloaded, a browser and a crawler, and another site's line.
"""

import datetime
import importlib.util
import sys
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

check("only apt.kidux.org's lines are read, by the day they were made",
      sorted(days) == [datetime.date(2026, 10, 18), datetime.date(2026, 10, 19)], str(sorted(days)))
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

sys.exit(1 if failed else 0)
