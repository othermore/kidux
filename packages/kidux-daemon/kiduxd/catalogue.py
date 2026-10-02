"""The modules the archive offers, from what apt and dpkg already know.

daemon.md section 9. The daemon never goes to the network for this: apt's
lists are as fresh as the last `System1.CheckUpdates`, which the panel runs
when the adult asks it to look for modules. Two outputs are read, and the
reading is a pure function of them so that it is tested against samples:

    apt-cache search --names-only --full '^kidux-module-'
        Package: kidux-module-hello
        Kidux-Name-es: Hola
        Kidux-Description-es: Una primera página para leer, ...
        Description: Kidux learning module: Hello, a first page to read
        ...

    dpkg-query -W -f '${Package} ${Version} ${db:Status-Status}\\n' 'kidux-module-*'
        kidux-module-hello 0.1.1 installed

A package whose name after `kidux-module-` is not a module id is left out:
the daemon only ever makes a package name from an id it has checked, so a
package it could not name is one it could not install either.

A module's name and description are in the machine's language (D47): an
installed module's name is its manifest's, in its own catalogue; a module
not installed has them from its record's `Kidux-Name-<lang>` and
`Kidux-Description-<lang>` fields (`XB-` in its `debian/control`), the
machine's language first, then English; and a module without them has
what its short description says, `Kidux learning module: <Name>, <what it
is>` (packaging.md, "Conventions"), in English.

Who a module is for (D55) comes the same way: an installed module's from
its manifest, one not installed from its record's `Kidux-Ages` (`4-8`, `2-`
or `-10`) and `Kidux-Before` (module ids separated by spaces).
"""

from typing import Callable

from kidux import modules as kidux_modules

PREFIX = "kidux-module-"
#: How every module's short description starts; the panel shows the rest.
DESCRIPTION_PREFIX = "Kidux learning module: "


def package_of(module_id: str) -> str:
    """The package of a module id the caller has checked."""
    return PREFIX + module_id


def installed_versions(dpkg_output: str) -> dict[str, str]:
    """Package name to version, for the packages dpkg has installed."""
    versions = {}
    for line in dpkg_output.splitlines():
        fields = line.split()
        if len(fields) == 3 and fields[2] == "installed":
            versions[fields[0]] = fields[1]
    return versions


def described(short_description: str) -> tuple[str, str]:
    """The name and the description in a module's short description, or ""
    for the name when it does not follow the convention."""
    text = short_description.strip()
    if not text.startswith(DESCRIPTION_PREFIX):
        return "", text
    name, separator, rest = text[len(DESCRIPTION_PREFIX):].partition(", ")
    if not separator:
        return name.strip(), ""
    rest = rest.strip()
    return name.strip(), rest[:1].upper() + rest[1:]


def records(apt_output: str) -> list[dict[str, str]]:
    """The records `apt-cache search --full` prints, each as its fields
    (continuation lines left out: only first lines are read)."""
    found: list[dict[str, str]] = []
    record: dict[str, str] = {}
    for line in apt_output.splitlines() + [""]:
        if not line.strip():
            if record:
                found.append(record)
            record = {}
        elif not line[0].isspace():
            name, separator, value = line.partition(":")
            if separator:
                record.setdefault(name.strip().lower(), value.strip())
    return found


def ages(field: str) -> tuple[int, int]:
    """A record's Kidux-Ages as (min_age, max_age), 0 for a bound not given:
    "4-8" (4, 8), "2-" (2, 0), "-10" (0, 10); (0, 0) for anything else."""
    least, separator, most = field.strip().partition("-")
    if not separator or not all(bound == "" or bound.isdigit() for bound in (least, most)):
        return 0, 0
    return int(least or 0), int(most or 0)


def before(field: str) -> list[str]:
    """A record's Kidux-Before as the module ids in it; what is not one is left out."""
    return [word for word in field.split() if kidux_modules.ID.match(word)]


def language_of(locale: str) -> str:
    """The language of a locale such as es_ES.UTF-8: es; en for none."""
    return locale.split(".")[0].split("_")[0].split("@")[0] or "en"


def available(apt_output: str, dpkg_output: str,
              installed_of: Callable[[str], dict | None], language: str = "en") -> list[dict]:
    """Every module package the archive offers, sorted by id, as
    {id, name, description, installed, version, offered_version, min_age,
    max_age, before}, `version` the installed one and `offered_version` the
    archive's,
    in `language` (a language code such as "es") where the package says it.

    `installed_of(id)` is what an installed module's manifest says, any of
    {name, min_age, max_age, before}, the name in the machine's language;
    or None.
    """
    versions = installed_versions(dpkg_output)
    found: dict[str, dict] = {}
    for record in records(apt_output):
        package = record.get("package", "")
        if not package.startswith(PREFIX) or package[len(PREFIX):] in found:
            continue
        module_id = package[len(PREFIX):]
        if not kidux_modules.ID.match(module_id):
            continue
        short_name, short_description = described(record.get("description", ""))
        name = next((record[f"kidux-name-{lang}"] for lang in (language, "en")
                     if record.get(f"kidux-name-{lang}")), short_name)
        description = next((record[f"kidux-description-{lang}"] for lang in (language, "en")
                            if record.get(f"kidux-description-{lang}")), short_description)
        installed = package in versions
        manifest = (installed_of(module_id) if installed else None) or {}
        least, most = ages(record.get("kidux-ages", ""))
        found[module_id] = {
            "id": module_id,
            "name": manifest.get("name") or name or module_id.capitalize(),
            "description": description,
            "installed": installed,
            "version": versions.get(package, ""),
            "offered_version": record.get("version", ""),
            "min_age": manifest.get("min_age", least),
            "max_age": manifest.get("max_age", most),
            "before": list(manifest.get("before", before(record.get("kidux-before", "")))),
        }
    return [found[module_id] for module_id in sorted(found)]
