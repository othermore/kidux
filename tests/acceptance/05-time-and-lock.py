#!/usr/bin/python3
# Step 9.4 on a real machine: a daily child with one minute is locked when
# it runs out, an adult gives more from the lock screen, the child locks
# themselves and continues, the daemon restarts mid-session, and the next
# day brings a fresh allowance. Every switch and freeze is logind's and
# systemd's own, observed from outside.
import subprocess

# The stand-in lock screen runs as this user (the fixtures in user-data).
subprocess.run(["useradd", "--system", "--no-create-home", "--shell", "/usr/sbin/nologin",
                "kidux-test-locker"], check=False)
subprocess.run(["systemctl", "daemon-reload"], check=True)
import datetime
import json
import sys
import time
import tomllib

CHILD, CHILD_PW, ADULT = "marta", "marta password", "the adult password"
failures = 0


def report(name, passed, detail=""):
    global failures
    print(("PASS  " if passed else "FAIL  ") + name, flush=True)
    if not passed:
        failures += 1
        if detail:
            print("      " + str(detail).replace("\n", "\n      "), flush=True)


def run(*argv):
    return subprocess.run(argv, capture_output=True, text=True)


def kidux_as(*args, user="debian"):
    return run("runuser", "-u", user, "--", "/usr/local/bin/kidux-as", *args)


def usage():
    with open(f"/home/.kidux/children/{CHILD}/usage.toml", "rb") as handle:
        return tomllib.load(handle)


def foreground():
    # The kernel's own answer, with no package needed: "tty5", "tty8".
    with open("/sys/class/tty/tty0/active") as handle:
        return int(handle.read().strip().removeprefix("tty") or 0)


def session_id():
    # The child's own session, class "user". Signing in also starts the
    # child's systemd user manager, which logind lists as a session of
    # class "manager"; that one has no terminal and is not what is locked.
    for line in run("loginctl", "list-sessions", "--no-legend").stdout.splitlines():
        fields = line.split()
        if len(fields) >= 6 and fields[2] == CHILD and fields[5] == "user":
            return fields[0]
    return None


def freezer():
    sid = session_id()
    if sid is None:
        return "gone"
    return run("systemctl", "show", f"session-{sid}.scope",
               "-p", "FreezerState", "--value").stdout.strip()


def wait(condition, seconds):
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        try:
            if condition():
                return True
        except Exception:
            pass
        time.sleep(1)
    return False


def lock_state():
    return usage()["session"]["lock"]


run("timedatectl", "set-ntp", "false")

result = kidux_as("set-policy", CHILD, "daily", "1")
report("an adult gives a child one minute a day", result.returncode == 0, result.stderr)

run("systemctl", "start", f"kidux-test-child@{CHILD}.service")
wait(lambda: session_id() is not None, 10)
report("the child's session has the screen",
       wait(lambda: run("loginctl", "activate", session_id() or "").returncode == 0
            and foreground() == 5, 10),
       f"foreground terminal {foreground()}")
report("the daemon sees the child's session appear",
       wait(lambda: usage()["session"]["active"], 15))

report("when the minute is up the session is locked",
       wait(lambda: lock_state() == "time_up", 100), usage())
report("the lock screen has the screen", wait(lambda: foreground() == 8, 5),
       f"foreground terminal {foreground()}")
report("everything the child was running is frozen", freezer() == "frozen", freezer())
used = usage()["seconds_used_today"]
time.sleep(15)
report("locked time is not counted", usage()["seconds_used_today"] == used,
       f"{used} -> {usage()['seconds_used_today']}")

result = kidux_as("grant", CHILD, "5", "a guess")
report("a wrong adult password gives nothing", result.returncode != 0
       and lock_state() == "time_up", result.stderr[-300:])

result = kidux_as("grant", CHILD, "5")
report("an adult gives five more minutes from the lock screen", result.returncode == 0,
       result.stderr)
report("the child has the screen back", wait(lambda: foreground() == 5, 5),
       f"foreground terminal {foreground()}")
report("and is running again", wait(lambda: freezer() == "running", 5), freezer())
report("the lock screen is gone",
       run("systemctl", "is-active", f"kidux-locker@{CHILD}.service").stdout.strip()
       != "active")

result = kidux_as("child-lock", user=CHILD)
report("the child locks the screen themselves", result.returncode == 0
       and wait(lambda: lock_state() == "requested", 5)
       and wait(lambda: foreground() == 8, 5), result.stderr)

result = kidux_as("continue", CHILD, "not my password")
report("continuing with the wrong password is refused",
       result.returncode != 0 and lock_state() == "requested", result.stderr[-300:])

result = kidux_as("continue", CHILD, CHILD_PW)
report("the child continues with their own password", result.returncode == 0
       and wait(lambda: foreground() == 5, 5), result.stderr)

# The session locking itself (D67): for idleness right after continuing it
# is refused, since that is a timer that ran out while it was frozen; for
# the lid it locks; and the minutes are the adult's to set, within reason.
result = kidux_as("child-lock-for", "idle", user=CHILD)
report("a lock for idleness right after continuing is refused",
       result.returncode != 0 and "NoSession" in result.stdout and lock_state() == "none",
       result.stdout + result.stderr)
result = kidux_as("child-lock-for", "lid", user=CHILD)
report("the session locks itself when its lid closes", result.returncode == 0
       and wait(lambda: lock_state() == "lid", 5)
       and wait(lambda: foreground() == 8, 5), result.stdout + result.stderr)
result = kidux_as("continue", CHILD, CHILD_PW)
report("and the child continues", result.returncode == 0
       and wait(lambda: foreground() == 5, 5), result.stderr)
refused = [kidux_as("set-config", key, value).stdout.strip()
           for key, value in (("idle_lock_minutes", "0"), ("screen_off_minutes", "500"))]
kidux_as("set-config", "idle_lock_minutes", "3")
report("the minutes a session may be left alone are an adult's to set, within reason",
       refused == ["org.kidux.Daemon1.Error.InvalidArgument"] * 2
       and kidux_as("get-config", "idle_lock_minutes").stdout.strip() == "3",
       str(refused))
kidux_as("set-config", "idle_lock_minutes", "5")

before = usage()["seconds_used_today"]
run("systemctl", "restart", "kidux-daemon")
restarted = wait(lambda: run("systemctl", "is-active", "kidux-daemon").stdout.strip()
                 == "active", 15)
time.sleep(3)
report("a daemon restart mid-session loses nothing", restarted
       and usage()["session"]["active"] and usage()["seconds_used_today"] >= before,
       usage())

# An adult sets what the child has left, from the panel (D50): five
# minutes, then none, which locks the session up at once.
result = kidux_as("set-time-left", CHILD, "5")
left = kidux_as("usage", CHILD).stdout.split()
report("an adult sets the child's time left to five minutes",
       result.returncode == 0 and len(left) == 2 and 290 <= int(left[1]) <= 300,
       result.stderr + str(left))
result = kidux_as("set-time-left", CHILD, "0")
report("and to none, which locks the session up at once",
       result.returncode == 0 and wait(lambda: lock_state() == "time_up", 10)
       and wait(lambda: foreground() == 8, 5), result.stderr + str(usage()))
kidux_as("grant", CHILD, "5")
wait(lambda: foreground() == 5, 5)

kidux_as("child-lock", user=CHILD)
wait(lambda: lock_state() == "requested", 5)
day_before = usage()["last_day"]
run("date", "-s", "+1 day")
result = kidux_as("continue", CHILD, CHILD_PW)
time.sleep(2)
report("the next day brings a fresh allowance", result.returncode == 0
       and usage()["last_day"] != day_before and usage()["seconds_used_today"] < 30,
       usage())

result = kidux_as("end", CHILD, ADULT)
report("an adult logs the child out", result.returncode == 0
       and wait(lambda: session_id() is None, 10),
       f"rc={result.returncode} {result.stderr[-300:]} "
       + run("loginctl", "list-sessions", "--no-legend").stdout)

# The days of the week (D54): today not ticked, the child is told it is
# not their day; an adult's grant still lets them in.
kidux_as("check-access", CHILD)
today = datetime.date.fromisoformat(usage()["last_day"]).weekday()
days = "".join("0" if day == today else "1" for day in range(7))
result = kidux_as("set-policy", CHILD, "daily", "60", days)
answer = kidux_as("check-access", CHILD).stdout.split()
report("on a day not ticked the child may not sign in, and is told why",
       result.returncode == 0 and answer == ["day_off", "0"], result.stderr + str(answer))
entries = [json.loads(line) for line in open("/home/.kidux/state/audit.log") if line.strip()]
report("the audit names the days",
       any(entry.get("action") == "policy set" and entry.get("days") == days
           for entry in entries), entries[-3:])
result = kidux_as("grant", CHILD, "15")
answer = kidux_as("check-access", CHILD).stdout.split()
# The whole grant, whatever the child used today before the day was unticked.
report("an adult's grant lets them in that day, with its minutes whole",
       result.returncode == 0 and answer == ["allowed", str(15 * 60)],
       result.stderr + str(answer))
kidux_as("set-policy", CHILD, "daily", "60", "1111111")

audit = open("/home/.kidux/state/audit.log").read()
order = ["\"policy set\"", "\"time_up\"", "\"grant\"", "\"requested\"",
         "\"continue\"", "\"log out\""]
positions = [audit.find(marker) for marker in order]
report("the audit trail holds every event, in order",
       all(p >= 0 for p in positions) and positions == sorted(positions),
       dict(zip(order, positions)))

sys.exit(failures)

