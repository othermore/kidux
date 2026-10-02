#!/usr/bin/python3
"""Everything kidux-common promises, checked on a machine rather than in a build:
the library imports, a Spanish session gets Spanish, an English one English,
and there are avatars for children to choose from."""
import subprocess
import sys

from kidux import avatars


def translated(language: str) -> str:
    # A fresh interpreter per language: the catalogue is chosen when the
    # module is imported, which is exactly what a session start does.
    result = subprocess.run(
        [sys.executable, "-c",
         "from kidux.i18n import _; print(_('Adult'))"],
        capture_output=True, text=True, check=True,
        env={"LANGUAGE": language, "LANG": f"{language}_ES.UTF-8"
             if language == "es" else "en_US.UTF-8", "PATH": "/usr/bin"},
    )
    return result.stdout.strip()


spanish = translated("es")
assert spanish == "Adulto", f"Spanish session said {spanish!r}"
print("es: Adulto")

english = translated("en")
assert english == "Adult", f"English session said {english!r}"
print("en: Adult")

names = avatars.available()
assert len(names) >= 6, f"only {len(names)} avatars installed: {names}"
assert avatars.FALLBACK in names, f"no {avatars.FALLBACK} to fall back to"
print("avatars:", " ".join(names))
print("PASS  the shared library works as installed")
