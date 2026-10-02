"""The real daemon and bus layer, with a fake machine underneath.

Run by test_bus.py as a subprocess on a private system bus. Everything the
daemon decides is real; only adduser and logind are stood in for, because the
tests must not create users or power anything off.
"""

import os
import sys
from pathlib import Path

# Run as a script, this file's directory is first on the path rather than the
# tree that holds kiduxd; put that tree first, wherever the tests are run from.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from gi.repository import Gio  # noqa: E402

from kidux import log, paths  # noqa: E402
from kiduxd import main  # noqa: E402
from kiduxd.accounts import FakeAccounts  # noqa: E402
from kiduxd.logind import FakeLogind  # noqa: E402

log.setup("daemon", debug=True)

accounts = FakeAccounts()
# The test process is the administrator, whatever uid it runs as.
accounts.add_user("admin", os.getuid(), (paths.ADMIN_GROUP,))
accounts.add_user("ana", 3001, (paths.CHILDREN_GROUP, "video"))



class FakeMachine:
    """Nothing of the machine is touched; apt offers one module."""

    def kidux_packages(self):
        return "kidux-base 0.2.3 installed\n"

    def modules_offered(self):
        return ("Package: kidux-module-hello\n"
                "Description: Kidux learning module: Hello, a first page to read\n\n", "")


connection = Gio.bus_get_sync(Gio.BusType.SYSTEM, None)
service, bus_object = main.build(
    connection, accounts=accounts, logind=FakeLogind(), machine=FakeMachine()
)
sys.exit(main.serve(connection, service, bus_object, watch_sessions=False, watch_input=False))
