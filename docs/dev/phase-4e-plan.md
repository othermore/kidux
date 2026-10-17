# Phase 4e plan — science and maths: Kig, Kalzium, Step and the simulations

Four modules that take Kidux into science and maths, where it has GCompris
for the youngest and nothing after: **Kig**, geometry a child moves with
the mouse; **Kalzium**, the periodic table with what each element is;
**Step**, a physics playground where a child builds an experiment and
presses play; and **Simulations**, a set of PhET's interactive
simulations of physics, chemistry, maths and the Earth, served on the
computer and chosen for ages six to fourteen. The first three are
programs of KDE's education suite that trixie ships, so each module is a
manifest, an icon, its words and a short starter, as Tux Typing's and
GCompris's are; the fourth is a web application served by
`kidux-webapps`, as Blockly Games is, from files fetched at development
time (D68). This plan is how. It follows phase-4c-plan.md's rules
(section 3 there) and D93: a commit per step, partial tests while
building and never the battery, every user-facing word through i18n in
both languages, a package's new version at its first change and `~dev`
builds of it until the owner tries the work and says yes.

Section 4 records what the owner decided on 2026-10-16, and the one
thing left for the owner to confirm, which the steps follow. Section 5
is the content, ready to use: every word of the four modules in English
and Spanish, and the list of simulations.

## 1. Steps

| Step | What | Size |
|---|---|---|
| 4.27 | Kig: geometry to move, a KDE program as a module | S |
| 4.28 | Kalzium: the periodic table | S |
| 4.29 | Step: a physics playground | S |
| 4.30 | Simulations: PhET's simulations, served on the computer, in a page of Kidux's own | L |
| 4.31 | Closing: the documents, the report | S |

4.27, 4.28 and 4.29 are the same work three times and go first, in that
order, so that what 4.27 settles (the starter, the restrictions, the
tests) is copied twice. 4.30 is the long one and stands alone.

## 2. The steps

### What the three KDE modules share

Each is `packages/kidux-module-<id>/`, started from `kidux-module-tuxtype`
(modules.md, section 5: a module that runs a program already in Debian
has no content): the manifest, `icon.svg`, `bin/kidux-module-<id>`, `po/`,
`tests/test_module.py` and `debian/`. Three things are the same in all
three and decided once, in 4.27:

- **The dependencies.** The program's package, and the Wayland plugin of
  its Qt, which the program's own package does not pull in and without
  which it opens nothing under labwc: `qtwayland5` for Kig, which is a
  KDE Frameworks 5 program on Qt 5; `qt6-wayland` for Kalzium and Step,
  Frameworks 6 on Qt 6, as `kidux-module-gcompris` already names it.
  Removing the module takes the program and the libraries that came for
  it alone (D100).
- **The starter**, a POSIX shell script installed to
  `/usr/libexec/kidux-module-<id>`, as Tux Typing's. It writes, the first
  time, a `kdeglobals` into the module's own `XDG_CONFIG_HOME` (which the
  launcher gives it, modules.md section 2), with KDE's action
  restrictions, which every Frameworks program reads from there:

  ```
  [KDE Action Restrictions][$i]
  ghns=false
  shell_access=false
  action/help_report_bug=false
  action/help_donate=false
  ```

  `ghns` is *Get Hot New Stuff*, the dialog that downloads experiments
  and the like from store.kde.org, which Step offers in its File menu and
  a child has no business in; `shell_access` keeps the programs from
  opening a terminal or running a command; the two help actions open a
  web browser the child has not, and would only fail. A `kdeglobals`
  already there is never touched, as GCompris's configuration is not.
  Then it `exec`s the program. Nothing else is set: the language is the
  session's, which the Frameworks read from `LANGUAGE` and `LANG`, and
  the program's own settings are its own, under the same directory.
- **The window.** Each starts in a window and the compositor gives it the
  room above the bar; its dialogs float over it. `app_ids` names what
  the Frameworks call the window on Wayland, the desktop file's name,
  and the binary's name beside it for a program that sets none:
  `["org.kde.kig", "kig"]`, `["org.kde.kalzium", "kalzium"]`,
  `["org.kde.step", "step"]`. The launcher's log says which it was
  (`toplevels:`), and the manifest keeps the one seen. `needs_windows`
  is not set: one main window each, as GCompris.
- **The tests.** Unit, as Tux Typing's: the manifest reads as the one
  reader reads it, the words are complete, the starter writes the
  restrictions once and `exec`s the program (a stand-in `kig` on the
  `PATH` prints what it got), the manifest's version is the package's.
  Acceptance, `tests/acceptance/21-module-kig.sh` and the next two
  numbers, with 24 left for 4.30 (`21-no-key-no-archive.sh` becomes
  `25-no-key-no-archive.sh` in 4.27, since it stays last): installs through the daemon with its program and its Wayland
  plugin, the manifest, icon and Spanish words in place, listed for a
  child switched off, removed without a trace and the program gone with
  it (D100). Session, `tests/session/36-module-kig.py` and the next two,
  with 39 left for 4.30 (`36-purge.py` becomes `40-purge.py` in 4.27): as `25-module-tuxtype.py`, Leo opens
  the tile, the window fills the room above the bar with the bar whole
  under it, its process has the module's directories and the
  restrictions file is there, the picture `module-<id>` taken once the
  window is drawn, Alt+F4 closes it and the launcher comes back, Leo logs
  out, the daemon removes it. Each picture is listed in
  `tests/lib/doc-screenshots.txt` and shown in the guide.
- **The documents.** The user guide, a section each after Gmail's in
  section 9, in both languages, with the words of section 5; the website,
  a card each in `site/en.toml` and `site/es.toml` and its place in
  `site/page.html`, and the licence line that names the modules' authors,
  on a branch of its own, `site-phase-4e`, since the site is built only
  with every picture it shows, and the modules' pictures come from the
  release run; the branch is picked onto `main` after it;
  architecture.md's table in section 8, a row each; the roadmap.
- **The icons**, drawn like the avatars (branding/README.md): flat
  shapes, no gradients, nothing thinner than four units, and nothing of
  KDE's own icons, which are theirs. Kig: a compass drawing an arc over
  a point and a line. Kalzium: four tiles of a periodic table, one
  lifted. Step: a ball on a spring, with a small arrow of its motion.
  Simulations: a flask beside a magnet with two field lines.

### 4.27 — Kig

**What it is.** Kig 25.04, `kig` in trixie: interactive geometry. A child
puts points, lines, circles and polygons on a canvas, drags any of them,
and sees what stays true: the perpendicular stays perpendicular, the
circle through three points follows them. Translated into Spanish, with
its menus and its construction help. 11 MB, plus Frameworks 5 and Qt 5,
which no other module brings: the first KDE 5 program on the machine,
so the install is long and the removal takes it all away again.

**The manifest.** `id = "kig"`, `name`, `description`, ages 10 to 14,
`recommended_before = ["gcompris"]` (GCompris has the first shapes),
`launch = { exec = "/usr/libexec/kidux-module-kig" }`, `app_ids` as
above, `categories = ["maths"]`, `memory_max = "1G"`.

**Found on the machine first**, with `tests/run vm up 04` and the
package pushed: whether Kig opens on labwc with `qtwayland5` and what
its window's `app_id` is; whether it asks anything at its first start
(it should not: an empty canvas); that its *Help* entries fail quietly
with the restrictions and that no menu reaches a terminal; and how the
canvas looks at scale 2 (`20-scale.py`'s setting): the session sets only
`QT_QPA_PLATFORM=wayland`, and Qt takes the scale from the compositor.
What is found goes into the starter's comment and this plan's section
4 if it changes a decision.

### 4.28 — Kalzium

**What it is.** Kalzium 25.04, `kalzium` with `kalzium-data`: the
periodic table. Every element with its facts, pictures and a drawing of
its atom, a timeline of their discovery, the states of matter at any
temperature on a slider, a glossary, and calculators of molecular mass
and the like for the older. Translated into Spanish. Frameworks 6 and
Qt 6, which GCompris already brings, so it is small to install.

**The manifest.** `id = "kalzium"`, ages 10 to 16, no
`recommended_before`, `categories = ["science"]`, `memory_max = "1G"`.
Nothing of Kalzium's reaches the internet: its data is in
`kalzium-data`.

**Found on the machine first**: as 4.27's, and whether its sidebar and
table fit 1280x800 at scale 1 and 2. Its window is `org.kde.kalzium`
and it asks nothing at its first start; at scale 1 the table, the
element's card and the legend fill the room above the bar, and at
scale 2, 640x400, they fit but crowded, the table small beside the card.

### 4.29 — Step

**What it is.** Step 25.04, `step`: a physics simulator. A child puts
bodies, springs, ropes, gravity and forces on a plane, presses play and
watches, with graphs and meters to read what happens; its example
experiments and the explanations of each object are translated into
Spanish (`step_example_files`, `step_objinfo_files`). Frameworks 6 and
Qt 6.

**The manifest.** `id = "step"`, ages 10 to 16,
`recommended_before = ["simulations"]` (the simulations show the ideas;
Step lets a child build them), `categories = ["science"]`,
`memory_max = "2G"`.

**The restrictions matter here**: Step's *File* menu has *Download New
Experiments*, which `ghns=false` removes. The session test checks that
the menu has no such entry, by Step's own log or the `kdeglobals` being
read: the simplest sure check is that the file is there and that the
process's `XDG_CONFIG_HOME` is the module's.

**Found on the machine first**: as 4.27's, and whether Step's world view
draws on the test machine without a GPU (it has an OpenGL option, off by
default; the default `QGraphicsView` is what the module keeps). Its
window is `org.kde.step`, it asks nothing at its first start, and its
File menu has *Open Tutorial* and *Examples* and no *Download New
Experiments*. At scale 1 the palette, the world and its four panels fit
the room above the bar; at scale 2 the panels on the right are too
short for their contents and overlap.

### 4.30 — Simulations

**What it is.** PhET Interactive Simulations, of the University of
Colorado Boulder: HTML5 simulations of physics, chemistry, maths, the
Earth and life, each one file that runs by itself in a browser, each
translated into Spanish and some sixty other languages, each with its
own *About* dialog that names its authors and licence. The module serves
a chosen set of them on the computer, under `kidux-webapps`, in a page
of Kidux's own that lists them by group and age in the child's language
and opens each one, so that nothing needs the internet (section 4,
decision 2 and the one to confirm).

**The licence, and the versions this takes.** PhET relicensed its
simulations on 29 March 2026: the files it publishes since are
*Creative Commons Attribution-NonCommercial 4.0*, which forbids
commercial use without an agreement, and Kidux's own licence lets an
organisation use Kidux only under a licence from the owner, which is
commercial use of what Kidux ships. The versions published *before*
that day are, by PhET's own agreement for its historical collection
(https://phet.colorado.edu/en/licensing/html), *Creative Commons
Attribution 4.0*: free to use and redistribute, commercially or not,
with the attribution *Simulation by PhET Interactive Simulations,
University of Colorado Boulder, licensed under CC BY 4.0
(https://phet.colorado.edu)* close to where they are used, human
readable, translatable and not otherwise changed; the PhET logo inside
a simulation visible, unobstructed and unaltered; and the PhET name
used for nothing promotional. PhET still serves every published
version at `https://phet.colorado.edu/sims/html/<sim>/<version>/<sim>_all.html`
(the `latest` directory holds the current one; a listing of the
directory is refused), and each file says inside it when it was built
(`buildTimestamp = '2026-01-30 13:30:03 UTC'`) and which licence it
carries (a link to `creativecommons.org/licenses/by/4.0`, or to
`by-nc/4.0`). So the module takes, for each simulation, the newest
version built before 29 March 2026 whose file names CC BY 4.0, and no
other: the build refuses a file that names `by-nc`, and the list
records each version and its sum, so that the same list gives the same
bytes. These versions are the ones PhET calls outdated and unmaintained:
they are the simulations as they were in early 2026, which is what a
child needs, and they never change under the module.

**The name.** The module is *Simulations* (*Simulaciones*), `id =
"simulations"`, not *PhET*: PhET is a trademark the agreement keeps for
its owner, so the name says what the module is and the description says
whose the simulations are, which the attribution requires, and that
Kidux is not connected with PhET (as D86 says of CodeCombat). The
package is `kidux-module-simulations`.

**The files, fetched at development time.** `upstream.toml` and a
build script, `ci/upstream/simulations.sh`, as Blockly Games has, with
one difference that is a small change to the machinery (D68): there is
no repository and no commit, since the simulations are built by PhET
and taken as files. `upstream.toml` gets `repository = ""` and
`commit = ""`, and `tests/project/upstream.sh` accepts the pair empty
together, the build then being a fetch of files alone;
`ci/build-upstream.sh` passes them through as they are, and the build
script takes the tarball's time from the newest `buildTimestamp` among
the files, since there is no commit's. The script reads the list,
`packages/kidux-module-simulations/sims.toml` (section 5.4), fetches
each file through `ci/upstream/fetch.sh url`, checks its sum against
the list's, its `buildTimestamp` against the cut-off and its licence
link, and packs them as `sims/<sim>_all.html` under one directory, with
PhET's attribution in a `LICENSE` beside them. The source tarball holds
the same files (D71). The first build of the list is what fills the
sums: `sims.toml` is written with each simulation's version and an
empty sum, the script writes the sums it finds into `build/` and the
developer copies them in, as `upstream.toml`'s sum is written by the
first build; a sum that then differs is an error. Finding each
version: from the current version's number, which the `latest` file
names (`"version":"1.9.3"`), the script that *prepares* the list (a
development tool, `ci/upstream/simulations-versions.py`, run by hand
once) tries the same minor's patches downwards and then the previous
minor's, and keeps the newest whose file is built before the cut-off
and names CC BY 4.0; what it finds is written into `sims.toml` and
committed, and the build never guesses.

**The page.** One `index.html` written at build time by
`webapp/page.py`, as hello-web's and BASIC's are, with every language's
words in it: Kidux's colours and type, a heading, the groups of section
5.4 in order, each a row of tiles, a tile the simulation's title in the
child's language and its ages; a tile opens the simulation *in the same
page*, in an `iframe` that fills the room under a slim bar of Kidux's
own with *Simulations* (back to the list) and the simulation's title,
so that a child always has the way back, which a simulation's page has
not. The simulation's address is `sims/<sim>_all.html?locale=<lang>`,
the file choosing its language by that parameter. At the foot of the
list, the attribution line, translated into the child's language as
the agreement allows, with PhET's address as text. The page needs
nothing of the internet, and `ci/upstream/check-site.py` holds the
files to that; the module names no `hosts`.

**The manifest.** `id = "simulations"`, ages 6 to 14, no
`recommended_before`, `launch = { webapp = "simulations" }`,
`categories = ["science", "maths"]`, `memory_max = "2G"`. The package
depends on `kidux-webapps` and installs the page and the files under
`/usr/share/kidux/webapps/simulations/`; its `debian/copyright` has
`Files: upstream/sims/*` under CC-BY-4.0 with the attribution, and
names that each file carries, in its *About*, the libraries inside it
under their own licences.

**Size.** The set in section 5.4 is 49 simulations of about 3.3 MB
each, all languages in each file: about 160 MB installed, between
Blockly Games and ScratchJr. The owner may cut the list; the groups
and the page take any number.

**Tests.** Unit: `sims.toml` reads, every simulation in it has a title in
every language the module has words for, the page builds with them,
`page.py`'s words are complete. Project: `tests/project/upstream.sh`'s
new case. Acceptance: installs through the daemon with
`kidux-webapps`, the server answers for the page and for one
simulation's file in Spanish, the file carries the CC BY 4.0 link and
not `by-nc`, listed for a child switched off, removed with the server
and the policy when it was the last web module (D100). Session,
`tests/session/39-module-simulations.py`, and acceptance
`tests/acceptance/24-module-simulations.sh`:
Leo opens the tile, the list is drawn in Spanish (the picture
`module-simulations`), a tile opened by keyboard shows a simulation in
the frame with the bar's *Simulations* above it (the picture
`module-simulations-open`), *Simulations* goes back to the list,
Alt+F4 closes it. Both pictures in the guide.

**Documents.** modules.md section 4 gets a sentence on a web application
whose files are fetched, not built; packaging.md's "Programs built at
development time" the same, and `upstream.toml`'s empty pair; the user
guide's section, with the licence and the attribution said plainly;
the website's card and its licence line; architecture.md section 8 and
the two decisions of section 4 as D101 and D102, once the owner has
confirmed the one to confirm.

### 4.31 — Closing

The documents read once more against what was built; the roadmap's
phase 4 ticked; the final message to the owner: what was built, how to
try each module on the MacBook, and the prompt for the review. No
battery: the owner tries the work first (CLAUDE.md).

## 3. Rules for this plan

As phase-4c-plan.md section 3, and:

- **Partial tests only.** Each step is tried on the machine left up
  (`tests/run vm up 04`, `vm push`, its session test with `vm test NN`)
  and its unit and acceptance tests; the battery is the owner's to ask
  for after their own tries.
- **Nothing of KDE's or PhET's is drawn.** The icons are Kidux's own,
  like the avatars. The PhET logo inside each simulation stays as it is.
- **The simulations' files are never edited**, and the attribution is
  never dropped: a file is taken whole or not at all.
- **The cut-off is a rule of the build, not a note.** A simulation file
  that names `by-nc` fails the build, whatever its date says.

## 4. What the owner decided

Decided 2026-10-16 by the owner.

1. **Four science and maths modules at once**: Kig, Kalzium and Step
   from trixie, each its own module, and a set of PhET's simulations
   served on the computer. Each is installed, enabled and removed on its
   own, as every module is.
2. **The simulations are shipped, not opened on PhET's site**, so that
   they work without the internet, as Blockly Games does; the page that
   lists them is Kidux's own, in both languages.
3. **Opus builds, Fable reviews.** The steps are built by Opus from this
   plan with partial tests only; Fable then reviews everything; the
   owner tries the work; the battery and the release come after.

**To confirm by the owner, before 4.30 starts** (proposed by Fable on
2026-10-16, after reading PhET's licensing): that the module takes the
historical versions of the simulations, published before 29 March 2026
under CC BY 4.0, and never a file under CC BY-NC 4.0, which Kidux's own
licence to organisations could not carry; and that the module is named
*Simulations*, with PhET named in its description as the simulations'
author, not in its name. The alternative, if the owner prefers the
current versions, is a door to phet.colorado.edu (D85), which ships
nothing and needs the internet; then 4.30 is a module like Wikipedia's,
with a page of Kidux's own that links to each simulation on the site,
and the rest of this plan stands.

## 5. The content

Every word below is used as written: the manifests' `name` and
`description`, the catalogues' Spanish, the panel's fields, the guide's
sections and the website's cards. English first, Spanish beside it.

### 5.1 The manifests and the catalogues

| Module | `name` | `description` (English) | Spanish `name` | Spanish `description` |
|---|---|---|---|---|
| kig | Kig | Geometry you can move: points, lines, circles and shapes that keep their rules when you drag them. | Kig | Geometría que se mueve: puntos, rectas, circunferencias y figuras que conservan sus reglas cuando las arrastras. |
| kalzium | Kalzium | The periodic table: every element, what it is like, its atom, and how matter changes with the temperature. | Kalzium | La tabla periódica: cada elemento, cómo es, su átomo, y cómo cambia la materia con la temperatura. |
| step | Step | A physics playground: put springs, weights and forces on the table, press play and see what happens. | Step | Un laboratorio de física: pon muelles, pesos y fuerzas sobre la mesa, dale a reproducir y mira qué pasa. |
| simulations | Simulations | Experiments to play with on the screen: numbers, forces, light, electricity, matter, planets and life. Simulations by PhET Interactive Simulations, University of Colorado Boulder, licensed under CC BY 4.0; Kidux is not connected with PhET. | Simulaciones | Experimentos para jugar en la pantalla: números, fuerzas, luz, electricidad, materia, planetas y vida. Simulaciones de PhET Interactive Simulations, Universidad de Colorado Boulder, bajo licencia CC BY 4.0; Kidux no tiene relación con PhET. |

Ages and what comes before, for `XB-Kidux-Ages` and `XB-Kidux-Before`:
Kig 10–14, before it GCompris; Kalzium 10–16; Step 10–16, before it
Simulations; Simulations 6–14.

The `debian/control` short descriptions: *Kidux learning module: Kig,
geometry to move for ages ten to fourteen*; *Kidux learning module:
Kalzium, the periodic table for ages ten and up*; *Kidux learning
module: Step, a physics playground for ages ten and up*; *Kidux learning
module: Simulations, PhET's simulations of science and maths, served on
this computer*. The long descriptions follow Tux Typing's shape: what
the program is, in the child's language, and the sentence about the
Modules page.

### 5.2 The user guide, section 9, after Gmail

**Kig**

> **Kig** is geometry a child can move. Points, lines, circles and
> shapes go on the canvas, and each keeps its rule when the child drags
> what it was built from: the middle stays in the middle, the parallel
> stays parallel. It is for children from ten to fourteen, in the
> child's language, and it works without the internet. What a child
> draws can be saved as a file in their folders.

> **Kig** es geometría que el niño puede mover. Los puntos, las rectas,
> las circunferencias y las figuras se ponen sobre el lienzo, y cada una
> conserva su regla cuando el niño arrastra aquello de lo que se
> construyó: el punto medio sigue en medio, la paralela sigue paralela.
> Es para niños de diez a catorce años, en el idioma del niño, y
> funciona sin internet. Lo que el niño dibuja se puede guardar como un
> archivo en sus carpetas.

**Kalzium**

> **Kalzium** is the periodic table. Each element opens with what it is
> like, where it was found, a picture of it and a drawing of its atom; a
> slider shows which elements are solid, liquid or gas at any
> temperature; and there is a glossary of the words. It is for children
> from ten up, in the child's language, and it works without the
> internet.

> **Kalzium** es la tabla periódica. Cada elemento se abre con cómo es,
> dónde se encontró, una foto y un dibujo de su átomo; un deslizador
> enseña qué elementos son sólidos, líquidos o gases a cada temperatura;
> y hay un glosario de las palabras. Es para niños de diez años en
> adelante, en el idioma del niño, y funciona sin internet.

**Step**

> **Step** is a physics playground. The child puts bodies, springs,
> ropes and forces on the plane, presses play and watches what happens,
> with meters and graphs to read it; the examples in its File menu are
> experiments ready to run. It is for children from ten up, in the
> child's language, and it works without the internet; its menu to
> download more experiments is switched off. An experiment can be saved
> as a file in the child's folders.

> **Step** es un laboratorio de física. El niño pone cuerpos, muelles,
> cuerdas y fuerzas sobre el plano, le da a reproducir y mira qué pasa,
> con medidores y gráficas para leerlo; los ejemplos de su menú Archivo
> son experimentos listos para correr. Es para niños de diez años en
> adelante, en el idioma del niño, y funciona sin internet; su menú para
> descargar más experimentos está apagado. Un experimento se puede
> guardar como un archivo en las carpetas del niño.

**Simulations**

> **Simulations** are experiments to play with on the screen: build a
> number, balance a seesaw, bend a ray of light, rub a balloon on a
> sweater, build an atom, put planets in orbit. They are PhET's
> interactive simulations, made by the University of Colorado Boulder
> and used in schools everywhere, chosen here for children from six to
> fourteen and sorted by group and age, in the child's language. They
> are on the computer and work without the internet. Each one opens in
> its own frame, with **Simulations** at the top to come back to the
> list. The simulations are the versions PhET published under the
> Creative Commons Attribution 4.0 licence; Kidux is not connected with
> PhET.

> **Simulaciones** son experimentos para jugar en la pantalla: formar un
> número, equilibrar un balancín, doblar un rayo de luz, frotar un globo
> en un jersey, construir un átomo, poner planetas en órbita. Son las
> simulaciones interactivas de PhET, hechas por la Universidad de
> Colorado Boulder y usadas en escuelas de todo el mundo, elegidas aquí
> para niños de seis a catorce años y ordenadas por grupo y edad, en el
> idioma del niño. Están en el ordenador y funcionan sin internet. Cada
> una se abre en su propio marco, con **Simulaciones** arriba para
> volver a la lista. Las simulaciones son las versiones que PhET publicó
> bajo la licencia Creative Commons Atribución 4.0; Kidux no tiene
> relación con PhET.

Each section ends with its picture, `module-<id>.png`, and Simulations
with `module-simulations-open.png` after the paragraph too.

### 5.3 The website's cards

| Card | `name` | `age` | `text` |
|---|---|---|---|
| kig (en) | Kig | Ages 10 to 14 | Geometry you can drag: shapes that keep their rules. |
| kig (es) | Kig | De 10 a 14 años | Geometría que se arrastra: figuras que conservan sus reglas. |
| kalzium (en) | Kalzium | Ages 10 and up | The periodic table, element by element. |
| kalzium (es) | Kalzium | De 10 años en adelante | La tabla periódica, elemento a elemento. |
| step (en) | Step | Ages 10 and up | Build a physics experiment and press play. |
| step (es) | Step | De 10 años en adelante | Monta un experimento de física y dale a reproducir. |
| simulations (en) | Simulations | Ages 6 to 14 | PhET's science and maths experiments, on the computer. |
| simulations (es) | Simulaciones | De 6 a 14 años | Los experimentos de ciencias y matemáticas de PhET, en el ordenador. |

The licence line of the website (`others`) adds *Kig, Kalzium, Step and
PhET's simulations* to the programs that belong to their authors; the
anchors are the guide's section names in each language.

### 5.4 The simulations

`packages/kidux-module-simulations/sims.toml`, as the build and the page
read it. The groups are the page's rows, in this order, each with its
title in both languages through the module's catalogue; a simulation
has its PhET name (its directory on the site), its title as PhET gives
it in each language (the Spanish ones are PhET's own translations), its
ages, its version (the newest built before 29 March 2026, found by the
versions tool and filled in by Opus) and its sum (filled in by the first
build). The titles are data of the simulations, not words of Kidux's,
which is why they are here and not in the catalogue.

```toml
# The simulations the module serves (phase-4e-plan.md, 4.30): PhET's
# historical versions, under CC BY 4.0, each the newest built before
# 29 March 2026. Versions and sums are filled in by the tools, never by
# hand; the build refuses a file that is not what is written here.
cutoff = "2026-03-29"
attribution = "Simulation by PhET Interactive Simulations, University of Colorado Boulder, licensed under CC BY 4.0 (https://phet.colorado.edu)"

[[groups]]
id = "numbers"          # Numbers and shapes / Números y formas
ages = "6-10"
sims = ["make-a-ten", "number-play", "number-compare", "number-pairs", "arithmetic",
        "area-builder", "quadrilateral", "fractions-intro", "build-a-fraction",
        "fraction-matcher"]

[[groups]]
id = "more-numbers"     # More numbers / Más números
ages = "9-14"
sims = ["number-line-integers", "ratio-and-proportion", "proportion-playground",
        "area-model-introduction", "equality-explorer-basics", "function-builder-basics",
        "unit-rates", "plinko-probability", "graphing-lines"]

[[groups]]
id = "forces"           # Forces and energy / Fuerzas y energía
ages = "8-14"
sims = ["forces-and-motion-basics", "balancing-act", "friction", "energy-skate-park-basics",
        "energy-forms-and-changes", "masses-and-springs-basics", "pendulum-lab",
        "projectile-motion", "gravity-force-lab-basics"]

[[groups]]
id = "light"            # Light, sound and waves / Luz, sonido y ondas
ages = "8-14"
sims = ["color-vision", "bending-light", "geometric-optics-basics", "waves-intro",
        "wave-on-a-string"]

[[groups]]
id = "electricity"      # Electricity and magnets / Electricidad e imanes
ages = "8-14"
sims = ["balloons-and-static-electricity", "john-travoltage", "magnet-and-compass",
        "magnets-and-electromagnets", "circuit-construction-kit-dc"]

[[groups]]
id = "matter"           # Matter and atoms / La materia y los átomos
ages = "9-14"
sims = ["states-of-matter-basics", "gases-intro", "density", "buoyancy-basics",
        "build-an-atom", "build-a-molecule", "concentration", "ph-scale-basics"]

[[groups]]
id = "earth"            # Earth, space and life / La Tierra, el espacio y la vida
ages = "8-14"
sims = ["gravity-and-orbits", "my-solar-system", "greenhouse-effect", "under-pressure",
        "natural-selection"]

[sims.make-a-ten]
title = { en = "Make a Ten", es = "Haz un Diez" }
version = ""
sha256 = ""
[sims.number-play]
title = { en = "Number Play", es = "Juego de Números" }
version = ""
sha256 = ""
[sims.number-compare]
title = { en = "Number Compare", es = "Comparar Números" }
version = ""
sha256 = ""
[sims.number-pairs]
title = { en = "Number Pairs", es = "Pares de Números" }
version = ""
sha256 = ""
[sims.arithmetic]
title = { en = "Arithmetic", es = "Aritmética" }
version = ""
sha256 = ""
[sims.area-builder]
title = { en = "Area Builder", es = "Constructor de Áreas" }
version = ""
sha256 = ""
[sims.quadrilateral]
title = { en = "Quadrilateral", es = "Cuadrilátero" }
version = ""
sha256 = ""
[sims.fractions-intro]
title = { en = "Fractions: Intro", es = "Fracciones: Intro" }
version = ""
sha256 = ""
[sims.build-a-fraction]
title = { en = "Build a Fraction", es = "Construye una fracción" }
version = ""
sha256 = ""
[sims.fraction-matcher]
title = { en = "Fraction Matcher", es = "Parejas de Fracciones" }
version = ""
sha256 = ""
[sims.number-line-integers]
title = { en = "Number Line: Integers", es = "Recta Numérica: Enteros" }
version = ""
sha256 = ""
[sims.ratio-and-proportion]
title = { en = "Ratio and Proportion", es = "Razón y Proporción" }
version = ""
sha256 = ""
[sims.proportion-playground]
title = { en = "Proportion Playground", es = "Pista de juego de proporciones" }
version = ""
sha256 = ""
[sims.area-model-introduction]
title = { en = "Area Model Introduction", es = "Modelo de Áreas: Introducción" }
version = ""
sha256 = ""
[sims.equality-explorer-basics]
title = { en = "Equality Explorer: Basics", es = "Explorador de Igualdades: Intro" }
version = ""
sha256 = ""
[sims.function-builder-basics]
title = { en = "Function Builder: Basics", es = "Generador de funciones: Intro" }
version = ""
sha256 = ""
[sims.unit-rates]
title = { en = "Unit Rates", es = "Razón unitaria" }
version = ""
sha256 = ""
[sims.plinko-probability]
title = { en = "Plinko Probability", es = "Probabilidad Plinko" }
version = ""
sha256 = ""
[sims.graphing-lines]
title = { en = "Graphing Lines", es = "Graficando Rectas" }
version = ""
sha256 = ""
[sims.forces-and-motion-basics]
title = { en = "Forces and Motion: Basics", es = "Fuerzas y Movimiento: Intro" }
version = ""
sha256 = ""
[sims.balancing-act]
title = { en = "Balancing Act", es = "Ley de equilibrio" }
version = ""
sha256 = ""
[sims.friction]
title = { en = "Friction", es = "Fricción" }
version = ""
sha256 = ""
[sims.energy-skate-park-basics]
title = { en = "Energy Skate Park: Basics", es = "Energía en la pista de patinaje: Intro" }
version = ""
sha256 = ""
[sims.energy-forms-and-changes]
title = { en = "Energy Forms and Changes", es = "Formas y Cambios de Energía" }
version = ""
sha256 = ""
[sims.masses-and-springs-basics]
title = { en = "Masses and Springs: Basics", es = "Masas y Resortes: Intro" }
version = ""
sha256 = ""
[sims.pendulum-lab]
title = { en = "Pendulum Lab", es = "Lab de Péndulo" }
version = ""
sha256 = ""
[sims.projectile-motion]
title = { en = "Projectile Motion", es = "Movimiento de un Proyectil" }
version = ""
sha256 = ""
[sims.gravity-force-lab-basics]
title = { en = "Gravity Force Lab: Basics", es = "Lab de Fuerza de Gravedad: Intro" }
version = ""
sha256 = ""
[sims.color-vision]
title = { en = "Color Vision", es = "Visión del color" }
version = ""
sha256 = ""
[sims.bending-light]
title = { en = "Bending Light", es = "Reflexión y Refracción de la Luz" }
version = ""
sha256 = ""
[sims.geometric-optics-basics]
title = { en = "Geometric Optics: Basics", es = "Óptica Geométrica: Intro" }
version = ""
sha256 = ""
[sims.waves-intro]
title = { en = "Waves Intro", es = "Ondas: Intro" }
version = ""
sha256 = ""
[sims.wave-on-a-string]
title = { en = "Wave on a String", es = "Onda en una cuerda" }
version = ""
sha256 = ""
[sims.balloons-and-static-electricity]
title = { en = "Balloons and Static Electricity", es = "Globos y electricidad estática" }
version = ""
sha256 = ""
[sims.john-travoltage]
title = { en = "John Travoltage", es = "Travoltaje" }
version = ""
sha256 = ""
[sims.magnet-and-compass]
title = { en = "Magnet and Compass", es = "Imán y brújula" }
version = ""
sha256 = ""
[sims.magnets-and-electromagnets]
title = { en = "Magnets and Electromagnets", es = "Imanes y Electroimanes" }
version = ""
sha256 = ""
[sims.circuit-construction-kit-dc]
title = { en = "Circuit Construction Kit: DC", es = "Kit de Construcción de Circuitos: CD" }
version = ""
sha256 = ""
[sims.states-of-matter-basics]
title = { en = "States of Matter: Basics", es = "Estados de la Materia: Intro" }
version = ""
sha256 = ""
[sims.gases-intro]
title = { en = "Gases Intro", es = "Gases: Intro" }
version = ""
sha256 = ""
[sims.density]
title = { en = "Density", es = "Densidad" }
version = ""
sha256 = ""
[sims.buoyancy-basics]
title = { en = "Buoyancy: Basics", es = "Flotabilidad: Intro" }
version = ""
sha256 = ""
[sims.build-an-atom]
title = { en = "Build an Atom", es = "Construye un Átomo" }
version = ""
sha256 = ""
[sims.build-a-molecule]
title = { en = "Build a Molecule", es = "Construye una Molécula" }
version = ""
sha256 = ""
[sims.concentration]
title = { en = "Concentration", es = "Concentración" }
version = ""
sha256 = ""
[sims.ph-scale-basics]
title = { en = "pH Scale: Basics", es = "Escala pH: Intro" }
version = ""
sha256 = ""
[sims.gravity-and-orbits]
title = { en = "Gravity and Orbits", es = "Gravedad y Órbitas" }
version = ""
sha256 = ""
[sims.my-solar-system]
title = { en = "My Solar System", es = "Mi Sistema Solar" }
version = ""
sha256 = ""
[sims.greenhouse-effect]
title = { en = "Greenhouse Effect", es = "Efecto Invernadero" }
version = ""
sha256 = ""
[sims.under-pressure]
title = { en = "Under Pressure", es = "Bajo presión" }
version = ""
sha256 = ""
[sims.natural-selection]
title = { en = "Natural Selection", es = "Selección Natural" }
version = ""
sha256 = ""
```

The page's own words, in the module's catalogue: the heading
*Simulations* / *Simulaciones*; the groups, *Numbers and shapes* /
*Números y formas*, *More numbers* / *Más números*, *Forces and energy* /
*Fuerzas y energía*, *Light, sound and waves* / *Luz, sonido y ondas*,
*Electricity and magnets* / *Electricidad e imanes*, *Matter and atoms*
/ *La materia y los átomos*, *Earth, space and life* / *La Tierra, el
espacio y la vida*; the ages as the panel says them, *Ages 6 to 10* /
*De 6 a 10 años*; the bar's *Simulations* / *Simulaciones*, which goes
back; and the attribution, *Simulations by PhET Interactive
Simulations, University of Colorado Boulder, licensed under CC BY 4.0
(https://phet.colorado.edu)* / *Simulaciones de PhET Interactive
Simulations, Universidad de Colorado Boulder, bajo licencia CC BY 4.0
(https://phet.colorado.edu)*.

### 5.5 Found so far, for the steps

- trixie: `kig` 4:25.04.0-1 (11 MB, Frameworks 5, Qt 5, with
  `/usr/share/locale/es/LC_MESSAGES/kig.mo`); `kalzium` and
  `kalzium-data` 4:25.04.0-1 (3 MB, Frameworks 6, Spanish in
  `kalzium-data`); `step` 4:25.04.0-1 (13 MB, Frameworks 6, Spanish for
  the program, its examples and its object descriptions). Desktop files
  `org.kde.kig`, `org.kde.kalzium`, `org.kde.step`.
- The session exports `QT_QPA_PLATFORM=wayland` (kidux-session);
  GCompris's module depends on `qt6-wayland`; Qt 5 needs `qtwayland5`.
- PhET: `build-an-atom` is at 1.9.3 (built 2026-08-06, CC BY-NC) and
  its 1.8.3 (built 2026-01-30, CC BY 4.0) is served at
  `/sims/html/build-an-atom/1.8.3/build-an-atom_all.html`, 3.2 MB, as
  are 1.8.0 to 1.8.2; 1.7.0 is not. A directory listing answers 403.
  The file names its licence by a link to creativecommons.org and its
  build by `buildTimestamp`. PhET's metadata
  (`https://phet.colorado.edu/services/metadata/1.3/simulations?format=json&type=html&locale=es&summary`)
  lists every HTML simulation with its Spanish title and its levels,
  which is where section 5.4's titles come from.
