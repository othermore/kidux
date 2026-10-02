#!/usr/bin/python3
"""The website builds, and says the same in every language.

    tests/project/site.py

The site is built into a scratch directory as ci/build-site.py builds it
(docs/dev/website.md). Every language must have the words the page asks
for and no others, so that a sentence added in one is missing nowhere and
one dropped from the page is not left behind; every picture, style and
link a page names must be there; each page must lead to the others, to the
contact address and to where a donation is made; and the steps to install
it sends a visitor to must be a section of the user guide in its language.
Given the package archive's tarball, it must unpack it under apt/.
"""

import io
import importlib.util
import re
import sys
import tarfile
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("build_site", REPO / "ci" / "build-site.py")
site = importlib.util.module_from_spec(spec)
spec.loader.exec_module(site)

failed = 0


def anchor(heading: str) -> str:
    """A heading's address in a Markdown file, as GitHub writes it."""
    kept = "".join(c for c in heading.lower() if c.isalnum() or c in " -")
    return kept.replace(" ", "-")


def check(name: str, passed: bool, detail: str = "") -> None:
    global failed
    print(("PASS  " if passed else "FAIL  ") + name)
    if not passed:
        failed += 1
        if detail:
            print("      " + detail)


with tempfile.TemporaryDirectory() as scratch:
    out = Path(scratch) / "site"
    try:
        built = site.build(out)
    except SystemExit as stopped:
        check("the website builds", False, str(stopped))
        sys.exit(1)
    check("the website builds", True)

    facts, words, pages = built["site"], built["words"], built["pages"]
    default = facts["site.default_language"]
    template = (REPO / "site" / "page.html").read_text(encoding="utf-8")
    asked = set(site.KEY.findall(template)) | set(re.findall(r"\{\{#if ([a-z0-9_.]+)\}\}", template))
    # What the page asks for that is a word: not a fact, and not what the
    # builder writes itself.
    own = {"lang", "root", "page_url", "alternates", "language_links", "language_script"}
    wanted = {key for key in asked if not key.startswith("site.") and key not in own} | {"language.name"}

    for language, table in words.items():
        missing = sorted(wanted - set(table))
        unused = sorted(set(table) - wanted)
        check(f"{language}: every word the page asks for, and no other",
              not missing and not unused,
              f"missing {missing}; not on the page {unused}")
    for language, table in words.items():
        guide = REPO / "docs" / language / "user-guide.md"
        headings = {anchor(line.lstrip("#").strip())
                    for line in guide.read_text(encoding="utf-8").splitlines()
                    if line.startswith("#")} if guide.is_file() else set()
        check(f"{language}: the steps to install it sends to are a section of the user guide",
              table.get("get.debian.anchor") in headings,
              f"{table.get('get.debian.anchor')!r} in {guide}")
    check("every fact the page asks for is in site.toml",
          all(key in facts for key in asked if key.startswith("site.")),
          str(sorted(key for key in asked if key.startswith("site.") and key not in facts)))

    for language, page in pages.items():
        text = page.read_text(encoding="utf-8")
        check(f"{language}: the page is whole, in its language",
              "{{" not in text and f'<html lang="{language}">' in text, str(page))
        named = re.findall(r'(?:src|href)="([^"#:]+?)(?:#[^"]*)?"', text)
        absent = sorted({name for name in named
                         if not ((page.parent / name).resolve().exists())})
        check(f"{language}: every picture, style and page it names is there", not absent,
              ", ".join(absent))
        others = [code for code in words if code != language]
        check(f"{language}: it leads to every other language",
              all(f'data-language="{code}"' in text and f'hreflang="{code}"' in text
                  for code in others), str(others))
        check(f"{language}: it says where to write and where to give",
              f'mailto:{facts["site.email"]}' in text
              and text.count(f'href="{facts["site.sponsors"]}"') >= 3, facts["site.email"])
    check("the default language's page is the site's root, and sends a first visit on",
          pages[default] == out / "index.html" and "kidux-language" in pages[default].read_text())

    styles = (out / "style.css").read_text(encoding="utf-8")
    absent = [name for name in re.findall(r'url\("((?!data:)[^"]+)"\)', styles)
              if not (out / name).exists()]
    check("the style's fonts are there", not absent, ", ".join(absent))

    # The package archive, published with the site.
    packed = Path(scratch) / "kidux-apt.tar"
    with tarfile.open(packed, "w") as tar:
        member = tarfile.TarInfo("./dists/stable/InRelease")
        member.size = 6
        tar.addfile(member, io.BytesIO(b"signed"))
    site.build(Path(scratch) / "with-archive", packed)
    check("given the package archive, it is unpacked under apt/",
          (Path(scratch) / "with-archive" / "apt" / "dists" / "stable" / "InRelease").read_bytes()
          == b"signed" and (Path(scratch) / "with-archive" / "index.html").is_file())

    # The same page with an image to download: the other half of what it says.
    template_facts = dict(facts, **{"site.download": "https://example.org/kidux.iso"})
    for language, table in words.items():
        try:
            page, _ = site.render(template, {**template_facts, **table, "lang": language, "root": "",
                                              "page_url": ""}, site.markup(facts, words, language))
            whole = "https://example.org/kidux.iso" in page and "{{" not in page
        except KeyError as missing:
            whole, page = False, f"lacks {missing.args[0]}"
        check(f"{language}: with an image to download, the page offers it", whole)

sys.exit(failed)
