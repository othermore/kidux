#!/usr/bin/python3
"""The hours Kidux is seen working on GitHub (ci/hours.py, D99).

    tests/project/hours.py

Madrid's 19:00 to 02:00 around a weekday night and all weekend; the next
opening and the last moment before now inside them; a changelog date that
keeps to them and to the entry before; and commits dated again for a push
with nothing of them changed but their dates.
"""

import datetime
import email.utils
import importlib.util
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("hours", REPO / "ci" / "hours.py")
hours = importlib.util.module_from_spec(spec)
spec.loader.exec_module(hours)

failed = 0


def check(name: str, passed: bool, detail: str = "") -> None:
    global failed
    print(("PASS  " if passed else "FAIL  ") + name)
    if not passed:
        failed += 1
        if detail:
            print("      " + detail)


def at(text: str) -> datetime.datetime:
    return datetime.datetime.fromisoformat(text).replace(tzinfo=hours.ZONE)


# 2026-10-12 is a Monday.
check("a weekday's day is outside the hours, its evening and its small hours inside",
      not hours.allowed(at("2026-10-13 11:00")) and not hours.allowed(at("2026-10-13 18:59"))
      and hours.allowed(at("2026-10-13 19:00")) and hours.allowed(at("2026-10-14 01:59"))
      and not hours.allowed(at("2026-10-14 02:00")))
check("the weekend is inside, Friday evening to Monday's small hours",
      hours.allowed(at("2026-10-17 12:00")) and hours.allowed(at("2026-10-18 03:00"))
      and hours.allowed(at("2026-10-19 01:30")) and not hours.allowed(at("2026-10-19 02:30")))
check("the hours next open at 19:00 that day, or are open now",
      hours.opens(at("2026-10-13 11:00")) == at("2026-10-13 19:00")
      and hours.opens(at("2026-10-13 20:00")) == at("2026-10-13 20:00"))
check("a stretch began at the 19:00 that opened it, Friday's for a weekend",
      hours.began(at("2026-10-13 20:00")) == at("2026-10-13 19:00")
      and hours.began(at("2026-10-14 01:00")) == at("2026-10-13 19:00")
      and hours.began(at("2026-10-18 12:00")) == at("2026-10-16 19:00")
      and hours.began(at("2026-10-19 01:00")) == at("2026-10-16 19:00"))
check("the last moment inside the hours before a weekday's noon is 01:59 that morning",
      hours.latest(at("2026-10-13 11:00")) == at("2026-10-13 01:59")
      and hours.latest(at("2026-10-13 23:00")) == at("2026-10-13 23:00"))

parsed = email.utils.parsedate_to_datetime
dated = parsed(hours.changelog_date(at("2026-10-13 11:00:30"), None))
check("a changelog date inside the hours, not after now, in Madrid's time",
      dated == at("2026-10-13 01:59") and dated.utcoffset() == at("2026-10-13 01:59").utcoffset(),
      str(dated))
previous = at("2026-10-13 01:59")
check("and after the entry before it, a minute on, never after now",
      parsed(hours.changelog_date(at("2026-10-13 11:00"), previous)) == at("2026-10-13 02:00")
      and parsed(hours.changelog_date(at("2026-10-13 01:59:20"), previous))
      == at("2026-10-13 01:59:20"))

# Commits dated again: the same trees, messages and author, inside the hours.
with tempfile.TemporaryDirectory() as scratch:
    def git(*args: str) -> str:
        return subprocess.run(["git", *args], cwd=scratch, capture_output=True, text=True,
                              check=True).stdout.strip()

    git("init", "-q", "-b", "main")
    git("config", "user.name", "Kidux tests")
    git("config", "user.email", "tests@example.org")
    for number, when in enumerate(("2026-10-13T10:00:00+02:00", "2026-10-13T11:00:00+02:00",
                                   "2026-10-13T12:00:00+02:00")):
        Path(scratch, f"file{number}").write_text(f"{number}\n")
        git("add", ".")
        subprocess.run(["git", "commit", "-q", "-m", f"Commit {number}\n\nIts body."],
                       cwd=scratch, check=True,
                       env={"GIT_AUTHOR_DATE": when, "GIT_COMMITTER_DATE": when,
                            "HOME": scratch, "PATH": "/usr/bin:/bin"})
    base = git("rev-parse", "HEAD~2")
    before = git("log", "--format=%T %s %an %ae", f"{base}..HEAD")
    pushed_at = at("2026-10-13 19:05:00")
    head = hours.redate(base, "HEAD", pushed_at, cwd=scratch)
    after = git("log", "--format=%T %s %an %ae", f"{base}..{head}")
    dates = [parsed(line) for line in git("log", "--format=%aD", f"{base}..{head}").splitlines()]
    committer = [parsed(line) for line in git("log", "--format=%cD", f"{base}..{head}").splitlines()]
    check("commits dated again keep their trees, messages and author",
          after == before and git("log", "-1", "--format=%b", head) == "Its body.", after)
    check("and are dated inside the hours, the last at the push, a minute apart, as committer too",
          dates == [pushed_at, pushed_at - datetime.timedelta(minutes=1)] and committer == dates,
          str(dates))
    check("with nothing after the base, the head is the head",
          hours.redate(head, head, pushed_at, cwd=scratch) == head)
    squeezed = hours.redate(base, "HEAD", at("2026-10-13 19:00:30"), cwd=scratch)
    tight = [parsed(line) for line in git("log", "--format=%aD", f"{base}..{squeezed}").splitlines()]
    check("and closer together when the hours have just opened",
          all(hours.allowed(when) for when in tight) and tight[0] > tight[1], str(tight))

sys.exit(failed)
