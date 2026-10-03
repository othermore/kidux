# Phase 4b plan — doors to the web, BASIC with its guide, and the website's visits

Four pieces of work the owner asked for on 2026-10-03, built on phase 4
(phase-4-plan.md): Google Analytics on the website, behind a cookie notice;
a BASIC module, wwwBASIC with a guide for the child beside it; a module that is a
door to CodeCombat's website; and one that is a door to Wikipedia. The two
doors need one thing the framework does not have, a web module that
reaches one website on the internet and nothing else, so that is built
before them and the two modules are made of it.

The contract a module is written to is [modules.md](modules.md), and this
plan changes that document where it says so. Every decision here goes
into the decision log of architecture.md (D83 to D87) as the first thing
built; section 4 words them.

## 1. Where we start

Phase 4 is built: six modules a child uses, two test modules, the
upstream builds, the website at `https://kidux.org/` with the package
archive's stable suite under `/apt`, the user guide's installation on
Debian checked by doing it. The framework is as modules.md says: a module
is a program (`launch = { exec = … }`) or a web application served by
`kidux-webapps` on `127.0.0.1:8123` and opened by `kidux-webapp <id>` in
Chromium's application window (`launch = { webapp = … }`), one page that
`webapp/page.py` writes at build time with every language's words in it,
as `kidux-module-hello-web` does. Chromium is held by one managed policy
for the whole machine, `/etc/chromium/policies/managed/kidux.json`,
shipped as a conffile of `kidux-webapps`, whose `URLAllowlist` is the
local server, the Scratch Foundation's and TurboWarp's library hosts, and
`blob:`.

What is not there: a module whose pages are on the internet; a way to hold
one such module to its own site when the policy is the whole machine's; a
BASIC; any measure of the website's visits.

## 2. The steps

| Step | What | Size |
|---|---|---|
| 4.9 | The website counts its visits with Google Analytics, once the visitor says yes | S |
| 4.10 | `kidux-module-basic`: wwwBASIC in an editor of Kidux's own, the guide beside it, the guide's first part | L |
| 4.11 | The guide's second part: more BASIC, drawing, colour, sound, and the programs to make | M |
| 4.12 | A web module that is a door to one website: `hosts` in the manifest, the policy generated from the installed modules, Chromium walled by a proxy per launch | M |
| 4.13 | `kidux-module-codecombat`: a door to codecombat.com | S |
| 4.14 | `kidux-module-wikipedia`: a door to Wikipedia and the Wikimedia projects | S |
| 4.15 | Closing | S |

In this order. 4.9 touches nothing the others do; 4.10 and 4.11 touch only
their own package; 4.13 and 4.14 cannot start before 4.12.

## 3. Rules for every step

The rules of phase-4-plan.md section 3 apply unchanged: the development
machine may have tools, a Kidux machine gets only what a package depends
on; versions bumped when a package is first touched, `~dev` builds, dated
by `date -R`; unit tests beside the code, acceptance checks in
`tests/acceptance/`, session tests in `tests/session/` with the purge test
renamed to stay last; a module test installs its module at its start and
removes it at its end; every picture the guide shows listed in
`tests/lib/doc-screenshots.txt`; documents changed in the same commit, in
the present; the quick loop first, the battery whole before the push;
batteries detached and waited for by PID. And these:

- **The commit is the step.** Each step is one commit (4.12 may be two:
  the framework, then Scratch's and TurboWarp's manifests), made when the
  step is done and its partial tests pass; the battery runs once, after
  4.15, before the owner is asked whether to push. Commits are authored
  `othermore <info@kidux.org>` (D80); nothing is pushed unless the owner
  asks.
- **A site on the internet is looked at from the machine left up.** What
  a website really needs, hosts, sign-in, WebGL, is found by opening it in
  the quick-loop VM as the child, never guessed from its home page: the
  method is in 4.12 under *Finding a site's hosts*.
- **Nothing a module names may be anyone's mark.** Icons are drawn like
  the avatars (branding/README.md): no CodeCombat logo, no Wikipedia globe.
  A module's name is the site's or the language's, as a word.
- **The BASIC guide is Kidux's own work.** Its model is the pair of books
  *BASIC para niños* (1984) and *BASIC avanzado para niños* (1987) by
  Sofía Watt and Miguel Mangada, Paraninfo: one idea per chapter, each
  idea tried at once on the machine, a mascot who talks in speech
  bubbles, *keep trying* exercises, a box of notes for the adult, games
  and useful programs at the end, and the same order of ideas. That
  method is what is taken, and nothing else: no sentence, no story, no
  program longer than the three or four lines that any BASIC lesson
  shares, no character (the mascot is Kidux's penguin chick,
  branding/README.md), and no picture of theirs. Every text, listing and
  drawing in the guide is written and drawn for Kidux, under the
  project's licence, in English first and Spanish beside it, and the
  developer documentation names the books as the model, nowhere else.
- **A module that opens a website says so, and says what it costs.** Its
  `description`, in every language, says it needs the internet, what
  account or subscription it takes, and, for CodeCombat, that Kidux is not
  connected with the site's makers (D86); the user guide says the same in
  more words.
- **The website is not changed by the module steps.** The site goes on
  showing the six modules it shows and the pictures it has;
  `30-every-module.py` goes on installing those six. Whether the three
  modules of this plan go on the site is the owner's call after they
  exist (section 4).

## 4. Decisions

Recorded in architecture.md's log by step 4.9's commit, numbered D83 to
D87, each *Decided 2026-10-03 by the owner, on phase-4b-plan.md*, worded
as here, with the rationale here; summarised so that the steps read on
their own.

- **D83 — The website counts its visits with Google Analytics, and only
  after the visitor says yes.** The owner wants to know whether anyone
  comes, and from where. Google's tag, `gtag.js`, with the measurement id
  as a fact of the site, `analytics` in `site/site.toml`; empty, the page
  carries no tag and no notice. Google's tag sets cookies, and the rules
  where the owner lives (the AEPD's, in Spain) want the visitor asked
  first, so the page loads nothing of Google's until the visitor accepts
  in a notice at the foot of the page; a refusal loads nothing, both
  answers are remembered in the browser, and a link in the footer asks
  again. The site sets no other cookie.
- **D84 — BASIC is wwwBASIC behind an editor of Kidux's own, in the
  browser, with the guide beside it.** The BASIC a child learns from is
  the one of the first home computers, the one *BASIC para niños*
  teaches: numbered lines, `PRINT`, `INPUT`, `GOTO`, a screen of text that
  also draws, colours and sounds. And the owner wants the lesson on the
  same screen as the machine. No program in trixie gives both: Matrix
  Brandy draws in an SDL window that can share a window with nothing;
  PC-BASIC has no installable package in trixie; `bwbasic` is text in a
  terminal; `yabasic` has no line numbers. Writing an interpreter would
  be two thousand lines with a long tail of small differences to chase.
  So the interpreter is **wwwBASIC** (`github.com/google/wwwbasic`,
  Apache-2.0, one JavaScript file, maintained, with its own test suite):
  a QBasic/BASICA BASIC, the books' *conventional BASIC*, that runs in a
  page, draws its own text screen on a canvas with the look of the PCs of
  the time, has `INPUT`, `INKEY$`, `READ`/`DATA`, `DIM`, `ON GOTO`, the
  string functions, `PSET`, `LINE`, `CIRCLE`, `PAINT`, `COLOR`, `BEEP`,
  `SOUND` and `PLAY`, and runs a program in slices so that a loop that
  never ends can be stopped. It arrives as every program not in trixie
  does, a pinned commit built into a tarball (D68, D71). Kidux adds no
  immediate mode and changes nothing in it: the child writes the program
  in an editor, presses *Run*, and sees it on the screen below; the guide
  is written for this machine, not for the one in the books, so what
  wwwBASIC does not do (`CONT`, reading a variable after a run, `GO TO`
  with a space) the guide does not teach. A child's programs are saved
  and opened as files, as Scratch's projects are (D75, D76), and the one
  being written is kept in the browser's storage between sessions.
  BASIC's words are the same in every language; the module's own words
  and its guide are in both.
- **D85 — A web module may be a door to one website on the internet,
  held to that site's hosts: the policy is the machine's ceiling, a proxy
  is the module's wall.** D42 foresaw a module that opens the web with a
  list of sites, switched on by an adult like any other. Chromium's
  managed policy is one for the whole machine and cannot hold one module
  to one site, so a module names its hosts in its manifest (`hosts`),
  `kidux-webapps` writes the policy from the manifests of the installed
  modules, its `URLAllowlist` the union of their hosts, and
  `kidux-webapp` starts every module's Chromium with a proxy that
  answers nothing (`--proxy-server=127.0.0.1:1`) and a bypass list of the
  module's own hosts, which is what confines each module to its site, the
  policy still refusing whatever no installed module names. Chromium
  honours these as documented (tried 2026-10-03: a host not in the
  bypass list fails with `ERR_PROXY_CONNECTION_FAILED` under the policy
  as it is). Scratch and TurboWarp name their library hosts the same way,
  and the policy carries no host of its own. A `web` module gets no
  `--enable-unsafe-swiftshader`, which is unsafe for pages from anywhere.
- **D86 — CodeCombat is a door to codecombat.com, nothing of it shipped,
  and Kidux says it is not connected with CodeCombat.** The levels are
  proprietary and cannot be served locally (architecture.md section 8);
  the site is translated and teaches real Python and JavaScript. The
  module reaches CodeCombat's own hosts and no other: an account is
  signed in with email and password, the sign-ins through Google,
  Facebook or Clever lead nowhere, a subscription is bought by the adult
  on another computer, and the module's words say the site is
  CodeCombat's, that most of it needs a paid subscription, and that Kidux
  has no connection with CodeCombat Inc.
- **D87 — Wikipedia is a door to the whole encyclopedia in the child's
  language, and the Wikimedia projects, with the rest of the internet
  closed.** The address is the child's language's edition; the hosts are
  Wikipedia's, Wikimedia's (where the pictures come from) and the sister
  projects'. It is the whole of Wikipedia, written for everyone, and the
  module's words say so, so that an adult switches it on knowing it.

Open for the owner, after the modules exist: whether BASIC, CodeCombat and
Wikipedia go on the website's list of modules (which would change its
title, *Six ways to learn*, the picture of the launcher with a tile for
every module, and `30-every-module.py`).

## 5. Steps

### 4.9 — The website counts its visits, once the visitor says yes — S

**Cause.** D83. The site is live and the owner has no way to know whether
anyone visits it; and a tag that sets cookies has to ask first.

**Change.**
- `site/site.toml`: a fact `analytics = "G-LHD6DKXB9P"`, with this comment
  above it: *Google Analytics' measurement id, `G-…`: with it the page asks
  the visitor whether it may count visits and, on a yes, loads Google's
  tag; empty, the page carries no tag and no notice.* And the comment above
  `download` ends at *the site says the image is on its way*: the words
  after it describe a button the page no longer has.
- `site/en.toml` and `site/es.toml`, a table `[cookies]` with four words:
  `text` (*This site counts its visits with Google Analytics, which sets
  cookies in your browser. May it?* / *Esta web cuenta sus visitas con
  Google Analytics, que deja cookies en tu navegador. ¿Puede?*), `accept`
  (*Yes* / *Sí*), `reject` (*No* / *No*) and `footer` (*Cookies* /
  *Cookies*), the footer link that asks again.
- `site/page.html`, all of it inside `{{#if site.analytics}} … {{#else}}
  {{/if}}` (the empty `{{#else}}` is required by the builder's `CHOICE`
  pattern):
  - at the end of `<body>`, the notice: `<div class="cookies" id="cookies"
    hidden role="dialog" aria-live="polite">` with the text and two
    buttons, `data-cookies="yes"` and `data-cookies="no"`;
  - in the footer, after the licence line, `<a href="#" data-cookies="ask">
    {{ cookies.footer }}</a>`;
  - a script, after the notice, that does all of this and nothing else:
    reads `localStorage["kidux-cookies"]` inside `try`; on `"yes"` loads
    the tag; on `"no"` does nothing; otherwise shows the notice. *Loading
    the tag* is Google's snippet made in script: `window.dataLayer`,
    `gtag('js', new Date())`, `gtag('config', '{{ site.analytics }}')`, and
    a `<script async src="https://www.googletagmanager.com/gtag/js?id=…">`
    element appended to `<head>`; nothing of Google's is in the page's
    HTML as a tag. The *yes* button stores `"yes"`, hides the notice and
    loads the tag; *no* stores `"no"`, hides the notice and, in case a yes
    came before, expires every cookie whose name begins `_ga` on the
    site's host and on `.kidux.org` (`document.cookie = name + "=;
    expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/; domain=…"`); the footer
    link clears the stored answer and shows the notice again. The script
    is the page's own, under its other script, in the same style.
- `site/style.css`: the notice is a bar fixed to the foot of the page in
  the brand's colours (branding/README.md), the text and the two buttons
  on one line on a wide screen and stacked on a phone, the buttons the
  page's `.button` classes; nothing of the page is covered that the bar
  does not scroll past.
- `tests/project/site.py`, four checks: `site.analytics` is empty or
  matches `^G-[A-Z0-9]{4,}$`; with the facts as they are, when the id is
  set, each language's built page carries the notice, the footer link,
  `localStorage.getItem("kidux-cookies")` and `googletagmanager.com/gtag/js?id=<id>`
  inside a script, and no `<script src="https://www.googletagmanager.com`
  tag anywhere; rendered with `site.analytics` empty (as the download
  check renders with another `download`), no page contains
  `googletagmanager`, `kidux-cookies` or the notice.
- `docs/dev/website.md`: section 1's sentence *The site uses no cookie
  and no tracker…* becomes what is true: the font is its own; the page
  takes two things from other servers, GitHub's Sponsor button where the
  page asks for a donation, and, once the visitor has said yes, Google's
  tag, which counts visits. A short section 5, *Visits*: the id
  (`analytics` in `site/site.toml`), where the owner reads the reports
  (`analytics.google.com`, the property the id belongs to), that nothing
  of Google's loads before the visitor accepts the notice, that the answer
  lives in the visitor's browser, and that the footer's *Cookies* asks
  again (D83).
- `docs/dev/roadmap.md`, phase 7: `- [x] The website counts its visits,
  once the visitor says yes (D83).`
- architecture.md's log: D83 to D87, as section 4 words them, all in this
  commit, so that every later step refers to a number that exists.

**Tests.** `tests/run project`. Then `ci/build-site.py` and the page
looked at from another computer (website.md section 3): the notice shows
once, *no* keeps it away on a reload and the browser's developer tools
show no request to Google, *yes* loads the tag, the footer link brings
the notice back; in both languages.

**Traps.** `localStorage` throws in a private window; every use is inside
`try`, and without it the notice simply shows each time. The tag's id is
letters, digits and a hyphen, so the builder's HTML escaping leaves it
whole, in a string as in an attribute.

**Documents.** website.md, roadmap.md, the log; nothing in the user guide,
which does not describe the website.

**Done when.** `tests/run project` is green and, once the owner has pushed,
`https://kidux.org/` and `/es/` show the notice, and the Analytics
property shows a visit after a yes.

### 4.10 — `kidux-module-basic`: wwwBASIC in an editor, and the guide's first part — L

**Cause.** D84. A BASIC of the eighties for a child who has done Scratch,
with its lesson on the same screen.

**Change.** A web module copied from `kidux-module-hello-web`, with the
interpreter from upstream and the editor, the screen's glue and the guide
of Kidux's own: `webapp/page.py` writes `index.html` at build time, as
hello-web's does, and the package installs it with its scripts, its
style, its pictures, the guide and wwwBASIC under
`/usr/share/kidux/webapps/basic/`. The package depends on `kidux-webapps
(>= 0.1.9)` and on nothing else.

*First, two hours that decide* (the step's first commit comes after
them, not before): a bare page in the quick-loop VM with `wwwbasic.js`,
a canvas with its `GraphicsBindings`, and this program run from a
textarea by a button:

```
10 INPUT "Your name"; N$
20 PRINT "Hello, "; N$
30 PRINT "Press a key"
40 K$ = INKEY$: IF K$ = "" THEN 40
50 PRINT "You pressed "; K$
60 PSET (100, 100), 14: CIRCLE (320, 200), 50, 12
70 SOUND 440, 5
```

It must take the name from the keyboard, see the key, draw and sound,
and a `10 GOTO 10` must be stoppable from a button. Then the same
program under node with `require('wwwbasic')` and a bindings object of
ours that collects what is printed and feeds keys from a list, which is
what the tests below are built on. If any of the five does not work and
cannot be made to work through wwwBASIC's bindings (its documented way
to add a statement or a function, and the only way Kidux touches it),
the step stops and the owner is told what failed, with the choices; the
plan is not changed by the agent on its own.

*wwwBASIC* arrives as Scratch did: `upstream.toml` with the repository,
the `commit` (the newest on the default branch when the step starts),
`version` `0+git<yyyymmdd>` of that commit and `source_sha256`;
`ci/upstream/wwwbasic.sh` needs no Node.js build: it fetches through
`ci/upstream/fetch.sh` and packs `wwwbasic.js`, `LICENSE`, `README.md`
and `test/` into the tarball `ci/build-upstream.sh` publishes (D71);
`tests/project/upstream.sh` checks it as it checks the others.
`debian/copyright`: `BUSL-1.1` for `Files: *`, `Apache-2.0` for
`Files: upstream/*`, copyright Google LLC; lintian overrides as Blockly
Games' for the minified-looking file if lintian says so. Nothing in
`wwwbasic.js` is edited: a need is met in Kidux's glue through its
bindings, or not at all.

*The manifest.* `id = "basic"`, `version = "0+git<yyyymmdd>"` (the
package's, as always), `name = "BASIC"`, `description = "BASIC as it was
on the first home computers, with its guide beside it: write a program,
press Run, and see. It draws, colours and sounds too."`, `min_age = 8`,
`max_age = 14`, `recommended_before = ["scratch"]`, `launch = { webapp =
"basic" }`, `categories = ["programming"]`, `memory_max = "2G"`. Spanish:
`BASIC`, `BASIC como en los primeros ordenadores de casa, con su guía al
lado: escribe un programa, pulsa Ejecutar y mira. También dibuja, colorea
y suena.`

*The page* (`webapp/index.html` written by `page.py`, `webapp/style.css`,
`webapp/machine.js`, `webapp/guide.js`): one page, the child's language
from `?lang=`, every language's words in it as hello-web's are. Two
halves side by side: the machine on the left, the guide on the right;
under 1000 px of width they stack, the machine first. The machine's half
is, top to bottom: the editor, a row of buttons, the screen.
- **The editor** is a `<textarea>` in the screen's monospace face, with
  a gutter that numbers its lines 1, 2, 3 (the BASIC numbers at the start
  of a line, 10, 20, 30, are the program's own, the names `GOTO` jumps
  to; the guide says so in chapter 1), spellcheck off, Tab inserting
  spaces. Its text is kept in `localStorage` after every change and comes
  back when the page opens, so that closing the module loses nothing; the
  storage is the module's own profile, which goes with the module.
- **The buttons**: *Run* (Ctrl+Enter too), *Stop* (Escape too), *New*,
  *Save*, *Open*. *Run* hands the editor's text to `basic.Basic(text,
  {bindings})` with the screen's bindings and gives the screen the
  keyboard's focus; *Stop* ends the run through the bindings' pace (the
  function wwwBASIC calls between slices, which tells it to quit); *New*
  empties the editor after *Are you sure?*; *Save* downloads the text as
  `<name>.bas` through Chromium's file dialog (D75, D76), the name asked
  in the page first, `program.bas` by default; *Open* opens the file
  dialog on a `.bas` and puts its text in the editor. The buttons' words,
  the question and the names are in the module's gettext domain.
- **The screen** is a canvas wwwBASIC draws on through its
  `GraphicsBindings`: its own text mode, font and colours, scaled by CSS
  to the half's width with `image-rendering: pixelated`. Keys go to it
  while a program runs: the page listens on the canvas and hands wwwBASIC
  what it expects (its `doc/keyboard.md` says which codes), so that
  `INPUT` reads a line and `INKEY$` sees a key. Sound is wwwBASIC's own,
  started on the first key or click (browsers want a gesture first; *Run*
  is one).
- **Errors**: what wwwBASIC reports, `… at line N`, is shown on the
  screen in a colour of its own, N translated by the page into the BASIC
  number at the start of that editor line when it has one (*Error in line
  30: …*), the editor's line otherwise; the editor scrolls to it. The
  message stays wwwBASIC's English text, which is short and the same the
  guide shows when it says what a mistake looks like.
- The page's own words (buttons, *Chapters*, *Next*, *Back*, *Type it in
  for me*, *For the adult*, *Are you sure?*, *Error in line*, *program*)
  are extracted by `ci/i18n-extract.sh` from `page.py` and written into
  the page for each language, as hello-web's are.

*The language the guide teaches* is what wwwBASIC has and the books
teach, written as wwwBASIC reads it: numbered lines (the guide numbers
them 10 by 10 as the books do, because `GOTO`, `GOSUB` and `ON GOTO`
need them and a line can be put between two), `PRINT` (`;` and `,`),
`LET` (optional), `INPUT "text"; A`, `GOTO`, `GOSUB`/`RETURN`, `IF … THEN
<line | statement>` and `ELSE`, `FOR … TO … STEP`/`NEXT`, `READ`/`DATA`/
`RESTORE`, `REM` and `'`, `DIM`, `ON … GOTO`/`GOSUB`, `END`, `STOP`,
`CLS`, `RANDOMIZE`, `INT`, `RND`, `ABS`, `SGN`, `SQR`, `LEN`, `LEFT$`,
`RIGHT$`, `MID$`, `CHR$`, `ASC`, `VAL`, `STR$`, `INKEY$`, `TAB`, `^`,
`AND`, `OR`, `NOT`, and for 4.11 `SCREEN`, `PSET`, `LINE`, `CIRCLE`,
`PAINT`, `COLOR`, `LOCATE`, `BEEP`, `SOUND`, `PLAY`, `SLEEP`. The guide
writes `GOTO` and `GOSUB` as one word, never uses `CONT`, never reads a
variable after a run, and stops a program with the *Stop* button or
Escape; where the books' machines differ from this one, the guide
follows this one without saying so. Before a chapter is written, its
statements are tried on the machine; the listing in the guide is what
ran.

*The guide* (`webapp/guide.js`, `content/`): the right half shows one
chapter at a time, with *Back* and *Next* and a *Chapters* list, and
remembers the chapter it was on in `localStorage`. Chapters are Markdown
files, `content/en/NN-slug.md` and `content/es/NN-slug.md`, the same
names, English the source and Spanish its translation with the hash
`tests/project/content.py` keeps (and `--update` writes); `page.py`
renders them to HTML at build time with `python3-markdown` (3.7, in
trixie, a build dependency), with these four conventions and no other:
- a fenced block marked `basic` is a listing, shown as the screen prints
  it, with a button *Type it in for me* under it, which puts the listing
  in the editor (replacing what is there, after *Are you sure?* when the
  editor is not empty and not a listing of the guide's) and focuses the
  *Run* button; the chapter always suggests typing it first;
- a blockquote is the mascot speaking: the penguin chick in a pose beside
  a speech bubble with the text; the pose is named in the first word when
  it is one of `[think]`, `[point]`, `[cheer]`, `[oops]`, otherwise the
  chick as it is;
- a block between a line `::: adult` and a line `:::` is the box for the
  adult, rendered from its own Markdown into a `<details>` closed by
  default, headed *For the adult*;
- a picture `![…](images/name.svg)` is a drawing from `content/images/`,
  shared by every language, with no words in it.
The drawings are SVGs drawn like the avatars (branding/README.md), flat
and friendly: the mascot's poses, a computer with a screen, memory as
shelves of boxes, a flowchart's shapes, dice, a hide-and-seek garden,
whatever a chapter needs to be fun; `page.py` inlines them so that the
page needs no other file. The guide's style is the brand's, cream and
ink, Andika for the text (the system's, which Kidux ships) and the
screen's monospace for listings.

*The chapters of the first part*, one idea each, in the books' order, each
with its *keep trying* exercises and its box for the adult; every listing
is written for Kidux, with the mascot and the child's world (the penguin's
friends, fish, snow, a fruit stand, the school) as the stories:

1. *Hello* — the editor, the screen and *Run*; what a program is; that
   the computer does exactly what it is told, in order; the numbers at
   the start of the lines and why they go 10 by 10.
2. *PRINT* — printing words, the first program, the mistakes with
   quotes, changing a line, a blank line, `,` and `;`, drawings made of
   letters; *New* when a new program starts.
3. *LET* — variables, numbers, changing a value, sums, `*` and `/`,
   string variables with `$`, joining strings with `+`.
4. *INPUT* — talking with the machine, numbers and words, the semicolon
   and the spaces, a program that asks your name and your age.
5. *GOTO* — the loop that never ends and *Stop*, counting by twos, a sum
   table, a jump forward, `END`.
6. *IF* — a question with one answer, `=`, `<`, `>`, `<=`, `>=`, `<>`,
   words in a condition, a shop with two things to buy, a mark that
   passes or fails.
7. *FOR and NEXT* — the loop that counts for you, `STEP`, a table in two
   columns, printing something fifty times.
8. *GOSUB and RETURN* — a piece of program used many times.
9. *READ and DATA* — a store of values, too many and too few, the marker
   value that says stop.
10. *REM* — notes to yourself.
11. *INT* — whole numbers.
12. *RND* — chance, a die, a hundred throws, counting how often a five
    comes.
13. *Flowcharts* — drawing a program before writing it, the shapes.
14. *Games* — the multiplication trainer, hide-and-seek with the penguin,
    guess my number, the mind reader: each with its listing, each using
    only what the chapters taught.
15. *Saving your programs* — *Save* and *Open*, where the file goes, that
    the editor keeps the program you are writing.

*The package.* `debian/control`: `Build-Depends` gains `python3-markdown`
and `nodejs <!nocheck>` (20.19 in trixie); `Depends: kidux-webapps (>=
0.1.9)`; the `XB-Kidux-*` fields by `tests/project/module-fields.py
--update`; `Description: Kidux learning module: BASIC, the home computer
of the eighties with its guide`, the long description saying it is
wwwBASIC in an editor of Kidux's own, with a guide in the child's
language, that programs are saved as files, and that nothing of it comes
from the internet. `debian/rules`: `page.py` at build (every language's
guide and words), the node tests and the Python tests under `nocheck`'s
guard, the files under `/usr/share/kidux/webapps/basic/`, `upstream/`
copied as Blockly Games' is. Icon: drawn like the avatars, a dark screen
with a light `>` prompt and a block cursor. `ci/build-all.sh`: the
package after `kidux-module-blockly-games`.

**Tests.**
- Unit, the listings: `tests/run-basic.js` loads `upstream/wwwbasic.js`
  under node with a bindings object of Kidux's (`webapp/test-bindings.js`,
  shared with the page's machine where it can be) that collects what is
  printed into a text buffer, records drawing and sound calls as lines,
  and feeds keys from a list; `tests/basic/NN-name.bas` with
  `NN-name.out` and, where the program reads, `NN-name.in`, one per
  statement the guide teaches, fail on the first difference. Every
  listing of the guide runs too: `tests/test_guide.py` extracts the
  `basic` blocks of every English and Spanish chapter, with the keys a
  comment in the block names (`' keys: Leo, 9, Enter`), runs each through
  the node runner, and fails when one stops with an error; so a listing
  in the guide is never wrong.
- Unit, the page: `page.py` renders the four conventions; the languages
  have the same chapters; every picture a chapter names exists; the words
  are complete; the error line's translation (editor line to BASIC
  number).
- Acceptance `09-module-basic.sh` (the number is free): installs through
  the daemon with `kidux-webapps`; the server answers `/basic/?lang=es`
  with a page whose title is the module's, and answers `wwwbasic.js`,
  `machine.js` and `guide.js` under `/basic/`; `upstream/LICENSE` is
  installed; the manifest, icon and Spanish catalogue are in place;
  listed for Marta, off; removed without a trace.
- Session `31-module-basic.py` (after `30-every-module.py`; the purge test
  becomes `34-purge.py` in this step, leaving 32 and 33 for 4.13 and
  4.14): installs, switches it on for Leo, signs in, opens the tile; waits
  for a window of module `basic`, maximised, on screen, titled `BASIC`;
  the editor has the focus: types `10 PRINT "HOLA"`, Enter, `20 GOTO 10`
  with `machine.type`, then Ctrl+Enter, waits two seconds, takes
  `module-basic` (listed in doc-screenshots), checks the screen's box is
  mostly not cream and the right half mostly cream with `colour_share`,
  presses Escape; Alt+F4; logs out; removes.
- The quick loop first: `tests/run vm up 04`, `vm push kidux-module-basic`,
  the tile opened by hand, `vm shot`: the three parts, a program typed,
  *Run*, a chapter's button, *Save* opening the file dialog in the child's
  Documents.

**Traps.**
- Chromium refuses to start audio before a user gesture; *Run* is a
  click or a key, so sound works from the first program.
- wwwBASIC compiles the whole text before running: a mistake anywhere
  stops the run before line 10 prints, with the message; chapter 2 shows
  it on purpose.
- wwwBASIC's `Error('… at line N')` counts the editor's lines; the page
  maps it as said above, and the mapping has its unit test.
- The listings' keys for the node runner are in a comment that is BASIC
  (`'` is `REM`), so the listing stays a program.
- `localStorage` throws in some states; every use is inside `try`, and
  the machine works without it.
- Every path the page names is relative and under `/basic/`, which the
  acceptance check's `curl` of each script proves.

**Documents.** User guide section 9, *BASIC*, both languages, after
TurboWarp: what it is, the three parts, that the guide is read on the
right and typed on the left, that *Save* keeps a program as a `.bas` file
in the child's Documents and *Open* brings it back, that the program
being written stays until *New*, *Stop* or Escape for a program that
never ends, and the picture. README's list, both languages.
architecture.md section 8: a row *BASIC* (wwwBASIC `0+git…`, Apache-2.0,
in an editor of Kidux's own, D84), and modules.md section 5 naming the
module among the web modules. docs/dev: a short `basic.md`, the module's
own document: what wwwBASIC is and how it arrives, the bindings Kidux
gives it, the page's three parts, the guide's conventions, the guide's
model (the two books, named, and the rule that nothing of theirs is
reproduced), and how a chapter is added. roadmap.md phase 4: `- [x]
BASIC: wwwBASIC in an editor of Kidux's own, with its guide beside it
(4.10, 4.11, D84).` ticked at 4.11.

**Done when.** The session test passes in both languages, the pictures
show a program in the editor, its output on the screen and the guide's
first chapter beside it, every listing of the first part runs under the
node runner, and the owner has typed through chapters 1 to 6 on the
MacBook without a surprise.

### 4.11 — The guide's second part — M

**Cause.** D84: the second book's ideas, and what the home computers had
that the books' machines did not all have: drawing, colour and sound.

**Change.** Chapters 16 to 30 in `content/en/` and `content/es/`, the same
conventions, the same rule of ownership, the pictures each needs; nothing
in wwwBASIC: a chapter is written for what it does, tried on the machine
first. The chapters:

16. *Inside the computer* — keyboard, memory, screen; what is kept and
    what is lost when the power goes; bits and bytes, lightly.
17. *The fifth operation* — powers with `^`, big numbers and `E+`, the
    grains of rice on a board told as the penguin's fish.
18. *Order of operations* — what the machine does first, parentheses,
    the shop sum that comes out wrong without them.
19. *CLS and CLEAR* — a clean screen, a clean memory, the difference
    with `NEW`.
20. *INPUT, more* — the prompt in the `INPUT`, several values at once.
21. *FOR and NEXT, more* — `STEP`, leaving a loop, a loop that waits
    (`PAUSE`), loops inside loops, the multiplication tables one by one.
22. *AND and OR* — two conditions, the table of yes and no, a line that
    catches a wrong answer, a program with a password.
23. *IF, more* — a menu, `ON … GOTO`, `ELSE`.
24. *READ, DATA and RESTORE* — a list of friends and what each plays,
    searching it, reading it again.
25. *DIM* — a shelf of variables, lists of things, a table with two
    subscripts.
26. *Putting things in order* — comparing, swapping with a spare box,
    sorting numbers and then names.
27. *Strings* — `LEN`, `LEFT$`, `RIGHT$`, `MID$`, `VAL`, `STR$`,
    `INKEY$`, a word shown letter by letter, a program that waits for any
    key.
28. *CHR$ and ASC* — the code of a letter, a secret-code game.
29. *Drawing, colour and sound* — `PSET`, `LINE`, `CIRCLE`, `PAINT`,
    `COLOR`, `BEEP`, `SOUND`: a house, a snowman, a flag, a tune, a
    bouncing dot.
30. *Programs to keep* — a reflex game, a basketball league of the
    penguin's friends, an address book, an alphabetical list, a library
    of the child's books, a drawing game with the arrow keys; and a last
    page on programming well: think first, draw the chart, name the
    variables, put `REM`s, catch wrong answers, make a menu.

**Tests.** The guide's listings run under the node runner (4.10's
`test_guide.py`), the drawing ones against the text-buffer screen that
records the calls; the languages have the same chapters; `tests/project/content.py`
passes. Session `31-module-basic.py` unchanged. The quick loop: the owner's
eye on chapter 29 in the VM, the drawings and a tune.

**Traps.** A chapter that needs something wwwBASIC lacks is written
another way, with what it has; wwwBASIC is not changed and not extended.
`PLAY`'s tune language is wwwBASIC's own; chapter 29 uses a few notes
of it and says where its rules are (the box for the adult).

**Documents.** docs/dev/basic.md's chapter list; the user guide's BASIC
section mentions drawing and sound; roadmap.md's line ticked.

**Done when.** Thirty chapters in two languages, every listing running,
and the owner has drawn the snowman on the MacBook.

### 4.12 — A web module that is a door to one website — M

**Cause.** D85. CodeCombat and Wikipedia are pages on the internet, and
the framework holds every Chromium to the local server by one policy for
the whole machine.

**Change.**

*The manifest* (modules.md section 1):
- `launch = { web = "https://codecombat.com/" }`, a third kind of launch:
  an `https://` address, in which `{lang}` stands for the child's language
  code (`https://{lang}.wikipedia.org/`). The reader, `kidux.modules` in
  `kidux-common` (bumped, `python3-kidux` 0.1.53), takes it as it takes
  `webapp` and `exec`: a manifest whose `launch` has none of the three, or
  whose `web` is not a string beginning `https://`, is skipped with a line
  in the log. For a `web` launch the reader adds to `app_ids` what
  Chromium calls the window, `chrome-<host>__*`, the host being the
  address's with `{lang}` as `*` (`chrome-codecombat.com__*`,
  `chrome-*.wikipedia.org__*`); a constant beside `WEBAPP_APP_ID`.
- `hosts = ["codecombat.com"]`, a top-level key: the names of the
  internet hosts the module's pages may reach, each standing for that
  host and every name under it (`codecombat.com` is also
  `www.codecombat.com`); lower-case DNS names, nothing else, no scheme,
  port, path or `*`. Default none. A value that is not a list of such
  names is dropped with a line in the log, as `app_ids` is. `Module`
  gains `hosts: tuple[str, ...]`, sorted, unique.
- Unit tests in `kidux-common/tests/test_modules.py`: a `web` manifest
  reads with its derived app id; `{lang}` in the host becomes `*`; an
  `http://` address is skipped; `hosts` read, sorted, deduplicated; a bad
  `hosts` dropped and logged.

*`kidux-webapp`* (`kidux-webapps` 0.1.10, `Depends: python3-kidux (>=
0.1.53)`):
- `kidux-webapp [--print] <module id>`: the argument is a module's id;
  the program reads its manifest with `modules.read` and refuses, with
  exit 2 and a line on stderr, an id that reads as no module or as one
  with neither `webapp` nor `web`.
- The address: for `webapp`, `http://127.0.0.1:8123/<webapp>/?lang=<lang>`
  as today; for `web`, the manifest's address with `{lang}` replaced by
  the language code, nothing else changed.
- The wall, for every module, local or not, two flags before `--app`:
  `--proxy-server=127.0.0.1:1`, a proxy nothing listens at, and
  `--proxy-bypass-list=<list>`: `127.0.0.1` first, then for each host of
  the manifest, in order, `host;*.host` (a bypass rule without `*`
  matches that host alone), all joined with `;`. hello-web's is
  `127.0.0.1`; CodeCombat's `127.0.0.1;codecombat.com;*.codecombat.com`.
  Everything the list does not name goes to the proxy and fails.
- `--enable-unsafe-swiftshader` only for a `webapp` launch (D85); a `web`
  module on a machine without graphics Chromium takes gets WebGL from the
  machine's flags if the adult adds it, and the guide's *Advanced* section
  already says what those are for.
- `argv(module, environ, flags)` takes a `Module`; `main` reads it. Unit
  tests: hello-web's line as today plus the two flags; a `web` module with
  two hosts; `{lang}` for a Spanish child; a module with `exec` only
  raises; an unknown id exits 2.

*The policy, generated* (`kidux-webapps`):
- `policies/kidux.json` becomes the base, installed at
  `/usr/share/kidux-webapps/policy.json`, the file as it is today with
  `URLAllowlist` reduced to `["127.0.0.1:8123", "blob:*"]`: no host of any
  module's.
- `bin/kidux-chromium-policy`, installed to `/usr/libexec/`, Python, run
  by root: reads the base, reads every installed module (`modules.installed()`;
  `--root` for the tests), writes `/etc/chromium/policies/managed/kidux.json`
  (`--output` for the tests) as the base with `URLAllowlist` =
  `127.0.0.1:8123`, then the union of the modules' hosts, sorted and
  unique, then `blob:*`; written to a temporary file beside it and
  renamed, mode 0644. Nothing but the allowlist comes from the modules.
- `debian/kidux-webapps.triggers`: `interest-noawait /usr/share/kidux/modules`,
  so that dpkg runs the package's postinst with `triggered` whenever a
  module's manifest is installed or removed, by the panel or by `apt`.
- `debian/kidux-webapps.postinst`: `set -e`, the `#DEBHELPER#` token, then
  `case "$1" in configure|triggered) /usr/libexec/kidux-chromium-policy ;; esac`.
  The token must come first: the conffile's removal (next) is finished
  there, and the generator writes the file after it.
- `debian/kidux-webapps.maintscript`: `rm_conffile
  /etc/chromium/policies/managed/kidux.json 0.1.10~`, so that a machine
  upgrading from 0.1.9 drops the shipped conffile and gets the generated
  file; `debian/rules` no longer installs anything under `/etc`.
  `debian/kidux-webapps.postrm`: on `purge`, `rm -f` the generated file.
- Unit tests `tests/test_policy.py`: a modules root with hello-web (no
  hosts), a module with two hosts and another repeating one gives the
  allowlist in order with no repeat; no modules gives the base's; every
  other key of the base is kept; the output has mode 0644.
- `debian/control`'s long description: the policy is written from the
  installed modules, and a module that opens a website names its hosts.

*The launcher* (`kidux-launcher` 0.3.18): `launch.command()` starts
`kidux-webapp <module id>` for a `web` launch as for a `webapp` one, and
passes the module's id in both cases (today it passes the `webapp` name,
which has always been the id); its test says so. launcher.md section 5,
the sentence on what the launcher starts.

*The daemon* (`kidux-daemon` 0.3.32): `advanced.py`'s `REFUSED` gains
`--no-proxy-server`, which would take the wall down from the panel's
*Advanced* page; the acceptance check that refuses a flag tries it.

*Scratch and TurboWarp* (`kidux-module-scratch` 15.2.0+build2.3,
`kidux-module-turbowarp` 0+git20260915.3): each manifest gains `hosts`
with the hosts its library comes from, found as *Finding a site's hosts*
says, expected Scratch: `assets.scratch.mit.edu`, `cdn.assets.scratch.mit.edu`,
`cdn2.scratch.mit.edu`, `cdn.scratch.mit.edu`; TurboWarp: the same four
and `trampoline.turbowarp.org`. Their library is opened in the quick-loop
VM after the change and a character from it dropped on the stage, in
each.

*Finding a site's hosts.* On the machine left up, with the module pushed
and switched on for Leo: `kidux-as set-config chromium_flags
'["--log-net-log=/tmp/net.json"]'` (the daemon lets that flag through),
the module opened from its tile and used as a child would for a few
minutes (CodeCombat: sign in, the first level; Wikipedia: an article with
pictures, a link to a sister project; Scratch: the library), closed, and
`/tmp/net.json` read with a short script in the scratchpad: every
`URL_REQUEST` whose end carries `ERR_PROXY_CONNECTION_FAILED` (the wall)
or `ERR_BLOCKED_BY_ADMINISTRATOR` (the ceiling), by host. Of those, the
site's own hosts go into `hosts`; trackers, advertising, Google's and
Facebook's sign-ins, payment pages do not, and the module's manifest
says in a comment which were left out and why. Then the flag is taken
back (`set-config chromium_flags '[]'`) and the module pushed again.

**Tests.**
- Unit, as above, in `kidux-common`, `kidux-webapps`, `kidux-launcher`,
  `kidux-daemon`.
- Acceptance `12-webapps.sh`: the policy is root's, 0644, and not a
  conffile (`dpkg-query -W -f='${Conffiles}' kidux-webapps` does not name
  it); with no installed module naming hosts its allowlist is
  `["127.0.0.1:8123", "blob:*"]`; `kidux-webapp --print hello-web` carries
  `--proxy-server=127.0.0.1:1` and `--proxy-bypass-list=127.0.0.1` before
  `--app=`; `--no-proxy-server` is refused as a machine flag.
  `13-module-scratch.sh` and `14-module-turbowarp.sh`: once installed, the
  allowlist holds their hosts, in order; once removed, it does not. The
  trigger is what makes that true, and these checks are what prove it
  runs.
- Session: `19-module-hello-web.py`, `26-module-scratch.py`,
  `27-module-turbowarp.py` and `31-module-basic.py` pass as they are;
  Scratch's library opens in the quick loop.

**Traps.**
- Chromium bypasses the proxy for loopback addresses on its own; the list
  names `127.0.0.1` anyway, so that the local server never depends on
  that.
- A bypass rule `codecombat.com` matches only that host; `*.codecombat.com`
  the names under it; both are written. In the policy's allowlist a bare
  host matches the names under it too, so one entry per host is enough
  there.
- dpkg runs an `interest-noawait` trigger when a file under the directory
  is installed or removed by any package; a module's manifest is such a
  file. If the acceptance check finds the policy stale after an install,
  the trigger file's path is wrong, not the idea.
- `rm_conffile` keeps a locally modified conffile as `.dpkg-bak`; a
  machine whose policy the owner edited by hand would have been
  hand-edited, which no Kidux machine is.
- The build chroot has no `/etc/chromium`; the generator's tests write to
  a temporary path, and the package build never runs the generator.
- Electron (ScratchJr) reads no managed policy and is not started by
  `kidux-webapp`; it is offline and is not touched.

**Documents.** modules.md section 1 (`launch.web`, `hosts`, the derived
app id), section 2 (a module that opens one website: what it is for an
adult), section 4 (the policy generated from the installed modules, the
proxy as each module's wall, the base file; the lists of hosts gone from
the text, since the manifests hold them); architecture.md's module
paragraph in section 5 (*Web-app modules*: a third kind) and D36's note
(superseded in part by D85 too); packaging.md where it lists what a
module installs, if it does; the user guide's section 9 introduction,
both languages: after the paragraph on modules made of web pages, one
saying that a few modules are a door to one website on the internet,
show that site and nothing else of it, and say so in their names and
descriptions. launcher.md section 5.

**Done when.** The three acceptance files and the four session tests
pass, Scratch's library opens in the quick loop, and `kidux-webapp
--print` shows the wall for hello-web.

### 4.13 — `kidux-module-codecombat` — S

**Cause.** D86; phase 4's last unticked module.

**Change.** Copied from `kidux-module-hello-web`, with no `webapp/` and no
`content/`:
- `module.toml`: `id = "codecombat"`, `version = "0.1.0"`, `name =
  "CodeCombat"`, `description = "The CodeCombat website, where you learn
  Python and JavaScript by playing. It needs the internet and a CodeCombat
  account, paid for most of it; Kidux is not connected with CodeCombat."`,
  `min_age = 9`, `max_age = 16`, `recommended_before = ["scratch"]`,
  `launch = { web = "https://codecombat.com/" }`, `hosts = ["codecombat.com"]`
  plus what *Finding a site's hosts* finds to be CodeCombat's own, with a
  comment naming what was left out, `categories = ["programming"]`,
  `memory_max = "3G"`. Spanish: `CodeCombat`, `La web de CodeCombat, donde
  se aprende Python y JavaScript jugando. Necesita internet y una cuenta
  de CodeCombat, de pago para casi todo; Kidux no tiene ninguna relación
  con CodeCombat.`
- `debian/control`: `Depends: kidux-webapps (>= 0.1.10)`; the fields;
  `Description: Kidux learning module: CodeCombat, a door to the CodeCombat
  website`, the long description saying the module ships nothing of
  CodeCombat and opens its website and no other, that an account is
  needed and a subscription for most of it, bought on another computer,
  that signing in is with email and password, and that Kidux and its
  author have no connection with CodeCombat Inc.; `debian/copyright`:
  `BUSL-1.1`, nothing else, since nothing of CodeCombat's is in it.
- Icon: a sword and a shield, drawn like the avatars.
- `ci/build-all.sh`: after `kidux-module-basic`.

**Tests.**
- Unit: the manifest reads, with `web` and `hosts`; the words are complete.
- Acceptance `17-module-codecombat.sh`: installs through the daemon; the
  manifest, icon and catalogue in place; the policy's allowlist holds
  `codecombat.com` (and the others) while it is installed; `kidux-webapp
  --print codecombat` as Marta carries `--app=https://codecombat.com/`,
  the bypass list with its hosts, and no `--enable-unsafe-swiftshader`;
  listed for Marta, off; removed, and the allowlist no longer holds its
  hosts.
- Session `32-module-codecombat.py`: installs, on for Leo, signs in, opens
  the tile; waits up to 90 s for a window of module `codecombat` whose
  title contains `CodeCombat`, maximised, on screen; takes
  `module-codecombat` (listed in doc-screenshots); the room above the bar
  not cream; Alt+F4; logs out; removes. The report says *the site did not
  answer* when the window is there and the title never comes: the
  battery's machines have the internet through QEMU's user network, and a
  site that is down is not Kidux's fault; the test still fails.
- The quick loop: the site opened as Leo, signed in with an account the
  owner makes for it (asked for by the final message, never typed by the
  agent into a document), the first level played, the net log read.

**Traps.**
- The site's sign-in page offers Google, Facebook and Clever; those lead
  to Chromium's blocked page, and the guide says to use email and
  password.
- The game draws with WebGL; a VM without graphics shows what it shows,
  and the picture is of the site's front page, which needs none.
- The site may ask for cookies' consent in a banner of its own; it is the
  site's, and stays.

**Documents.** User guide section 9, *CodeCombat*, both languages, after
BASIC: what it is, that it is CodeCombat's website and Kidux has no
connection with CodeCombat, that it needs an account and, past the first
levels, a subscription the adult buys on another computer, that the child
signs in with email and password, and the picture. README's list, both
languages, with the same words. architecture.md section 8's CodeCombat
row: `kidux-module-codecombat`, a door (D85, D86). roadmap.md phase 4:
the CodeCombat line ticked, reworded to D86.

**Done when.** The session test passes in both languages and the pictures
show CodeCombat's front page in each.

### 4.14 — `kidux-module-wikipedia` — S

**Cause.** D87.

**Change.** As 4.13:
- `module.toml`: `id = "wikipedia"`, `version = "0.1.0"`, `name =
  "Wikipedia"`, `description = "Wikipedia, the whole encyclopedia, in the
  child's language, with the rest of the internet closed. It is written
  for everyone, not only for children."`, `min_age = 8`, no `max_age`,
  `launch = { web = "https://{lang}.wikipedia.org/" }`, `hosts =
  ["wikipedia.org", "wikimedia.org", "wikidata.org", "wiktionary.org",
  "wikibooks.org", "wikiquote.org", "wikisource.org", "wikinews.org",
  "wikiversity.org", "wikivoyage.org", "mediawiki.org",
  "wikifunctions.org"]`, with a comment: Wikipedia, Wikimedia (the
  pictures and the sign-in) and the sister projects; whatever *Finding a
  site's hosts* shows to be theirs too; `categories = ["reading"]`,
  `memory_max = "2G"`. Spanish: `Wikipedia`, `Wikipedia, la enciclopedia
  entera, en el idioma del niño, con el resto de internet cerrado. Está
  escrita para todo el mundo, no solo para niños.`
- `debian/control`: `Depends: kidux-webapps (>= 0.1.10)`; `Description:
  Kidux learning module: Wikipedia, a door to the encyclopedia`, the long
  description saying it opens Wikipedia in the child's language and the
  Wikimedia projects, nothing else, and that it is the whole of Wikipedia.
- Icon: an open book, drawn like the avatars.
- `ci/build-all.sh`: after `kidux-module-codecombat`.

**Tests.**
- Unit, as 4.13.
- Acceptance `18-module-wikipedia.sh` (`19-no-key-no-archive.sh` stays
  last): as 4.13's, with `--app=https://es.wikipedia.org/` for a Spanish
  Marta (`LC_ALL=es_ES.UTF-8` as `12-webapps.sh` sets it) and
  `--app=https://en.wikipedia.org/` without it.
- Session `33-module-wikipedia.py`: as 4.13's, the title containing
  `Wikipedia`, picture `module-wikipedia`; then `machine.type("Debian")`
  and Enter in the front page's search box (which has the focus when the
  page loads; if it does not, Tab to it, counted once by hand), a wait
  for the title to contain `Debian`, and Alt+Left, after which the title
  no longer does: the way back a child has. Then Alt+F4, log out, remove.

**Traps.**
- An application window has no back button; Alt+Left and the mouse's own
  back button go back, and the guide says so. If Alt+Left is taken by
  labwc before Chromium sees it, keys.md says how a binding is checked,
  and the guide names what works.
- Wikipedia's pictures come from `upload.wikimedia.org`, under
  `wikimedia.org`; a page without pictures means the host is not in the
  list after all, which the net log shows.
- A language Kidux has and Wikipedia has not would get a dead address;
  every language Kidux ships has an edition, and modules.md says `{lang}`
  is the code as it is.

**Documents.** User guide section 9, *Wikipedia*, both languages, after
CodeCombat: the whole encyclopedia, in the child's language, that an
adult decides whether a child reads it, that a link out of Wikipedia leads
nowhere, Alt+Left to go back, and the picture. README's list.
architecture.md section 8: a *Wikipedia* row (D85, D87). roadmap.md
phase 4: `- [x] Wikipedia, a door to the encyclopedia (4.14, D87).`

**Done when.** The session test passes in both languages, the search works
and the pictures show each language's front page.

### 4.15 — Closing — S

- The roadmap's phase 4 lines as the steps wrote them; architecture.md
  section 8's date line says its rows were verified on this plan's date.
- The battery, whole, once, detached; its report read; every picture it
  refreshed committed in both languages; a failure that is a test's own
  fixed and that test run alone.
- The user guide's section 9 read whole in each language: the modules in
  the order a child would meet them, GCompris, Tux Typing, ScratchJr,
  Blockly Games, Scratch, TurboWarp, BASIC, CodeCombat, Wikipedia; its
  introduction saying what a door to a website is.
- The final message to the owner, in Spanish: what was built, what each
  door reaches and keeps out, what the owner must decide (the website's
  list; a CodeCombat account for the children), how to try each module on
  the MacBook, step by step, and whether to push.

## 6. Risks

- **wwwBASIC's keyboard and node bindings are the one thing not yet
  seen working.** The two hours at the start of 4.10 settle it before
  anything is built on it; a *no* goes to the owner, with what failed,
  and the agent does not write an interpreter instead. If 4.10 runs
  long, the guide's first part may stop at chapter 8 in its commit and
  the rest join 4.11, as long as every chapter shipped runs.
- **A site that changes.** CodeCombat's hosts are read from the site as
  it is; a new host one day shows as a blocked page or a missing picture,
  and the fix is the manifest's `hosts`, a one-line change and a package
  version. The guide says what a blocked page means.
- **The proxy flag and Chromium's future.** `--proxy-server` and
  `--proxy-bypass-list` are command-line equivalents of a product
  feature, not test flags, and have been stable for years; the policy's
  allowlist stands behind them whatever happens to them.
- **A trigger that does not fire** leaves a stale policy that refuses the
  new module's site: the module opens on Chromium's blocked page. The
  acceptance checks of 4.12 catch it on the acceptance machine before any
  family does.
- **The books' ownership.** The rule in section 3 is the line: method,
  order and spirit, never their words, programs, stories, character or
  pictures. A doubt about a listing is settled by writing it again from
  the idea, not from the page.
