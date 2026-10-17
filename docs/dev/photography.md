# Photography

`kidux-module-photography` is a guide to taking photographs with a real
camera, for a child of eight to twelve who reads well: thirty chapters,
from the dark box with a hole that every camera still is to the shutter,
the aperture and ISO, the camera's modes and working in manual, focus,
composition and light, each with something to try on the camera the same
day. The camera the guide is written with is the Olympus XZ-2, and every
box about it says that other cameras have the same under other names. It
is a web page served by `kidux-webapps`, in the child's language, and it
needs nothing from the internet. Everything in it is Kidux's own but the
photographs, which are free ones by other people, credited where they are
shown (section 5). This document is how it is made.

## 1. What it is made of

```
packages/kidux-module-photography/
  module.toml, icon.svg   the manifest and the tile's picture
  webapp/index.html.in    the page, with @PAGES@ where the languages go
  webapp/page.py          writes index.html at build time (section 2)
  webapp/style.css        the page, in the brand's colours
  webapp/guide.js         a chapter at a time: Back, Next, Chapters
  content/<lang>/NN-slug.md   the guide's chapters, English the source
  drawings/               the guide's drawings, shared by every language
  pictures/               the photographs, their credits, and the two
                          tools that make them (section 5)
  po/                     the page's words
  tests/                  section 7
```

On the machine the page, its script, its style and its photographs are
under `/usr/share/kidux/webapps/photography/`, served under
`/photography/` like every web module's (modules.md, section 4). The
drawings are inside the page.

## 2. The page

`page.py` runs when the package is built. It reads every language's
chapters with `python3-markdown`, translates the page's words through the
module's catalogue, and writes both, as one JSON object per language, into
`index.html` in place of `@PAGES@`. The page picks the language its
address names, `?lang=es`, or English. `guide.js` shows one chapter at a
time, numbered as its file is, with **Back**, **Next** and the list of
**Chapters**, and the keyboard's focus on *Next*, or on *Chapters* where
there is no next.

A photograph is an `<img>` with its width and height written in, read from
the JPEG at build time, so that one loaded only when it comes into view
keeps its room until then.

## 3. The guide

The guide is made like BASIC's (basic.md, section 4): one idea per
chapter, tried at once, a mascot who speaks in speech bubbles, *Keep
trying* exercises, and a box for the adult. The mascot is Kidux's penguin
chick (branding/README.md), the same drawings as BASIC's. A chapter is a
Markdown file, `content/en/NN-slug.md`, its first line its heading, and
its translation `content/es/NN-slug.md` with the English file's hash in
its front matter, which `tests/project/content.py` checks and `--update`
writes. Seven conventions, and no others:

- **A quotation** is the mascot speaking: the chick beside a speech
  bubble, in the pose its first word names, `[think]`, `[point]`,
  `[cheer]` or `[oops]`, or standing.
- **`::: try`** to **`:::`** is *Try it*: what the child does with the
  camera now, as an ordered list of short steps.
- **`::: camera`** to **`:::`** is the camera box, headed *On the Olympus
  XZ-2*, whose first line, the same in every box, says that other cameras
  have the same thing under other names and that chapter 3 says how to
  find it. Then which button, which dial, which menu, with the manual's
  page in brackets for the adult, `(manual, p. 16)`. A chapter with
  nothing to set says so in its box.
- **`::: adult`** to **`:::`** is the box for the adult, shut until it is
  opened: what the chapter teaches, what to help with, what to watch for.
- **`::: compare`** to **`:::`** holds two to four pictures, photographs
  or drawings, side by side, each with its words under it.
- **A drawing**, `![words](name.svg)`, from `drawings/`, put into the
  page as it is, its words read to those who cannot see it.
- **A photograph**, `![caption](name.jpg)`, from `pictures/`, a figure
  with its caption under it and, in smaller letters, its credit from
  `pictures/pictures.toml`, *Photo: <author>, <licence>*. With the title
  `"thirds"`, `![caption](name.jpg "thirds")`, the rule of thirds' grid
  is drawn over it in CSS, so that the same photograph is shown with and
  without it.

The guide gives the real numbers, 1/1000, F1.8, ISO 6400, and the real
reasons, in short sentences and the child's world: toys, a fountain, a
torch in a dark room, a friend against the window. Every camera box is
written from the XZ-2's manual (Olympus, 2012) and names its pages; the
manual itself is read, never copied, neither its text nor its pictures.
The Spanish boxes give the camera's menus in Spanish words of the guide's
own, since the manual the guide is written from is the English one.

## 4. The chapters

| Part | Chapters |
|---|---|
| Light and the camera, 1–4 | A box with a hole; why a lens; what a camera is made of; hold it still |
| Exposure, 5–15 | Too dark, too bright; the shutter; the aperture; ISO; the three together; how the camera measures light; the modes; working in manual; long exposures; painting with light; the flash |
| Focus and depth, 16–20 | Where the camera looks: the focus points; the focus modes; depth of field; macro; zoom and perspective |
| Making a picture, 21–27 | The rule of thirds; lines, frames and patterns; backgrounds; point of view; light's time and side; colour, and black and white; people and moments |
| After the click, 28–30 | Looking at your photographs; choosing, and telling a story; the words of photography |

Chapter 12, working in manual, is the course's centre: in light that holds
still, a measurement taken once and the dials left alone make every
picture alike, which no automatic mode does. Chapter 30 is the glossary,
each word with the chapter that teaches it, alphabetical in each language
on its own.

**Adding a chapter.** Write `content/en/NN-slug.md`, the next number; read
its camera box against the manual's pages; draw or find its pictures
(section 5); translate it to `content/es/NN-slug.md`, the same name; run
`tests/project/content.py --update`.

## 5. The pictures

Three kinds, decided once (D102):

- **Drawings**, SVG in `drawings/`, drawn for Kidux, flat, in the brand's
  colours, with no words in them, so that every language shares them.
  The one exception is a drawing of the camera's screen, `screen-*.svg`,
  which shows the camera's own glyphs and numbers, `P`, `125`, `F5.6`,
  `ISO 200`, the same in every language, drawn afresh after the manual's
  pictures and never traced from them. Each drawing says in a comment at
  its top what it shows and which chapter uses it.
- **Photographs**, JPEG in `pictures/`, each showing a chapter's effect.
  Every one of the first release is a free one from Wikimedia Commons,
  under CC0, CC BY, CC BY-SA or in the public domain, its licence, author
  and that it shows what the chapter says checked on its page when it is
  downloaded. None shows a child's face.
- **Generated pictures**, only where neither a photograph of the owner's
  nor a free one shows the effect, since a picture that did not come
  through a lens may lie in its details. The first release has none.

`pictures/pictures.toml` has one table per photograph, by its file's
name: `author`, `source` (the file's page on Commons), `licence`, and
`made` when the photograph is not the file as it is: cropped, or one half
of a comparison, or given more or less light. `debian/copyright` names
every photograph with its author, licence and source, and holds the
licences' texts. A generated picture would say `author = "generated"`,
its model, and its prompt's file in `pictures/prompts/`, under the
project's licence, credited *Picture made by a computer*.

Two development-time tools, run by hand and never installed, make the
files; they need `python3-pil`, which only the development machine has.

- `pictures/prepare.py <source> <name>` writes `pictures/<name>.jpg`: the
  source, cropped with `--crop`, no longer than 1400 pixels on its long
  side, a JPEG with no metadata at all and under 400 kB. Where a chapter
  needs one scene with a single thing changed and no free pair exists,
  one photograph is changed as the camera would change it, in linear
  light: `--stops N` gives it N stops more light, or fewer; `--light
  R,G,B` multiplies each colour's light, as a white balance does;
  `--grey` makes it grey from all its colours, and `--red-filter` from
  its red light alone, as a red filter does to black and white. The
  credit's `made` says which.
- `KIDUX_GEMINI_KEY_FILE=<file> pictures/generate.py <name>` asks
  Gemini's image model for a picture from `pictures/prompts/<name>.txt`
  and writes it through `prepare.py`. The key is read from the file the
  variable names, kept outside the repository, and goes only into the
  request's header. The owner looks at every generated picture before it
  is committed and refuses one whose physics is wrong.

The sources downloaded and generated are kept under `build/pictures-src/`,
outside the repository. A photograph of the owner's replaces a free one
the same way: its source under `build/photos/`, `prepare.py`, and its
entry's `source = "owner"`, credited *Photo: Kidux*.

## 6. Its words

The page's words, its buttons, the boxes' headings, the camera box's first
line, the credits' *Photo:*, are `N_()` strings in `page.py`'s `WORDS`,
extracted by `ci/i18n-extract.sh` into `po/kidux-module-photography.pot`
and translated in `po/es.po`. The camera's name is not translated. The
guide's own text is its chapters. A new language is a catalogue and a
directory of chapters, and no change to the code.

## 7. Tests

- `tests/test_guide.py`: every language has the same chapters; the page
  holds every language's words and chapters; the seven conventions render
  and none of their marks reaches the page; every drawing and photograph
  a chapter names is there; every photograph shown is credited and every
  credit is of a photograph shown; every photograph is small and has no
  metadata; every photograph not Kidux's is in `debian/copyright`; every
  chapter has its box for the adult, and every camera box names the
  manual's page; a comparison holds two to four pictures.
- `tests/test_module.py`: the manifest, the version, the catalogue.
- Acceptance `21-module-photography.sh` and session
  `37-module-photography.py`, which installs it through the daemon, opens
  it by keyboard, changes the page with *Next*, and takes its picture for
  the user guide.
