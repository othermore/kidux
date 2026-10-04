"""How a module is started: the command, and nothing else (D32, D42).

`command` is a pure function from a module and the child's home to the argv
the launcher runs, so that everything about how a module is started is in
one place and its test is the specification.

Every module runs in a systemd user scope of its own, `kidux-module-<id>`,
under the child's user manager: the scope is what ends it
(`systemctl --user stop`), caps its memory, is frozen with the session under
the lock screen (D40), and keeps the module running if the launcher
crashes, so the child's work is not lost. With `--scope`, systemd-run runs
the program itself, so the launcher's child process is the module.

A module sees what the child sees: their home, where the files they make
are shared by every module (D42), and the machine as any program of the
child's user sees it. What is the module's own is its settings and its
cache, kept in directories of its own under the child's home, apart from
every other module's, which stay when the module is removed (D89). There
is no sandbox: the child's Unix user is the boundary (D17).
"""

import logging
import os
import shlex
import subprocess

from kidux import modules as kidux_modules

log = logging.getLogger("kidux.launcher")


def data_home(home: str, module_id: str) -> str:
    return f"{home}/.local/share/kidux/{module_id}"


def config_home(home: str, module_id: str) -> str:
    return f"{home}/.config/kidux/{module_id}"


def cache_home(home: str, module_id: str) -> str:
    return f"{home}/.cache/kidux/{module_id}"


def directories(home: str, module_id: str) -> tuple[str, str, str]:
    """The three directories that are the module's own, made before it starts."""
    return data_home(home, module_id), config_home(home, module_id), cache_home(home, module_id)


#: Where xdg-user-dirs keeps the names of the child's folders, Documents and
#: Downloads in the child's language, read from XDG_CONFIG_HOME.
USER_DIRS = ("user-dirs.dirs", "user-dirs.locale")


def share_user_dirs(home: str, module_id: str) -> None:
    """Let the module find the child's folders by their names.

    A program asks for Documents or Downloads with xdg-user-dirs, which
    reads them from $XDG_CONFIG_HOME/user-dirs.dirs; the module's
    XDG_CONFIG_HOME is a directory of its own, so it would find nothing
    there and fall back to the home itself, or to an English ~/Downloads
    for a Spanish-speaking child. So the child's own files are linked into
    it, where the module has none of its own."""
    for name in USER_DIRS:
        child_s = os.path.join(home, ".config", name)
        module_s = os.path.join(config_home(home, module_id), name)
        if not os.path.exists(child_s) or (os.path.exists(module_s)
                                           and not os.path.islink(module_s)):
            continue
        if os.path.islink(module_s):
            os.unlink(module_s)
        os.symlink(child_s, module_s)


def unit(module_id: str) -> str:
    return f"kidux-module-{module_id}"


def running() -> list[str]:
    """The ids of the modules whose scope is active under the child's user
    manager now: those open, or one that outlived the launcher before this one."""
    try:
        listed = subprocess.run(
            ["systemctl", "--user", "list-units", "--plain", "--no-legend", "--state=active",
             unit("*") + ".scope"], capture_output=True, text=True, timeout=10, check=False)
    except (OSError, subprocess.TimeoutExpired):
        return []
    found = []
    for line in listed.stdout.splitlines():
        name = line.split()[0] if line.split() else ""
        if name.startswith("kidux-module-") and name.endswith(".scope"):
            found.append(name[len("kidux-module-"):-len(".scope")])
    return found


def stop(module_id: str) -> None:
    """End a module whatever it is doing: its scope stopped, every process
    in it with it. For a module that did not close when asked (D45)."""
    try:
        subprocess.run(["systemctl", "--user", "stop", unit(module_id) + ".scope"],
                       capture_output=True, timeout=30, check=False)
    except (OSError, subprocess.TimeoutExpired):
        log.warning("could not end %s", module_id, exc_info=True)


#: What opens a module made of web pages, a web application or a website,
#: in Chromium walled in to its own hosts (D36, D85).
WEBAPP = "/usr/libexec/kidux-webapp"

#: How a setting an adult gave starts in the module's environment (D90).
SETTING_ENV = "--setenv=KIDUX_SETTING_"


def setting_text(value) -> str:
    """A setting's value as the environment carries it: a switch 1 or 0,
    a number as Python writes it, a text as it is."""
    if isinstance(value, bool):
        return "1" if value else "0"
    return str(value)


def shown(argv: list[str]) -> str:
    """`argv` as the journal is told it: the settings' values left out, since
    what an adult set for a child, an account's address among them, is not
    the journal's."""
    return shlex.join(arg[:arg.index("=", len(SETTING_ENV)) + 1] + "…"
                      if arg.startswith(SETTING_ENV) else arg for arg in argv)


def command(module, home: str, settings: dict | None = None) -> list[str]:
    """The argv that starts `module` for the child whose home is `home`: its
    program, or for a web application or a website `kidux-webapp <module
    id>`, which reads the module's manifest, in the scope. `settings`, what
    an adult set in it for this child (D90), go into its environment as
    KIDUX_SETTING_<KEY>. What it writes on its standard output and error
    goes to the journal as `kidux-module-<id>`: a session's own, inherited,
    is the console of the terminal labwc draws on, which nobody sees.

    A web application whose name is not an id raises ValueError, as does a
    manifest with nothing to start.
    """
    program = module.launch.get("exec")
    webapp = module.launch.get("webapp")
    if isinstance(program, str) and program:
        started = shlex.split(program)
    elif isinstance(webapp, str) and kidux_modules.ID.match(webapp):
        started = [WEBAPP, module.id]
    elif kidux_modules.web_host(module.launch):
        started = [WEBAPP, module.id]
    else:
        raise ValueError(f"module {module.id} has nothing to start")
    data, config, cache = directories(home, module.id)
    return [
        "systemd-run", "--user", "--scope", "--quiet", "--collect",
        f"--unit={unit(module.id)}",
        f"--property=MemoryMax={module.memory_max}",
        f"--setenv=XDG_DATA_HOME={data}",
        f"--setenv=XDG_CONFIG_HOME={config}",
        f"--setenv=XDG_CACHE_HOME={cache}",
        *(f"{SETTING_ENV}{key.upper()}={setting_text(value)}"
          for key, value in sorted((settings or {}).items())
          if kidux_modules.SETTING_KEY.match(key)),
        "--",
        # It runs the module itself in its place, the same process.
        "systemd-cat", f"--identifier={unit(module.id)}",
    ] + started
