# Phase 4e plan — a photography guide for a child with a real camera, and the Modules page put right

A learning module that is a book: **Photography**, a guide of thirty
chapters for a child of eight or nine who has a camera in their hands,
from the box with a hole that every camera still is, through the three
knobs of exposure, how the camera measures light, its modes and working
in manual, focus and depth, to composition and light, with things
to try at every step, photographs that show each effect, drawings of what
the camera's screen shows, and Kidux's penguin as the teacher. It is
built like BASIC's guide (basic.md), without the machine beside it, and
it names one camera, the Olympus XZ-2, as its worked example, saying each
time that other cameras have the same thing under other names. And two
faults of the panel's Modules page, seen by hand on the MacBook, go first
(roadmap, phase 4). This plan is how. It follows phase-4d-plan.md's rules
and D93: a commit per step, partial tests while building, the whole
battery only for the release, every user-facing word through i18n in both
languages, a package's new version at its first change and `~dev` builds
of it until the owner tries the work and says yes.

Section 5 records what the owner decided on 2026-10-16, which the steps
follow, and the questions still open, which the owner answers before the
step that needs each.

## 1. Steps

| Step | What | Size |
|---|---|---|
| 4.27 | The Modules page: Remove keeps its place, and a module that is only a folder | M |
| 4.28 | The module's skeleton: package, page, the guide's conventions, tests, the first chapter | L |
| 4.29 | The pictures: drawings, the owner's photographs, the free ones, their credits | M |
| 4.30 | Part 1, chapters 1–4: light and the box | M |
| 4.31 | Part 2, chapters 5–15: exposure, metering and the modes | L |
| 4.32 | Part 3, chapters 16–20: focus and depth | M |
| 4.33 | Part 4, chapters 21–27: making a picture | L |
| 4.34 | Part 5, chapters 28–30: after the click, and the words | M |
| 4.35 | Closing: the documents, the website, the roadmap, the release | S |

Each step is one commit, or a few when a part's chapters are better
committed two or three at a time; a step's commit message says which step
it is. The steps run in order. Every picture of the first release is a
free one or a generated one (section 5, decision 12): each part's step
finds or makes its own pictures as it writes its chapters, and the list
of section 3 says which, so that the owner can later replace any of them
with a photograph of their own. Nothing is released with a picture
missing (4.35).

## 2. The steps

### 4.27 — The Modules page: Remove keeps its place, and a module that is only a folder

**Cause.** Two things seen by hand on the Modules page (roadmap):

1. *Remove* pressed on a module below the fold scrolls the page to the
   top, so the question is out of sight, and the scrollbar still shows
   the page at its end until it is scrolled up and down again.
2. A module that is a directory under `/usr/share/kidux/modules/` with no
   package behind it (a test's stand-in, such as the canary, copied there
   by hand) answers *That did not work.* to *Remove*, since `apt-get
   purge` has nothing to purge.

**What is known of the first.** `ask_remove_module` draws the whole page
again with `confirm_remove` set (`panel.py`, `modules()`), and the view
builds a new scrolling room each time (`view.py`,
`_draw_panel_modules`): `keep_place(old, new)` connects to the new
adjustment's `changed` signal and sets the old value back once the room
is tall enough, and `_remove_question` makes *Cancel* the widget to focus
(`self._focus = cancel`). Two things can put the page at the top in spite
of `keep_place`: the focus grab on *Cancel*, which GTK's scrolled window
follows (D63's "following the keyboard's focus") with an allocation not
yet made, so that it scrolls to where the row was measured, 0; or
`keep_place` disconnecting after its one `set_value`, before a later
layout pass of the same draw changes the adjustment's bounds again. A
scrollbar that shows the end while the content shows the top is the sign
of a value set during layout without the bar being drawn again. Which it
is, is found on the machine, not guessed.

**Work, first fault.**

1. Reproduce on the quick loop's machine (`tests/run vm up 15`, which
   leaves the canary in place): copy the canary's directory under five
   more names (`robin`, `wren`, …, each with its own `id`), so that the
   installed list is taller than the room at 1280×800, open the panel's
   Modules page, Tab to the last row's *Remove*, press it. Log, for this
   investigation only, the adjustment's value, upper and page size at
   each stage (`keep_place`'s `changed`, the focus grab, after the first
   frame), and read the log.
2. Fix it where the log says. The two ways known, the smaller first:
   - **Scroll to the row after layout**, with GTK 4's
     `Gtk.Viewport.scroll_to(widget)` (trixie's 4.18 has it) on the
     question's widget once the room has had its first allocation (a
     `map` or a tick callback on the room), and keep `keep_place` for
     every other redraw; the focus grab moves to the same moment, so that
     GTK does not scroll for it before the layout is real.
   - **Replace only the row**, as the progress bar is already followed in
     place (`_progress_followers`): when the page drawn again differs
     from the one shown only in a row's state (`confirm_remove`, a row's
     `job`), swap that row's widgets inside the grid that is already on
     screen, and draw nothing else again; the room, its adjustment and
     its scrollbar never change. More code, no race.
   The view logs `modules room kept at <value> of <upper>` once a redraw
   settles, so that a test can read it.
3. The question row must be in view after *Remove*, with the page where
   it was, and the scrollbar true to the content; after *Cancel* the
   page is still where it was.

**Work, second fault.** The owner's words: the page should say what the
module is, and remove the directory or say how to. So:

1. `kidux.modules.Module` (kidux-common) gains `package: str | None`:
   `kidux-module-<id>` when `/var/lib/dpkg/info/kidux-module-<id>.list`
   exists, since a module's id is also its package's name after
   `kidux-module-` (modules.md, section 1); `None` otherwise. A stat, not
   a `dpkg-query`, because the panel reads every manifest at every
   redraw. `Modules1.List` and the panel's rows carry it.
2. **The panel** (kidux-greeter): a row whose module has no package says
   so after its description, in the small letters *Needs windows* uses:
   *A folder, not from a package.* (new
   words, both languages). Its *Remove* asks *Remove the folder <name>?
   The children's own files stay.* instead of the usual question.
3. **The update runner** (kidux-daemon's `kidux-update`): `remove
   kidux-module-<id>` of a package dpkg does not have installed, whose
   manifest directory `/usr/share/kidux/modules/<id>/` exists, removes
   that directory and writes the Chromium policy again, as a package's
   removal triggers it (`/usr/libexec/kidux-chromium-policy`, when it is
   there), and says `done:removed`. It is the same job as a package's
   removal, with the same rules (`SessionActive`, `Busy`), the same
   audit line, `module removed`, and the same `ModulesChanged`. The
   daemon cannot do it itself: its unit's system is read-only
   (`ProtectSystem=strict`), and `kidux-update` runs as root in a unit
   of its own for this. A module that is neither a package nor a
   directory is purged as now, and apt says it is not there. daemon.md
   section 13 says so, and the decision goes to the log as D101,
   extending D100.
4. `kidux-common`, `kidux-greeter` and `kidux-daemon` each get
   their next number at their first change, dated by `ci/hours.py
   changelog-date <package>`, after reading each changelog on
   `origin/main` (the MacBook leaves all three alone meanwhile: section
   5, decision 9).

**Tests.**

- `tests/session/15-modules.py` gains: with stand-ins enough for the room
  to scroll, *Remove* pressed by keyboard on the last row leaves the
  question in view, read from the view's `modules room kept` line and
  from the picture (the question's *Remove* button, in its destructive
  colour, in the lower half of the screen); *Cancel* leaves the page
  where it was. The stand-ins are removed at the test's end, as the
  canary is.
- `tests/acceptance/08-modules.sh`: `kidux-as remove canary` on the
  stand-in answers `removed` and the directory is gone, before the
  check that removes it by hand (which then stands on a fresh copy).
- kidux-common's unit tests: `Module.package` for a packaged id and a
  bare directory, with `root=` as the other reader tests use it.
- kidux-greeter's: the row's note and the folder question in the
  screen's data; kidux-daemon's: `kidux-update remove` of a bare folder,
  run against a fake modules root and a fake `dpkg-query` and `apt-get`
  on its `PATH`, removes the folder and says `done:removed` without
  calling `apt-get`, and of a package still calls `apt-get purge`.
- The quick loop: `vm push kidux-common kidux-daemon kidux-greeter`,
  `vm test 15`, and the owner looks at the page over VNC.

### 4.28 — The module's skeleton

**Cause.** The guide needs a page to live in before a word of it is
written, and the page's conventions decide how every chapter is written;
both are fixed here, with the first chapter in both languages as the
reference for the rest (it is already in the tree,
`content/{en,es}/01-a-box-with-a-hole.md`, written with this plan).

**Work.**

1. `packages/kidux-module-photography/`, started by copying
   kidux-module-basic and taking the machine out: `module.toml` (id
   `photography`, name *Photography*, ages 8 to 12, no
   `recommended_before`, `launch = { webapp = "photography" }`, no
   `hosts`, no settings), `icon.svg` (a camera drawn like the avatars:
   Night body, Snow lens ring, Sun shutter button, on the Sky circle),
   `debian/` (version `0.1.0`, dated by `ci/hours.py changelog-date
   kidux-module-photography`; `control` as basic's without Node and
   wwwBASIC, its description an adult reads: *Kidux learning module:
   Photography, a guide for a child with a real camera*; the
   `XB-Kidux-` fields by `tests/project/module-fields.py --update`;
   `copyright`, section 4 below), `po/`, `webapp/`, `drawings/`,
   `pictures/`, `content/en/`, `content/es/`, `tests/`.
2. **The page**, `webapp/`: `page.py` writes `index.html` at build time
   from `index.html.in`, every language's words and chapters in it, as
   basic's does (its docstring names the conventions below);
   `guide.js` is basic's guide alone: one chapter at a time, *Back*,
   *Chapters*, *Next*, the chapter remembered in `kidux-photography-chapter`,
   and nothing of the editor; `style.css` is the guide's half of basic's
   made whole: one column of at most 72 characters of Andika at 20 px,
   centred on Cream, the pager sticky at the top, pictures as wide as
   the column and no taller than 60 % of the window. The page is served
   under `/photography/` with its pictures beside it,
   `/photography/pictures/<name>.jpg`, which kidux-webapps already serves
   as `image/jpeg`.
3. **The conventions** a chapter is read with, seven, and no others
   (`page.py` keeps each in a regular expression, as basic's does;
   test_guide.py holds the page to them):
   - **A quotation** is the mascot speaking: the chick beside a bubble,
     in the pose its first word names, `[think]`, `[point]`, `[cheer]`,
     `[oops]`, or standing. Basic's mascot drawings are copied into
     `drawings/` as they are; the mascot is the teacher the owner asked
     for, and it is Kidux's penguin, never Tux.
   - **`::: try`** to **`:::`** is *Try it*: what the child does with the
     camera now, as an ordered list of short steps, in a box with a Sun
     left border and the heading from the words (*Try it* / *Pruébalo*).
   - **`::: camera`** to **`:::`** is the camera box: a Sky box headed
     *On the Olympus XZ-2* (the camera's name is not translated; the rest
     of the heading is) whose first line, from the words and the same in
     every box, says *Other cameras have the same thing under other
     names; chapter 3 says how to find it.* Then the chapter's own text
     for this camera: which button, which dial, which menu, with the
     manual's page in brackets for the adult, as `(manual, p. 16)`.
   - **`::: adult`** to **`:::`** is the box for the adult, shut until it
     is opened, as basic's.
   - **`::: compare`** to **`:::`** holds two to four pictures,
     photographs or drawings, which are shown side by side, each with
     its caption under it: the same scene at f/1.8 and f/8, a tap at
     1/1000 and 1/8, the screen in P, A, S and M.
   - **A drawing**, `![words](name.svg)`, from `drawings/`, put into the
     page as it is, its words read to those who cannot see it. Drawings
     are flat, in the brand's colours, with no words in them, with one
     exception, section 3: a drawing of the camera's screen shows the
     camera's own glyphs and numbers, `P`, `125`, `F5.6`, `+0.0`, `ISO
     200`, which are the same in every language.
   - **A photograph**, `![caption](name.jpg)`, from `pictures/`, as a
     figure with its caption under it and, after the caption in smaller
     letters, its credit from `pictures/pictures.toml`: *Photo: <author>,
     <licence>*, the word from the words, the rest as the file says; a
     photograph of Kidux's own is credited *Photo: Kidux*. The
     Markdown title `"thirds"`, `![caption](name.jpg "thirds")`, draws
     the rule-of-thirds grid over the photograph in CSS, two lines each
     way in Snow at half opacity, so that the same photograph is shown
     with and without it.
   A chapter is `content/<lang>/NN-slug.md`, its first line its heading,
   its translation with the English file's hash in its front matter
   (`tests/project/content.py`), numbered in the page as basic's are.
4. **Tests**: `tests/test_module.py` (the manifest as the reader reads
   it, the version the changelog's, the catalogue complete) and
   `tests/test_guide.py`: every language has the same chapters; the page
   holds every language's words and chapters; the seven conventions
   render as above and nothing of their marks survives into the page;
   every drawing and every photograph a chapter names is there, every
   photograph named is in `pictures.toml` and every entry of
   `pictures.toml` is named by a chapter; every photograph is a JPEG no
   wider than 1400 pixels on its long side and under 400 kB; a
   `compare` block holds two to four pictures. Acceptance
   `tests/acceptance/21-module-photography.sh` (the present `21-no-key-no-archive.sh`
   becomes `22-`, as it has moved before): installs through the daemon
   with kidux-webapps, the manifest, icon, Spanish catalogue and page in
   place, the server answers the page with its title and a Spanish word
   of it, and a picture as `image/jpeg`, listed for a child switched off,
   removed without a trace. Session `tests/session/37-module-photography.py`:
   installed through the daemon, switched on for Leo, opened from its
   tile by keyboard (Chromium's window titled *Photography* in the
   child's language, above the bar), the first chapter on screen with
   its drawing and a photograph (colour shares: Cream around, a region
   that is not Cream where the picture is), *Next* by keyboard changes
   the page (`machine.changes`), the picture `module-photography` taken
   on the first chapter, Alt+F4 closes it, Leo logs out, the daemon
   removes it. `tests/lib/doc-screenshots.txt` gets
   `module-photography module-photography.png`; `ci/build-all.sh` lists
   the package after `kidux-module-gmail`.
5. The quick loop: `tests/run unit kidux-module-photography`, `vm up 04`,
   `vm push kidux-module-photography`, `vm test 37`, and the owner opens
   it over VNC.

### 4.29 — The pictures

**Cause.** The guide teaches with pictures, and three kinds are needed:
drawings of ideas and of the camera's screen, photographs that show an
effect, and photographs of the camera itself. Where each comes from, and
under what licence, is decided once (D102, section 5).

**Work.**

1. **Drawings**, SVG in `drawings/`, drawn by hand in the brand's style
   (flat shapes, the brand's colours, nothing thinner than four units),
   each saying in a comment which chapters use it. Three families: ideas
   (`camera-obscura.svg`, `lens-focus.svg`, `camera-parts.svg`,
   `holding.svg`, `aperture-blades.svg`, `sensor-pixels.svg`,
   `exposure-seesaw.svg`, `metering-patterns.svg`, `mode-dial.svg`,
   `flash-sync.svg`, `depth-of-field.svg`, `perspective.svg`,
   `background-pole.svg`, `background-moved.svg`, `heights.svg`,
   `light-sides.svg`, `story-strip.svg`), the camera's controls
   (`camera-top.svg`, `camera-back.svg`: the XZ-2's outline, with the
   controls the chapter speaks of in colour and the rest in Ink, nothing
   written), and the camera's screen (`screen-half-press.svg` with the
   green AF target, `screen-p.svg`, `screen-a.svg`, `screen-s.svg`,
   `screen-m.svg`, `screen-compensation.svg`, `screen-histogram.svg`,
   `screen-too-dark.svg` with the blinking `60" F1.8`,
   `screen-metering.svg`, `screen-live-guide.svg`,
   `screen-flash-modes.svg`, `screen-af-all.svg`, `screen-af-single.svg`,
   `screen-af-group.svg`, `screen-face.svg`, `screen-mf.svg`,
   `screen-playback-info.svg`): a dark rectangle with the glyphs the
   XZ-2 shows where it shows them, drawn afresh, never traced from the
   manual's pictures, which are Olympus's. The mascot's drawings are
   BASIC's.
2. **Photographs** in `pictures/`, JPEG, 1400 pixels on the long side,
   quality 82, metadata stripped (a photograph of the owner's carries the
   family's camera serial and GPS otherwise), each under 400 kB, by
   `pictures/prepare.py <source> <name>` (a development-time tool, run by
   hand, which crops, and changes a photograph as a camera would, in
   linear light: `--stops`, `--light`, `--grey`, `--red-filter`). `pictures/pictures.toml` has one table per picture, by its
   file's name: `author`, `source` (the file's page for a free one,
   `owner` for the owner's), `licence` (`CC0-1.0`, `CC-BY-2.0` to
   `CC-BY-4.0`, `CC-BY-SA-2.0` to `CC-BY-SA-4.0`, `public-domain`, or
   `GPL-3.0-or-later` for Kidux's own), and `made` when the picture is not the
   file as it is (cropped, one half of a comparison, given more or less
   light, its colours changed).
   `debian/copyright` lists every picture that is not Kidux's by name,
   author and licence, with the licence texts; the README's licence
   paragraph says the module's guide shows photographs by other people
   under Creative Commons licences and in the public domain, credited
   where they are shown.
3. **The owner's photographs, later.** The first release has none
   (decision 12). The list of section 3 is what to shoot when the owner
   wants to replace a picture: with the XZ-2 itself where the picture is
   of its effect, with another camera or a phone where it is of the
   camera; the owner copies them under `build/photos/` (not in the
   repository), `prepare.py` makes the guide's files from them, and the
   entry in `pictures.toml` changes to `source = "owner"`. No child's
   face in any picture committed: toys, hands, backs of heads,
   silhouettes, the penguin plush, an adult who agrees.
4. **Free photographs** first: Wikimedia
   Commons first, CC0, CC BY, CC BY-SA or public domain only, the file's
   page saved as the `source`; the historical pictures are all public
   domain (section 3 names them). The candidate list of section 3 is
   checked file by file at download time: the licence on the page, the
   author's name, and that the picture shows what the chapter says.
5. **Generated pictures, last.** D102: a guide that teaches what a
   camera does shows photographs a camera took wherever there is one,
   since a generated picture of "shallow depth of field" did not come
   through a lens and may lie in its details. Where neither the owner
   nor Commons has the effect, `pictures/generate.py <name> <prompt
   file>` asks Gemini's image model for it, with the key read from the
   file `KIDUX_GEMINI_KEY_FILE` names, which the owner keeps outside the
   repository (the key never an argument, never logged, never copied),
   and writes the result through `prepare.py`; the owner
   looks at every generated picture before it is committed, and refuses
   one whose physics is wrong (a sharp background at f/1.8, a frozen
   tap at 1/8). `pictures.toml` records `author = "generated"`, the
   model, and the prompt file, which is kept beside it in
   `pictures/prompts/`; its licence is the project's, `GPL-3.0-or-later`, and
   its credit reads *Picture made by a computer*, so that a child is
   never told a generated picture is a photograph.

**Tests.** `test_guide.py`'s checks of 4.28 (every picture present,
credited, within size); `tests/project/content.py` for the chapters;
lintian on the package (a JPEG is a static file; the build is
reproducible as any other). The owner looks at every photograph in the
page over VNC before the part that uses it is committed.

### 4.30 — Part 1, chapters 1–4: light and the box

Chapters 1 to 4 of section 3, English first, then Spanish, each chapter
read against the manual's pages its camera box names; `tests/project/content.py
--update`; `tests/run unit kidux-module-photography`; `vm push`, `vm test
37`; the owner reads them over VNC, in both languages (`KIDUX_VM_LANGUAGE=en`
for the English machine when they want to see it). One commit for the
part, or one per chapter when a chapter is long.

### 4.31 — Part 2, chapters 5–15: exposure, metering and the modes

As 4.30, chapters 5 to 15. This part has the most pairs of photographs
(exposure −2/0/+2, 1/1000 against 1/8, ISO 100 against 6400, light trails,
light painting, the flash's frozen splash, slow sync): each pair is the
same scene with the one setting changed, and a generated pair is asked
for as one picture split in two, so that nothing but that setting
differs.

### 4.32 — Part 3, chapters 16–20: focus and depth

As 4.30, chapters 16 to 20.

### 4.33 — Part 4, chapters 21–27: making a picture

As 4.30, chapters 21 to 27; the rule-of-thirds overlay is first used
here, on the owner's and the free photographs alike.

### 4.34 — Part 5, chapters 28–30: after the click, and the words

As 4.30, chapters 28 to 30; chapter 30 is the glossary, alphabetical in
each language on its own, since the words' order differs.

### 4.35 — Closing

1. `docs/dev/photography.md`: the module's document, as basic.md: what
   it is made of, the page, the guide's conventions, the chapters' table,
   the pictures and their credits, its words, its tests. `docs/dev/README.md`
   lists it, and names this plan as the current one.
2. The user guide, `docs/en/user-guide.md` and `docs/es/user-guide.md`:
   a section **Photography** after Gmail, in the order the guide keeps,
   with what the module is, what the child needs (a camera; any camera,
   the Olympus XZ-2 shown as the example), what the chapters cover, and
   its picture, `module-photography.png`, which the release run takes.
   README.md and README.es.md: the module in the list, and the licence
   paragraph as 4.29 says.
3. `docs/dev/roadmap.md`: the phase 4 lines for this work ticked, the
   two Modules faults' line ticked, micro:bit and the wwwBASIC pull
   request left as they are. `docs/dev/architecture.md`: D102 and D101
   in the decision log, section 8's table a row for Photography (ours;
   nothing of anyone else's but the credited photographs).
4. Then the owner tries the whole module on the machine left up, over
   VNC, in both languages (their acceptance test), and asks for the
   release, which happens on `kidux` (CLAUDE.md, "More than one
   development machine"): the battery once, `--release`, promotion,
   publication, each on the owner's word.
5. **After the release**, once its run has taken
   `docs/images/<language>/module-photography.png`: the website's card,
   in `site/page.html` as the others have one, with that picture of the
   page, and its words in `site/en.toml` and `site/es.toml`
   (`modules.photography`), `tests/project/site.py` holding them to the
   guide's heading; the site is built from that picture, so the card
   cannot come before it (decision 13).

## 3. The course

### Who it is for, and how it teaches

A child of eight or nine who reads well, with a real camera they are
allowed to use, and an adult nearby for the dark room, the candle and
the street at dusk. The course takes the camera seriously: it gives the
real numbers (1/1000, f/1.8, ISO 6400), the real reasons (light goes
straight; a smaller hole makes a sharper picture and a darker one; the
f-number is a fraction of the lens's length, which is why a bigger number
is a smaller hole), and the real history (Niépce's eight hours, the man
having his shoes shined in Daguerre's Paris, Muybridge's horse), in
short sentences and the child's world. Every chapter is one idea, tried
on the camera the same day. Each has: the idea, with its drawing or
photographs; the mascot's prompts (`> [point]`, `> [think]`); *Try it*,
the experiment, in steps; the camera box when the idea is a control; a
*Keep trying* list of variations; and *For the adult*, which says what
the chapter teaches, what to help with and what to watch for.

The camera is the Olympus XZ-2 (manual, 2012: a 1/1.7-inch sensor of 12
million pixels, a 6–24 mm lens that sees as a 28–112 mm one does, f/1.8
to f/2.5, a 3 EV ND filter, shutter 1/2000 to 60 s and bulb to 16
minutes, super macro from 1 cm, ISO 100 to 12800, a touch screen, a
pop-up flash; p. 92). Its controls, named as the manual names them: the
**mode dial** (iAUTO, P, A, S, M, C1, C2, SCN, ART; p. 8); the **shutter
button** and the **zoom lever** around it (p. 9, 10); the **control
ring** on the lens and the **sub dial** around the arrow pad (p. 2, 3);
the **lever** and **Fn2** on the lens's side, **Fn1** and **INFO** on the
back (p. 3); the **arrow pad**: up is exposure compensation, right is
flash, down is sequential shooting, self-timer and erase, left is the AF
target (p. 3); the **flash switch** that raises the flash (p. 24); the
**monitor**, which tilts and is touched (p. 3, 33). What the manual does
not have, the course does not claim: no Live Time, no Wi-Fi of its own.

In P, A and S the camera shows `125 F5.6` at the bottom of the screen,
the shutter speed and the aperture, with `ISO` at the left and the
exposure compensation after them (p. 8, 15–17): the screen drawings show
exactly this, so that the child knows what to look for.

### The chapters

Titles in English and Spanish; the slug names the file. **Idea** is what
the chapter teaches and how; **Try** the experiment; **Pictures** the
drawings (D), the owner's photographs (O), the free ones (C), the
generated ones (G) and the screen drawings (S), by the names `drawings/` and `pictures/` use;
**Camera** what the camera box says, with the manual's pages; **Adult**
the gist of the adult's box.

**Part 1 — Light and the box**

1. **A box with a hole** / **Una caja con un agujero**
   (`01-a-box-with-a-hole`, written). *Idea:* light goes in straight
   lines; a hole in a dark box draws the world upside down on the far
   wall, because the light from the top can only reach the bottom; this
   has been known for two thousand years (Mozi, Alhazen), and a camera
   is still that box. *Try:* a darkened room with a small hole in
   cardboard over the window, a white sheet opposite: the street upside
   down; or a shoebox with a pinhole and tracing paper. *Pictures:* D
   `camera-obscura.svg`; C `frisius-1545.jpg`; C `pinhole-box.jpg`.
   *Camera:* the XZ-2 is that box with a glass in the hole; the hole is
   behind the lens; the sensor is the wall (p. 2, 92). *Adult:* the
   experiment needs a really dark room and ten minutes for the eyes; why
   the image is dim and why it is upside down.
2. **Why a lens** / **Para qué sirve una lente** (`02-why-a-lens`).
   *Idea:* a bigger hole makes a brighter picture but a blurred one,
   because each point of the world becomes a patch; a lens bends the
   light so that a whole patch meets again at one point: that is focus,
   and it happens at one distance only, which is why a camera focuses.
   The eye has a lens too. *Try:* a magnifying glass projects the window
   onto a sheet of paper; move it until the window is sharp; measure the
   distance; try a nearer thing. *Pictures:* D `lens-focus.svg`; G
   `magnifier-window.jpg`. *Camera:* the lens is the glass tube at the
   front; the zoom lever makes it longer and shorter (p. 10); the cap
   and the cloth (p. 82). *Adult:* the magnifying glass and the sun:
   never focus the sun on anything; the image on the paper is the same
   the sensor gets.
3. **What a camera is made of** / **De qué está hecha una cámara**
   (`03-what-a-camera-is-made-of`). *Idea:* lens, aperture (a hole that
   opens and closes, like the pupil), shutter (a door that opens for a
   moment), sensor (millions of tiny buckets that count light, 12
   million on this one), the screen, the memory card; and how to find
   each control on any camera: a dial with letters, a ring or wheel for
   the numbers, a button with a lightning bolt, a button with a flower
   for close-ups. *Try:* a tour of the child's own camera with the
   drawing beside it; find the five things; switch it on, take one
   photograph of anything, look at it. *Pictures:* D `camera-parts.svg`;
   C `xz2-front.jpg`; D `camera-top.svg`; D `camera-back.svg`. *Camera:*
   names of parts (p. 2, 3): mode dial, shutter button, zoom lever,
   control ring, lever and Fn2, flash switch, the arrow pad's four jobs,
   the sub dial, the tilting touch screen, the card and battery door (p.
   5). *Adult:* the card and the battery; charging (p. 6); the strap
   round the wrist always.
4. **Hold it still, press gently** / **Sujeta firme, pulsa suave**
   (`04-hold-it-still`). *Idea:* most blurred pictures are the camera
   moving, not the subject; elbows in, breathe out, the shutter button
   has two steps: half-way focuses and shows a green square and beeps,
   all the way takes the picture; wait for the green; keep the horizon
   straight; the self-timer and a table are a tripod. *Try:* ten
   photographs of the same thing: five pressing fast, five the right
   way; look at them zoomed in on the screen. *Pictures:* C
   `shaken-lights.jpg`; C `shaken-toy.jpg`; D `holding.svg`; S
   `screen-half-press.svg`. *Camera:* half-press (p. 9), the AF target
   turning green (p. 9, 14), the stabilizer (p. 36), self-timer 2 s and
   12 s (p. 27), the level gauge (p. 69), zooming in on a picture to
   check it (p. 11, 29). *Adult:* the grip for small hands; the beep's
   volume (p. 60).

**Part 2 — Exposure: the three knobs, the meter and the modes**

5. **Too dark, too bright** / **Demasiado oscura, demasiado clara**
   (`05-too-dark-too-bright`). *Idea:* a photograph is a bucket of
   light: too little and it is dark, too much and it is white; the
   camera guesses the right amount, and guesses wrong with snow, a black
   cat or a window behind someone; the +/− knob tells it "brighter" or
   "darker"; what the histogram is, gently (a pile of all the dark
   pixels on the left and the bright ones on the right). *Try:* P mode;
   the same toy at −2, 0 and +2; a white sheet of paper at 0 and at +1;
   a dark jumper at 0 and −1. *Pictures:* C `exposure-minus2.jpg`; C
   `exposure-0.jpg`; C `exposure-plus2.jpg`; S
   `screen-compensation.svg`; S `screen-histogram.svg`. *Camera:* mode
   dial to P (p. 15); the sub dial changes the exposure compensation, ±3
   EV (p. 23); INFO shows the histogram (p. 14); not available in iAUTO
   or M (p. 23). *Adult:* compensation is kept until it is put back to
   0; the words over- and under-exposed.
6. **The shutter: how long the door is open** / **El obturador: cuánto
   tiempo está abierta la puerta** (`06-the-shutter`). *Idea:* the
   shutter speed is a time: 1/1000 of a second freezes a jump, 1/15
   blurs a running dog, 2 seconds turns a fountain to mist; the numbers
   on the screen are the bottom of the fraction (`125` is 1/125; `2"` is
   two seconds); slow times need the camera still. Muybridge's horse,
   1878: the first time anyone saw that all four hooves leave the
   ground. *Try:* S mode; a tap running, at 1/1000 and at 1/8; a friend
   waving a hand at 1/500 and 1/15; cars from the window at 1/4 with the
   camera on the sill. *Pictures:* G `tap-fast.jpg`; G `tap-slow.jpg`; C
   `muybridge-horse.jpg`. *Camera:* mode dial to S; the control ring
   sets the speed, the sub dial the compensation; the scale
   2"←1"←15←60→100→400→1000 (p. 17); the aperture blinks when it cannot
   keep up (p. 17); 1/2000 to 60 s (p. 92). *Adult:* fractions of a
   second for a child who has not met fractions: "one second cut into a
   thousand pieces".
7. **The aperture: how wide the window** / **El diafragma: cómo de ancha
   es la ventana** (`07-the-aperture`). *Idea:* inside the lens a ring
   of blades opens and closes a hole; its size is said as an f-number,
   which is a fraction: f/2 is the lens's length divided by 2, a big
   hole; f/8 is divided by 8, a small one; so the small number is the
   big hole, which everyone gets backwards once; each step (1.8, 2.8, 4,
   5.6, 8) halves the light. The pupil of a cat at noon and at night.
   *Try:* A mode; look into the lens while turning the ring and watch
   the blades; the same scene at f/1.8 and f/8 and see how the shutter
   time changed to keep the brightness. *Pictures:* C
   `aperture-real.jpg`; D `aperture-blades.svg`. *Camera:* mode dial to
   A; the control ring sets the aperture, the sub dial the compensation;
   F2 ← F5.6 → F8 (p. 16); the ND filter when it is too bright even at
   f/8 (p. 15, 16, 65). *Adult:* why the number is a fraction, for the
   adult to answer the "why backwards" question again later.
8. **ISO: how hard the camera listens** / **ISO: cuánto se esfuerza la
   cámara en escuchar** (`08-iso`). *Idea:* when there is little light
   the camera can turn up the volume of what the sensor heard; ISO 100
   is quiet and clean, ISO 6400 is loud and grainy, like a radio turned
   up with the hiss; the grain is called noise; use the lowest ISO the
   light allows, and let AUTO choose when in doubt. *Try:* a dim room,
   the same toy at ISO 100 (long time, camera on the table) and at ISO
   6400 (short time, in the hand); zoom into both on the screen; where
   is the noise worst (the shadows). *Pictures:* D `sensor-pixels.svg`;
   C `iso-200.jpg`; C `iso-6400.jpg`. *Camera:* ISO in the live control,
   OK then up/down to the ISO row, left/right to choose, AUTO or
   100–12800 (p. 35, 44); the AUTO limit 1600 (p. 61, 90). *Adult:*
   noise and the noise filter (p. 61); ISO as the third knob before the
   three meet.
9. **The three together** / **Los tres juntos**
   (`09-the-three-together`). *Idea:* shutter, aperture and ISO each let
   in or add light in steps that double or halve (a *stop*), so the same
   brightness is reached many ways, and what changes is the side effect:
   blur, depth, grain; a table of equal exposures (1/500 f/2.8, 1/250
   f/4, 1/125 f/5.6 …); the camera's own guess at the brightness is the
   next chapter, and who chooses which of the three is the one after it.
   *Try:* P mode; turn the control ring and watch both numbers change
   together while the picture stays as bright (program shift); take
   three of the same scene at three of the pairs and compare the
   background and anything moving. *Pictures:* D `exposure-seesaw.svg`;
   S `screen-too-dark.svg`. *Camera:* program shift in P with the
   control ring, `Ps` on the screen (p. 15); the blinking numbers mean
   "I cannot" (p. 15–17). *Adult:* the stops table; this is the chapter
   to read twice.
10. **How the camera measures light** / **Cómo mide la luz la cámara**
    (`10-metering`). *Idea:* the camera does not know what it is looking
    at; it measures how bright the scene is and makes it come out as a
    middle grey, which is right for a garden and wrong for snow (grey
    snow) and for a black cat (grey cat); so it can be asked to measure
    in three ways: the whole picture, cleverly weighed (ESP), the middle
    more than the edges (centre-weighted), or one small spot only
    (spot), which is the way to measure a face against a bright window;
    the measurement is made when the button is half-pressed and kept
    while it stays down (exposure lock), and can be locked with a button
    to measure one thing and frame another. *Try:* P mode; a white sheet
    of paper filling the screen and a dark jumper filling it: both come
    out grey; a friend against a window with ESP and then with spot on
    the face; the histogram for each. *Pictures:* C `snow-grey.jpg`; C
    `snow-white.jpg`; D `metering-patterns.svg`; C
    `backlit-as-measured.jpg`; C `backlit-on-the-face.jpg`; S
    `screen-metering.svg`. *Camera:* live control (OK), the metering
    row: ESP, centre-weighted, spot, spot HI for something bright that
    must stay bright, spot SH for something dark that must stay dark (p.
    35, 42); metering at the AF target, `[···]+Metering` (p. 61);
    half-press locks it (p. 42); AEL on Fn1 (p. 65); the histogram, red
    where it is too bright and blue too dark (p. 14). *Adult:* "the
    camera wants grey"; why snow needs +1 to +2 and a black dog −1 (p.
    81).
11. **The camera's modes: who chooses** / **Los modos de la cámara:
    quién elige** (`11-modes`). *Idea:* the mode dial says who decides
    the three knobs. iAUTO: the camera decides everything, and its guide
    asks in words what you want (brighter, blur the background, show the
    movement); SCN: you say what it is (a portrait, sport, a sunset,
    fireworks) and it chooses for that; ART: the camera's filters; P:
    the camera chooses the pair and you may shift it, and set ISO, the
    flash and the +/−; A: you choose the aperture (how much is sharp),
    the camera the time; S: you choose the time (freeze or blur), the
    camera the aperture; M: you choose both, and the camera only tells
    you what it measured. Which to use: A when depth matters, S when
    movement matters, M when the light holds still (next chapter); C1
    and C2 keep your own settings. *Try:* the same moving thing (a
    swing, a tap) in iAUTO, A at f/1.8, S at 1/1000 and S at 1/8; look
    at the numbers each one chose. *Pictures:* D `mode-dial.svg`; S
    `screen-p.svg`; S `screen-a.svg`; S `screen-s.svg`; S
    `screen-m.svg`; S `screen-live-guide.svg`. *Camera:* the mode dial
    and what each letter is (p. 8); P (p. 15), A (p. 16), S (p. 17), M
    (p. 18); the live guide in iAUTO (p. 22); SCN (p. 20), ART (p. 19);
    C1, C2 (p. 48); which knob does what in each: the control ring and
    the sub dial (p. 16–18, 89). *Adult:* a child who understands A and
    S understands the whole of exposure.
12. **Working in manual** / **Trabajar en manual**
    (`12-working-in-manual`). *Idea:* in the other modes the camera
    measures again for every picture and can change its mind: a white
    shirt walks in and the whole picture goes darker, the sun comes in a
    window and the next one is different; in M nothing changes until you
    change it, so a series under the same light comes out the same, the
    snow stays white, the black cat black, and a panorama's pieces
    match; that is why M is the most reliable mode when the light is
    steady and can be measured: a room lit by lamps, a cloudy afternoon,
    a stage, the night. How: measure once on something middle (grass, a
    grey jumper, the palm of a hand in the light; or spot on the
    subject), set the time for the movement and the aperture for the
    depth, move one of them until the meter's scale is at 0, take a test
    picture and read its histogram, then leave it and take the pictures;
    measure again only when the light changes (a cloud, a lamp switched
    on, moving from sun to shade); and when not to: light that changes
    all the time, walking from inside to outside. *Try:* a room lit by a
    lamp; M; meter on a grey thing, set it, take ten pictures of a toy
    moving around the room and see they all match; do the same in P with
    a white sheet passing behind and see P change. *Pictures:* S
    `screen-m.svg`; S `screen-histogram.svg`. *Camera:* mode dial to M,
    the control ring sets the time, the sub dial the aperture (p. 18;
    the dials can be swapped, p. 89); no +/− in M (p. 18); ISO set by
    hand, not AUTO, so that it does not change by itself (p. 44); *Live
    View Boost* off, so that the screen shows how bright the picture
    will be (p. 60); the histogram after a test shot (p. 14, 28); BULB
    for longer than 60 s (chapter 13). The camera box checks against the
    manual what the screen shows as a meter in M before it says it, and
    says the histogram where the manual says nothing more. *Adult:* the
    habit of a test shot, and why a professional at a wedding church
    works in M.
13. **Light that moves: long exposures** / **La luz que se mueve:
    exposiciones largas** (`13-long-exposures`). *Idea:* with seconds of
    time, moving lights draw lines and moving people vanish; the first
    photograph of a person, Daguerre's boulevard in 1838, caught only
    the man standing still to have his shoes shined, because the others
    moved during the minutes; cars become ribbons, a fountain silk, the
    stars arcs. *Try:* dusk, the camera on a wall or a small tripod, S
    mode at 4 s then 8 s, the self-timer so that the finger does not
    shake it; a torch waved by a friend; bulb for the sky with an adult.
    *Pictures:* C `car-trails.jpg`; C `daguerre-boulevard.jpg`; C
    `silky-river.jpg`; C `star-trails.jpg`. *Camera:* S down to 60"; M
    and BULB, the shutter open while the button is held, up to 16
    minutes (p. 18); the bulb timer (p. 61); the stabilizer off on a
    tripod (p. 36); noise reduction after a long exposure takes as long
    again (p. 18, 61); the ND filter for silky water in daylight (p.
    65). *Adult:* outside at dusk together; a tripod or a bean bag;
    battery.
14. **Painting with light** / **Pintar con luz**
    (`14-painting-with-light`). *Idea:* in a dark room with the shutter
    open for ten seconds, a torch moved in the air draws a line in the
    picture, and the person holding it, who is dark, does not appear;
    write your name (backwards, facing the camera, or read it in a
    mirror); a candle carried in a circle; a sparkler, outside, with an
    adult; a torch on the ceiling for a moment "paints" the room. *Try:*
    room dark, camera on the table, M at 10 s, f/5.6, ISO 200,
    self-timer; draw a star with the torch; then a friend's name; then
    light a toy from the side for two seconds and see where the shadows
    fall. *Pictures:* C `light-painting-circle.jpg`; C
    `light-painting-orb.jpg`. *Camera:* M, shutter to 10" with the ring,
    aperture with the sub dial (p. 18); focus first with the light on,
    then MF so that the camera does not hunt in the dark (p. 43); the
    self-timer (p. 27). *Adult:* candles and sparklers only with an
    adult, outside for the sparkler; dark room, cables on the floor.
15. **The flash: light that freezes** / **El flash: la luz que congela**
    (`15-the-flash`). *Idea:* the flash is a burst shorter than a
    thousandth of a second, so whatever it lights is frozen even when
    the shutter is slow; it only reaches a few metres (never from the
    back of a stadium); it makes hard shadows and red eyes; in daylight
    a little flash fills the shadows of a face against the sun
    (fill-in); with a slow shutter it draws a trail and then freezes the
    person at the end (slow sync, second curtain). *Try:* water poured
    into a bowl, flash on, 1/60: every drop frozen; a face with the
    window behind, with and without fill-in flash; slow sync at 1 s with
    a friend swinging a torch, Sync 2. *Pictures:* C `flash-splash.jpg`;
    C `fill-flash-pair.jpg`; D `flash-sync.svg`. *Camera:* slide the
    flash switch to raise it; the right arrow shows the modes: AUTO,
    red-eye, fill-in, off, slow sync, manual (p. 24, 25); Sync 2 fires
    just before the shutter closes (p. 52); the flash's slowest shutter
    (p. 61); too close is too bright (p. 25). *Adult:* never a flash
    within a metre of a face, and not at babies (p. 94); red-eye and
    why.

**Part 3 — Focus and depth**

16. **Focus: where the camera looks** / **El enfoque: adónde mira la
    cámara** (`16-focus-points`). *Idea:* the camera focuses on what is
    under its little square, not on what you are thinking of; it has 35
    of them across the picture, and it can choose among all of them
    (often the nearest thing), among a group, or use the one you choose;
    half-press, green square, beep; focus and recompose: focus on the
    subject, keep the button half-pressed, move the camera, press; tap
    the screen where it should look; faces are found by themselves, and
    even the nearest eye. *Try:* two toys, one near and one far, with
    all targets: which did it choose? then a single target on the far
    one; focus and recompose a toy at the edge of the picture; tap the
    screen on each. *Pictures:* G `focus-near.jpg`; G `focus-far.jpg`; S
    `screen-af-all.svg`; S `screen-af-single.svg`; S
    `screen-af-group.svg`; S `screen-face.svg`. *Camera:* the left arrow
    (AF target) shows the squares, the arrows move one, INFO chooses
    all, single or group, 7 × 5 or 5 × 5 (p. 26); focus lock (p. 14);
    the home position on Fn1 (p. 59, 65); touch to focus, or to focus
    and shoot (p. 33); face and eye priority (p. 44); the AF illuminator
    in the dark (p. 59). *Adult:* why autofocus fails on plain walls,
    glass, bars and in the dark, and what to do (p. 80).
17. **Focus modes: once, following, by hand** / **Los modos de enfoque:
    una vez, siguiendo, a mano** (`17-focus-modes`). *Idea:* single AF
    focuses once and keeps it while the button stays half-pressed, for
    what stands still; continuous AF keeps focusing while it is held,
    for what comes towards you; tracking follows one thing across the
    picture; manual focus is you turning the focus yourself, for the
    dark, the glass, the light painting, or a picture taken over and
    over at the same distance; the screen magnifies to help. *Try:* a
    friend walking towards the camera: S-AF (focused where they were)
    against C-AF; tracking on a toy pulled on a string; MF on a toy
    behind a window pane, where AF focuses on the glass. *Pictures:* G
    `dog-c-af.jpg`; G `dog-s-af.jpg`; S `screen-mf.svg`. *Camera:* the
    live control's AF mode: S-AF, super macro, C-AF, C-AF+TR, MF (p.
    43); MF with OK held, then the sub dial or the arrows (p. 43); MF
    assist magnifies (p. 59); the lever and the control ring for MF (p.
    43, 59); metres or feet (p. 64). *Adult:* sequential shooting with
    C-AF for sport (p. 27, 43).
18. **Depth of field: how much is sharp** / **La profundidad de campo:
    cuánto sale nítido** (`18-depth-of-field`). *Idea:* only one
    distance is perfectly sharp; in front and behind, things blur
    slowly; with a wide aperture the sharp slice is thin and the
    background melts (bokeh, the blurry lights); with a small one the
    slice is deep and everything is sharp; getting closer and zooming in
    make it thinner too; portraits like it thin, landscapes deep. *Try:*
    A mode; a row of pencils, focus on the second, f/1.8 then f/8; a toy
    at 30 cm with the garden behind, at both; the fairy lights at night,
    out of focus on purpose. *Pictures:* D `depth-of-field.svg`; C
    `dof-small-aperture.jpg`; C `dof-wide-aperture.jpg`; C `bokeh.jpg`;
    C `shallow-focus.jpg`. *Camera:* A mode, the ring (p. 16); the
    manual's own sentence, larger apertures decrease depth of field;
    Preview on Fn1 stops the lens down to show it before the shot (p.
    65). *Adult:* the circle of confusion in a sentence: a point out of
    focus is a little disc, and a smaller hole makes smaller discs.
19. **Very close: macro** / **Muy cerca: macro** (`19-macro`). *Idea:*
    the world at one centimetre: a coin is a landscape, a leaf has
    roads; the sharp slice is now paper-thin, so the camera must not
    move; the camera's own shadow falls on the subject; light from the
    side shows the texture. *Try:* super macro on a coin, a leaf, a
    fabric, a flower, the skin of an orange; the same coin with light
    from the front and from the side. *Pictures:* C `macro-coin.jpg`; C
    `macro-leaf.jpg`; G `coin-front-light.jpg`; G `coin-side-light.jpg`.
    *Camera:* AF mode Super Macro, from 1 cm, zoom and flash off in it
    (p. 43); normal focusing from 5 cm at wide (p. 92). *Adult:* an
    insect is photographed, never caught; the lens an inch from a leaf
    needs the sun behind the child's shoulder, not the camera's.
20. **Zoom: near and far, and what it does to faces** / **El zoom: cerca
    y lejos, y lo que les hace a las caras** (`20-zoom`). *Idea:* wide
    fits more in and makes near things huge (a nose), long fits less and
    flattens, bringing the mountain closer to the house; so a portrait
    is taken from further back with the zoom in, never from arm's length
    at wide; digital zoom is only cutting the picture smaller. *Try:* a
    friend's face from 60 cm at wide, then from 3 m zoomed in, both
    filling the frame: compare the noses; the same street at both.
    *Pictures:* D `perspective.svg`; G `zoom-wide.jpg`; G
    `zoom-tele.jpg`. *Camera:* the zoom lever, W and T (p. 10); 28 to
    112 mm (p. 92); the digital tele-converter is a crop (p. 65).
    *Adult:* "zoom with your feet" and when not to.

**Part 4 — Making a picture, not taking one**

21. **Where to put things: the rule of thirds** / **Dónde poner las
    cosas: la regla de los tercios** (`21-rule-of-thirds`). *Idea:* cut
    the picture in three each way; the eye likes things on the lines and
    where they cross; the horizon on a line, not in the middle; eyes on
    the top line; a running dog with room in front; the camera can draw
    the grid on its screen. *Try:* the grid on; a tree centred and then
    on a third; a friend looking left placed on the right third, then
    the left. *Pictures:* C `thirds-landscape.jpg`; C
    `post-centred.jpg`; C `post-on-a-third.jpg`; C
    `thirds-portrait.jpg`. *Camera:* Displayed Grid in the custom menu,
    Display (p. 60); the aspect ratios 4:3, 16:9, 3:2 and 1:1 (p. 39).
    *Adult:* a rule to learn and then to break on purpose.
22. **Lines, frames and patterns** / **Líneas, marcos y patrones**
    (`22-lines-frames-patterns`). *Idea:* a road, a fence, a railing
    lead the eye into the picture; a doorway, a branch, a window makes a
    frame inside the frame; repetition (tiles, windows, a row of boots)
    is calm, and one thing breaking it is the picture; symmetry and
    reflections in puddles. *Try:* a street with the road leading in; a
    friend seen through a door; a pattern and then the same with one
    thing out of place. *Pictures:* C `leading-lines.jpg`; C
    `frame-in-frame.jpg`; C `pattern-break.jpg`; C `reflection.jpg`.
    *Camera:* none; a note that every camera does this. *Adult:* looking
    before lifting the camera.
23. **Backgrounds, and tidying up** / **Los fondos, y ordenar la foto**
    (`23-backgrounds`). *Idea:* the pole growing out of a head, the bin
    behind the dog, the mess on the table: the camera sees everything;
    three steps left, kneel, or come closer and fill the frame; empty
    space on purpose (negative space) lets a small thing be the picture.
    *Try:* a portrait of a friend; find the ugliest thing behind them;
    move until it is gone; then come so close that only the face fits.
    *Pictures:* G `pole-behind.jpg`; G `pole-aside.jpg`; C
    `negative-space.jpg`. *Camera:* none. *Adult:* this is the habit
    that makes the most difference.
24. **Point of view** / **El punto de vista** (`24-point-of-view`).
    *Idea:* a photograph from standing height is the one everyone takes;
    kneel to a dog's eyes, lie down for the worm's view, climb a chair
    for the top of the table; children are photographed at their height,
    not from above. *Try:* the same shoe from five heights; a toy from
    its own eye level with the room behind, giant. *Pictures:* D
    `heights.svg`; G `heights-above.jpg`; G `heights-eye.jpg`; C
    `worm-view.jpg`. *Camera:* the screen tilts, so the camera goes on
    the floor while the child looks from above (p. 3). *Adult:* knees
    and elbows get dirty; good.
25. **Light has a time and a side** / **La luz tiene una hora y un
    lado** (`25-light-time-and-side`). *Idea:* an hour after sunrise and
    before sunset the light is low, warm and soft (golden hour); at noon
    it is hard and shadows are black holes under eyes; clouds are a
    giant soft lamp; light from the front flattens, from the side shows
    shape, from behind makes a halo or a silhouette; shadows can be the
    picture. *Try:* a face by a window turned three ways; the same
    corner at noon and at dusk; a friend against the sunset as a shape
    only (−1 or −2 compensation). *Pictures:* G `noon.jpg`; G
    `golden.jpg`; D `light-sides.svg`; G `window-front.jpg`; G
    `window-side.jpg`; G `window-back.jpg`; C `silhouette.jpg`.
    *Camera:* exposure compensation for a silhouette (p. 23); spot
    metering for a face against the light (chapter 10); fill-in flash
    (chapter 15). *Adult:* never look at the sun through the camera or
    point the lens at it for long (p. 94, 95).
26. **Colour, and no colour** / **El color, y el blanco y negro**
    (`26-colour`). *Idea:* one strong colour against a calm one; red and
    green, blue and orange are friends across the wheel; why pictures
    indoors come out orange and in the shade blue (the light has a
    colour; white balance tells the camera which white is white); black
    and white takes colour away and leaves shape and light, and the
    camera's monochrome mode with a red filter darkens the sky. *Try:*
    AUTO and then Tungsten white balance under a lamp; a sheet of paper
    for one-touch white balance; Monotone on a face and on a cloudy sky
    with the red filter; the Pin Hole art filter and back to chapter 1.
    *Pictures:* C `complementary.jpg`; C `white-balance-lamp.jpg`; C
    `white-balance-right.jpg`; C `colour-houses.jpg`; C
    `monotone-houses.jpg`; C `red-filter-houses.jpg`. *Camera:* white
    balance in the live control, the presets with their kelvins (p. 38),
    one-touch (p. 39); picture mode Monotone and its B&W filters (p. 37,
    50); the art filters (p. 19). *Adult:* kelvins in a sentence;
    filters are fun and the course goes back to plain.
27. **People and moments** / **Las personas y los momentos**
    (`27-people-and-moments`). *Idea:* the moment before and after the
    smile; wait, then take five in a row and choose; candid against
    posed; ask before photographing someone, and stop when they say so;
    eyes sharp above all; nobody looks good from below the chin. *Try:*
    sequential shooting of a friend telling a joke, choose the one; a
    portrait with the eyes on the top third, focused on the near eye.
    *Pictures:* C `burst-strip.jpg`; C `portrait-eyes.jpg`. *Camera:*
    sequential shooting, 5 and 15 a second, from the down arrow (p. 27);
    face and eye priority (p. 44); Portrait picture mode (p. 37).
    *Adult:* asking permission, and photographs of other people's
    children.

**Part 5 — After the click**

28. **Looking at your photographs** / **Mirar tus fotos**
    (`28-looking-at-your-photographs`). *Idea:* the playback button;
    zoom in to check the eyes; the overall display shows the numbers the
    camera used (shutter, f, ISO), which is how you learn from a picture
    that went wrong; the histogram once more; delete the clearly bad
    ones, keep the doubtful ones for the big screen; protect the best;
    the card fills, the battery empties. *Try:* look at today's pictures
    with INFO on; find the fastest and the slowest shutter among them;
    delete three. *Pictures:* S `screen-playback-info.svg`. *Camera:*
    playback, index, close-up to 14× (p. 11, 29); INFO (p. 28); erase
    (p. 12), protect with Fn1 (p. 31); the card and the USB cable to a
    computer, as a disk (p. 76). *Adult:* copying the pictures off the
    card with the child, and where to keep them.
29. **Choosing, and telling a story** / **Elegir, y contar una
    historia** (`29-telling-a-story`). *Idea:* ten pictures, keep one:
    the one that says the most with the least; five pictures in a row
    tell a story (a day, a walk, a shoe's life); print one and put it on
    the wall; ten projects to go on with: an alphabet of shapes, shadows
    for a week, the same tree in four seasons, every door in the street,
    a portrait of each person at home doing what they do, water in all
    its states, a colour a day, the view from a window every hour,
    something tiny and something huge, your town upside down (chapter
    1). *Try:* pick a project and do its first five. *Pictures:* D
    `story-strip.svg`. *Camera:* slideshow (p. 32); print order and
    printing (p. 70, 72) for the adult. *Adult:* printing one picture is
    worth more than a thousand on a screen.
30. **The words of photography** / **Las palabras de la fotografía**
    (`30-the-words`). The glossary: aperture, autofocus, bokeh, bulb,
    camera obscura, composition, depth of field, exposure, exposure
    compensation, f-number, fill-in flash, focal length, focus, golden
    hour, histogram, ISO, lens, macro, metering, noise, overexposed,
    pixel, playback, rule of thirds, sensor, shutter, shutter speed,
    silhouette, stop, telephoto, tripod, underexposed, white balance,
    wide angle, zoom; each in two lines, with the chapter it is taught
    in. In Spanish the same words in their own order: apertura o
    diafragma, autofoco, balance de blancos, bokeh, bulb, cámara oscura,
    composición, contraluz, distancia focal, enfoque, exposición,
    compensación de la exposición, flash de relleno, gran angular, hora
    dorada, histograma, ISO, lente u objetivo, macro, medición, número
    f, obturador, paso, píxel, profundidad de campo, regla de los
    tercios, reproducción, ruido, sensor, silueta, sobreexpuesta,
    subexpuesta, teleobjetivo, trípode, velocidad de obturación, zoom.
    No pictures.

### The photographs each chapter needs

Each chapter's effect is shown by a free photograph from Wikimedia Commons
where one shows it clearly, and otherwise by a picture generated with
Gemini (D103): the same scene made twice or three times with only the one
thing the chapter teaches changed, each looked at for its physics before
it is kept. Where one free photograph had to stand for a pair, it is
changed as a camera would change it (`prepare.py --stops`, `--light`,
`--red-filter`, or two crops), and its credit says so. A picture of the
XZ-2 itself is a free one or a drawing, never a generated one.

The table is what the owner shoots to replace any of them, and what is
shown until then: with the XZ-2 where the picture shows its effect
(settings noted on a card in the shot, or read later from the overall
display, p. 28), with another camera or a phone where the picture is of
the XZ-2. **E** is essential, **N** nice to have.

| Chapter | Shown now | What to shoot | |
|---|---|---|---|
| 3 | `xz2-front.jpg`; drawings of the top and the back | The XZ-2 on a plain table in daylight, from the front with the cap off, from the top (mode dial, shutter button, zoom lever, ON/OFF, flash switch), from the back (screen on, showing `P 125 F5.6`) | E |
| 3, 7 | drawings | Close-ups: the control ring with the lever and Fn2; the mode dial set to A | E |
| 15 | none | The flash raised | N |
| 1 | `pinhole-box.jpg`, dim | The window's view on a wall in a darkened room (hard; try once; Gemini draws a projector's frame round it) | N |
| 2 | `magnifier-window.jpg`, generated | A magnifying glass projecting the window on paper | E |
| 4 | `shaken-lights.jpg`, `shaken-toy.jpg` | A lamp at 1/4 s hand-held and the same from the table | E |
| 5 | `exposure-minus2.jpg`, `exposure-0.jpg`, `exposure-plus2.jpg`, one photograph given −2 and +2 stops | A toy at −2, 0, +2 | E |
| 6 | `tap-fast.jpg`, `tap-slow.jpg`, generated | A running tap at 1/1000 and at 1/8 | E |
| 7 | `aperture-real.jpg`, another camera's blades | The lens's blades seen from the front at f/8 in A mode | N |
| 8 | `iso-200.jpg`, `iso-6400.jpg` | A dim room, ISO 100 from the table and ISO 6400 hand-held | E |
| 10 | `snow-grey.jpg`, `snow-white.jpg`; `backlit-as-measured.jpg`, `backlit-on-the-face.jpg`, each pair one photograph | Snow at 0 and at +1.7; a toy against a window with ESP and with spot | N |
| 13 | `car-trails.jpg`, `silky-river.jpg` | A street at dusk, 4–8 s, from a wall or window sill; a fountain or stream at 1–2 s with the ND filter | E, N |
| 14 | `light-painting-circle.jpg`, `light-painting-orb.jpg` | A torch drawing in a dark room, 10 s | E |
| 15 | `flash-splash.jpg`, `fill-flash-pair.jpg`; slow sync a drawing | Water poured into a bowl, flash on, 1/60; a toy or an adult against the window, without and with fill-in flash; a torch swung for 1 s with the flash on Sync 2 | E, E, N |
| 16 | `focus-near.jpg`, `focus-far.jpg`, generated | Two toys, focused on the near one, then on the far one | E |
| 17 | `dog-c-af.jpg`, `dog-s-af.jpg`, generated | A dog or a friend running towards the camera, in C-AF and in S-AF | N |
| 18 | `dof-small-aperture.jpg`, `dof-wide-aperture.jpg`, `bokeh.jpg`, `shallow-focus.jpg` | A row of pencils, focus on the second, at f/1.8 and f/8; fairy lights out of focus | E, N |
| 19 | `macro-coin.jpg`, `macro-leaf.jpg`; `coin-front-light.jpg`, `coin-side-light.jpg`, generated | Super macro; the coin lit from the front and from the side | E |
| 20 | `zoom-wide.jpg`, `zoom-tele.jpg`, generated | A toy from 40 cm at wide and from 4 m zoomed in, the same size in the frame, a building far behind | E |
| 21 | `thirds-landscape.jpg`, `post-centred.jpg`, `post-on-a-third.jpg` (one photograph cropped twice), `thirds-portrait.jpg` | A landscape with the horizon on the lower third; a tree centred and on a third | E |
| 23 | `pole-behind.jpg`, `pole-aside.jpg`, generated; `negative-space.jpg` | An adult with a pole behind their head, and the same three steps aside | E |
| 24 | `heights-above.jpg`, `heights-eye.jpg`, generated; `worm-view.jpg`; the three heights a drawing | A toy from above and at its own eye level | E |
| 25 | `noon.jpg`, `golden.jpg`, `window-front.jpg`, `window-side.jpg`, `window-back.jpg`, generated; `silhouette.jpg`; the three sides a drawing | A corner at noon and at dusk; the plush by a window front, side and back lit | E |
| 26 | `white-balance-lamp.jpg`, `white-balance-right.jpg`, `colour-houses.jpg`, `monotone-houses.jpg`, `red-filter-houses.jpg`, each set one photograph | Under a lamp at AUTO and at the lamp's white balance; a sky in colour and in Monotone with the red filter | E |
| 27 | `burst-strip.jpg`, four frames | Five frames of a sequence (hands, a toy falling, a dog) | N |
| 29 | a drawing of five pictures | Five pictures that tell a small story | N |

### The free pictures to look for

All checked at download for licence and author; public domain unless
said. Gemma Frisius, *De radio astronomico*, 1545, the first printed
picture of a camera obscura (ch. 1). Niépce, *View from the Window at Le
Gras*, 1826–27 (ch. 13, optional). Daguerre, *Boulevard du Temple*, 1838
(ch. 13). Muybridge, *The Horse in Motion*, 1878 (ch. 6). From Wikimedia
Commons under CC0, CC BY or CC BY-SA: star trails; light painting; a
long-exposure waterfall; leading lines (a road or a pier); a frame within
a frame; a repeating pattern with a break; a reflection in water; a
silhouette at sunset; complementary colours; negative space; a
rule-of-thirds landscape. Each file's page is the `source` in
`pictures.toml`; CC BY-SA pictures are credited with the licence named,
and `debian/copyright` carries the licence text.

## 4. The package and its licences

```
packages/kidux-module-photography/
  module.toml, icon.svg
  content/en/NN-slug.md, content/es/NN-slug.md     the chapters
  drawings/*.svg                                   ideas, controls, screens, the mascot
  pictures/*.jpg, pictures/pictures.toml           photographs and their credits
  pictures/prepare.py, pictures/generate.py        development-time tools, not installed
  po/kidux-module-photography.pot, po/es.po        the page's words
  webapp/page.py, index.html.in, guide.js, style.css
  tests/test_module.py, tests/test_guide.py
  debian/                                          control, rules, changelog, copyright,
                                                   source/format, lintian-overrides
```

`debian/copyright`: `Files: *` GPL-3.0-or-later, Kidux's own, the text and the
drawings included; then one stanza per photograph that is not Kidux's,
`Files: pictures/<name>.jpg`, its author and licence, and the licence
texts at the end (CC0-1.0 and each CC BY and CC BY-SA version used; a public-domain
picture says so with its date). The manual of the XZ-2 is Olympus's: the
course names its pages and never copies a sentence or a picture of it,
and the PDF lives outside the repository, under `build/`, where the
developer keeps it to check the camera boxes against (section 5).

## 5. Rules, decisions and open questions

**Rules.** As phase-4d-plan.md section 3, and D93. Nothing of the owner's
family goes into a picture: no child's face, no address, no name but the
children the tests already use. The manual is read, never copied. A
chapter's camera box is checked against the manual's page it names before
the chapter is committed. The release is made on `kidux`; this machine,
`hija`, builds and tests.

**Decided 2026-10-16 by the owner.**

1. **The work of this stretch, on `hija`**: the two Modules page faults
   and a new module, a photography course for a child of eight or nine,
   made like BASIC's guide, with chapters and *Next*; micro:bit waits
   for its hardware; the wwwBASIC pull request stays on the roadmap
   until it is approved.
2. **The course covers** the mechanics (camera obscura, lenses,
   exposure, ISO, shutter time, aperture), the optics (depth of field),
   composition (the rule of thirds, patterns) and working with light
   (long exposures, drawing with a torch or a candle, the flash and how
   it freezes), pleasant for a child of eight or nine and told properly,
   with some depth. It also teaches the camera's modes, automatic,
   program, aperture priority, shutter priority and manual, and why
   manual is the most reliable when the light can be measured and holds
   still for a good while, and how to work that way; the focus modes and
   the focus points; and how the camera measures light, its metering
   modes (chapters 10, 11, 12, 16 and 17).
3. **The Olympus XZ-2 is the worked example**, its buttons and menus
   shown in sections that say so and say that other cameras have the
   same under other names, and how to find them.
4. **Three kinds of pictures**: the mascot as the teacher, which is
   Kidux's penguin; photographs that show each chapter's effect; and
   pictures of what the child should see on the camera, icons, focus, f,
   exposure.
5. **The pictures are free ones found and downloaded, or made**; the
   owner offered a Gemini key, kept in a file on the server and never in
   the repository, if generation is needed.
6. **UAT on the machine left up**, over VNC, since nothing has to be
   tested from a clean installation; then the release.

7. **Generated pictures only where none other is found** (D102, 4.29):
   free photographs first, drawings of Kidux's own
   for ideas, and a picture generated with Gemini only for an effect
   neither the owner nor Commons has; `pictures.toml` says so, with the
   model and the prompt as its source. The key is a file on the
   development machine, outside the repository, and never in a commit.
8. **The module is called Photography**, *Fotografía* in Spanish.
9. **The MacBook is not touching `kidux-common`, `kidux-greeter` or
   `kidux-daemon`** during this work: 4.27 bumps all three here.

Decided 2026-10-16 by the owner, during 4.27.

10. **A module that is only a folder is said so, and the update job
    removes its folder** (D101): `kidux-update`, which runs as root in a
    unit of its own, and not the daemon, whose system is read-only to it.

**Proposed by this plan, for the owner's yes or no.**

11. **The user guide's section comes after Gmail**, in the order the
    guide keeps.

Decided 2026-10-16 by the owner, after 4.27.

12. **No photographs of the owner's for now**: every picture of the
    course is a free one found on the internet or one generated with
    Gemini, and the owner may shoot some of their own once the course
    is done, to replace what they choose.

Decided 2026-10-17 by the owner, during 4.35.

13. **The website's card comes after the release**, as Mail's and
    Gmail's did: it shows the picture of the page, as every card does,
    which the release run takes (4.35, item 5).
14. **Every picture should show its effect clearly** (D103): a generated
    picture also where a free photograph shows its effect faintly or
    across two different scenes, with Gemini's best image model; then
    Fable reviews the pictures again, and the owner asks for any to be
    made again.

**Open, answered before the step that needs it.**

1. The manual is at `build/XZ_2_INST_Eng.pdf` on the development
   machine (`build/` is ignored by git). The Gemini key is in a file the
   owner keeps there, outside the repository; `generate.py` is told where
   in `KIDUX_GEMINI_KEY_FILE` at the call, and has no default.
2. The README's sentence on the photographs' licences, as 4.35 wrote
   it: *The Photography guide shows photographs by other people, under
   Creative Commons licences or in the public domain, each credited
   where it is shown.* The owner reads it in the review.
