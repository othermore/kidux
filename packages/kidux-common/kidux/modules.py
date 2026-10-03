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

#: A setting's key, which is also the name a module reads it by.
SETTING_KEY = re.compile(r"\A[a-z][a-z0-9_]{0,31}\Z")

#: What a setting may be (D90): each module declares its own, of these kinds.
SETTING_KINDS = ("switch", "integer", "number", "text", "secret")


@dataclass(frozen=True)
class Setting:
    """One thing an adult sets in a module for each child (D90): its name
    and what it does, both in English and translated through the module's
    catalogue, as the module's own name and description are."""
    key: str
    kind: str
    label: str
    description: str = ""
    default: object = None
    minimum: float | None = None
    maximum: float | None = None

    def value(self, raw):
        """`raw` as this setting's kind, within its limits; ValueError for
        anything else. A switch is True or False, an integer an int, a number
        a float, a text or a secret a str of one line."""
        if self.kind == "switch":
            if isinstance(raw, bool):
                return raw
        elif self.kind == "integer":
            if isinstance(raw, int) and not isinstance(raw, bool):
                return self._within(raw)
        elif self.kind == "number":
            if isinstance(raw, (int, float)) and not isinstance(raw, bool):
                return self._within(float(raw))
        elif isinstance(raw, str) and "\n" not in raw and len(raw) <= 1024:
            return raw
        raise ValueError(f"not a {self.kind} for {self.key}: {raw!r}")

    def _within(self, number):
        if self.minimum is not None and number < self.minimum:
            raise ValueError(f"{self.key} is at least {self.minimum}")
        if self.maximum is not None and number > self.maximum:
            raise ValueError(f"{self.key} is at most {self.maximum}")
        return number


def _settings(module_id: str, declared) -> tuple[Setting, ...]:
    """The `[[settings]]` of a manifest that are good, each once; a bad one
    is dropped with a line in the log."""
    if not isinstance(declared, list):
        log.warning("module %s: settings is not a list of tables", module_id)
        return ()
    found: list[Setting] = []
    for table in declared:
        try:
            if not isinstance(table, dict):
                raise ValueError("not a table")
            key, kind, label = table.get("key"), table.get("kind"), table.get("label")
            if not isinstance(key, str) or not SETTING_KEY.match(key):
                raise ValueError(f"key {key!r} is not a setting's name")
            if any(setting.key == key for setting in found):
                raise ValueError(f"{key} is declared twice")
            if kind not in SETTING_KINDS:
                raise ValueError(f"{key}'s kind {kind!r} is not one of {', '.join(SETTING_KINDS)}")
            if not isinstance(label, str) or not label:
                raise ValueError(f"{key} has no label")
            described = table.get("description")
            if not isinstance(described, str) or not described:
                raise ValueError(f"{key} does not say what it does in a description")
            limits = {}
            for name, field_name in (("min", "minimum"), ("max", "maximum")):
                if name in table:
                    if kind not in ("integer", "number") or isinstance(table[name], bool) \
                            or not isinstance(table[name], (int, float)):
                        raise ValueError(f"{key}'s {name} is not a number of an integer or a number")
                    limits[field_name] = table[name]
            plain = Setting(key, kind, label, described, None, **limits)
            fallback = {"switch": False, "integer": 0, "number": 0.0}.get(kind, "")
            if kind == "secret" and "default" in table:
                raise ValueError(f"{key} is a secret, which has no default")
            default = plain.value(table.get("default", fallback)) if "default" in table \
                else fallback
            found.append(Setting(key, kind, label, described, default, **limits))
        except ValueError as error:
            log.warning("module %s: a setting is left out: %s", module_id, error)
    return tuple(found)


@dataclass(frozen=True)
class SignIn:
    """How a module that opens a website signs a child in (phase-4c-plan.md,
    4.17): data the daemon acts on, never code. It sends `body`, with
    `{email}` and `{password}` where the child's settings go, as JSON to
    `url`, an https:// address on one of the module's hosts, and hands the
    child's session the cookies named in `cookies`. `script`, a file beside
    the manifest, then runs in the site's first page, with the child's
    language; `start` is where the window goes once it has."""
    url: str
    body: tuple[tuple[str, str], ...]
    cookies: tuple[str, ...]
    script: str = ""
    start: str = ""


def _sign_in(module_id: str, table, hosts: list[str], directory: Path) -> SignIn | None:
    if table is None:
        return None
    def on_hosts(address) -> bool:
        if not isinstance(address, str) or not address.startswith("https://"):
            return False
        host = urlsplit(address).hostname or ""
        return any(host == name or host.endswith("." + name) for name in hosts)

    try:
        if not isinstance(table, dict):
            raise ValueError("it is not a table")
        url, body, cookies = table.get("url"), table.get("body"), table.get("cookies")
        if not on_hosts(url):
            raise ValueError(f"its url {url!r} is not an https:// address on its hosts")
        if not isinstance(body, dict) or not body or \
                not all(isinstance(k, str) and isinstance(v, str) for k, v in body.items()):
            raise ValueError("its body is not a table of texts")
        if not isinstance(cookies, list) or not cookies or \
                not all(isinstance(c, str) and re.fullmatch(r"[A-Za-z0-9_.-]+", c) for c in cookies):
            raise ValueError("its cookies are not a list of cookie names")
        script = table.get("script", "")
        if script and (not isinstance(script, str) or "/" in script
                       or not (directory / script).is_file()):
            raise ValueError(f"its script {script!r} is not a file beside the manifest")
        start = table.get("start", "")
        if start and not on_hosts(start):
            raise ValueError(f"its start {start!r} is not an https:// address on its hosts")
        return SignIn(url, tuple(body.items()), tuple(cookies),
                      str(directory / script) if script else "", start or "")
    except ValueError as error:
        log.warning("module %s: its sign_in is left out: %s", module_id, error)
        return None


def _page_script(module_id: str, name, directory: Path) -> str:
    """The file a module made of web pages names to run in every page its
    window shows (phase-4c-plan.md, 4.18), beside its manifest; "" for none."""
    if not name:
        return ""
    if not isinstance(name, str) or "/" in name or not (directory / name).is_file():
        log.warning("module %s: its page_script %r is not a file beside the manifest",
                    module_id, name)
        return ""
    return str(directory / name)


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
    #: What an adult sets in it for each child, as its manifest declares.
    settings: tuple["Setting", ...] = ()
    #: How the daemon signs a child in to its website, when it does.
    sign_in: "SignIn | None" = None
    #: A script of its own that runs in every page its window shows, or "".
    page_script: str = ""


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
        if "sign_in" in manifest:
            # Its window opens on its own page first, Connecting…, served
            # by kidux-webapps, and keeps that page's name.
            app_ids.append(WEBAPP_APP_ID.format(id=module_id))

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
        settings=_settings(module_id, manifest.get("settings", [])),
        sign_in=_sign_in(module_id, manifest.get("sign_in"),
                         sorted(set(hosts)), directory),
        page_script=_page_script(module_id, manifest.get("page_script"), directory),
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


def text_in(module: Module, text: str, language: str) -> str:
    """One of the module's own words, a setting's label or description, in
    `language`, through the module's catalogue."""
    return _translations(module, language).gettext(text) if text else ""


def description_in(module: Module, language: str) -> str:
    if not module.description:
        return ""
    return _translations(module, language).gettext(module.description)
