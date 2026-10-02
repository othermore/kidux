"""kidux-launcher: the child's screen, the only program their session runs.

It runs as the child. It exits with status 0 only when the child logs out;
any other ending is a crash, which session-inner answers by starting it
again (launcher.md section 4).
"""

import logging
import logging.handlers
import os
import pwd
import sys

from kidux import log as kidux_log
from kidux import screen as kidux_screen

#: The layer-shell library the bar is drawn with (bar.py).
LAYER_SHELL = "libgtk4-layer-shell.so.0"


def with_layer_shell() -> None:
    """Start again with gtk4-layer-shell preloaded, unless it already is.

    The library has to be in the process before GTK connects to the
    compositor, and importing it through GObject introspection comes too
    late; so the launcher runs itself once more, the same process, with the
    library in LD_PRELOAD. The modules it starts do not inherit it (view.py).
    """
    preload = os.environ.get("LD_PRELOAD", "")
    if LAYER_SHELL in preload.replace(":", " ").split():
        return
    os.environ["LD_PRELOAD"] = f"{preload} {LAYER_SHELL}".strip()
    try:
        os.execv(sys.executable, [sys.executable, *sys.argv])
    except OSError:
        logging.getLogger("kidux.launcher").exception("could not preload %s", LAYER_SHELL)


def log_to_journal() -> None:
    """The session's output goes nowhere anyone reads; the journal does."""
    if os.environ.get("JOURNAL_STREAM") or not os.path.exists("/dev/log"):
        return
    handler = logging.handlers.SysLogHandler(address="/dev/log")
    handler.setFormatter(logging.Formatter("kidux-launcher: %(name)s: %(levelname)s: %(message)s"))
    logging.getLogger("kidux").addHandler(handler)


def main() -> int:
    with_layer_shell()
    log = kidux_log.setup("launcher")
    log_to_journal()
    os.environ.setdefault("GSETTINGS_BACKEND", "memory")

    import gi

    gi.require_version("Gtk", "4.0")
    gi.require_version("Adw", "1")
    from gi.repository import Adw, Gio

    from .bar import layer_shell
    from .daemon import SystemDaemon
    from .compositor import Labwc, NoCompositor
    from .desk import Desk
    from .view import Launcher, install_style

    username = pwd.getpwuid(os.getuid()).pw_name
    logged_out = []
    application = Adw.Application(application_id="org.kidux.Launcher",
                                  flags=Gio.ApplicationFlags.NON_UNIQUE)
    application.get_style_manager().set_color_scheme(Adw.ColorScheme.FORCE_LIGHT)

    def log_out():
        logged_out.append(True)
        application.quit()

    def activate(_application):
        try:
            compositor = Labwc()
        except Exception:  # noqa: BLE001 — the tiles still open modules without it
            log.exception("the compositor cannot be reached; modules open as they can")
            compositor = NoCompositor()
        # The window's title is what the compositor lists it as.
        window = Adw.ApplicationWindow(application=application, title="Kidux")
        install_style(window.get_display())
        # The room the display scale leaves, which the session tests read.
        width, height = kidux_screen.logical_size(window.get_display())
        roomy = kidux_screen.roomy(width, height)
        log.info("screen %dx%d%s", width, height, ", roomy" if roomy else "")
        if roomy:
            window.add_css_class("kidux-roomy")
        launcher = None

        def changed():
            if launcher is not None:
                launcher.desk_changed()

        desk = Desk(compositor, on_change=changed,
                    windows=os.environ.get("KIDUX_WINDOWS") == "1")
        launcher = Launcher(window, SystemDaemon(username), desk, on_log_out=log_out)
        compositor.on_change(desk.settle, on_close=launcher.close_module, on_home=desk.home,
                             on_switch=launcher.switch)
        launcher.present(application,
                         layer_shell() if isinstance(compositor, Labwc) else None)

    application.connect("activate", activate)
    try:
        application.run([])
    except Exception:
        log.exception("the launcher failed")
        return 1
    if logged_out:
        log.info("%s logged out", username)
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
