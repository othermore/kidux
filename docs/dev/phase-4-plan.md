# Phase 4 plan — content modules

The first content modules, built on the module framework of phase 3: a
typing course, the Scratch family for the two ages, and Blockly Games. With
them, the way a program that is not in Debian becomes a Kidux package: built
at development time in a machine of its own, published as a tarball, and
packaged from that tarball (D68). Steps 3.29 and 3.30 of phase-3-plan.md,
what the owner's fourth hand test asked for, are built first, in that order,
and then the steps below in theirs.

The contract a module is written to is [modules.md](modules.md), and this
plan changes that document where it says so. Every decision here is in the
decision log of architecture.md (D66 to D70); this plan says how each is
built.

## 1. Where we start

Steps 3.1 to 3.28 are built. The child's session runs under `labwc`; a
module is a Debian package with a manifest, installed and switched on from
the adult panel; a module is a program (GCompris, `kidux-module-hello`) or
a web application served by `kidux-webapps` on `127.0.0.1:8123` and opened
in Chromium's application window, held by a managed policy
(`kidux-module-hello-web`). Every package builds from its own directory in
`packages/`, in native source format, in an unshare chroot without the
network. The battery, `ci/test-release.sh`, builds everything, publishes
it to the local archive's testing suite, and runs the project checks, the
reproducibility rebuild, the acceptance machine and two session machines,
one in Spanish and one in English, whose pictures are the user guide's.

What is not there yet: any program that has to be built with Node.js, any
program that is not in trixie, and the words of the user guide about the
modules a child will really use.

## 2. The steps

| Step | What | Size |
|---|---|---|
| 3.29 (phase-3-plan.md) | Alt+Tab goes round the modules in the bar's order, Home out of it | S |
| 3.30 (phase-3-plan.md) | A session left alone locks, the screen turns off, the lid locks; the minutes an adult's setting | M |
| 4.1 | Upstream builds at development time: `ci/build-upstream.sh` and packages built from a tarball | M |
| 4.2 | The test modules named `[Test]`, and out of the user guide | S |
| 4.3 | `kidux-module-tuxtype`: typing | S |
| 4.4 | `kidux-module-scratch`: the official editor, and Chromium's policy for the child's work | M |
| 4.5 | `kidux-module-turbowarp`: Scratch made faster | S |
| 4.6 | `kidux-module-scratchjr`: ScratchJr, from the community desktop port | M |
| 4.7 | `kidux-module-blockly-games` | S |
| 4.8 | Closing: the roadmap, the pictures, what the owner tries by hand | S |

Sizes are relative effort, as in phase 3. Each step ends with its own
commit, tested on the machine left up for what it touches; the whole
battery runs before the work is pushed (CLAUDE.md).

## 3. Rules for every step

The rules of phase-3-plan.md section 5 apply to every step here, and so
do these:

- **The development machine may have tools installed; a Kidux machine gets
  only what a package depends on.** Node.js, Java or anything a build needs
  is installed on the development machine (from trixie with `apt`, or a
  pinned release under `build/`), and packaging.md lists it. What matters is
  the other direction: nothing a Kidux machine needs may be something the
  development machine happens to have. The package build in the chroot,
  the acceptance and session machines, which start from Debian, are what
  catch a forgotten dependency, and a module's `Depends` is written from
  what the program needs, never from what runs here.
- **A program that is not in trixie arrives as a tarball** built by
  `ci/build-upstream.sh` from a pinned commit of its repository, with its
  SHA-256 recorded in the package's `upstream.toml` and the tarball kept in
  a GitHub release of this repository (D68). Uploading those tarballs to
  GitHub releases is the one thing that goes to GitHub without the owner
  asking each time: it is part of the step. Commits are not pushed unless
  the owner asks.
- **Versions.** Every package a step touches gets a new version in its
  `debian/changelog`, dated by `date -R` (scratchpad `bump.py` does it),
  when it is first changed; a development build of it is
  `<version>~dev.<time>`, which the version itself replaces when its
  battery publishes it (D77). A package built from a
  tarball is versioned `<upstream version>` on its first release and
  `<upstream version>.1`, `.2` for a packaging change without a new
  tarball; the module's manifest `version` is the package's, as always.
- **Where the tests go.** As in phase 3: unit tests beside the code;
  acceptance checks as `kidux-as` commands called from numbered files in
  `tests/acceptance/`; session tests as numbered files in `tests/session/`,
  in name order, the purge test last, renamed to the number after a new
  test's. The battery runs every session test in Spanish, and in English
  the ones that take the guide's pictures or set the machine up
  (tests/README.md): what depends on the language is read from
  `sessionlib.SPEAKS`, never written in the test. A session test that waits more than four
  minutes without pressing a key presses one in its wait, since a child's
  session locks itself after five (3.30).
- **A module test installs its module at its start and removes it at its
  end**, as `19-module-hello-web.py` does, so that the launcher has one tile
  during the test and the picture of an empty launcher stays empty
  afterwards.
- **Pictures.** Every new screen the guide shows is listed in
  `tests/lib/doc-screenshots.txt`; the battery copies each language's to
  `docs/images/<language>/`, and the commit includes them.
- **Documents.** Each step changes the developer document of what it
  builds, in the present, and the user guide's section 9 says what each
  module is as it arrives, in both languages, in the same commit. The
  README's list of modules grows with each module, in both languages.
- **The quick loop before the battery.** A module is first tried on the
  machine left up (`tests/run vm up 04`, `vm push <package>`, `vm test NN`,
  `vm shot`), where a wrong app id, a window that does not appear, a missing
  library or a page that does not load is found in minutes. The battery
  runs whole, in one go, before the work is pushed; one whose only
  failures are a test's own fault needs no second run, only that test run
  again alone.
- **Waiting and killing.** A battery is started detached (`setsid nohup …
  &`), waited for by its PID (`while kill -0 <pid>; do sleep 30; done`),
  never with `pgrep -f` of its own command line; nothing under `packages/`
  or `tests/` is edited while it runs; leftover `/tmp/tmp.sbuild.*`
  directories after a run that died are removed before the next
  (`unshare --map-auto --map-root-user rm -rf`).

## 4. Decisions

Recorded in architecture.md's log; summarised here so that the steps read
on their own.

- **D66** Alt+Tab goes round the modules in the bar's order, from the one
  after the one on screen, wrapping from the last to the first; Home is not
  in the round.
- **D67** A session left alone locks itself, the screen turns off, and the
  lid locks; the minutes are two settings of the adult panel's System page,
  and the panel's own timeout is the lock's.
- **D68** A program that is not in trixie is built at development time in a
  machine of its own, published as a tarball whose hash is in git, and
  packaged from that tarball.
- **D69** The Scratch family: the official Scratch editor (AGPL-3) and
  TurboWarp beside it, each a module, served locally and opened in
  Chromium; ScratchJr from the community desktop port built for Linux;
  Blockly Games; Chromium's policy allows the child to save and open their
  own files, and reaches the Scratch Foundation's library servers.
- **D70** The test modules are named `[Test] …`, and are not in the user
  guide.

## 5. Steps

### 4.1 — Upstream builds at development time — M — **done 2026-09-30**

**Cause.** Scratch, TurboWarp, ScratchJr and Blockly Games are not in
trixie. Each is built with Node.js or Java from a git repository, with the
network, and none of that belongs in the package build, which runs in a
chroot without the network so that a package builds the same anywhere
(packaging.md). So the program is built on the development machine, by a
script, from a pinned commit, into a tarball; the package is built from
the tarball (D68).

**Change.** Three scripts in `ci/`, a file in each package built this way,
and the build of such a package staged from the tarball.

- `packages/<package>/upstream.toml`, read with Python's `tomllib`:

  ```toml
  [upstream]
  name = "scratch-gui"                                   # what it is
  repository = "https://github.com/scratchfoundation/scratch-editor"
  commit = "0123456789abcdef0123456789abcdef01234567"    # forty hex digits
  version = "11.2.0+git20261001"                         # the tarball's, the package's first
  node = "24.9.0"                                        # nodejs.org release; "" when Node is not needed
  build = "ci/upstream/scratch.sh"                       # the build script
  sha256 = ""                                            # written by the first build
  ```

  The tarball is `build/upstream/<package>_<version>.orig.tar.xz`, one
  top-level directory `<package>-<version>/` with the built tree in it.
  `version` is `<upstream's own version>+git<yyyymmdd of the commit>`
  (`0+git<yyyymmdd>` for a repository with no version of its own), and
  the package's `debian/changelog` version starts with it.

- `ci/build-upstream.sh <package> [--publish]`:
  1. Reads `upstream.toml`. Checks what the machine needs and says what is
     missing, as `ci/build-package.sh` says how to make the chroot: `git`,
     `curl`, `xz-utils`, `tar`, `python3`, `make` and `unshare`, all of
     which a Debian development machine has. Nothing else is installed for
     these builds: Java is not needed, since Blockly Games' build takes the
     Closure Compiler's native build from npm, and no native Node module
     is built.
  2. Node, when `node` is not empty, never the system's: `ci/upstream/node.sh
     <version>` downloads
     `https://nodejs.org/dist/v<version>/node-v<version>-linux-x64.tar.xz`
     and `SHASUMS256.txt` from the same directory, checks the sum, and
     unpacks it to `build/upstream/node/v<version>/`, kept for the next
     build; the build script gets it first in `PATH`.
  3. The build: the package's script, run from a fresh
     `build/upstream/work/<package>/` (removed first), with
     `UPSTREAM_REPOSITORY`, `UPSTREAM_COMMIT`, `UPSTREAM_VERSION`,
     `UPSTREAM_PACKAGE` and `UPSTREAM_OUT` (`build/upstream/`) in its
     environment. The script fetches the commit
     (`git init && git remote add origin "$UPSTREAM_REPOSITORY" && git
     fetch --depth 1 origin "$UPSTREAM_COMMIT" && git checkout FETCH_HEAD`),
     builds, and writes the tarball to `$UPSTREAM_OUT`, made with
     `tar --sort=name --owner=0 --group=0 --numeric-owner
     --mtime="@$(git log -1 --format=%ct)" -cJf`, so that the same tree
     gives the same bytes. Its output is logged to
     `build/upstream/<package>.log` and shown.
  4. The tarball's SHA-256 printed and, when `upstream.toml` has
     `sha256 = ""`, written there; when it has one and it differs, the
     script says so and exits 1: a version's bytes never change, and a new
     build is a new `version`. The work directory is removed after a
     successful build; it stays after a failed one, to be looked at.
  5. `--publish`: `gh release create "upstream/<package>/<version>"
     --title "<package> upstream <version>" --notes "<repository> at
     <commit>, node <node>, sha256 <sum>" build/upstream/<file>`. When the
     release exists, its asset's sum is compared and nothing is uploaded.
- `ci/fetch-upstream.sh <package>`: when `build/upstream/<file>` is missing,
  `gh release download "upstream/<package>/<version>" --pattern "<file>"
  --dir build/upstream/`; then the sum is checked against `upstream.toml`,
  and a mismatch is an error. On GitHub's runners `GH_TOKEN` is
  `${{ github.token }}`; `gh` (2.46 in trixie) joins the tools the `build`
  job installs.
- `ci/build-package.sh`: when `$SOURCE_DIR/upstream.toml` exists, the
  build is staged: `ci/fetch-upstream.sh` first; then
  `$BUILD_DIR/staged/<package>/` is a fresh copy of `$SOURCE_DIR` with the
  tarball unpacked into `upstream/` inside it (`tar -xJf … --strip-components=1`),
  and sbuild runs on that copy, with `--dpkg-source-opt=-z1` so that a
  source tarball of a few hundred megabytes is packed in seconds. The
  package's `debian/rules` installs from `upstream/`. The source format
  stays native: the package is ours, built from a tree we made. Nothing of
  this reaches `packages/`, whose files are hashed by `ci/test-release.sh`'s
  `published`.
- `ci/upstream/`: `node.sh`, one build script per package (each step
  writes its own), and `check-site.py <directory> <prefix>`, which walks a
  built site's `.html` and `.js` files and fails on a root-absolute
  reference (`src="/`, `href="/`, `"/static/`) that does not start with the
  prefix the site is served under, the usual way a site built for a root
  breaks under `/<id>/`.
- `tests/project/upstream.sh`: for every `packages/*/upstream.toml`, the
  fields are there, `commit` is forty hex digits, `sha256` is empty or
  sixty-four, the changelog's version starts with `version`, the build
  script exists and passes `sh -n`; and no `packages/*/upstream/` directory
  is tracked by git.
- `.gitignore` gains `packages/*.orig.tar.xz` beside the `.dsc` and
  `.tar.xz` patterns already there.
- `ci/build-all.sh` lists the new packages as they arrive; `packaging.md`
  gets a section "Programs built at development time" saying all of this
  and listing what the development machine needs installed for it, and
  `layout.md` the new files.

**Tests.** `tests/project/upstream.sh`, above. The build script is proved
by step 4.4, the first tarball; the fetch by the reproducibility stage,
which builds every package twice and gets the tarball from
`build/upstream/` both times. A unit test of `check-site.py` on two small
trees, one right and one wrong.

**Traps.**
- `npm ci` of the Scratch monorepo downloads hundreds of megabytes and the
  build takes ten to thirty minutes; `build/upstream/<package>.log` says
  where it is.
- The system's `nodejs` (20.19 in trixie) is never used, even when it
  would do: the version in `upstream.toml` is part of what the tarball's
  sum stands for.
- `gh release create` needs the repository's default remote; it is
  `origin`, GitHub.
- A tarball built twice from the same commit may differ by a byte
  webpack put a date in: the recorded sum is the truth, not the rebuild.
- A library a build installed on the development machine is not thereby
  on a Kidux machine: a module's `Depends` names what the program needs,
  and the session machine, which starts from Debian, is where a missing
  one shows.

**Done when.** `tests/run project` passes with the new check; the two
scripts are documented in packaging.md; step 4.4 uses them.

### 4.2 — The test modules named `[Test]`, and out of the user guide — S — **done 2026-09-30**

**Cause.** *Hello*, *Hello on the web*, the canary and the robin are the
framework's own tests. An adult who reads the guide, or the panel's
Modules page, takes them for something a child is meant to use (D70).

**Change.**
- `kidux-module-hello` (0.1.6): manifest `name = "[Test] Hello"`, Spanish
  `[Prueba] Hola`; description unchanged. `kidux-module-hello-web` (0.1.4):
  `name = "[Test] Hello on the web"`, `[Prueba] Hola en la web`. The
  catalogues (`ci/i18n-extract.sh`, then the Spanish entries by hand, no
  fuzzy ones) and `tests/project/module-fields.py --update` for the
  `XB-Kidux-Name-*` fields.
- `tests/lib/seed/modules/canary/module.toml` and `robin/module.toml`:
  `name = "[Test] Canary"`, `"[Test] Robin"`; app ids, window titles and
  programs unchanged. `tests/lib/seed` is hashed by `published`, so the
  battery rebuilds nothing for it.
- `tests/acceptance/10-module-hello.sh`: `offered_in en_US.UTF-8 '[Test]
  Hello'` and `es_ES.UTF-8 '[Prueba] Hola'` (the pattern is a whole line,
  `grep -qx`). `tests/lib/sessionlib.py`: `LANGUAGES[*]["hello"]` is the
  new name in each language; `17-module-hello.py` reads it as before.
- The user guide, both languages: the sections *Hello* and *Hello on the
  web* of section 9 go; the sentence about Chromium's size and the way a
  web module opens moves to section 9's opening paragraph, since every
  web module shares it. `tests/lib/doc-screenshots.txt` loses
  `module-hello` and `module-hello-web`, and `docs/images/*/module-hello*.png`
  are removed with `git rm`. The README changes nothing here: it names
  GCompris, the one real module until 4.3.
- `modules.md` section 5 says the reference modules carry `[Test]` in
  their names so that an adult sees on the panel what they are.

**Tests.** The acceptance and session tests above, run in both languages.

**Traps.** `tests/session/16-module-open.py` checks the bar by colour and
by ids, never by the names, so it stays; `grep -rn "Canary\|Hola\b"
tests/` before the battery finds anything else that names them.

**Done when.** The panel's Modules page picture (`panel-modules.png`, both
languages) shows the tagged names; the guide's section 9 has GCompris and
its opening paragraph only.

### 4.3 — `kidux-module-tuxtype`: typing — S — **done 2026-09-30**

**Cause.** Phase 4's first module: a typing course for children, `tuxtype`
1.8.3-7 in trixie (architecture.md section 8), translated, with Spanish
word lists of its own.

**Change.** A package like `kidux-module-gcompris`: manifest, icon, words,
a starter, and a dependency on the program.
- `module.toml`: `id = "tuxtype"`, `name = "Tux Typing"`, `description =
  "Learn to type: catch the falling letters and words with the keyboard,
  in the child's language."`, `min_age = 6`, `max_age = 12`,
  `recommended_before = ["gcompris"]`, `launch = { exec =
  "/usr/libexec/kidux-module-tuxtype" }`, `app_ids = ["tuxtype",
  "TuxType", "Tux Typing"]` (corrected from the launcher's `toplevels:`
  line on the first try), `memory_max = "1G"`, `categories = ["typing"]`.
- `bin/kidux-module-tuxtype`: `exec tuxtype -w`, windowed, since the
  compositor gives it the room above the bar either way and a window
  that starts fullscreen keeps a title bar (modules.md section 2), with
  `SDL_VIDEODRIVER` unset, so that it draws through XWayland: there
  `sdl12-compat` scales its 640x480 pictures to the room it is given,
  while as a Wayland window it stays at 640x480 in a corner. It has its
  home in the module's `XDG_DATA_HOME`, where it keeps `~/.tuxtype`, and
  `--theme espanol` for a Spanish-speaking child. Otherwise the language
  is the session's (`tuxtype` reads `LANG`, and its
  Spanish word lists come with `tuxtype-data`); sound goes through
  `sdl12-compat`, which trixie's `libsdl1.2debian` is, to SDL 2 and
  PipeWire.
- `debian/control`: `Depends: tuxtype, tuxtype-data`; the `XB-Kidux-*`
  fields; the description for apt.
- Icon: drawn like the avatars, a keyboard with three keys lit, no Tux
  (the mascot's shape is Debian's package's, not ours).

**Tests.** Unit: the manifest reads, the words are complete (copied from
gcompris's). Acceptance: `10-module-hello.sh`'s pattern is generic enough
that no new acceptance file is needed; the archive offers `tuxtype`
(`kidux-as modules-available` names it in both languages). Session
`25-module-tuxtype.py`: installs through the daemon, switches it on for
Leo, signs in, opens the first tile, waits for a window whose module is
`tuxtype` (`window_of` by app id), checks it is maximised and on screen,
takes `module-tuxtype` (listed in doc-screenshots), checks the room above
the bar is not the launcher's cream (`colour_share(CREAM, ABOVE_THE_BAR)
< 0.2`), closes it with Alt+F4, and removes the module. The purge test
becomes `26-purge.py` in this step.

**Traps.**
- `kidux-session` exports `SDL_VIDEODRIVER=wayland`, and as a Wayland
  window `tuxtype` shows its game at 640x480 in a corner of the room;
  hence the starter's unset. Fullscreen (`-f`) fills the room too, once
  the launcher takes it out of fullscreen, but with D60's title bar; the
  XWayland window has none.
- The app id through XWayland is its `WM_CLASS`, `tuxtype`, which the
  manifest lists.

**Documents.** User guide section 9, *Tux Typing*, both languages, with
the picture; README's list of modules (a line each), both languages;
modules.md unchanged.

**Done when.** The session test passes in both languages and the pictures
show the game.

### 4.4 — `kidux-module-scratch`: the official editor, and Chromium's policy for the child's work — M — **done 2026-10-01**

**Cause.** Scratch is the module the requirements name first (requirements.md
section on modules; architecture.md section 8): the editor children know
from school, served locally, without the community. It is not in Debian,
it is built with Node.js, and since November 2024 its code is AGPL-3
(D69). And the kiosk's Chromium policy blocks every download and every
file dialog (D36), which would leave a child unable to save or open a
project.

**Change.**

*The tarball* (`ci/upstream/scratch.sh`, `upstream.toml`):
- `repository`: `https://github.com/scratchfoundation/scratch-editor`.
  `commit`: the newest tag named `scratch-gui@<x.y.z>` (`git ls-remote
  --tags`), or, when there is none, the default branch's head; recorded as
  a hash either way. `version`: `<the version in
  packages/scratch-gui/package.json at that commit, without any prerelease
  suffix>+git<yyyymmdd>`. `node`: the version `.nvmrc` at that commit
  asks for, else the newest 24.x on nodejs.org.
- The script: fetch the commit; `npm ci` at the monorepo's root with
  `NODE_OPTIONS=--max-old-space-size=6144`; then the site built for the
  path it is served under. `grep -n publicPath packages/scratch-gui/webpack.config.js`
  first: when it reads an environment variable (`ROOT` or another), the
  build runs with it set to `/scratch/`; when it does not, the script
  patches that `publicPath` to `'/scratch/'` with `sed` before the build
  and the log shows the patched line. Then `npm run build` at the root
  (the workspace builds `scratch-vm`, `scratch-render` and the rest that
  `scratch-gui` needs, in order). The built site is
  `packages/scratch-gui/build/`: `index.html`, `static/`, the chunks.
  `*.map` files are deleted. `ci/upstream/check-site.py build /scratch/`
  must pass. The tarball's top directory is `kidux-module-scratch-<version>/`
  with the site's files in it, plus `LICENSE` from the repository's root.
- The build's source (D71): every build script fetches through
  `ci/upstream/fetch.sh`, and the first build of a version packs what it
  fetched, npm's cache, the Node.js release and the scripts into
  `<package>_<version>.source.tar.xz`, `source_sha256` in `upstream.toml`.
  `ci/build-upstream.sh <package> --from-source` must give the recorded
  tarball from it alone, offline, before anything is published; each
  Scratch-family step does so for its own tarball.
- `ci/build-upstream.sh kidux-module-scratch --publish`, which puts the
  tarball and its source in the release.

*The package* (`kidux-module-scratch`, copied from `kidux-module-hello-web`
and cut down):
- `module.toml`: `id = "scratch"`, `name = "Scratch"`, `description =
  "Make games and stories with blocks, as at school. Its characters,
  backdrops and sounds come from the internet."`, `min_age = 8`,
  `max_age = 16`, `recommended_before = ["scratchjr"]`, `launch = { webapp
  = "scratch" }`, `memory_max = "3G"`, `categories = ["programming"]`.
- `debian/rules`: `override_dh_auto_install` copies `upstream/` to
  `/usr/share/kidux/webapps/scratch/` (`cp -a upstream/. $(WEBAPP)/`),
  installs the manifest, the icon and the catalogues; `override_dh_auto_build`
  compiles the catalogues only; `Depends: kidux-webapps (>= <the version
  of this step>)`.
- `debian/copyright`: DEP-5; `Files: upstream/*`, `License: AGPL-3.0`,
  with the full text, and a paragraph naming the third-party components
  the built site carries, under their own licences, as
  `packages/scratch-gui/package.json` at the commit lists them.
- `debian/kidux-module-scratch.lintian-overrides`: the tags a built site
  cannot avoid, each with a comment: `source-is-missing` (the source is
  the repository at the recorded commit), `embedded-javascript-library`,
  `very-long-line-length-in-source-file`, and any `privacy-breach-*` tag
  raised by a page that names the Scratch Foundation's servers, since
  the policy below allows exactly those. Anything else lintian says is
  fixed, not overridden.
- Icon: coloured blocks stacked, drawn like the avatars; not the cat,
  which is the Scratch Foundation's mark.

*Chromium's policy* (`kidux-webapps`, bumped): `URLAllowlist` gains
`assets.scratch.mit.edu`, `cdn.assets.scratch.mit.edu`,
`cdn2.scratch.mit.edu` and `cdn.scratch.mit.edu`, where the library of
sprites, backdrops, sounds and the tutorials' pictures live, and, for
step 4.5, `trampoline.turbowarp.org`; `DownloadRestrictions` goes from 3
to 1 (dangerous file types still blocked; a `.sb3` is not one);
`AllowFileSelectionDialogs` becomes `true`, and `PromptForDownloadLocation`
`true`: a download asks in the file dialog where to keep it, from the
child's Downloads folder, named in their language, which `xdg-user-dirs`
makes (D76). Scratch's *Save to your computer* is such a download, of a
file the page makes at a `blob:` address, which the allowlist admits as
`blob:*` (D75); *Load from your computer* is the open dialog. The policy's
comment in modules.md section 4 and the acceptance check in `12-webapps.sh`
say the new list: the allowlist is `127.0.0.1:8123`, the hosts named here
and `blob:*`, nothing else.

*The session's memory.* Scratch in Chromium needs more than hello's page,
and the session machines' 2 GB (`sessionlib.Machine.boot`) hold it: the
editor opens and runs in them in both languages. A Chromium the journal
says was killed (`oom`) would be the sign to give them more.

**Tests.**
- Unit, in the package: the manifest reads; the words are complete.
- `tests/project/upstream.sh` passes; `check-site.py` passed in the build.
- Acceptance `12-webapps.sh`: the policy's allowlist and the two changed
  keys as above; the server answers `/scratch/` with the editor's
  `index.html` once the module is installed there (a new check in the
  module's own acceptance file, `13-module-scratch.sh`, and
  `13-no-key-no-archive.sh` renamed `19-no-key-no-archive.sh`, which stays
  last with room for the modules before it: install through the
  daemon, `curl -fsS http://127.0.0.1:8123/scratch/ | grep -q '<title>'`,
  remove).
- Session `26-module-scratch.py`: as 4.3's test, with Chromium: the window
  is `on_screen() == "scratch"`, its title contains `Scratch`, the top
  strip of the picture is the editor's menu bar purple (`#855CD6`, share
  above 0.3 in `(0, 0, 1, 0.06)`), `module-scratch` taken for the guide,
  the module closed with Alt+F4 and removed. Scratch may ask *leave
  site?* before closing when the project changed; it has not, but if the
  window is still there after fifteen seconds the test presses Enter once
  and waits again, and says so in its report line. Purge becomes `28`.

**Traps.**
- The monorepo's `npm run build` builds every package; a failure in one
  we do not ship (a test package, a native `canvas` build) is looked at
  before anything else is tried: `npm run build --workspaces --if-present`
  with the workspaces `scratch-gui` needs, or `npm run build -w
  packages/scratch-gui` after `-w` for each of its siblings, is the
  fallback, in the order `package.json`'s `dependencies` names them.
- A site built for the root fails under `/scratch/` with a blank page and
  404s in `kidux-webapps`' log (`journalctl -u kidux-webapps`); that is
  what `check-site.py` catches before the package is even built.
- Chromium's policy blocks a navigation, not a `fetch`; the allowlist
  entries make no difference to the library if that is so, and every
  difference if it is not. Either way the entries are right, and the
  owner's hand test opens the library.
- Scratch's tutorials embed videos from YouTube in a frame: the frame
  shows Chromium's blocked page, which is what the guide says happens to
  anything outside the module.

**Documents.** User guide section 9, *Scratch*, both languages: what it
is, that its library comes from the internet, where a project is saved
and how it is opened again, and that the tutorials' videos stay closed;
section 8's *Modules* page needs nothing. README's list. modules.md
section 4 (the policy) and a paragraph in section 2 about a web module
that saves the child's work through the browser's dialogs. architecture.md
section 8's Scratch row (AGPL-3, built at development time, D68, D69).

**Done when.** The editor opens in the session machines in both languages
with its menu bar on the picture, and the battery is green.

### 4.5 — `kidux-module-turbowarp`: Scratch made faster — S — **done 2026-10-01**

**Cause.** Scratch 3 is heavy for an old computer (architecture.md asks
4 GB for it). TurboWarp is Scratch's editor with a compiler that runs
projects many times faster, the same blocks and the same project files,
and its code is GPL-3 over the BSD-3 Scratch code it forked before the
licence change (D69). An adult who finds Scratch slow, or whose machine
does not build it, switches TurboWarp on instead.

**Change.** The same pipeline and package as 4.4, for
`https://github.com/TurboWarp/scratch-gui`:
- `upstream.toml`: `commit` the `develop` branch's head; `version`
  `0+git<yyyymmdd>` (the fork has no version of its own); `node` the
  newest 20.x or 22.x nodejs.org release the repository's `package.json`
  `engines` allows, else 20.19.x, which is trixie's.
- `ci/upstream/turbowarp.sh`: fetch, `npm ci`, the path: TurboWarp's
  webpack configuration reads `ROOT` for the path it is served under; the
  script sets `ROOT=/turbowarp/` and checks the built `index.html` with
  `check-site.py build /turbowarp/`, patching `publicPath` as 4.4 does if
  `ROOT` is not read. `npm run build`; `build/` is the site (`index.html`
  is the editor); `*.map` deleted; the licence files at the repository's
  root copied.
- The package: `id = "turbowarp"`, `name = "TurboWarp"`, `description =
  "Scratch, made faster: the same blocks and the same projects, for a
  slower computer or when Scratch does not run well."`, ages 8 to 16,
  `recommended_before = ["scratchjr"]`, webapp `turbowarp`, `memory_max =
  "3G"`; copyright GPL-3 for TurboWarp's changes and BSD-3 for Scratch's
  code; the same lintian overrides as 4.4; icon: the same blocks in
  another arrangement, no TurboWarp mark.
- The policy needs nothing new: 4.4 added `trampoline.turbowarp.org`,
  through which TurboWarp fetches the library, and the Scratch hosts.

**Tests.** As 4.4: acceptance `14-module-turbowarp.sh`, session
`27-module-turbowarp.py` (menu bar red `#FF4C4C`, title contains
`TurboWarp`, picture `module-turbowarp`), purge renamed.

**Traps.** TurboWarp's addons ask nothing of the network on a local page;
its *cloud variables* connect only for a project loaded from turbowarp.org,
which the policy keeps closed; a *Load from Scratch* by project id asks
`api.scratch.mit.edu`, which is not in the allowlist, and fails quietly:
the guide says the way in is a file.

**Documents.** User guide section 9, *TurboWarp*, both languages, right
after Scratch, saying in one paragraph when to choose it; README's list;
architecture.md section 8 row.

### 4.6 — `kidux-module-scratchjr`: ScratchJr, from the community desktop port — M — **done 2026-10-01**

**Cause.** ScratchJr is the Scratch for children of five to seven, without
words. MIT ships it for tablets and Chromebooks only, and its pure-web
version has been "planned" for years; the one way to have it on Linux is
the community port that puts the app's own HTML5 code in Electron,
`jfo8000/ScratchJr-Desktop` (BSD-3), made for Windows and Mac and built on
Linux by Arch's community package (D69). It is a program module, like
GCompris, that carries its own Electron.

**Change.**

*The tarball* (`ci/upstream/scratchjr.sh`, `upstream.toml`):
- `repository`: `https://github.com/jfo8000/ScratchJr-Desktop`, `commit`
  the default branch's head, `version` `<package.json version>+git<yyyymmdd>`,
  `1.3.2+git20201121`; `node` 24.21.0.
- The port is written for Electron 1.8 through `electron-compile`, which
  no longer builds. `ci/upstream/scratchjr.sh` takes its code as it is and
  gives it what a current Electron needs, and nothing else: the pages'
  modules bundled by webpack into the `appEntry.js` each page loads, which
  `electron-compile` used to transpile on the fly; the window given Node in
  its pages (`nodeIntegration`, no context isolation), as Electron 1.8 did
  by default; `remote`, which Electron no longer has, left out of the
  client; no application menu, no Windows installer hook, and no
  `BrowserView`, which the port makes and never loads. Electron (44.5.1),
  webpack and `@electron/packager` are pinned in the script, and the
  packager makes the Linux x64 app, from Electron's zip, which the script
  fetches through `fetch.sh` and checks against the sums the `electron`
  package carries (`--electron-zip-dir`), so that the packager downloads
  nothing; npm's lock file is kept for the source tarball, since the port
  has none. Its database is `sql.js`, JavaScript, so nothing is compiled
  against Electron. The script prints what `ldd` finds missing. The tarball's top directory is
  `kidux-module-scratchjr-<version>/` with the packaged app, plus the
  port's licence as `LICENSE.scratchjr`.

*The package* (`kidux-module-scratchjr`, `Architecture: amd64`):
- Installs `upstream/` to `/usr/lib/kidux-module-scratchjr/`;
  `override_dh_strip`, `override_dh_dwz` empty (the binaries are
  Electron's, not built here); `dh_shlibdeps` runs, so that
  `${shlibs:Depends}` names the libraries the binaries need, and for that
  the build-depends list the packages of the libraries they link to, as
  `objdump -p` names them; `dh_shlibdeps -l` points at Electron's own
  directory, and `override_dh_makeshlibs` is empty, so that Electron's
  libraries get no ldconfig trigger.
- `bin/kidux-module-scratchjr`, the starter, runs
  `/usr/lib/kidux-module-scratchjr/ScratchJr` and nothing else. The port
  keeps the child's projects, one database, in `ScratchJR` in the child's
  Documents folder (Electron's `app.getPath('documents')`, which follows
  `xdg-user-dirs`, so `Documentos` in Spanish), and makes it at start: the
  child's work, in their home, kept when the module is removed (modules.md
  section 2). Electron's own settings and cache go under the directories
  the launcher gives, and go with the module.
- `module.toml`: `id = "scratchjr"`, `name = "ScratchJr"`, `description =
  "Stories and games with blocks, without a word to read, for the
  youngest."`, `min_age = 5`, `max_age = 7`, `launch = { exec =
  "/usr/libexec/kidux-module-scratchjr" }`, `app_ids` as the launcher's
  `toplevels:` line shows them on the first try (an X11 class, both
  spellings), `memory_max = "2G"`, `categories = ["programming"]`.
- Icon: blocks again, smaller and rounder, drawn like the avatars.
- `debian/copyright`: BSD-3 for the port and ScratchJr; MIT for Electron;
  Chromium's BSD-3 for what Electron carries; a paragraph saying so.
- Lintian: the overrides an Electron binary needs, each with a comment:
  `embedded-library` for the libraries Chromium builds into it, and
  `unstripped-binary-or-object` for its Vulkan loader; nothing else.

**Tests.** Unit: manifest, words, and the language the starter passes.
Acceptance `15-module-scratchjr.sh`:
installs through the daemon, `ldd` on the binary and on every library it
carries finds nothing `not found`, removes. Session
`28-module-scratchjr.py`: as 4.3's, its first screen checked by its sky
blue rather than by the cream it has a lot of, and after the window appeared,
`ScratchJR` exists in Leo's Documents folder (its name from
`sessionlib.SPEAKS`), and stays there after the module is removed; picture
`module-scratchjr`; purge renamed.

**Traps.**
- Electron's sandbox: on Debian the kernel allows unprivileged user
  namespaces, which is what Chromium's sandbox uses, so nothing is
  set-uid, and the app starts as it is.
- Electron 44 draws through X11 unless told otherwise, so through
  XWayland in the session, and its window's class is `scratchjr`, which
  `app_ids` lists.
- dpkg-source's own ignore list drops every `*.so`, which left Electron's
  `libffmpeg.so` out of the package: `ci/build-package.sh` passes a
  package built from an upstream tarball only `-I.git`.
- Bundled by webpack, snap.svg and its `eve` load as AMD modules and
  `eve` is undefined, so the app stops at its splash: the script turns
  webpack's AMD parsing off, and they load as CommonJS, as
  `electron-compile` loaded them.
- The projects' folder is `app.getPath('documents')`, which xdg-user-dirs
  answers from `$XDG_CONFIG_HOME/user-dirs.dirs`; the launcher links the
  child's into every module's settings directory (modules.md section 2),
  without which it was the home itself.
- The app's language is the page's `navigator.language`, which Electron
  does not take from `LANG`: the starter passes `--lang=<es-ES>` from the
  child's locale. The first start's question of where the app is used,
  for usage figures it sends nowhere and with no translation, is taken as
  unanswered by the script, and the app opens on its home screen.

**Documents.** User guide section 9, *ScratchJr*, both languages, first
of the programming modules, saying where projects live; README's list;
architecture.md section 8 row; modules.md section 2's paragraph about
the child's folders, which a module finds through the launcher's links.

### 4.7 — `kidux-module-blockly-games` — S — **done 2026-10-01**

**Cause.** Google's Blockly Games are a set of puzzles that teach the
ideas behind blocks, from a maze to a movie, offline, in sixty-five
languages, Apache-2.0: a module between ScratchJr and Scratch for the
children who read a little (D69).

**Change.** The pipeline once more, for `https://github.com/google/blockly-games`:
- `upstream.toml`: `commit` the default branch's head, `version`
  `0+git<yyyymmdd>` of that commit, `node` 24.21.0, the release the other
  modules' builds use.
- `ci/upstream/blockly-games.sh` does what the Makefile's `deps`, `games`
  and `offline` targets do, with what this machine has. The Makefile
  fetches its third-party code with `svn` from GitHub, which GitHub no
  longer serves, at its newest; the script fetches the same code with
  `git`, each repository at a commit it names, so that the same script
  makes the same tarball. The Makefile compiles with the Closure
  Compiler's Java build; the script gives it the compiler's native Linux
  build, from npm, behind a `java` that runs it, and `python` that is
  `python3`. Then `make games`, and the site as `offline` makes it,
  written out without its bash-only patterns; the soundfonts' `README.txt`
  stays in it, since it is their attribution (CC-BY-3.0). `check-site.py`
  with `/blockly-games/` finds nothing: the site links relatively.
- The package: `id = "blockly-games"`, `name = "Blockly Games"`
  (`Juegos de Blockly` in Spanish, as the games call themselves),
  `description = "Puzzles with blocks: a maze, a bird, a turtle, a movie
  and music, one step harder each time."`, `min_age = 6`, `max_age = 12`,
  `recommended_before = ["scratchjr"]`, webapp `blockly-games`,
  `memory_max = "2G"`; copyright Apache-2.0 for the games, and each
  third-party part under its own licence (Ace BSD-3-Clause, SoundJS and
  Babel Expat, the soundfonts CC-BY-3.0); overrides as 4.4's.
- `kidux-webapp` opens `/blockly-games/?lang=es`, which is the site's own
  language parameter: nothing to add.

**Tests.** As 4.4: acceptance `16-module-blockly-games.sh`, session
`29-module-blockly-games.py` (the title is the games' name in the
child's language, from `sessionlib.SPEAKS`, the room above the bar not
cream, picture `module-blockly-games`), purge renamed.

**Traps.** A game that sounds (`Music`) needs nothing of the machine but
the browser. The games keep a child's progress in the browser's storage,
which is under the module's settings directory and goes with the module;
the guide says so.

**Documents.** User guide section 9, *Blockly Games*, both languages;
README's list; architecture.md section 8 row.

### 4.8 — Closing — S — **done 2026-10-01**

- The roadmap's phase 4 items ticked; `docs/dev/README.md` unchanged;
  architecture.md section 8's date line says the rows were verified in
  phase 4.
- Every picture the guide shows, in both languages, from the last green
  battery, committed; the guide's section 9 read once more as a whole in
  each language, so that the modules are in the order a child would meet
  them: GCompris, Tux Typing, ScratchJr, Blockly Games, Scratch, TurboWarp.
- The final message to the owner, in Spanish: what was built, what was
  decided along the way, and how to try each module on the MacBook, step
  by step, commands without `$`, no reboot, no change to the network.

## 6. Risks

- **A build that does not build.** Scratch's monorepo moves; a commit
  that fails to build is the step's first finding, and the fix is to pin
  the newest commit that builds (the tags first), never to patch the
  editor's code beyond the path it is served under.
- **A dependency the development machine hides.** A program built here
  runs here with whatever is installed; the session machine, which starts
  from Debian, is the proof that the package's `Depends` is complete, and
  every module step ends with it.
- **Chromium's memory in the session machines.** Said in 4.4: 2 GB
  hold the editor; more would be the answer if a Chromium were killed,
  and the battery's four machines still fit the development machine.
- **Electron on Linux from a port made for Mac and Windows.** 4.6 lists
  the three things that usually go wrong (the sandbox, Wayland, the
  class) and what to do for each; if the app still does not open after
  those, the step ends with the tarball built and the findings written in
  the plan, and the module waits.
- **Time.** The nine steps are twenty-five hours or so of unattended
  work; 4.7 and then 4.6 are the ones to leave for a later sprint if it
  has to be shorter, since nothing after them depends on them.
