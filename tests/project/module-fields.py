#!/usr/bin/python3
"""Every module package names and describes itself in each language it ships,
and says who it is for.

    tests/project/module-fields.py            check
    tests/project/module-fields.py --update   write the fields from the sources

The panel offers the modules the archive has, and of one that is not
installed the machine knows only what the archive's index says (D47). So
each module's `debian/control` carries, in its binary paragraph,
`XB-Kidux-Name-<lang>` and `XB-Kidux-Description-<lang>` for English and for
every language it has a `po/<lang>.po` for: the same words as its manifest's
`name` and `description`, and their translations in its catalogue. This
fails when they differ, so the words in the index cannot drift from the
module's own; `--update` writes them from the manifest and the catalogue.

After them, from the manifest too (D55): `XB-Kidux-Ages`, its `min_age` and
`max_age` as `4-8`, or `2-` or `-10` with one of them, absent when neither
is set; and `XB-Kidux-Before`, its `recommended_before`, the ids separated
by spaces, absent when there are none.
"""

import gettext
import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SOURCE_LANGUAGE = "en"


def expected(package: Path) -> dict[str, str]:
    """The fields a module's control should carry, in order: English first,
    then its catalogues' languages by name."""
    manifest = tomllib.loads((package / "module.toml").read_text())
    fields = {f"XB-Kidux-Name-{SOURCE_LANGUAGE}": manifest["name"],
              f"XB-Kidux-Description-{SOURCE_LANGUAGE}": manifest["description"]}
    for po in sorted((package / "po").glob("*.po")):
        with tempfile.NamedTemporaryFile(suffix=".mo") as compiled:
            subprocess.run(["msgfmt", "-o", compiled.name, str(po)], check=True)
            with open(compiled.name, "rb") as handle:
                catalogue = gettext.GNUTranslations(handle)
        fields[f"XB-Kidux-Name-{po.stem}"] = catalogue.gettext(manifest["name"])
        fields[f"XB-Kidux-Description-{po.stem}"] = catalogue.gettext(manifest["description"])
    ages = ages_field(manifest.get("min_age", 0), manifest.get("max_age", 0))
    if ages:
        fields["XB-Kidux-Ages"] = ages
    if manifest.get("recommended_before"):
        fields["XB-Kidux-Before"] = " ".join(manifest["recommended_before"])
    return fields


def ages_field(least: int, most: int) -> str:
    """A module's ages as its package says them: 4-8, 2- or -10; "" for none."""
    if not least and not most:
        return ""
    return f"{least or ''}-{most or ''}"


def stated(control: str) -> dict[str, str]:
    """The XB-Kidux- fields a control file carries."""
    fields = {}
    for line in control.splitlines():
        name, separator, value = line.partition(":")
        if separator and name.startswith("XB-Kidux-"):
            fields[name] = value.strip()
    return fields


def updated(control: str, fields: dict[str, str]) -> str:
    """The control file with its XB-Kidux- fields replaced by `fields`, just
    before the binary paragraph's Description."""
    lines = [line for line in control.splitlines() if not line.startswith("XB-Kidux-")]
    at = max(i for i, line in enumerate(lines) if line.startswith("Description:"))
    lines[at:at] = [f"{name}: {value}" for name, value in fields.items()]
    return "\n".join(lines) + "\n"


def main(argv: list[str]) -> int:
    update = argv[1:] == ["--update"]
    failed = 0
    for package in sorted(p for p in REPO.glob("packages/kidux-module-*")
                          if (p / "debian" / "control").is_file()):
        control_file = package / "debian" / "control"
        control = control_file.read_text()
        fields = expected(package)
        if update:
            control_file.write_text(updated(control, fields))
            print(f"WROTE {package.name}")
        elif stated(control) == fields:
            languages = sum(1 for name in fields if name.startswith("XB-Kidux-Name-"))
            print(f"PASS  {package.name} names itself in {languages} languages, and says "
                  "who it is for, as its manifest and catalogue do")
        else:
            failed += 1
            print(f"FAIL  {package.name}: its control's XB-Kidux- fields are not its "
                  "manifest's and catalogue's words; tests/project/module-fields.py --update",
                  file=sys.stderr)
            for name, value in fields.items():
                if stated(control).get(name) != value:
                    print(f"      {name}: {value}", file=sys.stderr)
    return failed


if __name__ == "__main__":
    sys.exit(main(sys.argv))
