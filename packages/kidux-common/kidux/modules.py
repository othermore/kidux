"""The learning modules installed on this computer (docs/dev/modules.md).

Each module package installs /usr/share/kidux/modules/<id>/module.toml and,
beside it, icon.svg. This is the one reader of those manifests (D34): the
daemon asks it what is installed, the launcher what to draw a tile for, the
panel what to put a switch beside. A manifest that cannot be read is skipped
and logged: one broken module must never cost a child the others.

A module's name and description are English in the manifest and translated
through the module's own gettext domain, which its package installs.
"""

import fnmatch
import gettext
import logging
import re
import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlsplit

from . import paths

log = logging.getLogger("kidux.modules")

#: A module's id: also its directory and the end of its package's name.
ID = re.compile(r"\A[a-z][a-z0-9-]{0,31}\Z")

#: The scope's memory cap for a module whose manifest names none.
DEFAULT_MEMORY_MAX = "2G"

#: A name in a manifest's `hosts`: a lower-case DNS name, at least two
#: labels, nothing else.
HOST = re.compile(r"\A(?=.{1,253}\Z)[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?"
                  r"(?:\.[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?)+\Z")


@dataclass(frozen=True)
class Module:
    id: str
    name: str
    description: str = ""
    #: The path of icon.svg beside the manifest, or "" when there is none.
    icon: str = ""
    #: {"exec": "/path"}, {"webapp": "<id>"}, or {"web": "https://…"}, an
    #: address on the internet in which {lang} is the child's language.
    launch: dict = field(default_factory=dict)
    i18n_domain: str = ""
    min_age: int = 0
    max_age: int = 0
    memory_max: str = DEFAULT_MEMORY_MAX
    #: Whether it is only for a child whose modules open in windows (D46):
    #: `needs_windows = true` in its manifest.
    needs_windows: bool = False
    #: The ids of the modules best done before this one (D55), for the
    #: panel to say; never enforced.
    recommended_before: tuple[str, ...] = ()
    #: What its windows are called, as globs: a Wayland window's app_id, an
    #: X11 window's WM_CLASS. How the launcher knows which module a window
    #: is of (D58); a web application's is Chromium's, always there.
    app_ids: tuple[str, ...] = ()
    #: Its manifest's version, which its package's is: what the panel shows.
    version: str = ""
    #: The internet hosts its pages may reach, each with every name under
    #: it (D85): sorted, each once.
    hosts: tuple[str, ...] = ()


#: What Chromium calls the window of `kidux-webapp <id>` (launch.py): the
#: address's host and path, and its profile.
WEBAPP_APP_ID = "chrome-127.0.0.1__{id}_-*"

#: What Chromium calls the window of a module that opens a website: the
#: address's host, {lang} in it as any name, then anything.
WEB_APP_ID = "chrome-{host}__*"


def web_host(launch: dict) -> str | None:
    """The host of a `web` launch's address, {lang} in it as written, or
    None when the launch is not an https:// address with a host."""
    address = launch.get("web")
    if not isinstance(address, str) or not address.startswith("https://"):
        return None
    if not urlsplit(address.replace("{lang}", "lang")).hostname:
        return None
    return re.split(r"[/:?#]", address[len("https://"):], maxsplit=1)[0].lower()


def claims(module: "Module", app_id: str) -> bool:
    """Whether a window called `app_id` is one of `module`'s."""
    return any(fnmatch.fnmatchcase(app_id, pattern) for pattern in module.app_ids)


def _root(root: Path | None) -> Path:
    return paths.MODULES_DIR if root is None else Path(root)


def read(module_id: str, root: Path | None = None) -> Module | None:
    """The module with this id, or None when its manifest cannot be used."""
    if not ID.match(module_id or ""):
        log.warning("not a module id: %r", module_id)
        return None
    directory = _root(root) / module_id
    try:
        manifest = tomllib.loads((directory / "module.toml").read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError, UnicodeDecodeError) as error:
        log.warning("skipping module %s: %s", module_id, error)
        return None

    launch = manifest.get("launch")
    if manifest.get("id") != module_id:
        problem = "its id is not its directory's name"
    elif not isinstance(manifest.get("name"), str) or not manifest["name"]:
        problem = "it has no name"
    elif not isinstance(launch, dict) or not (
            isinstance(launch.get("exec"), str) or isinstance(launch.get("webapp"), str)
            or "web" in launch):
        problem = "it says neither a program, a web application nor a website to launch"
    elif "web" in launch and web_host(launch) is None:
        problem = "its website is not an https:// address"
    else:
        problem = None
    if problem:
        log.warning("skipping module %s: %s", module_id, problem)
        return None

    def number(key: str) -> int:
        value = manifest.get(key, 0)
        return value if isinstance(value, int) and not isinstance(value, bool) else 0

    before = manifest.get("recommended_before", [])
    if not isinstance(before, list):
        log.warning("module %s: recommended_before is not a list of ids", module_id)
        before = []
    for other in before:
        if not isinstance(other, str) or not ID.match(other):
            log.warning("module %s: %r in recommended_before is not a module id",
                        module_id, other)

    app_ids = manifest.get("app_ids", [])
    if not isinstance(app_ids, list) or not all(isinstance(a, str) and a for a in app_ids):
        log.warning("module %s: app_ids is not a list of names", module_id)
        app_ids = []
    if isinstance(launch.get("webapp"), str):
        app_ids = [*app_ids, WEBAPP_APP_ID.format(id=launch["webapp"])]
    elif web_host(launch):
        app_ids = [*app_ids, WEB_APP_ID.format(host=web_host(launch).replace("{lang}", "*"))]

    hosts = manifest.get("hosts", [])
    if not isinstance(hosts, list) or not all(isinstance(h, str) and HOST.match(h) for h in hosts):
        log.warning("module %s: hosts is not a list of host names", module_id)
        hosts = []

    icon = directory / "icon.svg"

    return Module(
        id=module_id,
        name=manifest["name"],
        description=str(manifest.get("description", "")),
        icon=str(icon) if icon.is_file() else "",
        launch=dict(launch),
        i18n_domain=str(manifest.get("i18n_domain") or f"kidux-module-{module_id}"),
        min_age=number("min_age"),
        max_age=number("max_age"),
        memory_max=str(manifest.get("memory_max") or DEFAULT_MEMORY_MAX),
        needs_windows=manifest.get("needs_windows") is True,
        recommended_before=tuple(other for other in before
                                 if isinstance(other, str) and ID.match(other)),
        app_ids=tuple(app_ids),
        version=str(manifest.get("version", "")),
        hosts=tuple(sorted(set(hosts))),
    )


def installed(root: Path | None = None) -> list[Module]:
    """Every module whose manifest reads, sorted by id."""
    try:
        entries = sorted(entry.name for entry in _root(root).iterdir() if entry.is_dir())
    except OSError:
        return []
    return [module for module in (read(name, root) for name in entries) if module is not None]


def _translations(module: Module, language: str) -> gettext.NullTranslations:
    return gettext.translation(module.i18n_domain, localedir=str(paths.LOCALE_ROOT),
                               languages=[language or "C"], fallback=True)


def name_in(module: Module, language: str) -> str:
    """The module's name in `language`, a locale such as "es_ES.UTF-8"; its
    English one when the module has no catalogue for it."""
    return _translations(module, language).gettext(module.name)


def description_in(module: Module, language: str) -> str:
    if not module.description:
        return ""
    return _translations(module, language).gettext(module.description)
