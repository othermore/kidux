# Tux Typing: a program of Kidux's own, and a course with the ñ and the accents

The plan for the Tux Typing module after its first lessons (D112): what Tux
Typing does that its data cannot put right, the package that puts it right,
and the course and the word lists that build on it. Every fact about Tux
Typing here is from its source, 1.8.3 as Debian ships it (`tuxtype`
1.8.3-7 in trixie), and was tried on a session machine.

## 1. What Tux Typing does

Tux Typing's practice, the screen a lesson's `<prac>` opens, draws a
keyboard and two hands, writes the next character large, lights the finger
that types it and frames its key. All of it comes from the theme's
`keyboard.lst`, which `LoadKeyboard()` in `src/alphabet.c` reads, one key a
line, in either of two shapes:

- `finger|key`: the finger alone. With a theme loaded (`settings.use_english`
  is 0 as soon as `--theme` names a directory that exists, `kidux-es` and
  `kidux-en` alike), the key gets no position (`keyname` "None"): no label
  on the drawn keyboard, no frame when it is next.
- `finger|key|US key`: the character the US keyboard has on that physical
  key. `map_keys()` turns it into the key's position (`C10` for `;`, the ñ
  key of a Spanish keyboard) and the finger of that position, which
  replaces the finger of the first field.

Then, on every key pressed in a practice (`src/practice.c`, the
`SDL_KEYDOWN` handler), Tux Typing *learns* the key: it looks the pressed
character up in the table and gives its entry the position and the finger
of the physical key, read from the SDL keysym through a switch that knows
the US keyboard's keys only (`SDLK_a` to `SDLK_z`, the digits, the US
punctuation). A key the switch does not know, the ñ, leaves `tmp` at -1,
and `updatekeylist()` then gives the entry the position "None" and the
finger -1. So the ñ, the comma, the full stop and the hyphen of a Spanish
keyboard light their finger until the first time the child presses them,
and never again in that run of the program; the journal shows
`GetFinger() - Unicode char '' has no valid finger.` each time one of
them is next. This is what the owner saw: the ñ without its finger.

The keyboard's labels are drawn once per practice, by `GenerateKeyboard()`
in `alphabet.c`, for every entry of the table that has a position: so with
a short table the labels are the keys learnt in earlier practices of the
same run (a s d f after the first lesson), and with a long table every
key, upper and lower case both, the capital drawn nine pixels up and left
of the small letter, each with the dark halo of `SimpleText()`. Either
way it is ugly, and the owner wants the keyboard to show only the keys of
the exercise, so that a child finds them at once.

A dead key, the acute accent of a Spanish keyboard, arrives as a key down
with no character (`keysym.unicode` 0). The practice counts it as a wrong
key (`wrong_chars++`, the error sound) because only Shift is excused;
`GetIndex(0)` even returns the index of the first empty entry of the
table. The games, `src/playgame.c` and `src/laser.c`, take the 0 as a
letter typed. So nothing with an accent can be practised or played.

The games take their words from the theme's `words/*.txt`, the first line
of each the list's name in the menu. Debian's Spanish theme has three
lists, "Words Uno", "Words Dos" and "Words Tres", ASCII only, with
MONTANA, LAPIZ, DEBIL, CIGARO, ESCUSADO and PLASTICO among them. The games
compare case-insensitively and accept ñ and the accented vowels: a typed
character between U+00E0 and U+00FF is raised to its capital, and every
character of a word must be in `keyboard.lst`.

None of this is data: the learning, the counting and the drawing are the
program's. D112 chose a theme over a patched program while a theme was
enough; it no longer is.

## 2. The package: kidux-tuxtype

A program of Kidux's own, built from Debian's source with four small
patches, beside Debian's `tuxtype`, which it neither replaces nor
conflicts with: the module runs Kidux's binary and Debian's data.

- `packages/kidux-tuxtype/`, a native package, version `1.8.3+deb7.1`:
  the upstream version `1.8.3+deb7` (Tux Typing 1.8.3 as Debian's
  1.8.3-7 patches it) and Kidux's count after the dot, as
  kidux-module-basic's `0+git20261018.1`. Its one binary package,
  `kidux-tuxtype`, `Architecture: any`, installs `/usr/games/kidux-tuxtype`
  and the two folders Tux Typing will not start without,
  `/var/games/tuxtype/words` and `/etc/tuxtype`, which Debian's `tuxtype`
  makes too; `Depends: tuxtype-data (>= 1.8.3), fonts-sil-andika`, as
  Debian's `tuxtype` has. No desktop file, no menu entry, no manual page,
  no setgid: the module starts it, nothing else does. Its window is called
  `kidux-tuxtype`, which the module's `app_ids` name.
- `upstream.toml` with empty `repository` and `commit`, as the
  simulations have (docs/dev/packaging.md, "Programs built at development
  time"): the build script `ci/upstream/tuxtype.sh` fetches
  `tuxtype_1.8.3.orig.tar.gz` and `tuxtype_1.8.3-7.diff.gz` through
  `ci/upstream/fetch.sh`, from `snapshot.debian.org`, which keeps them
  after the pool drops them, checks each against the SHA-256 written in
  `packages/kidux-tuxtype/debian-source.toml`, unpacks the one, applies
  the other with `patch -p1`, removes the `debian/` directory the diff
  brings, and packs `tuxtype-1.8.3+deb7/` with `ci/upstream/pack.sh`,
  dated by `$UPSTREAM_KEEP/time` as the simulations' build is. The
  tarball is published with `ci/build-upstream.sh kidux-tuxtype
  --publish` before the release, like BASIC's.
- `debian/rules`: `override_dh_auto_configure` copies
  `upstream/tuxtype-1.8.3+deb7/` to `build/tuxtype/`, applies
  `patches/*.patch` there with `patch -p1` (D88), and runs Debian's
  `configure` line; `dh $@ --sourcedirectory=build/tuxtype`; install
  copies `build/tuxtype/src/tuxtype` to
  `debian/kidux-tuxtype/usr/games/kidux-tuxtype`. Build-Depends are
  Debian's: `libsdl1.2-dev`, `libsdl-image1.2-dev`, `libsdl-mixer1.2-dev`,
  `libsdl-ttf2.0-dev`, `libsdl-pango-dev`, `libsdl-net1.2-dev`,
  `librsvg2-dev`, `libt4k-common0-dev`, all in trixie.
- `debian/copyright`: `Files: *` GPL-2+ as Tux Typing's (Tux4Kids, and
  the Debian maintainers for the diff), `Files: debian/* patches/*`
  Kidux's, GPL-3.0-or-later; the patches are offered under Tux Typing's
  own licence, said there.
- `tests/run reproducible` must pass on it: the build is autotools and C,
  with nothing of the build's time in it; if anything of the kind shows,
  it is fixed in a patch, not worked around.

## 3. The patches

Each a file in `packages/kidux-tuxtype/patches/`, numbered, with a header
that says what it does and why, in the present tense. They are kept
small enough to offer to Tux4Kids, whose repository has had no release
since 2014; Kidux counts on keeping them.

1. **`01-keep-the-tables-positions.patch`**, `alphabet.c`:
   `updatekeylist()` returns at once when the entry already has a
   position, or when the character to learn from is -1. The table is the
   truth about where a key is; learning only fills in what the table left
   out. `GetIndex()` returns -1 for the character 0.
2. **`02-dead-keys-are-not-typing.patch`**, `practice.c`, `playgame.c`,
   `laser.c`: a key down whose `keysym.unicode` is 0 is not a key typed:
   the practice neither counts it wrong nor learns from it, and the games
   ignore it, as all three ignore Shift.
3. **`03-label-the-keys-in-use.patch`**, `alphabet.c`, `practice.c`:
   `GenerateKeyboard(keyboard, only)` takes the characters to label, and
   labels one key once: for each position, the first entry of the table
   that is unshifted and whose character, lowered, is among them; nothing
   for a position already labelled, nothing shifted. The practice passes
   the characters of the exercise, so a lesson's keyboard shows the keys
   that lesson uses and no other; `only` NULL labels every key, for any
   other caller. The label is the character alone, rendered with
   `TTF_RenderUTF8_Blended` in black at a size that fits the key, no
   outline, placed as the key images expect; what it looks like is judged
   on the session machine's screen, not in the code.
4. **`04-list-the-word-lists-in-order.patch`**, `titlescreen.c`: the
   games' menu sorts the theme's word lists by their file names, which the
   theme numbers from the easiest to the hardest, instead of taking them
   in the disk's order.
5. Nothing else. Debian's `titlescreen.c` fix and translations come with
   the diff.

What to confirm on the session machine before the patches are called
done, each with a screenshot in `build/vm/` and the journal:

- the ñ keeps its finger and its frame through a whole drill, and so do
  the comma and the full stop in lessons 11 and 12;
- the keyboard of lesson 2's drill shows j, k, l and ñ, and nothing else;
  the keyboard of its words shows the letters of its words;
- the labels are clean at the launcher's size (the window is 640 by 480
  scaled);
- an accented vowel typed as the dead key and then the vowel counts as
  one correct character and no error, in the practice and in Comets and
  Cascade. Under sdl12-compat the dead key is one `SDL_KEYDOWN` with no
  character and the vowel the next, with the accented character; if the
  machine shows otherwise, the patch follows what the machine shows. On
  the test machine the acute dead key is `sendkey apostrophe` (the key
  right of the ñ on the Spanish layout), and `Machine.type` in
  `tests/lib/sessionlib.py` learns to type á é í ó ú that way.

## 4. The module: kidux-module-tuxtype 0.1.5, as `~dev` builds

The same version the work is in; nothing of it is published yet (D93).

- `Depends: kidux-tuxtype (>= 1.8.3+deb7.1), tuxtype-data`; `tuxtype` no
  longer. `bin/kidux-module-tuxtype` runs `/usr/games/kidux-tuxtype`.
  A machine upgraded from 0.2.6 keeps Debian's `tuxtype` as a package
  nothing needs, which is harmless.
- **The keyboard tables, both long.** `lessons/keyboard-es.lst` and a new
  `lessons/keyboard-en.lst`, every line `finger|key|US key` except the
  space, which stays `5| ` (its finger from the file; `map_keys` has the
  space too, so either shape is fine). Spanish: the letters with
  themselves, `ñ` with `;` and `Ñ` with `:`, the comma and the full stop
  with themselves, the hyphen with `/`, and the accented vowels with their
  vowel, lower and upper case (`0|á|a`, `0|Á|A`, … the games need the
  capitals). English: each key with itself, from Debian's own table.
  `lessons/keyboard-tuxtype.lst` goes, and `keyboard_keys()` in
  `lessons/build.py` reads the second field of either shape. A check that
  every key a practice uses has a position (three fields), so that it
  gets its frame and its label.
- **Two lessons more in Spanish**, 13 and 14, with the accents, at the
  end: 13 brings `á é`, 14 `í ó ú`. Their first page says how an accent
  is typed, the dead key right of the ñ and then the vowel; their second
  page says the dead key goes with the right little finger and the vowel
  with its own. Drills of vowel pairs (`aá eé á é áé éá`), words with
  accents that children know (`mamá papá café bebé sofá`; `allí río león
  avión tú menú`), every line within the limits the build checks. The
  English course stays at twelve: the check that every language has the
  same number of lessons goes, and `test_lessons.py` says what each has.
  `learnt` in `build.py` counts a lesson's accented keys as its own.
- **Word lists of Kidux's own for the Spanish games**, in
  `lessons/words-es/*.txt`, UTF-8, the first line the list's name, then
  one word a line in capitals, with the ñ and the accents written as they
  are: six or so lists a child of six to twelve knows the words of, from
  short and easy to long, for instance "Palabras cortas", "Animales",
  "Comida", "En casa", "La naturaleza", "Con tilde"; MONTAÑA among them,
  nothing a parent would not want on the screen, every word spelt as the
  dictionary has it. `build.py` puts them in `kidux-es/words/` instead of
  the link to Debian's, keeps the link for a language without lists, and
  checks each list: a name, capitals only, every character in that
  language's table, no word longer than twelve characters, no duplicates.
  English keeps Tux Typing's own lists.
- `es.toml` and `en.toml` say where each language's words come from, in
  the same way `keyboard` names the table.

## 5. Tests

- Unit tests of the module (`tests/test_lessons.py`, `tests/test_module.py`):
  fourteen Spanish lessons and twelve English, the file names of the two
  new ones, the long tables with the ñ, the accented vowels and their
  capitals, the word lists built and checked, the starter running
  `kidux-tuxtype`.
- `tests/session/25-module-tuxtype.py`, on the Spanish machine and the
  English one: after the first lesson's practice as it is, lesson 2 (the
  Spanish machine) or the first (English): type the whole drill with
  `Machine.type`, the ñ included, and report that the journal has no
  `has no valid finger` line and that the practice ended (Tux Typing's
  results screen); then lesson 14 on the Spanish machine: type `mamá`
  and report no error counted, from the screen's `Errors` region staying
  as it was or from the journal. Screenshots `module-tuxtype-lesson` and
  `module-tuxtype-lesson-fingers` stay as the guide's pictures, now with
  the labelled keys of the lesson; a screenshot of the accents lesson,
  `module-tuxtype-lesson-accents`, for the guide too
  (`tests/lib/doc-screenshots.txt`).
- The package builds and `lintian` passes; `tests/run reproducible`
  passes on `kidux-tuxtype`; `tests/project/upstream.sh` accepts its
  `upstream.toml`; `ci/build-upstream.sh kidux-tuxtype --from-source`
  gives the recorded tarball.
- The quick loop: `tests/run vm up 04`, `tests/run vm push kidux-tuxtype
  kidux-module-tuxtype`, `tests/run vm test 25`, in Spanish and in English
  (`KIDUX_VM_LANGUAGE=en`). The whole battery waits for the release
  (CLAUDE.md, "Partial tests while developing").

## 6. Documents

- `docs/dev/architecture.md`: D113, Kidux builds Tux Typing itself,
  refining D112, with the four things data cannot do; D112 stays, marked
  as refined.
- `docs/dev/tuxtype.md`, new, like `basic.md`: how the module works,
  the rebuilt program and its patches, the tables, the lessons' format,
  the word lists, and what to do when Debian moves Tux Typing on.
- `docs/dev/roadmap.md`: the line for this work.
- `docs/dev/packaging.md`, "Programs built at development time": Tux
  Typing as the second program taken as files, Debian's source.
- `docs/en/modules/tuxtype.md` and `docs/es/modules/tuxtype.md`: the
  course's length in each language, the accents lessons, the keyboard
  that shows the keys of the exercise, the Spanish word lists Kidux
  brings, the picture of the accents lesson; "what the course does not
  cover yet" is capitals alone. `docs/en/user-guide.md` and
  `docs/es/user-guide.md`, the Tux Typing section, in step.
- `debian/changelog` of both packages, dated by `ci/hours.py
  changelog-date`.
