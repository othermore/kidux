#!/usr/bin/python3
"""One session test, against the machine a run left up.

    KIDUX_VM_STOP_AFTER=15 tests/run session
    tests/lib/session-one.py tests/session/16-module-open.py

The machine has to be where the test expects it: tests start where the one
before left off (tests/README.md). The pictures are numbered from 50, so
that they do not overwrite the run's.
"""

import importlib.util
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import sessionlib  # noqa: E402
from sessionlib import MONITOR, Machine  # noqa: E402


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(__doc__, file=sys.stderr)
        return 2
    if not MONITOR.exists():
        print(f"no machine is up ({MONITOR} is missing)", file=sys.stderr)
        return 1
    path = Path(argv[1])
    spec = importlib.util.spec_from_file_location(f"session_{path.stem.replace('-', '_')}", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    machine = Machine()
    machine.pictures = 50
    module.run(machine)
    print(f"==> {sessionlib.failures} failed")
    return sessionlib.failures


if __name__ == "__main__":
    sys.exit(main(sys.argv))
