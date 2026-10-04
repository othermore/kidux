# The website

Kidux's website is its shop window: one page that tells a parent, in a
minute, what Kidux is and why they want it, shows it, says what it costs
whom, and asks for a donation (D79). It is in English and Spanish, like
everything else, and published on GitHub Pages.

## 1. What it is made of

```
site/site.toml       the facts, the same in every language: the site's address,
                     the repository, where a donation is made, who answers
                     and where, and where an image is downloaded from
site/page.html       the page, once, with {{ key }} where a word or a fact goes
site/en.toml         the words, one file per language, the same keys in each
site/es.toml
site/style.css       the brand's colours and type (branding/README.md)
site/fonts/          Andika, as WOFF2, with its licence
ci/build-site.py     builds all of it into build/site/
tests/project/site.py   checks it, with every other project check
.github/workflows/site.yml   publishes it
.github/FUNDING.yml  the repository's own Sponsor button
```

`ci/build-site.py` writes the default language's page (`default_language`,
English) at the site's root and every other in a folder of its name
(`es/`), each linking to the others. A first visit to the root goes to the
visitor's own language when the site has it, and a language chosen by hand
is remembered in the browser. Its font is its own. It takes two things
from other servers: GitHub's Sponsor button, in the part of the page that
asks for a donation, fetched when that part comes into view; and, once the
visitor has said yes in the notice at the foot of the page, Google's tag,
which counts visits (section 5). It sets no cookie of its own.

**The words.** A sentence on the page is a key in every `site/<language>.toml`.
`tests/project/site.py` fails when a language lacks a word the page asks
for, or keeps one the page no longer uses, so the languages cannot drift
apart. A language is added by adding its file, with its own name under
`[language]`; nothing else changes. The words are short on purpose: the
page is read in a minute.

**The pictures.** The page names its pictures as `images/<language>/<name>.png`,
and the builder copies each from `docs/images/<language>/`, where the
battery puts the screens of its last run (`tests/lib/doc-screenshots.txt`).
The site holds no picture of its own, so it shows Kidux as it is, in each
language. The brand's pieces come from `branding/` the same way. A picture
the page names and the battery does not take stops the build. The two the
page opens with, a child's launcher with a tile for every module and two
modules in windows, are taken by `tests/session/30-every-module.py`, which
installs six of them, so that the picture stays clean: BASIC, Blockly
Games, CodeCombat, Scratch, Tux Typing and Wikipedia. The pictures are
written by a release run of the battery alone (D93), so the site shows
released screens.

**The font.** `site/fonts/Andika-*.woff2` are Debian's `fonts-sil-andika`
6.200 in the web's format and otherwise untouched, since the font's
licence reserves its name for unchanged copies:

```python
from fontTools.ttLib import TTFont        # with brotli
font = TTFont("/usr/share/fonts/truetype/andika/Andika-Regular.ttf")
font.flavor = "woff2"
font.save("site/fonts/Andika-Regular.woff2")
```

## 2. What it says

The page follows D78 to the letter. Kidux is free for families; a school
or any other organisation gets its licence free too, by writing for it,
which is how the owner learns where Kidux is used; and the code is
published, each version free software four years on. It never calls Kidux
open source or free software, which the licence is not.

It says only what is true of Kidux today, and of the two ways to install
it (D81) it says which is which. Kidux's own image is *coming soon*, with
what installing from it will be;
where the image is downloaded from is a fact, `download` in
`site/site.toml`, and once it is set to an address the same card says
*available today* and offers the download. Installing on Debian is
*available today*, and its button leads to the steps, section 2 of the
user guide in the page's language, by the heading's address in the words,
`get.debian.anchor`; `tests/project/site.py` fails if the guide has no
such section. The guide itself is a step away everywhere: *Guide* in the
page's header, *Read the guide* beside *Get Kidux* at the top, and, in
the part that shows the modules, each module's name leads to its own
section of the guide and a button to the modules' section, by headings'
addresses the words hold (`modules.anchor`, `modules.<id>.anchor`), every
one of which the same check holds to a heading of the guide in that
language; so a visitor sees how much there is and what each module does. Both states of the image's card are written, in every
language, and checked.

## 3. Building and looking at it

```
ci/build-site.py                 # into build/site/
python3 -m http.server 8080 --directory build/site
```

and `http://<this machine>:8080/` from any browser on the network. The
development machine's own Chromium opens nothing but Kidux's modules (its
policy, modules.md section 4), so the page is looked at from another
computer.

## 4. Publishing

`.github/workflows/site.yml` builds the site and publishes it on GitHub
Pages whenever `site/`, `docs/images/`, `branding/` or the builder changes
on `main`, and when run by hand. It does nothing while the repository has
no Pages site.

The package archive is published with it, under `apt/`: the workflow takes
the stable suite's tarball from the repository's `archive` release, where
`ci/publish-public.sh` sends it, and `ci/build-site.py --archive` unpacks
it beside the pages (packaging.md, "The public archive"). So
`https://kidux.org/apt` is the same site, and a site is never published
without it.

Turning Pages on, once, by the owner: the repository's *Settings*, *Pages*,
*Source: GitHub Actions*. GitHub publishes Pages from a private repository
only on a paid plan; from a public one, on any.

**The site's domain** is `kidux.org`: `url` in `site/site.toml`, and the
links in both READMEs. A Pages site published by a workflow takes its
domain from the repository's Pages settings, *Custom domain*, not from a
`CNAME` file. The domain's DNS has four `A` records for `kidux.org`, to
`185.199.108.153`, `185.199.109.153`, `185.199.110.153` and
`185.199.111.153`, and a `CNAME` for `www` to `othermore.github.io`;
GitHub then issues the certificate, and *Enforce HTTPS* is ticked. The
`github.io` address sends visitors on to the domain.

**Donations.** The page's *Donate* buttons and the repository's *Sponsor*
button (`.github/FUNDING.yml`) lead to the owner's GitHub Sponsors page,
`sponsors` in `site/site.toml`, and the part of the page that asks for a
donation shows GitHub's own button under ours, `sponsors_button`.

## 5. Visits

The site counts its visits twice, so that the owner can compare the two
and keep one (D94).

**Google Analytics**, in its consent mode. The measurement id is a fact,
`analytics` in `site/site.toml`; the reports are at
`analytics.google.com`, in the property the id belongs to, which the
owner's Google account holds. The page's own script loads Google's tag on
every visit, after telling it that its storage is denied: the visit is
counted without cookies. A notice, a card in the brand's night over the
page's corner, asks whether it may use cookies, to tell a new visit from
a returning one, with *Yes, with cookies* and *No, without cookies* weighing
the same: a yes grants the tag its storage, a no keeps it denied and
clears any `_ga` cookie a yes left. The answer is kept in the visitor's
browser (`kidux-cookies` in its local storage), for every language of the
site, and the footer's *Cookies* asks again; while the card shows, the
page leaves room for it under the footer. The tag is made by the script,
never written in the page as a `<script src>`.

**GoatCounter**, which uses no cookies: `goatcounter` in `site/site.toml`,
the address it counts at, `https://kidux.goatcounter.com/count`, with its
reports at `https://kidux.goatcounter.com`. Its script, `count.js`, loads
on every visit, and the footer says that visits are also counted with it.

`tests/project/site.py` checks both: Google's storage denied before the
tag counts and granted only on a yes, the card and its words in every
language, GoatCounter's script and the footer's line; and that with both
facts empty the page carries nothing of either and no card.
