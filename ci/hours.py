#!/usr/bin/python3
"""The hours Kidux is seen working on GitHub (D99), and the dates that keep to them.

    ci/hours.py allowed                   exit 0 inside the hours; 1 outside, saying when they open
    ci/hours.py next [--calendar]         when the hours next open: now, inside them; as systemd's
                                          calendar time with --calendar
    ci/hours.py changelog-date <package>  a debian/changelog date inside the hours, not after now
                                          and after the package's last entry
    ci/hours.py redate <base> <head>      the commits after <base> up to <head> made again, dated
                                          inside the hours and ending now; prints the new head

Nothing of Kidux's reaches GitHub, or carries a time that is read there,
outside these hours, Madrid's: from 19:00 to 02:00 around a weekday night,
and the whole of Saturday and Sunday, so from Friday 19:00 to Monday 02:00
without a break. A commit's dates, the author's and the committer's, are
set inside them when it is pushed (ci/push.sh); a changelog's date, which
the built package carries and the archive shows, is taken from here when a
package gets its version. A date in the past keeps a build reproducible,
since dpkg clamps only file times newer than it (D23).
"""

import datetime
import email.utils
import os
import subprocess
import sys
import zoneinfo
from pathlib import Path

ZONE = zoneinfo.ZoneInfo("Europe/Madrid")
OPENS = datetime.time(19, 0)
CLOSES = datetime.time(2, 0)
#: The last minute before the hours close, for a date that has to be inside
#: them and before now.
LAST = datetime.time(1, 59)
SATURDAY, SUNDAY = 5, 6
REPO = Path(__file__).resolve().parents[1]


def now() -> datetime.datetime:
    return datetime.datetime.now(ZONE)


def allowed(when: datetime.datetime) -> bool:
    """Whether `when`, in Madrid's time, is inside the hours."""
    if when.weekday() in (SATURDAY, SUNDAY):
        return True
    return when.time() >= OPENS or when.time() < CLOSES


def opens(when: datetime.datetime) -> datetime.datetime:
    """When the hours next open: `when` itself inside them, else 19:00 that day."""
    if allowed(when):
        return when
    return when.replace(hour=OPENS.hour, minute=0, second=0, microsecond=0)


def began(when: datetime.datetime) -> datetime.datetime:
    """When the stretch of hours `when` is in began: the 19:00 that opened
    it, Friday's for a weekend. For a `when` inside the hours."""
    day = when.date()
    if when.time() < CLOSES or when.weekday() in (SATURDAY, SUNDAY):
        day -= datetime.timedelta(days=1)
    while day.weekday() in (SATURDAY, SUNDAY):
        day -= datetime.timedelta(days=1)
    return datetime.datetime.combine(day, OPENS, ZONE)


def latest(when: datetime.datetime) -> datetime.datetime:
    """The last moment inside the hours that is not after `when`."""
    if allowed(when):
        return when
    return when.replace(hour=LAST.hour, minute=LAST.minute, second=0, microsecond=0)


def changelog_date(when: datetime.datetime, previous: datetime.datetime | None) -> str:
    """A changelog date inside the hours, not after `when`, and after the
    entry before it, `previous`, when there is one: a minute after it when
    the hours give nothing later, and `when` itself at the worst."""
    date = latest(when)
    if previous is not None and date <= previous:
        date = min(previous + datetime.timedelta(minutes=1), when)
    return email.utils.format_datetime(date.astimezone(ZONE))


def previous_entry(package: str) -> datetime.datetime | None:
    """The date of the package's newest changelog entry, or None: a new
    package's changelog is created empty, and its first entry dated by
    this."""
    changelog = REPO / "packages" / package / "debian" / "changelog"
    if not changelog.is_file():
        raise SystemExit(f"no such package: {package}")
    if not changelog.read_text(encoding="utf-8").strip():
        return None
    said = subprocess.run(["dpkg-parsechangelog", "-l", str(changelog), "-S", "Date"],
                          capture_output=True, text=True, check=True).stdout.strip()
    return email.utils.parsedate_to_datetime(said) if said else None


def git(*args: str, cwd=None) -> str:
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True,
                          check=True).stdout.strip()


def redate(base: str, head: str, when: datetime.datetime, cwd=None) -> str:
    """The commits after `base` up to `head`, each made again with the same
    tree, message, author and committer, dated inside the hours: the last
    at `when`, each earlier one a minute before, closer when the hours have
    not been open for that long. A merge is made again with its parents,
    each dated again when it is one of these commits and kept as it is
    when it is already on the other side. The new head; `head` itself with
    nothing to date."""
    commits = git("rev-list", "--topo-order", "--reverse", f"{base}..{head}", cwd=cwd).split()
    if not commits:
        return git("rev-parse", head, cwd=cwd)
    since = max(1, int((when - began(when)).total_seconds()))
    step = min(60, max(1, since // len(commits)))
    made: dict[str, str] = {}
    for place, commit in enumerate(commits):
        parents = [made.get(old, old) for old in git("log", "-1", "--format=%P", commit,
                                                      cwd=cwd).split()]
        tree, name, address = git("log", "-1", "--format=%T%n%an%n%ae", commit,
                                  cwd=cwd).splitlines()
        message = subprocess.run(["git", "log", "-1", "--format=%B", commit], cwd=cwd,
                                 capture_output=True, text=True, check=True).stdout
        dated = when - datetime.timedelta(seconds=step * (len(commits) - 1 - place))
        stamp = f"@{int(dated.timestamp())} {dated.strftime('%z')}"
        environment = {**os.environ, "GIT_AUTHOR_NAME": name, "GIT_AUTHOR_EMAIL": address,
                       "GIT_AUTHOR_DATE": stamp, "GIT_COMMITTER_NAME": name,
                       "GIT_COMMITTER_EMAIL": address, "GIT_COMMITTER_DATE": stamp}
        with_parents = [item for parent in parents for item in ("-p", parent)]
        made[commit] = subprocess.run(["git", "commit-tree", tree, *with_parents], cwd=cwd,
                                      input=message, env=environment, capture_output=True,
                                      text=True, check=True).stdout.strip()
    return made[commits[-1]]


def main(args: list[str]) -> int:
    moment = now()
    if args == ["allowed"]:
        if allowed(moment):
            return 0
        print(f"outside the hours Kidux is seen working (19:00 to 02:00 on a weekday, "
              f"all weekend); they open at {opens(moment):%Y-%m-%d %H:%M}", file=sys.stderr)
        return 1
    if args in (["next"], ["next", "--calendar"]):
        print(opens(moment).strftime("%Y-%m-%d %H:%M:%S" if len(args) == 2 else "%c %Z"))
        return 0
    if len(args) == 2 and args[0] == "changelog-date":
        print(changelog_date(moment, previous_entry(args[1])))
        return 0
    if len(args) == 3 and args[0] == "redate":
        if not allowed(moment):
            print("the commits are dated at a push, inside the hours", file=sys.stderr)
            return 1
        print(redate(args[1], args[2], moment))
        return 0
    print(__doc__, file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
