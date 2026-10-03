"""The machine's advanced settings: what depends on its hardware (D52).

Set by an adult on the panel's System page, under Advanced, kept in the
machine's config.toml, and written where the program that needs them reads
them, since that program runs as the child and does not speak to the daemon.
Chromium's flags are the first: what draws a web module cleanly on one
machine's graphics may draw it as noise on another's (D51). The pointer's
speed and the touchpad's scroll are the others, for a child's session's
labwc (kidux.pointer; phase-4c-plan.md, 4.19).
"""

import os
import re
import tempfile
from pathlib import Path

from kidux import paths, pointer

#: A flag: --name or --name=value, the value without spaces or control
#: characters.
FLAG = re.compile(r"\A--[a-z0-9][a-z0-9-]*(=[^\s\x00-\x1f\x7f]+)?\Z")
MOST_FLAGS = 20
LONGEST_FLAG = 200

#: Flags that would take a web module out of Kidux's hold (D36): another page
#: or profile, a door for another program to drive the browser, extensions,
#: the sandbox or the web's own rules turned off, another way to the network.
#: The adult is trusted; a flag copied from a forum should still not undo
#: what the rest of the policy does.
REFUSED = frozenset({
    # Another page, profile or window
    "--app", "--app-id", "--kiosk", "--user-data-dir", "--profile-directory", "--incognito",
    "--guest", "--new-window", "--homepage",
    # A door for another program to drive the browser
    "--remote-debugging-port", "--remote-debugging-pipe", "--remote-debugging-address",
    "--remote-allow-origins",
    # Extensions
    "--load-extension", "--disable-extensions-except", "--enable-remote-extensions",
    # The sandbox, in whole or in part
    "--no-sandbox", "--single-process", "--no-zygote", "--disable-setuid-sandbox",
    "--disable-seccomp-filter-sandbox", "--disable-namespace-sandbox",
    # The web's own rules
    "--disable-web-security", "--allow-file-access-from-files",
    "--allow-running-insecure-content", "--ignore-certificate-errors",
    "--unsafely-treat-insecure-origin-as-secure", "--disable-site-isolation-trials",
    # Another way to the network
    "--proxy-server", "--no-proxy-server", "--proxy-pac-url", "--proxy-auto-detect",
    "--proxy-bypass-list", "--host-resolver-rules", "--host-rules", "--auth-server-allowlist",
    "--auth-server-whitelist",
})


def check_flags(value) -> list[str]:
    """A list of Chromium flags as the panel sends it, checked; ValueError
    with what is wrong."""
    if not isinstance(value, (list, tuple)) or not all(isinstance(v, str) for v in value):
        raise ValueError("chromium_flags is a list of flags")
    flags = [v.strip() for v in value if v.strip()]
    if len(flags) > MOST_FLAGS:
        raise ValueError(f"at most {MOST_FLAGS} flags")
    for flag in flags:
        if len(flag) > LONGEST_FLAG or not FLAG.match(flag):
            raise ValueError(f"not a flag: {flag[:40]!r}")
        if flag.split("=", 1)[0] in REFUSED:
            raise ValueError(f"not a flag Kidux lets a web module run with: {flag.split('=', 1)[0]}")
    return flags


def _write(path: Path, text: str) -> None:
    """`text` in `path` whole, readable by everyone and written by root only."""
    path.parent.mkdir(mode=0o755, parents=True, exist_ok=True)
    handle = tempfile.NamedTemporaryFile("w", dir=path.parent, prefix=f".{path.name}.",
                                         delete=False)
    try:
        with handle:
            handle.write(text)
        os.chmod(handle.name, 0o644)
        os.replace(handle.name, path)
    except BaseException:
        os.unlink(handle.name)
        raise


def write_flags(flags: list[str], path: Path | None = None) -> None:
    """The flags where kidux-webapp reads them, one a line; no file at all
    when there are none."""
    path = path or paths.CHROMIUM_FLAGS
    if not flags:
        path.unlink(missing_ok=True)
        return
    _write(path, "".join(f"{flag}\n" for flag in flags))


def write_input(pointer_step: int, scroll_step: int, path: Path | None = None) -> None:
    """The pointer's speed and the touchpad's scroll where a child's session
    reads them, as the `<libinput>` part of labwc's configuration."""
    _write(path or paths.INPUT_XML,
           "<!-- The panel's Advanced settings, written by kidux-daemon. -->\n"
           + pointer.libinput(pointer_step, scroll_step))
