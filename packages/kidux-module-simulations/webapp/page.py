#!/usr/bin/python3
"""Makes the page of kidux-module-simulations, when the package is built.

    python3 webapp/page.py <locale dir> <sims.toml> <template> <page>

The page lists PhET's simulations by group, in the order sims.toml gives
them, each group with its ages, and opens one in a frame under a bar with
the way back to the list (phase-4e-plan.md, 4.30). It is shown in the
language its address names, `?lang=es`, or in English: every language's
words and every simulation's titles are written into it here, so that it
needs nothing but itself and the simulations' files beside it. Its words
are translated through the module's own catalogue, compiled into
<locale dir>/<lang>/LC_MESSAGES/kidux-module-simulations.mo; the
simulations' titles are PhET's own, from sims.toml.
"""

import gettext
import json
import sys
import tomllib
from pathlib import Path


def N_(message: str) -> str:
    return message


DOMAIN = "kidux-module-simulations"
WORDS = {
    "title": N_("Simulations"),
    # The bar's button over an open simulation, back to the list.
    "back": N_("Simulations"),
    # A group's ages; {low} and {high} are numbers.
    "ages": N_("Ages {low} to {high}"),
    "attribution": N_("Simulations by PhET Interactive Simulations, University of Colorado "
                      "Boulder, licensed under CC BY 4.0 (https://phet.colorado.edu)"),
}
#: The groups' names, by the id sims.toml gives each.
GROUPS = {
    "numbers": N_("Numbers and shapes"),
    "more-numbers": N_("More numbers"),
    "forces": N_("Forces and energy"),
    "light": N_("Light, sound and waves"),
    "electricity": N_("Electricity and magnets"),
    "matter": N_("Matter and atoms"),
    "earth": N_("Earth, space and life"),
}


def languages(locale: Path) -> list[str]:
    """English, and every language the module has a catalogue for."""
    found = sorted(d.name for d in locale.iterdir() if (d / "LC_MESSAGES").is_dir())
    return ["en"] + [lang for lang in found if lang != "en"]


def pages(locale: Path, listed: dict) -> dict:
    """Every language's words and groups, the simulations' titles in it."""
    found = {}
    for lang in languages(locale):
        translations = gettext.translation(DOMAIN, str(locale), languages=[lang], fallback=True)
        groups = []
        for group in listed["groups"]:
            low, high = (int(age) for age in group["ages"].split("-"))
            groups.append({
                "name": translations.gettext(GROUPS[group["id"]]),
                "ages": translations.gettext(WORDS["ages"]).format(low=low, high=high),
                "sims": [{"id": sim,
                          "title": listed["sims"][sim]["title"].get(
                              lang, listed["sims"][sim]["title"]["en"])}
                         for sim in group["sims"]],
            })
        found[lang] = {"words": {key: translations.gettext(text) for key, text in WORDS.items()},
                       "groups": groups}
    return found


def main(args: list[str]) -> int:
    locale, listing, template, output = map(Path, args[1:5])
    with listing.open("rb") as file:
        listed = tomllib.load(file)
    text = template.read_text(encoding="utf-8")
    data = json.dumps(pages(locale, listed), ensure_ascii=False, sort_keys=True)
    output.write_text(text.replace("@PAGES@", data.replace("</", "<\\/")), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
