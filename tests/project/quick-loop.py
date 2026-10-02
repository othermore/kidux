#!/usr/bin/python3
"""The quick loop's pieces that decide something (tests/lib/vm.py).

    tests/project/quick-loop.py

A development version must sort below the tree's own build of the same
version, which replaces it, and above the version before, and never repeat;
a push must see what the archive holds; what a push restarts must be what
the package runs; and the runner must take the loop's words.
"""

import datetime
import importlib.util
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tests" / "lib"))
spec = importlib.util.spec_from_file_location("vm", REPO / "tests" / "lib" / "vm.py")
vm = importlib.util.module_from_spec(spec)
spec.loader.exec_module(vm)

failed = 0


def check(name: str, passed: bool, detail: str = "") -> None:
    global failed
    print(("PASS  " if passed else "FAIL  ") + name)
    if not passed:
        failed += 1
        if detail:
            print("      " + detail)


def newer(first: str, second: str) -> bool:
    return subprocess.run(["dpkg", "--compare-versions", first, "gt", second]).returncode == 0


first = vm.dev_version("0.2.22", datetime.datetime(2026, 9, 26, 18, 30, 5))
later = vm.dev_version("0.2.22", datetime.datetime(2026, 9, 26, 18, 31, 0))
check("a development version is the tree's with the time appended, before it",
      first == "0.2.22~dev.20260926183005", first)
check("it is older than the tree's own build of that version, which replaces it",
      newer("0.2.22", first))
check("and newer than the version before", newer(first, "0.2.21"))
check("a later push is newer than an earlier one", newer(later, first))

index = ("Package: kidux-greeter\nVersion: 0.2.22\nDescription: a: b\n\n"
         "Package: python3-kidux\nSource: kidux-common\nVersion: 0.1.9~dev.1\n\n"
         "Package: kidux-greeter\nVersion: 0.2.23~dev.20260926183005\n")
check("a push reads the archive's versions of the package's binaries",
      vm.versions_in(index, {"kidux-greeter"}) == ["0.2.22", "0.2.23~dev.20260926183005"],
      str(vm.versions_in(index, {"kidux-greeter"})))

entry = vm.changelog_entry("kidux-greeter", first, "A Maintainer <a@example.org>",
                           "Sat, 26 Sep 2026 18:30:05 +0200")
parsed = subprocess.run(["dpkg-parsechangelog", "-l-", "-S", "Version"], input=entry,
                        capture_output=True, text=True).stdout.strip()
check("its changelog entry is one dpkg reads", parsed == first, parsed)

import tempfile  # noqa: E402

with tempfile.TemporaryDirectory() as scratch:
    copy = Path(scratch)
    (copy / "module.toml").write_text('id = "x"\nversion = "0.1.2"\n')
    (copy / "pkg").mkdir()
    (copy / "pkg" / "__init__.py").write_text('VERSION = "0.1.2"\n')
    vm.restate(copy, "0.1.2", "0.1.2~dev.1")
    check("the development version is restated in the manifest and a VERSION constant",
          'version = "0.1.2~dev.1"' in (copy / "module.toml").read_text()
          and 'VERSION = "0.1.2~dev.1"' in (copy / "pkg" / "__init__.py").read_text())

commands, notes = vm.after_install(["kidux-daemon"], child_signed_in=True)
check("the daemon is restarted", commands == ["systemctl restart kidux-daemon"], str(commands))
commands, notes = vm.after_install(["kidux-greeter"], child_signed_in=False)
check("the sign-in screen is started again when nobody is signed in",
      commands == ["systemctl restart greetd"], str(commands))
commands, notes = vm.after_install(["kidux-greeter"], child_signed_in=True)
check("and left for the child signed in to log out", commands == [] and len(notes) == 1,
      str(commands))
commands, notes = vm.after_install(["kidux-common"], child_signed_in=False)
check("the library restarts everything that imports it that can be",
      commands == ["systemctl restart kidux-daemon", "systemctl restart greetd"]
      and any("launcher" in note for note in notes), str(commands))
commands, notes = vm.after_install(["kidux-module-hello", "kidux-session"], child_signed_in=False)
check("a module and the session wait", commands == [] and len(notes) == 2, str(notes))

usage = subprocess.run([str(REPO / "tests" / "run"), "vm", "push"], capture_output=True, text=True)
check("tests/run vm push without a package is refused", usage.returncode == 2, usage.stderr)
bad = subprocess.run([str(REPO / "tests" / "run"), "vm", "push", "kidux-archive-keyring"],
                     capture_output=True, text=True)
check("and the archive's key is never pushed", bad.returncode == 2, bad.stderr)
unknown = subprocess.run([str(REPO / "tests" / "run"), "vm", "fly"], capture_output=True, text=True)
check("an unknown word is refused", unknown.returncode == 2)

sys.exit(failed)
