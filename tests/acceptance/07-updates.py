#!/usr/bin/python3
# Step 9.8 on a real machine: updates are looked for and installed through
# the daemon, in a unit of their own, and refused while a child is signed in.
# The package it updates is made here, in the machine, and served from a
# directory: the real archive is never touched.
import subprocess
import time

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


def kidux_as(*args):
    return run("runuser", "-u", "debian", "--", "/usr/local/bin/kidux-as", *args)


def version():
    return run("dpkg-query", "-W", "-f=${Version}", "kidux-test-canary").stdout.strip()


made = run("/usr/local/bin/kidux-as", "canary")
report("a package at 1.0, with 1.1 waiting in a local repository", made.returncode == 0
       and version() == "1.0", made.stdout + made.stderr)

# Debian's own updates for the cloud image may be found too; ours has to be.
checked = kidux_as("check-updates")
found = checked.stdout.split()
report("looking for updates finds it, by name", checked.returncode == 0
       and found[:1] == ["checked"] and "kidux-test-canary" in found[1].split(","),
       checked.stdout + checked.stderr)

# A child signed in: nothing may be installed under their session.
run("systemctl", "start", "kidux-test-child@marta.service")
for _ in range(30):
    if "marta" in run("loginctl", "list-sessions", "--no-legend").stdout:
        break
    time.sleep(1)
refused = kidux_as("apply-updates")
report("installing is refused while a child is signed in",
       refused.returncode == 2 and "SessionActive" in refused.stdout, refused.stdout + refused.stderr)
run("systemctl", "stop", "kidux-test-child@marta.service")
for _ in range(30):
    if "marta" not in run("loginctl", "list-sessions", "--no-legend").stdout:
        break
    time.sleep(1)
time.sleep(2)

applied = kidux_as("apply-updates")
# A kernel among Debian's updates asks for a restart, which is an ending too.
report("installing ends with the update in place", applied.returncode == 0
       and applied.stdout.split()[:1] in (["updated"], ["restart-needed"])
       and version() == "1.1",
       applied.stdout + applied.stderr + version())

unit = run("systemctl", "show", "kidux-update.service", "-p", "LoadState", "--value").stdout.strip()
report("the job's unit is gone once it is done", unit in ("not-found", ""), unit)

audit = open("/home/.kidux/state/audit.log").read()
report("the audit trail has the check, the start and the end",
       '"update check"' in audit and '"update started"' in audit and '"update finished"' in audit,
       audit[-600:])

run("rm", "-f", "/etc/apt/sources.list.d/kidux-test-canary.list")
raise SystemExit(failures)
