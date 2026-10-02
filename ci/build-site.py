#!/usr/bin/python3
"""Builds Kidux's website into build/site/ (docs/dev/website.md).

    ci/build-site.py [<output directory>]

The site is one page in every language: `site/page.html` filled with the
words of `site/<language>.toml` and the facts of `site/site.toml`. The
default language's page is the site's root, every other in a folder of
its name. Adding a language is adding its file of words.

A `{{ key }}` in the page is a word or a fact, written safe for HTML;
`{{#if key}} … {{#else}} … {{/if}}` keeps one part or the other by whether
a fact is set. The pictures a page names, `images/<language>/<name>.png`,
are copied from `docs/images/<language>/`, the battery's own, and the
brand's from `branding/`, so the site shows the screens as they are and
holds no copy of its own.

A word the page asks for and a language lacks, or a picture that is not
there, stops the build.
"""

import html
import re
import shutil
import sys
import tomllib
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SITE = REPO / "site"
PICTURES = REPO / "docs" / "images"
BRAND = REPO / "branding"

KEY = re.compile(r"\{\{\s*([a-z0-9_.]+)\s*\}\}")
CHOICE = re.compile(r"\{\{#if ([a-z0-9_.]+)\}\}\n?(.*?)\{\{#else\}\}\n?(.*?)\{\{/if\}\}\n?", re.DOTALL)


def flatten(table: dict, prefix: str = "") -> dict[str, str]:
    """A table of tables as one of dotted keys."""
    flat = {}
    for key, value in table.items():
        if isinstance(value, dict):
            flat.update(flatten(value, f"{prefix}{key}."))
        else:
            flat[f"{prefix}{key}"] = str(value)
    return flat


def facts() -> dict[str, str]:
    return flatten(tomllib.loads((SITE / "site.toml").read_text(encoding="utf-8")), "site.")


def languages() -> dict[str, dict[str, str]]:
    """Every language's words, by its code."""
    return {path.stem: flatten(tomllib.loads(path.read_text(encoding="utf-8")))
            for path in sorted(SITE.glob("[a-z][a-z].toml"))}


def address(site: dict[str, str], language: str) -> str:
    """A language's page, from the site's root."""
    return "" if language == site["site.default_language"] else f"{language}/"


def markup(site: dict[str, str], words: dict[str, dict[str, str]], language: str) -> dict[str, str]:
    """What the page takes as HTML, not as words: the links to the other
    languages, and what sends a first visit to the visitor's own."""
    default = site["site.default_language"]
    root = "" if language == default else "../"
    alternates = "\n".join(
        f'<link rel="alternate" hreflang="{code}" href="{html.escape(site["site.url"] + address(site, code))}">'
        for code in words)
    links = " ".join(
        f'<a href="{root}{address(site, code) or "./"}" lang="{code}" hreflang="{code}" '
        f'data-language="{code}">{html.escape(words[code]["language.name"])}</a>'
        for code in words if code != language)
    script = ""
    if language == default:
        others = ", ".join(f'"{code}"' for code in words if code != default)
        script = ("<script>\n"
                  "// A first visit goes to the visitor's language, when the site has it.\n"
                  "(function () {\n"
                  "  try {\n"
                  f"    var others = [{others}], chosen = localStorage.getItem(\"kidux-language\");\n"
                  "    var own = (navigator.language || \"\").slice(0, 2).toLowerCase();\n"
                  "    if (!chosen && others.indexOf(own) >= 0) {\n"
                  "      localStorage.setItem(\"kidux-language\", own);\n"
                  "      location.replace(own + \"/\" + location.hash);\n"
                  "    }\n"
                  "  } catch (error) {}\n"
                  "})();\n"
                  "</script>")
    return {"alternates": alternates, "language_links": links, "language_script": script}


def render(template: str, values: dict[str, str], raw: dict[str, str]) -> tuple[str, set[str]]:
    """The page with its words: (the HTML, the keys it asked for)."""
    asked: set[str] = set()

    def choose(match: re.Match) -> str:
        asked.add(match.group(1))
        return match.group(2) if values.get(match.group(1)) else match.group(3)

    def fill(match: re.Match) -> str:
        key = match.group(1)
        asked.add(key)
        if key in raw:
            return raw[key]
        if key not in values:
            raise KeyError(key)
        return html.escape(values[key], quote=True)

    return KEY.sub(fill, CHOICE.sub(choose, template)), asked


def build(out: Path) -> dict:
    """Build the site into `out`: what was built, for the checks."""
    site = facts()
    words = languages()
    default = site["site.default_language"]
    if default not in words:
        raise SystemExit(f"no words for the default language: site/{default}.toml")
    template = (SITE / "page.html").read_text(encoding="utf-8")
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)

    pages, asked, text = {}, {}, ""
    for language, own in words.items():
        root = "" if language == default else "../"
        values = {**site, **own, "lang": language, "root": root,
                  "page_url": site["site.url"] + address(site, language)}
        try:
            page, asked[language] = render(template, values, markup(site, words, language))
        except KeyError as missing:
            raise SystemExit(f"site/{language}.toml lacks {missing.args[0]}") from None
        target = out / address(site, language) / "index.html"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(page, encoding="utf-8")
        pages[language] = target
        text += page

        for name in sorted(set(re.findall(rf"images/{language}/([a-z0-9-]+\.png)", page))):
            source = PICTURES / language / name
            if not source.is_file():
                raise SystemExit(f"the page shows {name}, and docs/images/{language}/ has none")
            (out / "images" / language).mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, out / "images" / language / name)

    style = (SITE / "style.css").read_text(encoding="utf-8")
    (out / "style.css").write_text(style, encoding="utf-8")
    shutil.copytree(SITE / "fonts", out / "fonts")
    (out / "brand").mkdir()
    for name in sorted(set(re.findall(r"brand/([a-z0-9.-]+\.(?:svg|png))", text + style))):
        source = BRAND / ("svg" if name.endswith(".svg") else "png") / name
        if not source.is_file():
            raise SystemExit(f"the page shows {name}, and branding/ has none")
        shutil.copyfile(source, out / "brand" / name)
    # GitHub Pages: the files as they are.
    (out / ".nojekyll").write_text("")
    return {"site": site, "words": words, "asked": asked, "pages": pages}


def main(arguments: list[str]) -> int:
    out = Path(arguments[1]) if len(arguments) > 1 else REPO / "build" / "site"
    built = build(out.resolve())
    for language, page in built["pages"].items():
        print(f"{language}: {page}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
