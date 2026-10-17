# Phase 4f plan — a guide beside a module, and the first guides

A child opens Kig and sees an empty canvas with forty tools; opens Step and
sees a blank world. Neither says what to do. This phase gives a module a
**guide**: lessons of Kidux's own, written for a child of ten to twelve
who reads, shown by the launcher in a pane beside the program, with steps
to follow, what the child should see, an idea to go on with, and
**missions**, files of the program's own half done, with what to try
written inside them. The pane is the launcher's, so it works the same for
a child without windows, where the program fills what the pane leaves,
and for a child with them. Then the guides: Kig's, Step's and a short
one for Kalzium. This plan is how. It follows phase-4c-plan.md's rules
(section 3 there) and D93: a commit per step, partial tests while
building and never the battery, every user-facing word through i18n in
both languages, a package's new version at its first change and `~dev`
builds of it until the owner tries the work and says yes.

Section 4 records what the owner decided, which the steps follow. Section 5 is the content, ready to
use: every word of the pane, every lesson in English and Spanish, and
every mission file.

## 1. Steps

| Step | What | Size |
|---|---|---|
| 4.32 | Found on the machine first: a pane on the right under labwc, the keyboard, the widths, a second file in a running program, links out of a module | S |
| 4.33 | The guide in the manifest, the lessons' format, and their reader (`kidux.lessons`, kidux-common) | M |
| 4.34 | The pane in the launcher, its button on the bar, the missions' button, what is remembered | L |
| 4.35 | Kig's guide: six lessons and four missions | M |
| 4.36 | Step's guide: six lessons and five missions | M |
| 4.37 | Kalzium's guide: three lessons | S |
| 4.38 | Links out of a module get Kidux's answer, a bubble, and open nothing | S |
| 4.39 | Closing: the documents, the report | S |

4.32 decides the shape of 4.34 and is done first. 4.33 and 4.34 are the
framework; 4.35 to 4.37 are content on it, each a package's new version;
4.38 is a session change found in 4.32 and owed to Step.

## 2. The steps

### 4.32 — Found on the machine first

On the machine left up (`tests/run vm up 04`), with a scratch script of
`tests/lib/sessionlib.py`'s `Machine`, and nothing committed before
these are known:

1. **A pane on the right.** A throwaway GTK 4 window under
   `gtk4-layer-shell`, as the bar is made (`bar.py`): anchored to the
   right, top and bottom edges, layer `TOP`, `set_exclusive_zone` of its
   width, 426 pixels, keyboard mode `ON_DEMAND`, run as Leo in his
   session with the launcher's own `LD_PRELOAD` of the library. Then Kig
   opened from its tile. Expected, since labwc keeps a maximised window
   inside the room the layer surfaces' exclusive zones leave, as it does
   for the bar: Kig's window fills the room to the left of the pane and
   above the bar, and the launcher's own window behind it too. Checked
   for a child without windows and, with `KIDUX_WINDOWS=1`, for one with
   them (a window maximised by its own button respects the pane too; a
   floating one may be put under it, which is the child's choice); for
   the X11 canary (D58; `tests/lib/seed/modules/x11-canary`), which the
   launcher maximises itself; and at scale 2, where the pane's width is
   what section 4.34 says. If labwc does not keep a maximised window out
   of a right exclusive zone, the step stops and the owner is told, with
   labwc's window rules (`SnapToRegion` with `<regions>`, labwc-notes.md)
   as the alternative to design.
2. **The keyboard.** With `ON_DEMAND`, a click in the pane takes the
   keyboard and a click in the program gives it back; Tab inside the pane
   stays in it. Checked, and checked that Alt+F4 and Alt+Tab, labwc's
   keys to the launcher, still work with the pane focused.
3. **A second file in a running program.** `kig a.kig` while Kig is open:
   a second Kig process and window, which the desk shows as a second
   window of the module. `step a.step` the same. Known, so that 4.34's
   mission button starts the program only when the module is not
   running.
4. **Links out of a module**, for 4.38. As Leo, `xdg-settings get
   default-web-browser` and `xdg-mime query default text/html` (both
   answer `chromium.desktop` on the test machine, found on 2026-10-17),
   and what Step's *Open in browser*, in its context information pane,
   does: it asks the desktop to open a local HTML file, and gets a plain
   Chromium window, outside any module's wall, in the kiosk. What KIO
   and `xdg-open` read to choose: `mimeapps.list` from
   `XDG_CONFIG_DIRS`, and the desktop files of `XDG_DATA_DIRS`.

What is found goes into this plan's section 4 where it changes a
decision, and into labwc-notes.md where it is about labwc.

**Found, 2026-10-17.** A pane on the right, 426 pixels, anchored right,
top and bottom with an exclusive zone of its width: Kig's window and the
X11 canary's, maximised by the kiosk's rule or, with windows, through
foreign-toplevel, fill the room to its left; the pane stops above the
bar, which keeps the whole width; the launcher's own window does the same
(labwc-notes.md). The layout stands as planned. As Leo, the desktop's
default for `text/html` and `x-scheme-handler/http` is
`chromium.desktop`, and `xdg-open` is there, as 4.38 assumes.

### 4.33 — The guide in the manifest, and the lessons' reader

**The manifest** (modules.md section 1) gets `guide = true`: the module
has lessons beside its manifest, under `content/<lang>/`, the directory
a module's content already lives in (section 3 there), installed by its
package to `/usr/share/kidux/modules/<id>/content/<lang>/`. `kidux.modules`
reads it into `Module.guide`, the guide's directory, `content/`, only
when the manifest says so and `content/en/` beside it holds at least one
lesson; otherwise "", with
a line in the log, as every wrong field is treated. English is the
reference tree and `tests/project/content.py` holds the Spanish lessons
to it, as for every module's content; the missions, which are not text
files to it, are held by each module's own unit test (4.35).

**A guide** is `content/<lang>/NN-<slug>.md`, one file per lesson, in the
order of their numbers, plus `content/<lang>/missions/<file>` for the
program's files a lesson opens, and `content/images/<file>.svg` or
`.png`, shared by the languages. A lesson is Markdown of a small, fixed
subset, read by one reader for every guide:

- `# Title`, once, first: the lesson's name, in the list and at the top.
- Paragraphs; `**bold**` for what the child presses or sees named in the
  program (*Archivo*, *Punto*), `*italic*` for a word being taught,
  `` `code` `` never (these guides are not about typing).
- `## Heading` for a part of the lesson.
- Numbered lists, `1.`, for steps; bullet lists, `-`, for choices.
- `![what it shows](images/<file>)`, a picture of Kidux's own, drawn like
  the avatars, on a line of its own.
- `> [think] …`, `> [point] …`, `> [cheer] …`: the mascot speaking, in
  the pose its first word names, as the BASIC guide's (phase-4b-plan.md
  4.10): the chick beside a speech bubble.
- `@mission missions/<file>` on a line of its own: the lesson's mission,
  a file of the program's, which the pane shows as a button (4.34).
- `::: try` to `:::`: a box, *Try this*, with ideas to go on with.

Nothing else: no links, no HTML, no tables. `kidux.lessons`
(kidux-common, GTK-free) reads a guide directory into a list of lessons,
each a title and a list of blocks, `("heading", level, text)`,
`("paragraph", runs)` with runs of plain, bold and italic text,
`("steps", [runs…])`, `("bullets", [runs…])`, `("image", path, alt)`,
`("mascot", pose, runs)`, `("mission", path)` and `("try", [blocks])`,
and refuses a file it cannot read with a line in the log and the lesson
left out, never the whole guide. Its test is the specification: each
block from its lines, a run with bold inside, a lesson without a title
skipped, a missing picture or mission logged and skipped, the order by
number.

**Words** of the pane are the launcher's, in its catalogue (section
5.1); the lessons' words are the module's content, in its two trees.

**Documents.** modules.md section 1 (`guide`) and section 3 (the guide's
files and format); architecture.md, D103 (section 4).

### 4.34 — The pane

**What it is.** A third window of the launcher, `guide.py`, a layer-shell
surface on the right edge, anchored top and bottom, layer `TOP`, with an
exclusive zone of its width, so that every maximised window and the
launcher's own fill the room to its left: for a child without windows
the program is beside it; for a child with them, their windows have the
rest of the desk and the pane stays (section 4, decision 2). On the
right, since the programs' palettes and toolbars are on the left and the
guide pushes none of them; the bubbles (D98), which rise from the bar's
right end on the overlay layer, rise over the pane's foot, and pass. Its
width is a third of the output's logical width, never under 300 pixels:
426 at 1280x800, 300 at 640x400 (scale 2, which leaves the program 340,
cramped but usable; D49's scale 2 is for a screen that is small anyway).
**Folded**, it is a rail of 28 pixels along the edge, with the book icon
and the module's name written upwards, and its exclusive zone is the
rail's, so that the program has the rest: the child folds it for room
and unfolds it by a click on the rail or by the bar's *Guide*. Its
colours and type are the launcher's (view.py's CSS, `kidux-roomy` and
the rest), its text 20 pixels, and it scrolls as D63's rooms do
(`kidux.scroll.scroller`).

**What it shows.** At the top, the module's name, and beside it *Fold*,
a chevron pointing at the edge; for a child with windows the name is a
drop-down, with every open module that has a guide, to change the guide
by hand, and beside it *Pin*, a pin icon that lights when pressed
(below); under it,
either the **list of lessons**, each a button with its number and title,
or **one lesson**: its title, its blocks drawn one under another, a
heading as a heading, a paragraph as a `Gtk.Label` with Pango markup for
bold and italic, wrapping, steps as a column of rows numbered in a
circle, bullets with a dot, a picture with `drawing()` at the pane's
width, the mascot's bubble as the launcher draws its notices (the chick
at 64 pixels beside a rounded box), *Try this* as a box in the module's
tile colour, and the mission as a box, *Mission* (below);
at the bottom, *Lessons* (back to the list), *Back* and *Next* between
the lessons. The keyboard reaches everything by Tab inside the pane
(`ON_DEMAND`), the arrows scroll, and Escape goes from a lesson to the
list.

**When it shows.** The pane follows the module on screen, which the
desk tells the launcher at every change (`desk_changed`), by one rule
for each of the child's modes (section 4, decision 2):

- *Without windows*, one module fills the screen at a time: the pane
  shows the guide of the module on screen, unfolded or folded as that
  module's guide was left; when the module on screen has no guide, or
  home is on screen, the pane goes away altogether. Two modules with a
  guide open at once swap guides as the child swaps between them.
- *With windows*, several windows are in view at once, so the pane
  stays for as long as any open module has a guide: it shows the guide
  of the module whose window is in use, and, when that module has none
  or home is in use, keeps showing the guide it last showed, so that a
  child reading Kig's lesson while they copy its numbers into Step does
  not lose the page. The child may also choose: the drop-down at the top
  lists every open module with a guide and shows the one picked, and
  *Pin* keeps the guide shown whatever window comes into use, until it
  is pressed again or that module closes; a guide picked from the
  drop-down is pinned, since choosing it is asking for it to stay. The
  pane goes away only when the last open module with a guide closes.

In both modes a module with a guide opens with its pane unfolded, the
list of lessons first, the first time; after that, what the child left:
folded or unfolded, and the lesson the child was in. That is remembered
for each module in the launcher's state file in the child's home,
`~/.local/share/kidux/launcher.json`, `{"guides": {"<id>": {"folded":
false, "lesson": 3}}}`, a JSON file of the launcher's own written whole
and renamed into place when it changes, and read at start (not
`kidux.state`, whose files are the daemon's and given to the
administrators, which a child's process cannot do); a file that does not
read is logged and ignored. The pin is of the session, not remembered: a new
session starts unpinned.

**The bar** gets *Guide*, a button with a book icon drawn like the bar's
others, between the time and *Close*, shown only while the pane is
there, lit while it is unfolded; it folds and unfolds the pane. Alt+Tab
and the bar's buttons change the module on screen and the pane follows
by the rule above; *Close* closes the module and the pane goes with it
or, with windows, passes to the next guide open; the lock screen covers
it like everything else (it is on the `TOP` layer, under the lock
screen's own). Under the bar's question *<name> has not closed…*
nothing changes.

**The missions.** A lesson's `@mission missions/<file>` is a file of the
program's, read-only in the module's directory. The first time a
module's pane is shown, the launcher copies the guide's missions into
the child's Documents, in a folder named in the child's language from
the launcher's catalogue, *Missions of <name>* (section 5.1), one file
each named as the lesson's language gives it (the file's name in
`content/<lang>/missions/` is already the child's language's), without
overwriting a file already there, so that a child's saved work stays.
The pane shows a lesson's mission as a box, *Mission*, with the sentence
*Open it from <name>: File, Open, Documents, Missions of <name>, <file>*:
the pane is there only while the module is open, a second start of the
program would be a second window, and File, Open is a thing to learn.
The sentence's words are the launcher's; the file's name is the
mission's.

**Tests.** Unit, GTK-free, in the launcher: the rule of what the pane
shows, in each mode, for every change of the module on screen, from
`desk.py`'s own test's shape; the state read and written; the missions'
copy that never overwrites. Session, `tests/session/41-guide.py`
(`40-purge.py` becomes `42-purge.py`), with Kig installed through the
daemon as `36-module-kig.py` does: Leo opens Kig, the pane is there on
the right with Kig's lessons in Leo's language and Kig filling the rest
(the picture `module-kig-guide`, in the guide and on the website; the
pane's cream in the right third, Kig's grid in the rest), the bar's
*Guide* lit; the missions copied into Leo's Documents; a click on the
first lesson shows it (the picture `module-guide-lesson`); *Fold* leaves the rail and Kig fills the room up to it; the
bar's button unfolds it to the same lesson; a second module without a
guide (the canary) opened and shown takes the pane away, and Kig shown
again brings it back; Leo logs out and in, opens Kig, and the pane comes
back as left. For a child with windows, `21-windows.py` gains a check
that with Kig and the canary open the pane stays, showing Kig's guide
while the canary is in use, and goes when Kig closes; and, with Kig and
Step open, that Step's window in use shows Step's guide, that Kig's
picked from the drop-down stays with Step in use, pinned, and that the
pin let go follows the window in use again.
`13-every-screen-fits.py` gains the pane at scale 2.

**Documents.** launcher.md, a section for the pane; the user guide's
section 5, *A guide beside a module*, and section 9's modules that have
one (section 5.5); the website (section 5.5); architecture.md, D103.

### 4.35 — Kig's guide

`kidux-module-kig` gets `guide = true`, `content/en/` and `content/es/`
with the six lessons of section 5.2 and their four missions, and
`content/images/` with the lessons' pictures, drawn like the avatars:
Opus draws each as the lesson describes it. The missions are Kig's own
files, written by hand in Kig's native format, each tried by opening it
in Kig on the machine left up and photographed; the format is section
5.2's, and where Kig refuses a file, a construction saved from Kig
itself in the VM is read and the file made to match. The package's
version goes to 0.2.0 (D93).

**Tests.** The module's unit test reads the guide with `kidux.lessons`
and finds six lessons with titles in both languages, every picture
present, and every mission a lesson names present in its language's
tree, the same lessons naming one in both. Session, `36-module-kig.py`: the picture
`module-kig` is taken with the pane (the tile's first open), and a new
check opens the copy of lesson 2's mission in Kig, as the starter does
with a file, and finds Kig's window titled with the file's name.

### 4.36 — Step's guide

As 4.35 for `kidux-module-step`: section 5.3's six lessons and five
missions, Step's files in its own XML, each tried in Step; version
0.2.0. The notes inside a mission are Step's *Note* objects, in the
language of the mission's tree. Session, `38-module-step.py`: a check
opens the copy of lesson 1's mission in Step, as the starter does with a
file, and finds Step's window titled with the file's name.

**Found, 2026-10-17.** Every mission opens in Step, titled with its name,
its objects in the World list. With the pane beside it, Step's world
view is about 90 pixels wide at 1280x800: its four panels on the right,
World, Properties, Context information and Undo history, take the rest,
so a mission's note and objects are hardly seen until the child folds
the guide or closes a panel. Kig's and Kalzium's fit. What to do is the
owner's to decide.

### 4.37 — Kalzium's guide

As 4.35 for `kidux-module-kalzium`: section 5.4's three lessons, no
missions; version 0.2.0. Simulations get no guide: each simulation is
made to be explored alone, and its page already says what each is.

### 4.38 — Links out of a module

**Cause.** Step's *Open in browser*, and any program that asks the
desktop to open a web page or an HTML file, gets a plain Chromium window
in the child's session, with tabs and an address bar, outside every
module's wall (4.32). The machine's policy still holds it to the
installed modules' hosts, but it is not Kidux's kiosk.

**Change.** The child's session gives every program Kidux's answer to a
link out: `kidux-session` puts `/usr/share/kidux/session/xdg` first in
`XDG_CONFIG_DIRS` and `/usr/share/kidux/session/share` first in
`XDG_DATA_DIRS`; the first holds a `mimeapps.list` whose default for
`text/html`, `x-scheme-handler/http` and `x-scheme-handler/https` is
`kidux-closed.desktop`, the second that desktop file under
`applications/`, hidden from menus, whose `Exec` is
`/usr/libexec/kidux-closed %u`: a small program of `kidux-session`'s
that sends the desktop's notification (D98) *That opens the internet,
which is closed here.* as a notice from the module, through the bubble's
own `module_of` (the caller's scope), and exits 0. KIO and `xdg-open`
both read those files, so Step's button, a link in GCompris's help or
any other goes to the bubble and opens nothing; `kidux-webapp`, which
starts its Chromium itself, is untouched. The KDE modules' starters keep
what the session set, since they only put their own directory first.

**Tests.** Unit: the desktop file and the list parse, `kidux-closed`'s
notice. Session: in `38-module-step.py`, `xdg-open` of an `.html` file
as Leo in his session sends the bubble and starts no Chromium (no
`chromium` process of Leo's).

**Documents.** session.md section 3; modules.md section 2 (a module that
opens a link gets the bubble); the user guide's section 5, one
sentence; architecture.md, D104.

### 4.39 — Closing

The documents read once more against what was built; the roadmap's
item ticked; the final message to the owner: what was built, how to try
each part on the MacBook, and the prompt for the final review. No
battery.

## 3. Rules for this plan

As phase-4c-plan.md section 3, and:

- **Partial tests only**, on the machine left up; the battery is the
  owner's to ask for after their own tries and Fable's final review.
- **The lessons are used as written** in section 5, in both languages;
  a word changed is a word changed in both, and the Spanish hashes
  recomputed (`tests/project/content.py --update`).
- **Every mission file is opened in its program on the machine before it
  is committed**, and photographed; a file the program refuses is fixed,
  not dropped.
- **Nothing of KDE's or PhET's is drawn**: the lessons' pictures are
  Kidux's own, like the avatars.

## 4. What the owner decided

Decided 2026-10-16 by the owner.

1. **A module may have a guide beside it**, lessons of Kidux's own with
   examples and ideas, shown beside the program and not inside it, and
   the modules a child cannot find their way in alone get one: Kig and
   Step first.
2. **One pane, two modes.** For a child without windows the room above
   the bar is split, the guide on the right, a third, and the program
   filling the rest; the pane shows the guide of the module on screen,
   swaps it for another module's, and goes away for a module without
   one. For a child with windows the guide takes the right edge and the
   windows have the rest of the desk; the pane stays while any open
   module has a guide, shows the guide of the module in use, keeps the
   last shown when that module has none, and goes away when the last
   module with a guide closes.
3. **The pane folds to a rail** along the edge, for room, and unfolds
   again from the rail or from the bar, in both modes. With windows, the
   child may pick a guide by hand from the pane's top, and pin it so
   that it stays whatever window comes into use.
4. **Fable plans, Opus builds, Fable reviews**, then the owner's hand
   tests, then the battery and the release.

Confirmed 2026-10-17 by the owner, on Fable's proposal:

5. **The pane is the launcher's own, a layer-shell surface with an
   exclusive zone**, not a second window the compositor places: it works
   the same in both modes, needs no window rules, opens and folds at
   once, and follows the module on screen. For a child with windows this
   is "the guide at the edge, the windows beside it" rather than two
   windows side by side, which labwc can only do with rules that act
   once, when a window appears, and never again.
6. **The lessons are drawn by the launcher from a small Markdown**, not
   shown as web pages: a browser in the launcher would be a second
   engine on the machine (D36), and a lesson needs headings, steps,
   pictures and the mascot, nothing more.
7. **Missions are copied into the child's Documents**, in a folder named
   in their language, and opened from the program's own File, Open when
   the program is already running: a second start would be a second
   window, and opening a file is itself a thing to learn.
8. **Kalzium gets a short guide; the Simulations none.**
9. **Links out of a module get a bubble and open nothing** (4.38), for
   every program in a child's session.

## 5. The content

### 5.1 The pane's words (kidux-launcher's catalogue)

| English | Spanish |
|---|---|
| Guide | Guía |
| Fold | Plegar |
| Pin (the guide stays while other windows are in use) | Fijar (la guía se queda aunque uses otras ventanas) |
| Lessons | Lecciones |
| Back | Volver |
| Next | Siguiente |
| Try this | Prueba esto |
| Mission | Misión |
| Open it from {name}: File, Open, Documents, {folder}, {file}. | Ábrela desde {name}: Archivo, Abrir, Documentos, {folder}, {file}. |
| Missions of {name} | Misiones de {name} |
| That opens the internet, which is closed here. (4.38, kidux-session) | Eso abre internet, que aquí está cerrado. |

### 5.2 Kig's guide

**Pictures** (`content/images/`): `kig-point-line.svg`, two points and a
line through them; `kig-middle.svg`, a segment with its midpoint marked;
`kig-circles.svg`, two circles crossing at two points; `kig-parallels.svg`,
a line, a point and the perpendicular and the parallel through it;
`kig-triangle.svg`, Euclid's two circles with the equilateral triangle;
`kig-angles.svg`, a triangle with its three angles marked. Each flat, in
Kidux's colours, 360 wide.

**Mission files** (`content/<lang>/missions/`), Kig's native XML. The
shape, to be checked against a file Kig saves itself (4.35):

```xml
<!DOCTYPE KigDocument>
<KigDocument axes="1" grid="1" Version="1.0" CompatibilityVersion="0.7.0">
 <CoordinateSystem>Euclidean</CoordinateSystem>
 <Objects>
  <Data type="double" id="1">-3</Data>
  <Data type="double" id="2">1</Data>
  <Object type="FixedPoint" id="3"><Parent id="1"/><Parent id="2"/></Object>
  <Draw object="3" color="#e4572e" shown="true" width="-1" point-style="Round"
        style="SolidLine"><Name>A</Name></Draw>
  …
 </Objects>
</KigDocument>
```

Each point is two `Data` doubles and a `FixedPoint` with them as parents;
a segment is `SegmentAB` with two point parents, a circle by centre and
point `CircleBCP`, a midpoint the property `mid-point` of a segment, a
label `TextLabel`; `Draw` makes each object visible with its colour and
its name. The four missions:

- `middle.kig` / `medio.kig` (lesson 2): points A (-4, 1) and B (3, 1)
  in orange, the segment AB in ink, its midpoint M in blue, and a label
  at (-4, 3): *Drag A. Where does M go?* / *Arrastra A. ¿Adónde va M?*
- `two-circles.kig` / `dos-circunferencias.kig` (lesson 3): points A
  (-2, 1) and B (2, 1), off the axis whose numbers would cover their
  names, the circle centred A through B, and a label in two lines:
  *Draw the circle centred B through A. Where do they cross?* / *Dibuja
  la circunferencia con centro B que pasa por A. ¿Dónde se cruzan?*
- `parallels.kig` / `paralelas.kig` (lesson 4): the line through (-5, -2)
  and (5, 1), a point P at (0, 3) in orange, and a label: *Draw the
  parallel and the perpendicular to the line through P, then drag P.* /
  *Dibuja la paralela y la perpendicular a la recta por P, y luego
  arrastra P.*
- `triangle.kig` / `triangulo.kig` (lesson 5): points A (-2, 1) and B
  (2, 1), the circle centred A through B, and a label: *One circle is
  drawn. Draw the other, find C, and join the three.* / *Una
  circunferencia ya está. Dibuja la otra, encuentra C y une los tres.*

**Lessons.** English, then Spanish, for each file.

`01-points-and-lines.md`

```
# Points and lines

Kig is a sheet of paper where everything can move. You put points on it,
join them with lines, and then drag the points: the lines follow.

![Two points and the line through them](images/kig-point-line.svg)

1. Press **Point** on the left, then click twice on the canvas. Two
   points appear, A and B.
2. Press **Line by two points** (the straight line in the toolbar) and
   click A, then B. A line runs through both.
3. Press the arrow at the top of the left toolbar, the pointer. Now
   drag A somewhere else.

> [point] The line turns to follow A. It always goes through both
> points: that is its rule.

## A triangle

1. Put three points.
2. Press **Segment** (the short line) and click two of them. A segment
   joins them.
3. Join the other two pairs. You have a triangle.
4. Drag a corner. The triangle changes shape but stays a triangle.

::: try
Make a square with four segments. Then drag one corner. Is it still a
square? In the lesson about parallels you will learn how to make one
that stays square.
:::
```

```
# Puntos y rectas

Kig es una hoja de papel en la que todo se puede mover. Pones puntos,
los unes con rectas, y luego arrastras los puntos: las rectas los
siguen.

![Dos puntos y la recta que pasa por ellos](images/kig-point-line.svg)

1. Pulsa **Punto** a la izquierda y haz clic dos veces en el lienzo.
   Aparecen dos puntos, A y B.
2. Pulsa **Recta por dos puntos** (la línea recta de la barra) y haz
   clic en A y luego en B. Una recta pasa por los dos.
3. Pulsa la flecha de arriba de la barra de la izquierda, el puntero.
   Ahora arrastra A a otro sitio.

> [point] La recta gira para seguir a A. Siempre pasa por los dos
> puntos: esa es su regla.

## Un triángulo

1. Pon tres puntos.
2. Pulsa **Segmento** (la línea corta) y haz clic en dos de ellos. Un
   segmento los une.
3. Une las otras dos parejas. Tienes un triángulo.
4. Arrastra una esquina. El triángulo cambia de forma, pero sigue
   siendo un triángulo.

::: try
Haz un cuadrado con cuatro segmentos. Luego arrastra una esquina. ¿Sigue
siendo un cuadrado? En la lección de las paralelas aprenderás a hacer
uno que se quede cuadrado.
:::
```

`02-the-middle.md`

```
# The middle of a segment

A segment has a middle, and Kig can find it for you. Better: the middle
it finds stays in the middle when you move the ends.

![A segment with its midpoint](images/kig-middle.svg)

@mission missions/middle.kig

1. Open the mission. You see a segment from A to B and its midpoint M.
2. Drag A up. Drag B far to the right. Watch M.

> [think] M is always exactly halfway, however you move A and B. Kig
> remembers that M is *the middle of AB*, not a point you put there.

## Do it yourself

1. Press **Segment** and click twice on the canvas.
2. Press **Midpoint** in the toolbar and click the segment. The midpoint
   appears.
3. Now press **Point** and click near the segment, but not on it. That
   point is free: drag the segment's ends and it stays where it is.

::: try
Find the midpoint of each side of a triangle, and join the three
midpoints. What shape is inside? Drag a corner of the big triangle.
:::
```

```
# El medio de un segmento

Un segmento tiene un medio, y Kig lo encuentra por ti. Y mejor aún: el
medio que encuentra sigue en el medio cuando mueves los extremos.

![Un segmento con su punto medio](images/kig-middle.svg)

@mission missions/medio.kig

1. Abre la misión. Ves un segmento de A a B y su punto medio M.
2. Arrastra A hacia arriba. Arrastra B lejos, a la derecha. Mira M.

> [think] M está siempre justo a mitad de camino, muevas como muevas A y
> B. Kig recuerda que M es *el medio de AB*, no un punto que pusiste
> ahí.

## Hazlo tú

1. Pulsa **Segmento** y haz clic dos veces en el lienzo.
2. Pulsa **Punto medio** en la barra y haz clic en el segmento. Aparece
   el punto medio.
3. Ahora pulsa **Punto** y haz clic cerca del segmento, pero no encima.
   Ese punto es libre: arrastra los extremos del segmento y se queda
   donde está.

::: try
Encuentra el punto medio de cada lado de un triángulo y une los tres
puntos medios. ¿Qué figura hay dentro? Arrastra una esquina del
triángulo grande.
:::
```

`03-circles.md`

```
# Circles

A circle is all the points at the same distance from its centre. In Kig
you draw one with its centre and one point it passes through.

![Two circles crossing](images/kig-circles.svg)

@mission missions/two-circles.kig

1. Open the mission. There is a circle with centre A through B.
2. Press **Circle by centre and point**, click B, then click A. A second
   circle, centred B, through A.
3. The circles cross at two places. Press **Intersection** in the
   toolbar and click one circle, then the other. Kig marks both
   crossing points.
4. Drag B away from A. The circles grow together and the crossing
   points move with them.

> [cheer] Both circles are the same size, always: each one's radius is
> the distance from A to B. Dragging changes that distance for both.

## A point that lives on a circle

1. Draw a circle. Press **Point** and click exactly on the circle's
   line.
2. Drag that point. It slides along the circle and never leaves it.

::: try
Draw a circle, then a segment from its centre to a point on it. Drag the
point round. The segment is always a *radius*: its length never changes.
:::
```

```
# Circunferencias

Una circunferencia es todos los puntos que están a la misma distancia
de su centro. En Kig dibujas una con su centro y un punto por el que
pasa.

![Dos circunferencias que se cruzan](images/kig-circles.svg)

@mission missions/dos-circunferencias.kig

1. Abre la misión. Hay una circunferencia con centro A que pasa por B.
2. Pulsa **Circunferencia por centro y punto**, haz clic en B y luego
   en A. Una segunda circunferencia, con centro B, que pasa por A.
3. Las circunferencias se cruzan en dos sitios. Pulsa **Intersección**
   en la barra y haz clic en una circunferencia y luego en la otra. Kig
   marca los dos puntos de cruce.
4. Arrastra B lejos de A. Las dos circunferencias crecen a la vez, y
   los puntos de cruce se mueven con ellas.

> [cheer] Las dos circunferencias son siempre del mismo tamaño: el
> radio de cada una es la distancia de A a B. Al arrastrar cambias esa
> distancia para las dos.

## Un punto que vive en una circunferencia

1. Dibuja una circunferencia. Pulsa **Punto** y haz clic justo encima
   de su línea.
2. Arrastra ese punto. Se desliza por la circunferencia y nunca se sale.

::: try
Dibuja una circunferencia y luego un segmento desde su centro hasta un
punto de ella. Arrastra el punto alrededor. El segmento es siempre un
*radio*: su longitud no cambia nunca.
:::
```

`04-parallels.md`

```
# Perpendicular and parallel

Two lines are *perpendicular* when they cross like a plus sign. Two
lines are *parallel* when they never cross, like the rails of a train.
Kig draws both for you, and they keep their rule when you move things.

![A line, a point, and the perpendicular and parallel through it](images/kig-parallels.svg)

@mission missions/parallels.kig

1. Open the mission. There is a line and a point P off it.
2. Press **Perpendicular** in the toolbar, click the line, then click
   P. A line through P crosses the first at a right angle.
3. Press **Parallel**, click the line, then click P. A line through P
   that never meets the first.
4. Drag P. Both new lines move with it and keep their rule.
5. Now drag one of the two points the first line goes through. The
   first line turns, and the other two turn with it.

> [think] The parallel and the perpendicular are *made from* the first
> line. Change the first, and they change. That is what Kig is for.

## A square that stays square

1. Draw a segment AB.
2. Perpendicular to AB through A; perpendicular to AB through B.
3. Circle centred A through B. Where it crosses the perpendicular at A,
   mark the intersection: call it D.
4. Parallel to AB through D. Where it crosses the perpendicular at B is
   C.
5. Join A, B, C, D with segments. Drag A or B: it stays a square.

::: try
Hide the lines and circles you used (right-click, Hide) and keep only the
square. It still works.
:::
```

```
# Perpendicular y paralela

Dos rectas son *perpendiculares* cuando se cruzan como un signo más.
Dos rectas son *paralelas* cuando nunca se cruzan, como los raíles de un
tren. Kig dibuja las dos por ti, y conservan su regla cuando mueves las
cosas.

![Una recta, un punto, y la perpendicular y la paralela que pasan por él](images/kig-parallels.svg)

@mission missions/paralelas.kig

1. Abre la misión. Hay una recta y un punto P fuera de ella.
2. Pulsa **Perpendicular** en la barra, haz clic en la recta y luego en
   P. Una recta por P cruza la primera en ángulo recto.
3. Pulsa **Paralela**, haz clic en la recta y luego en P. Una recta por
   P que nunca toca la primera.
4. Arrastra P. Las dos rectas nuevas se mueven con él y conservan su
   regla.
5. Ahora arrastra uno de los dos puntos por los que pasa la primera
   recta. La primera gira, y las otras dos giran con ella.

> [think] La paralela y la perpendicular están *hechas a partir de* la
> primera recta. Cambia la primera y cambian ellas. Para eso sirve Kig.

## Un cuadrado que se queda cuadrado

1. Dibuja un segmento AB.
2. Perpendicular a AB por A; perpendicular a AB por B.
3. Circunferencia con centro A que pasa por B. Donde cruza la
   perpendicular de A, marca la intersección: llámala D.
4. Paralela a AB por D. Donde cruza la perpendicular de B está C.
5. Une A, B, C y D con segmentos. Arrastra A o B: sigue siendo un
   cuadrado.

::: try
Oculta las rectas y circunferencias que usaste (clic derecho, Ocultar) y
deja solo el cuadrado. Sigue funcionando.
:::
```

`05-the-triangle.md`

```
# A triangle with three equal sides

This is the oldest construction in geometry, two thousand years old.
With two circles you make a triangle whose three sides are exactly the
same length, and it stays that way when you drag it.

![Two circles and the equilateral triangle](images/kig-triangle.svg)

@mission missions/triangle.kig

1. Open the mission. Points A and B, and the circle centred A through B.
2. Draw the circle centred B through A.
3. Mark where the circles cross, with **Intersection**. Pick the upper
   point and call it C.
4. Join A to B, B to C and C to A with segments.
5. Drag A or B. The triangle grows and shrinks, but its three sides
   stay equal.

> [think] Why? AC is a radius of the first circle, so it is as long as
> AB. BC is a radius of the second, so it is as long as AB too. Three
> equal sides.

::: try
Hide the two circles. Then find the midpoint of each side and join the
midpoints: four small triangles, all equal. Drag A.
:::
```

```
# Un triángulo con tres lados iguales

Esta es la construcción más antigua de la geometría, de hace dos mil
años. Con dos circunferencias haces un triángulo cuyos tres lados miden
exactamente lo mismo, y sigue así cuando lo arrastras.

![Dos circunferencias y el triángulo equilátero](images/kig-triangle.svg)

@mission missions/triangulo.kig

1. Abre la misión. Los puntos A y B, y la circunferencia con centro A
   que pasa por B.
2. Dibuja la circunferencia con centro B que pasa por A.
3. Marca dónde se cruzan, con **Intersección**. Quédate con el punto de
   arriba y llámalo C.
4. Une A con B, B con C y C con A con segmentos.
5. Arrastra A o B. El triángulo crece y encoge, pero sus tres lados
   siguen siendo iguales.

> [think] ¿Por qué? AC es un radio de la primera circunferencia, así
> que mide lo mismo que AB. BC es un radio de la segunda, así que mide
> lo mismo que AB también. Tres lados iguales.

::: try
Oculta las dos circunferencias. Luego busca el punto medio de cada lado
y une los puntos medios: cuatro triángulos pequeños, todos iguales.
Arrastra A.
:::
```

`06-measure.md`

```
# Measure it

Kig can tell you how long a segment is and how big an angle is, and the
numbers change as you drag.

![A triangle with its three angles marked](images/kig-angles.svg)

1. Draw a triangle with three segments.
2. Press **Angle** in the toolbar and click three corners in turn: the
   middle click is the corner the angle is at. A small arc marks it.
3. Right-click the arc, choose **Add text label**, and pick the angle's
   size. A number in degrees appears.
4. Do the same at the other two corners.
5. Drag a corner and watch the three numbers.

> [cheer] Add the three numbers. However you drag, they always make 180.
> Every triangle in the world does this.

## Lengths

1. Right-click a segment, **Add text label**, and pick its length.
2. Drag an end and watch the number.

::: try
Draw a right angle with a perpendicular, and a triangle on it. Measure
the three sides. Multiply each by itself: the two short ones added give
the long one. That is Pythagoras, and Kig lets you check it.
:::
```

```
# Mídelo

Kig te dice cuánto mide un segmento y cuánto abre un ángulo, y los
números cambian mientras arrastras.

![Un triángulo con sus tres ángulos marcados](images/kig-angles.svg)

1. Dibuja un triángulo con tres segmentos.
2. Pulsa **Ángulo** en la barra y haz clic en tres esquinas seguidas: el
   clic del medio es la esquina donde está el ángulo. Un arco pequeño lo
   marca.
3. Haz clic derecho en el arco, elige **Añadir etiqueta de texto** y
   escoge el tamaño del ángulo. Aparece un número en grados.
4. Haz lo mismo en las otras dos esquinas.
5. Arrastra una esquina y mira los tres números.

> [cheer] Suma los tres números. Arrastres como arrastres, siempre dan
> 180. Todos los triángulos del mundo hacen esto.

## Longitudes

1. Clic derecho en un segmento, **Añadir etiqueta de texto**, y escoge
   su longitud.
2. Arrastra un extremo y mira el número.

::: try
Dibuja un ángulo recto con una perpendicular, y un triángulo sobre él.
Mide los tres lados. Multiplica cada uno por sí mismo: los dos cortos
sumados dan el largo. Eso es Pitágoras, y Kig te deja comprobarlo.
:::
```

### 5.3 Step's guide

**Pictures**: `step-fall.svg`, a ball with a downward arrow;
`step-spring.svg`, two balls joined by a spring; `step-pendulum.svg`, a
ball on a rod from a fixed point; `step-throw.svg`, a ball and the arc
it flies; `step-graph.svg`, a small graph with a curve; `step-bounce.svg`,
a ball bouncing off a box.

**Mission files**, Step's XML (`StepCoreXML`, as Step's own examples in
`/usr/share/doc/step/examples/`): a `<world>` with `<item class="…">`
elements, each with `<name>`, `<color>`, and its properties; a *Note*
is `<item class="Note">` with `<position>`, `<size>` and `<text>` holding
the note's words (Step writes them as rich text; plain text inside works
too). Distances are metres, masses kilograms, time seconds. The five
missions:

- `fall.step` / `caida.step` (lesson 1): a `Particle` of mass 1 at
  (0, 3), velocity (0, 0); a `WeightForce` with `weightConst` 9.80665;
  a `Note` at (-4, 4), size (200, 60): *Press Simulate. Then give the
  ball a sideways push: set its velocity to (2, 0).* / *Pulsa Simular.
  Luego dale a la bola un empujón de lado: pon su velocidad en (2, 0).*
- `spring.step` / `muelle.step` (lesson 2): two `Particle`s of mass 1 at
  (-1, 0) and (1, 0), a `Spring` between them with `restLength` 1,
  `stiffness` 5 and `damping` 0, no gravity; a note: *The spring is
  stretched. Press Simulate and watch. Then make it stiffer: stiffness
  50.* / *El muelle está estirado. Pulsa Simular y mira. Luego hazlo más
  duro: rigidez 50.*
- `pendulum.step` / `pendulo.step` (lesson 3): a `Particle` of mass 1 at
  (1.5, 0), a `Stick` of `restLength` 1.5 from the world (`body1` 0,
  `localPosition1` (0, 0)) to the particle, a `WeightForce`; a note:
  *Press Simulate. Then stop, move the ball lower, and press again: does
  it swing slower?* / *Pulsa Simular. Luego para, pon la bola más abajo y
  pulsa otra vez: ¿se balancea más despacio?*
- `throw.step` / `lanzamiento.step` (lesson 4): a `Particle` of mass 1 at
  (-4, 0), velocity (4, 6); a `WeightForce`; a `Tracer` on the particle
  (`body` the particle, `localPosition` (0, 0)); a note: *Press Simulate
  and watch the path. Then try velocity (6, 4). Which goes further?* /
  *Pulsa Simular y mira el camino. Luego prueba la velocidad (6, 4).
  ¿Cuál llega más lejos?*
- `bounce.step` / `rebote.step` (lesson 6): a `Box` at (0, -2), size
  (8, 0.5), held where it is by an `Anchor`, and a `Disk` of mass 1 and
  radius 0.3 at (0, 2), velocity (1, 0); a `WeightForce`; a
  `GJKCollisionSolver`; a note: *Press Simulate. The disk bounces on
  the box. Add a second disk and let them crash.* / *Pulsa Simular. El
  disco rebota en la caja. Añade un segundo disco y haz que choquen.*

Each file is written by hand after reading Step's own examples for the
exact properties each class needs (Step 25.04 names them in its
`objinfo` pages too), opened in Step on the machine, and photographed.

**Lessons.**

`01-a-ball-falls.md`

```
# A ball falls

Step is a world where things obey the laws of physics. You put things in
it, press **Simulate**, and watch what the laws do to them.

![A ball with the arrow of its fall](images/step-fall.svg)

@mission missions/fall.step

1. Open the mission. A ball floats in the air, and a note tells you what
   to try.
2. Press **Simulate** at the top. The ball falls. Press it again to stop.
3. Nothing pulls the ball but **gravity**, the weight force, which you
   can see in the **World** list on the right.
4. Click the ball. In **Properties** you see its *position*, its
   *velocity* and its *mass*. Change the velocity to (2, 0) and simulate
   again.

> [think] The ball now moves sideways while it falls. The sideways push
> does not change how fast it falls: gravity only pulls down.

## Do it yourself

1. Press **New** in the toolbar for an empty world.
2. In the palette on the left, press **Particle** and click on the
   canvas. That is a ball.
3. Press **WeightForce** in the palette and click on the canvas: that
   switches gravity on.
4. Simulate.

::: try
Put two balls, one with mass 1 and one with mass 100, at the same height.
Which lands first? Galileo tried this from a tower.
:::
```

```
# Una bola cae

Step es un mundo donde las cosas obedecen las leyes de la física. Pones
cosas en él, pulsas **Simular** y miras qué les hacen las leyes.

![Una bola con la flecha de su caída](images/step-fall.svg)

@mission missions/caida.step

1. Abre la misión. Una bola flota en el aire, y una nota te dice qué
   probar.
2. Pulsa **Simular** arriba. La bola cae. Pulsa otra vez para parar.
3. A la bola solo tira la **gravedad**, la fuerza del peso, que puedes
   ver en la lista **Mundo** de la derecha.
4. Haz clic en la bola. En **Propiedades** ves su *posición*, su
   *velocidad* y su *masa*. Cambia la velocidad a (2, 0) y simula otra
   vez.

> [think] Ahora la bola se mueve de lado mientras cae. El empujón de
> lado no cambia lo rápido que cae: la gravedad solo tira hacia abajo.

## Hazlo tú

1. Pulsa **Nuevo** en la barra para un mundo vacío.
2. En la paleta de la izquierda, pulsa **Partícula** y haz clic en el
   lienzo. Eso es una bola.
3. Pulsa **FuerzaPeso** en la paleta y haz clic en el lienzo: eso
   enciende la gravedad.
4. Simula.

::: try
Pon dos bolas, una de masa 1 y otra de masa 100, a la misma altura.
¿Cuál llega antes al suelo? Galileo lo probó desde una torre.
:::
```

`02-a-spring.md`

```
# A spring

A spring pulls when you stretch it and pushes when you squash it. The
harder you stretch it, the harder it pulls.

![Two balls joined by a spring](images/step-spring.svg)

@mission missions/spring.step

1. Open the mission. Two balls, a spring between them, already
   stretched. No gravity here.
2. Press **Simulate**. The balls bounce towards each other and back,
   again and again.
3. Stop. Click the spring. In **Properties**, *stiffness* says how hard
   it is. Change it to 50 and simulate.

> [point] A stiffer spring bounces faster. The balls move the same way
> whether the spring is soft or hard, only quicker.

## Do it yourself

1. New world. Two **Particles**.
2. Press **Spring** in the palette, then drag from one ball to the
   other.
3. Drag one ball away to stretch the spring, and simulate.

::: try
Add **WeightForce** and hang the spring from an **Anchor**: a ball that
bobs up and down. Change the ball's mass. Heavier, slower?
:::
```

```
# Un muelle

Un muelle tira cuando lo estiras y empuja cuando lo aplastas. Cuanto
más lo estiras, más fuerte tira.

![Dos bolas unidas por un muelle](images/step-spring.svg)

@mission missions/muelle.step

1. Abre la misión. Dos bolas, un muelle entre ellas, ya estirado. Aquí
   no hay gravedad.
2. Pulsa **Simular**. Las bolas van la una hacia la otra y vuelven, una
   y otra vez.
3. Para. Haz clic en el muelle. En **Propiedades**, *rigidez* dice lo
   duro que es. Cámbiala a 50 y simula.

> [point] Un muelle más duro rebota más deprisa. Las bolas se mueven
> igual con el muelle blando o duro, solo que más rápido.

## Hazlo tú

1. Mundo nuevo. Dos **Partículas**.
2. Pulsa **Muelle** en la paleta y arrastra de una bola a la otra.
3. Arrastra una bola para estirar el muelle, y simula.

::: try
Añade **FuerzaPeso** y cuelga el muelle de un **Ancla**: una bola que
sube y baja. Cambia la masa de la bola. ¿Más pesada, más lenta?
:::
```

`03-a-pendulum.md`

```
# A pendulum

A weight on a rod that hangs from a point: that is a pendulum, the heart
of an old clock.

![A ball on a rod from a fixed point](images/step-pendulum.svg)

@mission missions/pendulum.step

1. Open the mission. A ball hangs from a rod, held at the top.
2. Press **Simulate**. It swings left and right, and keeps swinging.
3. Stop. Drag the ball a little lower, so that the rod is shorter, and
   simulate again. Count the swings in ten seconds, before and after.

> [think] A shorter pendulum swings faster. The weight of the ball does
> not matter: try mass 10. Only the length does. Galileo noticed this
> watching a lamp swing in a church.

## Do it yourself

1. New world, **WeightForce** on.
2. A **Particle**. Then **Stick** in the palette: click on empty space
   first, then on the ball. A stick from a fixed point to the ball.
3. Drag the ball to one side and simulate.

::: try
Hang a second ball from the first with another stick: a double pendulum.
Simulate. Can you guess where it will go? Nobody can.
:::
```

```
# Un péndulo

Un peso en una varilla que cuelga de un punto: eso es un péndulo, el
corazón de un reloj antiguo.

![Una bola en una varilla desde un punto fijo](images/step-pendulum.svg)

@mission missions/pendulo.step

1. Abre la misión. Una bola cuelga de una varilla, sujeta por arriba.
2. Pulsa **Simular**. Se balancea a izquierda y derecha, y sigue.
3. Para. Arrastra la bola un poco más abajo, para que la varilla sea
   más corta, y simula otra vez. Cuenta los vaivenes en diez segundos,
   antes y después.

> [think] Un péndulo más corto se balancea más deprisa. El peso de la
> bola no importa: prueba con masa 10. Solo importa la longitud.
> Galileo se dio cuenta mirando una lámpara que se balanceaba en una
> iglesia.

## Hazlo tú

1. Mundo nuevo, **FuerzaPeso** encendida.
2. Una **Partícula**. Luego **Varilla** en la paleta: haz clic primero
   en un sitio vacío y luego en la bola. Una varilla desde un punto fijo
   hasta la bola.
3. Arrastra la bola a un lado y simula.

::: try
Cuelga una segunda bola de la primera con otra varilla: un péndulo
doble. Simula. ¿Adivinas adónde irá? Nadie puede.
:::
```

`04-throw-it.md`

```
# Throw it

Throw a ball and it flies in a curve: up, over and down. Step can draw
that curve for you.

![A ball and the arc it flies](images/step-throw.svg)

@mission missions/throw.step

1. Open the mission. A ball on the left, with a velocity already set,
   and a **Tracer** on it that draws where it goes.
2. Press **Simulate**. The ball flies in an arc and the tracer leaves
   its path behind.
3. Stop and press **Undo** until the ball is back. Click it and set the
   velocity to (6, 4). Simulate. Then (4, 6). Which throw goes further?
   Which goes higher?

> [think] The first number is the sideways speed, the second the upward
> speed. Up decides how high; sideways, with the time it is in the air,
> decides how far.

## Do it yourself

1. New world, **WeightForce** on, a **Particle**.
2. In **Properties**, set its velocity to (5, 5).
3. **Tracer** in the palette, then click the ball.
4. Simulate.

::: try
Find the velocity that lands the ball exactly at x = 10. Then try to do
it with a smaller total speed.
:::
```

```
# Lánzala

Lanza una bola y vuela en una curva: sube, pasa y baja. Step puede
dibujarte esa curva.

![Una bola y el arco que recorre](images/step-throw.svg)

@mission missions/lanzamiento.step

1. Abre la misión. Una bola a la izquierda, con una velocidad ya puesta,
   y un **Trazador** en ella que dibuja por dónde va.
2. Pulsa **Simular**. La bola vuela en un arco y el trazador deja su
   camino detrás.
3. Para y pulsa **Deshacer** hasta que la bola vuelva. Haz clic en ella y
   pon la velocidad en (6, 4). Simula. Luego (4, 6). ¿Qué lanzamiento
   llega más lejos? ¿Cuál sube más?

> [think] El primer número es la velocidad de lado, el segundo la de
> subida. La de subida decide la altura; la de lado, con el tiempo que
> está en el aire, decide la distancia.

## Hazlo tú

1. Mundo nuevo, **FuerzaPeso** encendida, una **Partícula**.
2. En **Propiedades**, pon su velocidad en (5, 5).
3. **Trazador** en la paleta, y luego clic en la bola.
4. Simula.

::: try
Busca la velocidad que haga caer la bola justo en x = 10. Luego intenta
hacerlo con una velocidad total más pequeña.
:::
```

`05-measure.md`

```
# Measure it

Scientists do not only watch: they measure. Step has meters and graphs
that read numbers off your world while it runs.

![A small graph with a curve](images/step-graph.svg)

1. Make a ball with gravity, as in the first lesson, high up.
2. Press **Meter** in the palette and click on the canvas. In its
   **Properties**, choose the ball as *object* and *velocity* as
   *property*. The meter shows a number.
3. Simulate. The number grows as the ball falls faster and faster.
4. Stop, undo. Now press **Graph** and click on the canvas. In its
   properties, X is *time* of the world, Y is the ball's *position*.
5. Simulate. A curve is drawn: the ball's height against time.

> [think] The curve bends more and more: the ball covers more distance
> each second. That is what *accelerating* looks like on a graph.

::: try
Graph the ball's velocity against time. It is a straight line. Why is
one a curve and the other a line?
:::
```

```
# Mídelo

Los científicos no solo miran: miden. Step tiene medidores y gráficas
que leen números de tu mundo mientras funciona.

![Una gráfica pequeña con una curva](images/step-graph.svg)

1. Haz una bola con gravedad, como en la primera lección, bien alta.
2. Pulsa **Medidor** en la paleta y haz clic en el lienzo. En sus
   **Propiedades**, elige la bola como *objeto* y *velocidad* como
   *propiedad*. El medidor enseña un número.
3. Simula. El número crece mientras la bola cae cada vez más rápido.
4. Para, deshaz. Ahora pulsa **Gráfica** y haz clic en el lienzo. En sus
   propiedades, X es el *tiempo* del mundo, Y es la *posición* de la
   bola.
5. Simula. Se dibuja una curva: la altura de la bola frente al tiempo.

> [think] La curva se dobla cada vez más: la bola recorre más distancia
> cada segundo. Así se ve *acelerar* en una gráfica.

::: try
Dibuja la gráfica de la velocidad de la bola frente al tiempo. Es una
línea recta. ¿Por qué una es curva y la otra recta?
:::
```

`06-bounce.md`

```
# Bounce and crash

Balls bounce off walls and crash into each other. Step knows how.

![A ball bouncing off a box](images/step-bounce.svg)

@mission missions/bounce.step

1. Open the mission. A disk above a box held still by an anchor,
   gravity on, and a collision solver in the world list, which is what
   makes things bounce instead of passing through.
2. Press **Simulate**. The disk falls, hits the box and bounces.
3. Add a second **Disk** from the palette, give it a velocity towards
   the first, and simulate. They crash and fly apart.

> [cheer] Every bounce obeys one rule: what one ball loses in speed, the
> other gains. Nothing is lost, only passed on.

## Do it yourself

1. New world. **Box** from the palette, drawn wide and flat.
2. **Anchor** from the palette, then click the box: it stays where it
   is, whatever pulls it.
3. A **Disk** above it. **WeightForce**, and click on the canvas.
4. Simulate. A new world already has its collision solver.

::: try
Make a slope: a box turned by setting its *angle* to 0.3. Let a disk roll
down it. Then try **Gas** from the palette: a hundred particles bouncing
in a box, which is what air is.
:::
```

```
# Rebota y choca

Las bolas rebotan en las paredes y chocan unas con otras. Step sabe
cómo.

![Una bola que rebota en una caja](images/step-bounce.svg)

@mission missions/rebote.step

1. Abre la misión. Un disco sobre una caja sujeta por un ancla,
   gravedad encendida, y en la lista del mundo un resolutor de
   colisiones, que es lo que hace que las cosas reboten en vez de
   atravesarse.
2. Pulsa **Simular**. El disco cae, golpea la caja y rebota.
3. Añade un segundo **Disco** de la paleta, dale una velocidad hacia el
   primero y simula. Chocan y salen despedidos.

> [cheer] Cada rebote obedece una regla: lo que una bola pierde de
> velocidad, la otra lo gana. Nada se pierde, solo se pasa.

## Hazlo tú

1. Mundo nuevo. **Caja** de la paleta, dibujada ancha y plana.
2. **Ancla** de la paleta, y luego clic en la caja: se queda donde está,
   tire lo que tire de ella.
3. Un **Disco** encima. **FuerzaPeso**, y clic en el lienzo.
4. Simula. Un mundo nuevo ya trae su resolutor de colisiones.

::: try
Haz una rampa: una caja girada poniendo su *ángulo* en 0,3. Deja que un
disco ruede por ella. Luego prueba **Gas** de la paleta: cien partículas
rebotando en una caja, que es lo que es el aire.
:::
```

### 5.4 Kalzium's guide

**Pictures**: `kalzium-table.svg`, a few tiles of the table with one
lit; `kalzium-states.svg`, three tiles, a solid, a liquid and a gas;
`kalzium-molecule.svg`, two atoms joined.

`01-find-an-element.md`

```
# Find an element

Everything around you is made of about ninety different kinds of atoms,
the *elements*. The periodic table shows them all on one sheet.

![Tiles of the table, one lit](images/kalzium-table.svg)

1. Find the tile with **O** on it, near the top right. Click it. The
   panel on the left shows oxygen: its number, 8, its mass, and a
   drawing of its atom.
2. Now find **Fe**, iron, in the middle. Click it. Read where it was
   discovered and what it is used for.
3. Type *gold* in the search box at the top. The table lights the tile
   of gold, **Au**.

> [think] The number on each tile counts the atom's protons. Hydrogen
> has 1, oxygen 8, gold 79. The table is in that order, left to right
> and down.

::: try
Find the element you are made of most. Hint: it is in you, in the air
and in the sea, and its tile is **O**'s neighbour, with number 6.
:::
```

```
# Encuentra un elemento

Todo lo que te rodea está hecho de unos noventa tipos de átomos, los
*elementos*. La tabla periódica los enseña todos en una sola hoja.

![Casillas de la tabla, una iluminada](images/kalzium-table.svg)

1. Busca la casilla con una **O**, cerca de arriba a la derecha. Haz
   clic. El panel de la izquierda enseña el oxígeno: su número, 8, su
   masa y un dibujo de su átomo.
2. Ahora busca **Fe**, el hierro, en el medio. Haz clic. Lee dónde se
   descubrió y para qué se usa.
3. Escribe *oro* en la caja de búsqueda de arriba. La tabla ilumina la
   casilla del oro, **Au**.

> [think] El número de cada casilla cuenta los protones del átomo. El
> hidrógeno tiene 1, el oxígeno 8, el oro 79. La tabla va en ese orden,
> de izquierda a derecha y hacia abajo.

::: try
Encuentra el elemento del que estás hecho sobre todo. Pista: está en ti,
en el aire y en el mar, y su casilla es vecina de la **O**, con el
número 6.
:::
```

`02-hot-and-cold.md`

```
# Hot and cold

Every element is a solid, a liquid or a gas, depending on how hot it is.
Kalzium has a slider that changes the temperature of the whole table.

![Three tiles: a solid, a liquid, a gas](images/kalzium-states.svg)

1. In the **Gradients** menu at the top, choose **State of matter**.
   The tiles take three colours: solid, liquid and gas.
2. Open the **View** tab of the panel on the left. It has a temperature
   slider, in kelvin, K: 0 K is the coldest there can be, and a room is
   about 293 K. Put it there: most tiles are solid, a few are gases, and
   only two are liquids.
3. Drag the slider down, towards 0. Watch the gases turn liquid, then
   solid, one by one.
4. Drag it up, past 1000 K. The metals melt. Keep going: they boil.

> [point] Mercury, **Hg**, is a liquid at room temperature: the silver
> inside an old thermometer. Bromine, **Br**, is the other.

::: try
Find the temperature where iron melts. Then the one where it boils.
Which element stays solid longest as you heat the table?
:::
```

```
# Caliente y frío

Cada elemento es un sólido, un líquido o un gas, según lo caliente que
esté. Kalzium tiene un deslizador que cambia la temperatura de toda la
tabla.

![Tres casillas: un sólido, un líquido, un gas](images/kalzium-states.svg)

1. En el menú **Gradientes** de arriba, elige **Estado de la materia**.
   Las casillas toman tres colores: sólido, líquido y gas.
2. Abre la pestaña **Ver** del panel de la izquierda. Tiene un
   deslizador de temperatura, en kelvin, K: 0 K es lo más frío que puede
   haber, y una habitación está a unos 293 K. Ponlo ahí: casi todas las
   casillas son sólidos, unas pocas gases, y solo dos líquidos.
3. Arrastra el deslizador hacia abajo, hacia 0. Mira cómo los gases se
   vuelven líquidos, y luego sólidos, uno a uno.
4. Arrástralo hacia arriba, más allá de 1000 K. Los metales se funden.
   Sigue: hierven.

> [point] El mercurio, **Hg**, es líquido a temperatura ambiente: la
> plata de dentro de un termómetro antiguo. El bromo, **Br**, es el
> otro.

::: try
Busca la temperatura a la que se funde el hierro. Luego la que lo hace
hervir. ¿Qué elemento aguanta sólido más tiempo mientras calientas la
tabla?
:::
```

`03-build-a-molecule.md`

```
# How heavy is water?

Atoms join into *molecules*. Water is two hydrogens and one oxygen,
written H2O. Kalzium can weigh a molecule for you.

![Two atoms joined](images/kalzium-molecule.svg)

1. Press **Perform calculations** in the toolbar. A calculator opens.
2. Choose the **Molecular mass calculator** in the list and type *H2O*.
   It answers about 18: two atoms of mass 1 and one of mass 16.
3. Try *CO2*, the gas you breathe out. Then *NaCl*, table salt.

> [think] The mass of a molecule is just its atoms' masses added up. You
> can check: find H and O in the table and add 1 + 1 + 16.

::: try
Sugar is C6H12O6. Guess its mass before you type it, from the table.
Then see if the calculator agrees.
:::
```

```
# ¿Cuánto pesa el agua?

Los átomos se unen en *moléculas*. El agua son dos hidrógenos y un
oxígeno, y se escribe H2O. Kalzium puede pesar una molécula por ti.

![Dos átomos unidos](images/kalzium-molecule.svg)

1. Pulsa **Realizar cálculos** en la barra. Se abre una calculadora.
2. Elige **Calculadora de masas moleculares** en la lista y escribe
   *H2O*. Responde unos 18: dos átomos de masa 1 y uno de masa 16.
3. Prueba *CO2*, el gas que echas al respirar. Luego *NaCl*, la sal de
   mesa.

> [think] La masa de una molécula es solo la suma de las masas de sus
> átomos. Puedes comprobarlo: busca H y O en la tabla y suma 1 + 1 + 16.

::: try
El azúcar es C6H12O6. Adivina su masa antes de escribirla, con la tabla.
Luego mira si la calculadora está de acuerdo.
:::
```

### 5.5 The user guide, the website and the READMEs

**The user guide, section 5, a new part after *Opening a module*:**

> ### A guide beside a module
>
> Some modules come with a guide: lessons written for the child, with
> steps to follow, what to look for, and ideas to go on with. The guide
> opens on the right when the module opens, and the module takes the
> rest of the screen. **Fold**, at the top of the guide, folds it to a
> thin strip along the edge, for room; a click on the strip, or
> **Guide** on the bar, opens it again, at the lesson the child was in.
> For a child with windows the guide stays while a module with one is
> open, and shows the guide of the module in use; the name at its top
> is a list to pick another, and **Pin** keeps the one chosen whatever
> window is in use. A lesson may have a *mission*, a file of the module's half done,
> with what to try written inside it: the first time the guide opens,
> the missions are copied into the child's **Documents**, in a folder
> named after the module, and the lesson says how to open its mission
> from the module's own **File**, **Open**. Kig, Step and
> Kalzium have a guide.

> ### Una guía al lado de un módulo
>
> Algunos módulos vienen con una guía: lecciones escritas para el niño,
> con pasos que seguir, qué mirar e ideas para continuar. La guía se
> abre a la derecha cuando se abre el módulo, y el módulo ocupa el
> resto de la pantalla. **Plegar**, arriba de la guía, la pliega en una
> tira estrecha pegada al borde, para tener sitio; un clic en la tira, o
> **Guía** en la barra, la abre otra vez, en la lección en la que estaba
> el niño. Para un niño con ventanas la guía se queda mientras haya
> abierto un módulo que la tenga, y enseña la del módulo que está en
> uso; el nombre de arriba es una lista para elegir otra, y **Fijar**
> mantiene la elegida uses la ventana que uses. Una lección puede tener una *misión*, un archivo del módulo a
> medio hacer, con lo que probar escrito dentro: la primera vez que se
> abre la guía, las misiones se copian en los **Documentos** del niño,
> en una carpeta con el nombre del módulo, y la lección dice cómo abrir
> su misión desde el propio módulo, con **Archivo**, **Abrir**. Kig,
> Step y Kalzium tienen guía.

And one sentence in section 5 under *The child's screen*, after the
sentence about links in web modules: *A program that tries to open a
web page or the internet gets a bubble saying it is closed here, and
nothing opens.* / *Un programa que intenta abrir una página web o
internet recibe una burbuja que dice que aquí está cerrado, y no se
abre nada.*

Section 9: Kig's, Step's and Kalzium's sections each gain a sentence,
*It comes with a guide of six lessons* (Kalzium: three) / *Viene con
una guía de seis lecciones* (*tres*), and Kig's picture is taken with
the guide beside it.

**The website**: the cards of Kig, Step and Kalzium add *, with a guide*
/ *, con guía* at the end of their text, and the *grow* part of the page
(the paragraph on windows) gets one sentence, in both toml files, under
a new key `guide`: *A module that is hard to start comes with a guide
beside it: lessons, missions and ideas, in the child's language.* /
*Un módulo difícil de empezar viene con una guía al lado: lecciones,
misiones e ideas, en el idioma del niño.*

**The READMEs**: Kig's, Step's and Kalzium's lines end *, with a guide*
/ *, con guía*.

**Architecture**: a row in section 8's table is not needed; two
decisions, D103 (the pane: the launcher's own layer surface on the
right, folding to a rail, one rule for each mode with the drop-down and
the pin for a child with windows, the lessons' small
Markdown drawn by the launcher, the missions in Documents) and D104
(links out of a module get a bubble and open nothing), written from
section 4.
