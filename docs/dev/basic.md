# BASIC

`kidux-module-basic` is the home computer of the eighties for a child of
eight to fourteen: a BASIC interpreter on the left of one window, with an
editor, its buttons and its screen, and a guide to it on the right, in the
child's language (D84). The interpreter is Google's wwwBASIC; everything
around it, the editor, the page and the guide, is Kidux's own. This
document is how it works, what the interpreter does and does not do, and
how the guide is written.

## 1. What it is made of

```
packages/kidux-module-basic/
  upstream.toml           wwwBASIC: its repository, commit, version and sums
  module.toml, icon.svg   the manifest and the tile's picture
  webapp/index.html.in    the page, with @PAGES@ where the languages go
  webapp/page.py          writes index.html at build time (section 4)
  webapp/style.css        both halves, in the brand's colours
  webapp/machine.js       the editor, its buttons, the screen, sound
  webapp/guide.js         the guide: a chapter at a time, Back, Next, Chapters
  webapp/check.js         what the page says about a program before and
                          after a run; read by the page and by the tests
  webapp/runner.html, runner.js   one run of a program (section 3)
  content/<lang>/NN-slug.md       the guide's chapters, English the source
  drawings/               the guide's drawings, shared by every language
  po/                     the page's words
  tests/                  section 6
```

On the machine the page and its scripts are under
`/usr/share/kidux/webapps/basic/`, served by `kidux-webapps` like every
web module's (modules.md, section 4), and wwwBASIC is under its
`wwwbasic/` with its licence and README.

## 2. wwwBASIC

wwwBASIC (`https://github.com/google/wwwbasic`, Apache-2.0, Google LLC) is
a BASIC in JavaScript in the manner of GW-BASIC and QBasic: it compiles a
whole program to JavaScript and runs it on a canvas, with the PC's text
mode, its graphics modes and its letters. It arrives as Kidux's other
upstream programs do (D68, D71): `upstream.toml` pins a commit,
`ci/upstream/wwwbasic.sh` fetches it through `ci/upstream/fetch.sh` and
packs `wwwbasic.js`, `wwwbasic.mjs`, `LICENSE`, `README.md` and its
`test/` into the tarball, with nothing to build. The page loads
`wwwbasic.mjs`, a JavaScript module, and the tests load the same file
under Node.js, so that what they try is what the page runs.

What Kidux needs of wwwBASIC is met first through its bindings, the
object of functions it calls to draw, print, read a key or make a sound.
What a binding cannot do, a small fix to wwwBASIC can (D88): each is a
patch in the package's `patches/`, applied by `debian/rules` to a copy
of `wwwbasic.mjs` in `build/wwwbasic/`, which the tests try and the
package installs, while the tarball stays wwwBASIC's own. The patched
file says at its top that Kidux changed it, as its licence asks. The
fixes, `patches/sleep-and-timer.patch`:

- `SLEEP n` waits n thousandths of a second. `wwwbasic.mjs` read `SLEEP`
  itself as its number and stopped every program that used it; the fix
  is the line `wwwbasic.js` already has.
- `TIMER` is the seconds since midnight, as on the PC. wwwBASIC counted
  them from 1970, a number too long for a variable, which keeps about
  seven figures, so `T = TIMER` lost the seconds.

Anything bigger, a statement wwwBASIC lacks, is not added: the guide is
written for what the machine does. What it had to be written around:

- **The program is read whole before it runs.** A mistake on any line
  stops the run before the first line prints; the guide's chapter 2 shows
  it on purpose.
- **Lines run in the editor's order.** The numbers at the start of the
  lines are names that `GOTO`, `GOSUB`, `THEN` and `RESTORE` jump to, not
  an order: a line typed out of order runs where it is. The guide numbers
  lines 10 by 10 and types them in order. A jump to a number no line has
  is not an error for wwwBASIC, so the page checks for it first
  (section 3).
- **Its errors.** A line it cannot read is reported as `… at line N`, N
  counted in the editor's lines, which the page turns into the line's
  BASIC number. What goes wrong while a program runs names the program's
  last line, so the page names no line then. `RETURN` without `GOSUB` and
  `NEXT` without `FOR` end in JavaScript's own errors, which the page
  explains as one of the two. A closing quote missing at the end of a line
  is no mistake to it; an opening one is.
- **Its letters are the PC's.** The screen draws a character by its place
  in the PC's table (code page 437), so the page hands the program over
  with each Spanish letter at its place there, and Á, Í, Ó and Ú, which
  the table has not, without their accent. wwwBASIC draws that table with
  the browser's monospace face at a size too small for accents and
  tildes: á shows as a, and ñ as n, while ü, ¿ and ¡ show whole. So the
  guide writes without accents, as the home computers did, and chapter 1
  tells the adult why.
- **Its numbers.** A variable is single precision, as in the BASICs of
  the time: it keeps about seven figures, while a calculation printed
  directly keeps about sixteen; chapter 17 says so. Numbers from 10^21 up
  are written short, `1e+21`. `VAL` of a string that is not a number is
  `NaN`, not 0, so the guide never asks for it.
- **What the guide leaves out.** `TAB(n)` writes n marks instead of moving
  along the line, so the guide uses `SPACE$(n)`; a backslash in a string
  is lost; `PLAY` and `BEEP` make no sound, so the guide's sounds are
  `SOUND`; `SCREEN 13`'s colours are wrong, so the guide draws in
  `SCREEN 12`. Numbers printed after `;` have no spaces around them, so
  the guide puts them in the strings.

## 3. The page

The left half, the machine, is the editor, a row of buttons and the
screen; the right half is the guide. Under 1000 pixels of width they
stack, the machine first.

- **The editor** is a text area with a margin that numbers its lines 1, 2,
  3, which the page's messages name when a line has no BASIC number. Its
  text is kept in the module's browser storage, `kidux-basic-program`,
  after every change, and comes back when the module opens: closing it
  loses nothing. Tab writes two spaces; Escape, then Tab, leaves the
  editor, so that the keyboard alone reaches the buttons and the guide.
  Ctrl+Enter runs the program.
- **Run** first looks for a jump to a line that is not there and, finding
  one, says so and marks it. Otherwise it starts a run: a frame of its
  own, `runner.html`, where `runner.js` gives wwwBASIC its graphics
  bindings in 40 columns and hands it the program; the frame takes the
  keyboard, so `INPUT` and `INKEY$` read what the child types. The frame
  tells the page what happens by messages: the run ended, an error, a
  sound, Escape (stop) and Ctrl+Enter (run again).
- **Stop**, or Escape, takes the frame away, which ends everything the run
  was doing whatever it was doing, and leaves a picture of its screen in
  its place. A new run starts in a new frame, so nothing of the last one
  is left over.
- **Sound** is played by the page, not by the frame: `SOUND frequency,
  duration` is passed up, and the page plays it as a square wave, one
  tone after another. Chromium lets a page make a sound only after a
  click or a key, and *Run* is one.
- **Errors** are said under the screen in the child's words, with
  wwwBASIC's own text after them in brackets, and the editor marks the
  line when one is known.
- **New** empties the editor after asking; **Save** downloads the program
  as `program.bas`, named in the child's language, which Chromium's file
  dialog asks where to keep, in the child's Downloads (D76); **Open**
  opens the same dialog on `.bas` files. The guide's *Type it in for me*
  puts a listing in the editor, asking first when the editor holds the
  child's own work.
- **Type it in for me is an adult's setting** for each child (D90): the
  manifest declares `type_in`, a switch, on by default, which the panel
  shows in BASIC's *Settings*. Off, `kidux-webapp` opens the page with
  `type_in=0` in its address, and the page puts `no-type-in` on its root,
  which hides every *Type it in for me* and every passage of the guide
  marked `::: type-in`.

The guide shows one chapter at a time with *Back*, *Next* and
*Chapters*, and remembers the chapter it was on, `kidux-basic-chapter`.
Storage may be refused; the page works without it.

## 4. The guide

The guide's model is the pair of books *BASIC para niños* (1984) and
*BASIC avanzado para niños* (1987) by Sofía Watt and Miguel Mangada,
Paraninfo. What is taken from them is their method and the order of
their ideas, and nothing else: one idea per chapter, each tried at once
on the machine, a mascot who talks in speech bubbles, *keep trying*
exercises, a box of notes for the adult, games at the end. No sentence,
story, program, character or picture of theirs is in the guide. Every
text, listing and drawing is written and drawn for Kidux, for this
machine, under the project's licence; the mascot is Kidux's penguin
chick (branding/README.md).

A chapter is a Markdown file, `content/en/NN-slug.md`, its first line its
heading, and its translation `content/es/NN-slug.md` with the English
file's hash in its front matter, which `tests/project/content.py` checks
and `--update` writes. `page.py` reads every language's chapters at build
time with `python3-markdown` and writes them, with the page's words from
the module's catalogue, into `index.html`. Five conventions, and no
others:

- **A listing** is a fenced block marked `basic`. It is shown as the
  screen prints it, with *Type it in for me* under it. After `basic`,
  `keys=` names the keys the tests type when it reads, separated by
  commas, `Enter` for the Enter key, `Space` and `Comma` for a space and
  a comma, and `Up`, `Down`, `Left` and `Right` for the arrows (`basic
  keys=Leo,Comma,9,Enter`), `forever` says it never ends by itself, and
  `mistake` that it is wrong on purpose, which the tests hold to stopping
  BASIC before it prints anything; none of them is shown. They are kept
  out of the listing because the listing is what the child types.
- **A quotation** is the mascot speaking: the chick beside a speech
  bubble, in the pose its first word names, `[think]`, `[point]`,
  `[cheer]` or `[oops]`, or standing.
- **`::: adult`** to **`:::`** is the box for the adult, closed until it
  is opened.
- **`::: type-in`** to **`:::`** speaks of *Type it in for me*, and is
  not shown when an adult has switched it off for the child.
- **A picture**, `![words](name.svg)`, is a drawing from `drawings/`, put
  into the page as it is, its words read to those who cannot see it.
  Drawings are outside `content/` because every directory there is a
  language.

The drawings are SVG, flat and friendly, drawn like the avatars
(branding/README.md), with no words in them, so that every language
shares them.

The guide is written for children who read: short sentences, the child's
world (the penguin's friends, fish, snow, school) for its stories, and a
chapter's *keep trying* asking for changes to its own listings. Listings
are capital letters, numbered 10 by 10, `GOTO` and `GOSUB` as one word.
Spanish listings are in Spanish, without accents, keeping ü, ¿ and ¡,
which the screen shows; a word with ñ goes only in a string, where it
reads with n, and only when it still reads right that way (`MUNECO`, but
`EDAD` rather than `AÑOS`), never in a variable's name.

The chapters, one idea each, in the books' order:

| Part | Chapters |
|---|---|
| First, 1–15 | Hello; PRINT; LET; INPUT; GOTO; IF; FOR and NEXT; GOSUB and RETURN; READ and DATA; REM; INT; RND; flowcharts; games to make; saving your programs |
| Second, 16–30 | Inside the computer; the fifth operation, `^`; what the computer does first; CLS; INPUT, more; FOR and NEXT, more, with `SLEEP`; AND and OR; menus, `ON … GOTO` and `ELSE`; READ, DATA and RESTORE; DIM; putting things in order; strings and `INKEY$`; CHR$ and ASC; drawing, colour and sound; programs to keep |

**Adding a chapter.** Write `content/en/NN-slug.md`, the next number, and
each listing in it first in the editor, on the machine, until it does
what the chapter says; give a listing that reads its `keys=`, and one
that never ends `forever`. Draw what it needs in `drawings/`. Translate it
to `content/es/NN-slug.md`, the same name, and run
`tests/project/content.py --update`. The module's tests then run every
listing of both languages.

## 5. Its words

The page's words, its buttons, its messages, *Type it in for me*, *For
the adult*, are `N_()` strings in `page.py`'s `WORDS`, extracted by
`ci/i18n-extract.sh` into `po/kidux-module-basic.pot` and translated in
`po/es.po`. The guide's own text is its chapters. A new language is a
catalogue and a directory of chapters, and no change to the code.

## 6. Tests

- `tests/run-basic.js` runs a program under Node.js through wwwBASIC with
  bindings of its own, which keep what is printed as text, record what is
  drawn and sounded as lines, and type keys from a list. With a directory
  it runs every `NN-name.bas` there, typing `NN-name.in`, against
  `NN-name.out`; `tests/basic/` has one program for each statement the
  guide teaches. Each runs in a process of its own and is ended after a
  second and a half, so one that never ends harms nothing; there
  wwwBASIC's waits take no time and its clock runs a thousand times
  faster, so that `SLEEP` and `TIMER` cost the tests nothing.
- `tests/check-test.js`: what `check.js` says about a program: its lines'
  BASIC numbers, its jumps to no line, wwwBASIC's errors explained with
  the editor's line turned into a BASIC number, and the letters handed to
  the screen.
- `tests/test_guide.py`: the page holds every language's words and
  chapters, each numbered as its file is, the five conventions, every drawing named is there, the same
  chapters in every language, and every listing of the guide, in every
  language, runs through `run-basic.js` without an error and ends unless
  it is `forever`, or, marked `mistake`, stops BASIC before it prints.
- `tests/test_module.py`: the manifest, the version, the catalogue.
- Acceptance `09-module-basic.sh` and session `31-module-basic.py`, which
  types a program, runs it and takes the guide's picture.

The listings need wwwBASIC, which only the package build has under
`upstream/`; outside it, `WWWBASIC=<path to wwwbasic.mjs>` and `NODE` say
where it and Node.js are.
