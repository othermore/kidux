# Tux Typing

`kidux-module-tuxtype` is the typing course for a child of six to twelve:
Tux Typing's games, letters and words that fall to be typed, and Kidux's
own lessons, which teach typing with all ten fingers a row at a time, in
the child's language (D112). The program is Tux Typing as Debian builds
it, built again by Kidux with four small patches for keyboards other than
the US one, as a package of its own, `kidux-tuxtype` (D113). This document
is how the two packages are made, what the patches do, and how the lessons
and the word lists are written.

## 1. What it is made of

```
packages/kidux-tuxtype/
  upstream.toml           Tux Typing's source: its version and sums
  debian-source.toml      the Debian files it is taken from, by address and SHA-256
  patches/NN-*.patch      Kidux's patches, each saying what it does and why
  debian/                 builds the program from upstream/ with the patches

packages/kidux-module-tuxtype/
  module.toml, icon.svg   the manifest and the tile's picture
  bin/kidux-module-tuxtype   the starter: the child's language's theme
  lessons/<lang>.toml     a language's lessons and the words of their pages
  lessons/keyboard-<lang>.lst   a language's keyboard table
  lessons/words-<lang>/   a language's word lists for the games, if it has its own
  lessons/build.py        builds a theme of Tux Typing's for each language
  po/                     the manifest's words
  tests/                  section 6
```

On the machine the program is `/usr/games/kidux-tuxtype`, its words,
pictures, sounds and Debian's themes are tuxtype-data's under
`/usr/share/tuxtype/`, and Kidux's themes are
`/usr/share/tuxtype/themes/kidux-<lang>/`. Debian's own `tuxtype` is
neither needed nor in the way: a machine that had it keeps it.

## 2. The program: kidux-tuxtype

Tux Typing (`https://github.com/tux4kids/tuxtype`, Tux4Kids, GPL-2, many
of its files GPL-3 or later) is in trixie as `tuxtype` 1.8.3-7. Its
upstream has had no release since 2014, and Debian's diff adds a fix to
its title screen and translations. Kidux takes that source as Debian
publishes it: `ci/upstream/tuxtype.sh`, run by `ci/build-upstream.sh
kidux-tuxtype`, fetches `tuxtype_1.8.3.orig.tar.gz` and
`tuxtype_1.8.3-7.diff.gz` from snapshot.debian.org, where every file Debian
has published stays, refuses either unless its SHA-256 is the one
`debian-source.toml` names (the sums of Debian's `.dsc`), applies the
diff, leaves out its `debian/`, and packs the tree as
`kidux-tuxtype_1.8.3+deb7.orig.tar.xz`, dated by Debian's changelog entry
(packaging.md, "Programs built at development time"). The version,
`1.8.3+deb7`, is Tux Typing's and Debian's revision; the package's,
`1.8.3+deb7.<n>`, counts Kidux's builds of it.

`debian/rules` copies `upstream/` to `build/tuxtype/`, applies
`patches/*.patch` there, makes the build system again with `autoreconf`
as Debian's build does, runs Debian's `configure` line, and installs the
program alone as `/usr/games/kidux-tuxtype`, with the two folders it will
not start without, `/var/games/tuxtype/words` and `/etc/tuxtype`. No
desktop file, no menu entry, no manual page and no setgid bit: the module
is what starts it. Its window is called `kidux-tuxtype`, which the
module's `app_ids` name.

### The patches

Each is small, says at its top what it does and why, and is offered to
Tux4Kids (roadmap); while it is not taken, Kidux keeps it (D88).

1. **`01-keep-the-tables-positions.patch`.** Tux Typing's practice learns
   where a key is from each key pressed (`updatekeylist()` in
   `src/alphabet.c`), through a switch on the SDL key that knows the US
   keyboard's keys only. A key it does not know, the ñ, the comma, the
   full stop or the hyphen of a Spanish keyboard, was given no place and
   no finger the first time it was pressed, and its finger was never lit
   again in that run; the journal said `GetFinger() - Unicode char ''
   has no valid finger.` each time. Now the table is the truth: learning
   fills in only a key the table left without a place, and nothing is
   learnt from a key the switch does not know. And `GetIndex(0)` is -1:
   the empty entries after the table's last matched the character 0.
2. **`02-dead-keys-are-not-typing.patch`.** The acute accent of a Spanish
   keyboard is a dead key: it gives no character, and puts the accent on
   the vowel typed next. Under sdl12-compat it arrives as a key down with
   no character, and the vowel after it as a key down with the accented
   one, which is what the session test sees. The practice counted the
   dead key wrong, with the error sound, and the games took its 0 for a
   letter. A key down with no character is now neither right nor wrong in
   the practice, as Shift was already, and no letter in Fish Cascade and
   Comet Zap.
3. **`03-label-the-keys-in-use.patch`.** The practice's keyboard is
   `keyboard.png` with a label drawn on each key by `GenerateKeyboard()`.
   It labelled every entry of the table that had a place, the capital
   drawn up and to the left of the small letter, so that each key held two
   overlapping letters, and a plain blit of each label, a surface with
   alpha, onto the keyboard, another, turned the letters' soft edges into
   dark specks and lines; a single letter blitted so still had them. Now a
   practice labels
   the keys of its own line and no other, each key once with the small
   letter its first unshifted entry gives, in black at 14 points, centred
   on the key, blended pixel by pixel by the label's own alpha. A lesson's
   keyboard shows the keys it teaches, and a child finds them at once.
4. **`04-list-the-word-lists-in-order.patch`.** The games' menu of word
   lists (`chooseWordList()` in `src/titlescreen.c`) took a theme's lists
   in the order `readdir()` gives them, the disk's, so that the Spanish
   lists came in any order, the accents' among the first. The theme's
   lists are now sorted by their file names, which the theme numbers from
   the easiest to the hardest; the lists all users share and a child's
   own follow them, as before.

What stays as Tux Typing has it: the practice's figures, *Time*, *Chars*,
*CPM*, *WPM*, *Errors* and *Accuracy*, are in English, untranslated in
Tux Typing itself; and a lesson that ends goes back to the main menu, not
to the list of lessons.

When Debian moves Tux Typing on, `debian-source.toml` names the new files
and their sums, `upstream.toml` the new version, with its sums emptied for
the first build to write, and each patch is applied to the new source and
tried again on a session machine, section 6.

## 3. The themes

Tux Typing takes its menus' language from the session, and its lessons,
its games' words and its keyboard table from the theme it is started with,
`--theme <name>`, a folder of `/usr/share/tuxtype/themes/`. The starter
gives it `kidux-<lang>` for the child's language, `kidux-en` for a
language Kidux has no lessons in. `lessons/build.py` writes each theme
from the language's `lessons/<lang>.toml`:

```
settings.txt   theme_locale_name, for Tux Typing's own words
keyboard.lst   the language's keyboard table (section 4)
words/         the language's word lists (section 5), or a link to the
               base theme's words
images         a link to the base theme's pictures, when there is one
scripts/       a lesson a file, named as the list of lessons shows it
```

## 4. The keyboard tables

`keyboard.lst` gives each key a line, read by its characters' positions:
the finger first (0 to 3 the left hand's little, ring, middle and index
fingers, 4 and 5 the thumbs, 6 to 9 the right hand's index, middle, ring
and little), `|`, the key, `|`, and the key of the US keyboard in the same
place, from which Tux Typing knows where the key is, to frame it when it
is next and to label it. Without that last character a key has no place.
So every line of Kidux's tables has it, but the space's, whose place Tux
Typing knows. The Spanish table puts the ñ where the US keyboard has the
semicolon, the hyphen where it has the slash, and each accented vowel, in
both cases, on its vowel; the English one is Tux Typing's own with each
key's place.

## 5. The lessons and the word lists

A language's lessons are its `lessons/<lang>.toml`: the file name pattern,
the words of the pages, and one `[[lesson]]` each with its keys, the name
its file shows when they are not plain letters, the lines that bring the
keys and that place the fingers, a drill of the keys, and a line of words
made only of keys already learnt. Spanish has fourteen, English twelve:
the home row, the top row, the bottom row with the comma and the full
stop, and in Spanish two more of the accented vowels, which teach the dead
key to the right of the ñ and then the vowel. A lesson is four pages, in
the shape Tux Typing's own lessons have: the keys, Enter; the fingers over
a keyboard, P for the drill; Now, words, P for the words; and well done.

`build.py` refuses a lesson Tux Typing could not show well: a line longer
than its page, a practice longer than one line of the practice's screen, a
key not learnt yet, a key the table lacks or does not place, or a
character the script reader takes for markup.

A language with word lists of its own names their folder in `word_lists`.
Spanish has seven, from *Palabras cortas* to *Con tilde*, words a child of
six to twelve knows, in capitals, with the ñ written in every list that
has it and the accents only in the last, as the course has them only at
its end. Each list's first line is its name in the games' menu, then a
word a line. `build.py` refuses a list with no name, a word not in
capitals, longer than twelve characters, typed with a key the table lacks,
or there twice. English uses Tux Typing's own lists.

## 6. Tests

- `tests/test_lessons.py` builds the themes and checks their lessons,
  tables and word lists, and that each of build.py's refusals happens;
  `tests/test_module.py` reads the manifest and runs the starter.
- `tests/session/25-module-tuxtype.py` installs the module through the
  daemon, opens it, and in each language types the first lesson whole; in
  Spanish it also types the second, the ñ's, and checks that Tux Typing
  never logs a key without a finger, and the drill of the thirteenth, the
  accents', with the dead key, and checks that the practice's error count
  stays 0. Its pictures of the first lesson's keyboard and of the
  accents' practice are the guide's.
- kidux-tuxtype builds identically twice (`tests/run reproducible
  kidux-tuxtype`), and its tarball again from its source tarball alone
  (`ci/build-upstream.sh kidux-tuxtype --from-source`).
