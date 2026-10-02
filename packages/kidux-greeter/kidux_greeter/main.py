"""kidux-greeter: the sign-in screen, or with --lock <child>, the lock screen.

The one rule this file exists for (docs/dev/greeter.md, section 6): it never
crash-loops. greetd restarts a greeter that exits, with no limit, so a
greeter that dies on start would flash forever in front of a child. Anything
that goes wrong once the window exists becomes a screen with *Try again* and
*Turn off*; anything before that is logged, followed by a pause, and only
then an exit.

The sign-in screen exits on purpose in one case only: greetd accepted the
session, which it starts once the greeter is gone. The lock screen never
exits on its own: the daemon stops its unit.
"""

import argparse
import logging
import logging.handlers
import os
import signal
import sys
import time

from kidux import log as kidux_log
from kidux import paths
from kidux import screen as kidux_screen

#: How long a greeter that cannot even start waits before exiting, so that a
#: broken installation costs a restart every few seconds rather than a busy
#: loop.
START_FAILURE_PAUSE = 5


def parse(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="kidux-greeter", description=__doc__.splitlines()[0])
    parser.add_argument("--lock", metavar="CHILD",
                        help="be the lock screen over CHILD's session")
    parser.add_argument("--debug", action="store_true")
    return parser.parse_args(argv)


def build(arguments: argparse.Namespace):
    """Everything that can fail before there is a window to show a failure on."""
    import gi

    gi.require_version("Gtk", "4.0")
    gi.require_version("Adw", "1")
    from gi.repository import Adw, Gio

    from . import view as view_module
    from .daemon import SystemDaemon
    from .flow import Lock, SignIn
    from .greetd import Greetd

    daemon = SystemDaemon()
    if arguments.lock:
        paths.child_dir(arguments.lock)  # refuses a name with a path in it
        flow = Lock(daemon, arguments.lock)
        greetd = None
    else:
        greetd = Greetd()
        flow = SignIn(daemon, greetd)

    application = Adw.Application(application_id="org.kidux.Greeter",
                                  flags=Gio.ApplicationFlags.NON_UNIQUE)
    # The trusted screens follow Kidux's own colours, never a desktop's
    # dark-mode preference: there is no desktop here.
    application.get_style_manager().set_color_scheme(Adw.ColorScheme.FORCE_LIGHT)

    finished_on_purpose = []

    def finished():
        # A session was accepted, which greetd starts once the greeter is
        # gone, or a new keyboard layout was set, which cage takes only when
        # it starts: either way, the greeter's work is done.
        if greetd is not None:
            greetd.close()
        finished_on_purpose.append(True)
        application.quit()

    def activate(_application):
        window = Adw.ApplicationWindow(application=application)
        view_module.install_style(window.get_display())
        # The room the display scale leaves, which the session tests read.
        width, height = kidux_screen.logical_size(window.get_display())
        roomy = kidux_screen.roomy(width, height)
        logging.getLogger("kidux.greeter").info("screen %dx%d%s", width, height,
                                                ", roomy" if roomy else "")
        if roomy:
            window.add_css_class("kidux-roomy")
        screen = view_module.View(window, flow, lock=bool(arguments.lock),
                                  on_exit=finished)
        daemon.subscribe(screen.attention, screen.children_changed)
        # Something to draw from the first frame, while the daemon is asked
        # what the first screen is.
        window.set_content(view_module.spinner())
        # No fullscreen() request: cage already gives its one window the
        # whole output.
        window.present()
        screen.run("start")

    application.connect("activate", activate)
    return application, finished_on_purpose


def log_to_journal() -> None:
    """Send the log to the journal when stderr does not go there.

    greetd does not connect a greeter's output to the journal, and a failure
    nobody can read is a failure nobody fixes. systemd sets JOURNAL_STREAM
    when stderr is already the journal, as it is for the lock screen's unit.
    """
    if os.environ.get("JOURNAL_STREAM") or not os.path.exists("/dev/log"):
        return
    handler = logging.handlers.SysLogHandler(address="/dev/log")
    handler.setFormatter(logging.Formatter("kidux-greeter: %(name)s: %(levelname)s: %(message)s"))
    logging.getLogger("kidux").addHandler(handler)


def main(argv: list[str] | None = None) -> int:
    arguments = parse(sys.argv[1:] if argv is None else argv)
    log = kidux_log.setup("greeter", debug=arguments.debug)
    log_to_journal()
    # _greetd has no dconf and no accessibility bus; without these GTK spends
    # its start-up looking for them and fills the journal with the failures.
    os.environ.setdefault("GSETTINGS_BACKEND", "memory")
    os.environ.setdefault("NO_AT_BRIDGE", "1")
    try:
        application, finished_on_purpose = build(arguments)
    except Exception:  # noqa: BLE001 — see the module docstring
        log.exception("the greeter cannot start")
        time.sleep(START_FAILURE_PAUSE)
        return 1
    status = application.run([])
    if status != 0:
        time.sleep(START_FAILURE_PAUSE)
    elif finished_on_purpose:
        end_compositor()
    return status


def end_compositor() -> None:
    """End the cage this program runs in, now that the program is done.

    cage does not always notice its one client leave: it can sit on the
    greeter's exit and keep the screen, and greetd, waiting for cage, never
    starts the next greeter. The greeter's parent is that cage, because
    session-inner `exec`s it; nothing else is signalled.
    """
    parent = os.getppid()
    try:
        name = open(f"/proc/{parent}/comm").read().strip()
    except OSError:
        return
    if name == "cage":
        os.kill(parent, signal.SIGTERM)


if __name__ == "__main__":
    sys.exit(main())
