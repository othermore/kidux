"""Translation, set up by the act of importing this module.

Importing this installs the catalogue and gives you `_`. That is deliberate:
if setting up translation were a call someone had to remember, someone would
one day forget, and a Spanish-speaking six-year-old would meet an English
screen. Getting it wrong has to be harder than getting it right.

    from kidux.i18n import _
    label = _("Adult")

Kidux has one gettext domain for every program it ships, so a word is
translated once and reads the same on the sign-in screen, the lock screen, the
launcher and the adult panel.

A screen does not choose its language here. The trusted screens use the default
in config.toml; a child's session uses the language on that child's profile,
set by LANG before the program starts. This module only makes whatever the
environment asked for actually work.
"""

import gettext as _gettext
import os
from pathlib import Path

from . import paths


def _install() -> _gettext.NullTranslations:
    """Find the catalogue for the current locale, or fall back to English.

    English is the source language and has no catalogue: an untranslated string
    is already English, which is why `NullTranslations` is a correct fallback
    rather than a failure. Any other language missing its catalogue is a
    packaging bug, and showing English is still better than crashing on a
    screen a child is sitting in front of.
    """
    localedir = Path(os.environ.get("KIDUX_LOCALE_ROOT", paths.LOCALE_ROOT))
    return _gettext.translation(
        paths.GETTEXT_DOMAIN,
        localedir=str(localedir),
        fallback=True,
    )


_translation = _install()

#: Translate one string.
_ = _translation.gettext

#: Translate a string that has a singular and a plural form. Needed because
#: "1 minute left" and "5 minutes left" are not the same sentence in every
#: language, and time is the thing Kidux talks to children about most.
ngettext = _translation.ngettext

#: Translate a string that needs a context to disambiguate it. "Lock" the verb
#: on a button and "Lock" the noun in a sentence are one word in English and
#: two in Spanish.
pgettext = _translation.pgettext


def translations(language: str) -> _gettext.NullTranslations:
    """The catalogue for one language, whatever this process started in.

    For the one screen that changes language while it runs: the sign-in
    screen, which switches to a child's language the moment their picture is
    tapped, so two siblings with different languages each meet their own.
    Everything else uses `_`, fixed when the program starts.

    `language` is a locale name such as "es_ES.UTF-8"; an unknown one gives
    English, the source language, rather than an error. The result has
    `gettext`, `ngettext` and `pgettext`, like the module's own.
    """
    localedir = Path(os.environ.get("KIDUX_LOCALE_ROOT", paths.LOCALE_ROOT))
    return _gettext.translation(
        paths.GETTEXT_DOMAIN,
        localedir=str(localedir),
        languages=[language or "C"],
        fallback=True,
    )


def N_(message: str) -> str:
    """Mark a string for translation without translating it yet.

    For strings defined at import time, before anything knows which language
    the screen will be in: a table of module names, the vocabulary in
    `kidux.vocabulary`. `xgettext` sees the string here; `_()` translates it
    where it is finally shown.
    """
    return message


def reload_for_testing() -> None:
    """Pick up a different locale or catalogue directory after import.

    Only the tests need this. A running program's language is fixed before it
    starts and never changes underneath it, because a child's session is
    started in their language by greetd.
    """
    global _translation, _, ngettext, pgettext
    _translation = _install()
    _ = _translation.gettext
    ngettext = _translation.ngettext
    pgettext = _translation.pgettext
