# Learning modules: what one is, and how to make one

A learning module is what a child opens from the launcher: GCompris, a typing
course, Scratch, a set of micro:bit projects. Each one is a Debian package,
`kidux-module-<name>`, that an adult can install, enable, disable or remove
on its own from the adult panel, whatever it shares with the others. The
framework that installs, launches and isolates them is
[phase-3-plan.md](phase-3-plan.md); this document is the contract a module is
written to, so that content can be prepared before the framework lands, and
so that the framework is built to this and not the other way round.

## 1. The manifest

A module installs one file, `/usr/share/kidux/modules/<id>/module.toml`:

```toml
id = "scratch"
version = "1.0.0"
name = "Scratch"                       # English; translated through i18n_domain
description = "Make games and stories with blocks."
min_age = 7
max_age = 14
recommended_before = ["typing"]        # best done first; optional
launch = { webapp = "scratch" }        # or { exec = "/usr/libexec/kidux-module-x" },
                                       # or { web = "https://{lang}.example.org/" }
hosts = ["assets.scratch.mit.edu"]     # internet hosts its pages may reach; optional
app_ids = ["org.example.Scratch"]      # what its windows are called; see below
categories = ["programming"]
i18n_domain = "kidux-module-scratch"   # the gettext domain of name and description
memory_max = "2G"                      # the scope's MemoryMax; optional
needs_windows = true                   # only for a child with windows; optional

[[settings]]                           # what an adult sets for each child; optional
key = "type_in"
kind = "switch"                        # switch | integer | number | text | secret
label = "Type it in for me"            # translated through i18n_domain
description = "A button types each program into the editor."   # required, translated
default = true
```

Beside it, `icon.svg`: the tile's picture, drawn like the avatars, so that no
icon theme is needed and the tile is the same on every machine.

- `id` is lower-case letters, digits and hyphens, and is also the package
  name after `kidux-module-`.
- `min_age` and `max_age` are for the adult panel to suggest, never to
  enforce: an adult enables what they like for whom they like. The panel
  shows them beside the module's name, *Ages 7 to 14*, or with one
  bound, *Ages 7 and up* or *Ages up to 14* (D55).
- `recommended_before` names the modules a child does well to have done
  before this one, by id, and the panel says them under the name, on a
  line of their own, *Recommended before: Typing*, by their names where
  the machine has them (D55). A suggestion
  too: nothing is enforced, and a module named there need not exist.
- What a module lets a child reach on the internet is decided by what the
  module is. A native program, or a web application held to its own local
  server (D36), is closed; a web module reaches the hosts its `hosts` names
  and nothing else (D85); a module that opens a website says so in its name
  and description, and an adult switches it on or not (D42).
- `launch` is one of three: `webapp`, a web application the package
  installs under `/usr/share/kidux/webapps/<id>/`, served on
  `127.0.0.1:8123` by `kidux-webapps` and opened in a Chromium application
  window; `web`, an `https://` address on the internet, in which `{lang}`
  stands for the child's language code (`https://{lang}.wikipedia.org/`),
  opened the same way; or `exec`, a native program. Whichever it is, the
  launcher starts it in a systemd user scope, `kidux-module-<id>`, which is
  how it is ended and how its memory is capped.
- `hosts` names the internet hosts a web module's pages may reach, each
  standing for itself and every name under it: lower-case DNS names, no
  scheme, port, path or `*`. A web application names the hosts its library
  comes from, if it has one on the internet; a website names its own. The
  module's Chromium reaches those and nothing else (section 4).
- `name` and `description` are what the adult panel and the launcher show,
  in the language of whoever is looking, through the module's own gettext
  domain; the package installs the catalogue.
- `app_ids` says what the module's windows are called, as globs: a Wayland
  window's `app_id`, an X11 window's `WM_CLASS` class. It is how the
  launcher knows which module a window is of, since the compositor says
  nothing of a window's process (D58, launcher.md section 5). A web module
  needs none: the reader adds Chromium's name for its window,
  `chrome-127.0.0.1__<webapp>_-*` for a web application and
  `chrome-<host>__*` for a website, `{lang}` in the host as `*`
  (`chrome-*.wikipedia.org__*`). A window no manifest claims is taken
  for the module the child has just opened, so a module that forgets it
  still opens; the launcher's log names every window's `app_id`
  (`toplevels:`), which is where to read it.
- `[[settings]]` are what an adult sets in the module for each child, on
  the panel's Modules page (D90). Each module declares its own, and Kidux
  keeps no list of them: it knows only their kinds, a `switch`, an
  `integer` or a `number` (with an optional `min` and `max`), a `text`
  of one line, or a `secret`, a text never shown again once set. Each
  has a `key`, the name the module reads it by (lower-case letters,
  digits and `_`), a `label` and a `description` of what it does, both
  English in the manifest and translated through the module's catalogue,
  and a `default` of its kind (a secret has none). The module reads them
  as `KIDUX_SETTING_<KEY>` in its environment, a switch as `1` or `0`;
  a web application finds them in its address too, `?lang=es&type_in=0`.
  A secret never reaches the child's session: the daemon keeps it and
  uses it itself, for `sign_in`.
- `[sign_in]` says how a module that opens a website signs a child in
  with the account an adult gave: data, never code. `url`, an `https://`
  address on the module's `hosts`; `body`, a table of texts sent as JSON
  in which `{key}` is the setting of that key; `cookies`, the names of the
  session's cookies the answer sets; `script`, optional, a file beside
  the manifest run in the site's first page with `window.KIDUX.lang` the
  child's language; and `start`, optional, where the window goes then.
  The daemon makes the request (`Modules1.SignIn`, daemon.md) and hands
  the child's session only those cookies; `kidux-webapp` opens the
  module's own page first, `webapps/<id>/index.html`, which its package
  ships and which says *Connecting…* or what went wrong with *Try again*,
  and then drives the window through Chromium's DevTools pipe
  (`kidux.browser`, D91). Without an account given, the website opens as
  it is. CodeCombat is the one that does (phase-4c-plan.md, 4.17).
- `needs_windows = true` says the module is only for a child whose modules
  open in windows (D46): a real web browser, an editor with several files
  open. The launcher shows no tile for it to a child without windows, and
  the panel's Modules page shows that child's switch for it off and not to
  be switched on, with *Needs windows* beside the module's description.

One reader, `kidux.modules` in `kidux-common` (D34), reads manifests for the
daemon, the launcher and the panel alike. It uses a manifest only when its
`id` is the directory's name and matches the rule above, `name` is there, and
`launch` names a string `exec` or `webapp`, or a `web` address that begins
`https://` and has a host; any other is skipped with a line in the log, and
the other modules are unaffected. What a manifest leaves out
has a default: `i18n_domain` `kidux-module-<id>`; `memory_max` `2G`;
`description` empty; the ages `0`, no suggestion; `recommended_before`
none, and of a list only the strings that are module ids are kept, the
rest dropped with a line in the log; `app_ids` none, and a value that is
not a list of names is dropped with a line in the log; `settings` none,
and a setting whose table is wrong, which has no `description`, or whose
default is not of its kind, is dropped with a line in the log; `hosts` none, kept
sorted and each once, and a value that is not a list of host names is
dropped with a line in the log; `needs_windows` false, as is any value but
`true`. Without `icon.svg` the
tile shows Kidux's mascot.

## 2. What a module may and may not do

- It runs **as the child**, inside the child's session, with the child's
  language, keyboard and display scale in its environment, in a systemd
  user scope of its own, `kidux-module-<id>` (launcher.md, section 5). It
  sees what the child sees and nothing more: the child's home, never
  `/home/.kidux` nor another child's files, which the Unix user closes to
  it (D17). There is no sandbox around it (D42).
- **It has the screen, less the bar.** For a child without windows every
  main window of a module fills the room above the launcher's bar, without
  a frame, and a dialog floats over its window; for a child with windows
  (D46) every window is in the compositor's frame, among the other
  modules' (launcher.md section 5). A module should start in a window and
  not ask for the whole screen: it gets the room above the bar either way,
  and labwc gives a window taken out of fullscreen a title bar, which is
  how one that asks for it ends up without windows (labwc-notes.md, D60). A
  program that starts fullscreen by itself usually has an option not to,
  as GCompris's `--window`. Other modules
  can be open at the same time, and the child moves between them with the
  bar, Super or Alt+Tab, so a module must not assume it is the only thing
  running.
- **It may be made for Wayland or for X11.** A program with no Wayland of
  its own, a Tk one for instance, runs through XWayland, which the
  compositor starts for it (D58). It works as any other, but on a screen at
  a size that is not a whole multiple of 100 % it is drawn blurred,
  enlarged from 1: so a program that speaks Wayland is the one chosen when
  there is one. An SDL 1.2 program is the exception: `sdl12-compat` scales
  its fixed-size pictures to its window only through XWayland, so its
  starter unsets the `SDL_VIDEODRIVER=wayland` the session sets (Tux
  Typing's does).
- **The child's home is shared by every module.** A file made in one is
  there for the next: what a child writes in one module they open, send or
  print in another, as on any computer. A module saves the child's work
  where the child can find it, in their home and its usual folders, never
  hidden under a directory of its own.
- **A web module keeps the child's work through the browser.** A page
  cannot write to the child's home, so it saves as a web page does: a
  download, which asks in Chromium's file dialog where to keep it, from
  the child's Downloads folder, and it opens a file again through the same
  dialog, which shows the child's home. The policy leaves both open for
  this (section 4). What the child keeps
  is then a file in their home; what a page keeps in Chromium's own
  storage is under the module's settings directory, which no other module
  reaches and which stays when the module is removed (D89).
- **A module may be a door to one website** (D85): the site's own pages,
  in a Chromium window like any web module's, and nothing else of the
  internet. It is for what cannot be shipped, a site whose content lives
  only there, and it is the adult's choice: its name and description say
  that it opens a website, whose site it is, and what the site asks for,
  an account or a subscription, before the adult switches it on. What the
  child does there is the site's, under the site's rules; Kidux only keeps
  the door to that site and no other.
- Its own settings, data and cache go under `~/.config/kidux/<id>/`,
  `~/.local/share/kidux/<id>/` and `~/.cache/kidux/<id>/`, which the
  launcher creates and hands it as `XDG_CONFIG_HOME`, `XDG_DATA_HOME` and
  `XDG_CACHE_HOME`, so that its settings are its own and no other module's.
  Removing the module leaves them in the child's home (D89): a child's
  progress, settings and anything a module kept there for them are found
  again when the module is installed again. Into the first it links the child's `user-dirs.dirs` and
  `user-dirs.locale`, where xdg-user-dirs looks them up: a program asking
  for Documents or Downloads finds the child's, named in their language,
  and not the home itself or an English `~/Downloads`.
- It never asks for a password. The adult password is never typed inside a
  child's session (D6), and the child's password is for signing in.
- It never handles time. The daemon counts and locks; a module is frozen
  under the lock screen like everything else in the session and continues
  where it was.
- It must survive being frozen for hours and thawed, and being killed: the
  session can end while it is open, with warning, when time runs out and an
  adult chooses to end it.
- Progress, if it reports any, goes as JSON to
  `~/.local/share/kidux/progress/<id>.json`, which the adult panel reads.

## 3. Languages

Every string a child or an adult reads is translatable, in English and
Spanish from the first release, through the module's own gettext domain,
`kidux-module-<id>`: its catalogues are in the package's `po/`, extracted
by `ci/i18n-extract.sh` from the package's programs in `bin/` and from the
`name` and `description` of its manifest, and checked by
`tests/project/i18n.sh` like Kidux's own. The same name and description,
in English and in every language it has a catalogue for, are also in the
binary paragraph of its `debian/control`, as `XB-Kidux-Name-<lang>` and
`XB-Kidux-Description-<lang>`: the archive's index keeps them, and the
panel shows them for a module that is not installed yet, when the machine
has nothing of the module but that index (D47). After them, who the module
is for, from the manifest (D55): `XB-Kidux-Ages`, `4-8`, or `2-` or `-10`
with one bound, absent when the manifest has none, and `XB-Kidux-Before`,
the `recommended_before` ids separated by spaces, absent when there are none.
`tests/project/module-fields.py` fails when they are not the manifest's
and the catalogue's words and the manifest's ages and modules first, and
`--update` writes them; lintian, which knows
no such fields, is told to expect them in the package's
`debian/<package>.lintian-overrides`. A new language is a
new catalogue and the fields it brings; nothing of Kidux's changes. Lesson content lives in the
package, under `packages/kidux-module-<id>/content/<lang>/`, since a source
package holds only its own directory; English is the reference tree, and
`tests/project/content.py` fails when the Spanish tree is missing a file or
was translated from an older English one. A third-party program is only
chosen as a module if it already speaks both languages.

## 4. Packaging

A module is a Debian source package under `packages/kidux-module-<id>/`,
built and checked exactly like every other package (packaging.md): native
format, `debhelper-compat 13`, lintian clean, reproducible. It installs the
manifest, the icon, its content and its translations, and depends on
whatever program it runs. It never depends on another module. If it is a
web application it depends on `kidux-webapps` and installs its pages
under `/usr/share/kidux/webapps/<id>/`; a module that opens a website
depends on `kidux-webapps` and installs no pages, only its manifest, its
icon and its words.

`kidux-webapps` is what web applications share, and nothing of any one of
them: `kidux-webapps.service`, a static server of its own on
`127.0.0.1:8123`, run by systemd as a user it makes for it
(`DynamicUser`), with no capabilities, a read-only system, no homes and no
address but the loopback one to reach; it serves files under
`/usr/share/kidux/webapps/` and nothing else, refusing any path that leads
out of it, by `..`, an encoded `..` or a symbolic link, and never listing a
directory. `/usr/libexec/kidux-webapp <module id>`, which the launcher
runs, reads the module's manifest and opens a Chromium application window
(`--app`, no tabs and no address bar) on its address: a web application's,
`http://127.0.0.1:8123/<webapp>/?lang=<the child's language>`, or a
website's, the manifest's `web` with `{lang}` the child's language. It
gives it a profile of the module's own under its `XDG_CONFIG_HOME` (D44),
Chromium's own words in the child's language (`--lang=<the child's
language>`, from `chromium-l10n`, which `kidux-webapps` depends on, since
Debian's Chromium has only English without it), and, for a web
application only, WebGL drawn in software where the machine has no
graphics Chromium takes (`--enable-unsafe-swiftshader`: Scratch's stage
needs WebGL, and Chromium no longer falls back to SwiftShader by itself;
it is unsafe for pages from anywhere, D85). After Kidux's own flags come
the machine's, one a line from `/etc/kidux/chromium-flags`, which the
daemon writes from the panel's *Advanced* settings (D51, D52), so that
one there wins over Kidux's for the same thing; `kidux-webapp --print
<module id>` prints the command line instead of running it. A module that
carries Chromium of its own, as ScratchJr's Electron, draws as Chromium
does on the machine's graphics, so its starter reads the same file and
passes the same options.

Two things hold a web module's Chromium to what is its own (D85). The
first is each module's **wall**: every Chromium `kidux-webapp` starts has a
proxy that answers nothing, `--proxy-server=127.0.0.1:1`, and a bypass
list of the server and the module's `hosts`, each with every name under
it (`--proxy-bypass-list=127.0.0.1;codecombat.com;*.codecombat.com`), so
that whatever else a page asks for fails; the daemon refuses every proxy
flag among the machine's, which would take the wall down. The second is
the **policy** every Chromium on the machine is held by, whatever starts
it, `/etc/chromium/policies/managed/kidux.json`.
`/usr/libexec/kidux-chromium-policy` writes it, when `kidux-webapps` is
configured and whenever a package installs or removes a module's manifest
(a dpkg trigger on `/usr/share/kidux/modules`), from the base,
`/usr/share/kidux-webapps/policy.json`, and the installed modules: it
blocks every address but the server's, the union of the installed
modules' `hosts`, and `blob:`, the address of a file a page makes itself
and hands to the browser to save, as Scratch saves a project (D75); and
it turns off signing in, sync, extensions, incognito and guest windows,
adding people, translation, the password manager, printing, the search
engine and reporting (D36), and leaves the developer tools to
`kidux-webapp`'s own pipe, their pages blocked like any other address
(D91). Nothing but the allowlist comes from
the modules. It lets a child keep their work: the file dialogs are open, so
that a module opens a child's files from their home, and a download is
refused only when its type is dangerous (`DownloadRestrictions` 1), each
asking in the file dialog where to keep it (`PromptForDownloadLocation`),
from the child's Downloads folder, named in their language (D76). A child
has no other Chromium.

## 5. The reference module

The reference modules, and the tests' own stand-ins, carry `[Test]` in
their names, `[Prueba]` in Spanish (`[Test] Hello`, `[Test] Canary`), so
that an adult who sees them on the panel's Modules page knows they are not
for a child (D70); the user guide does not list them.

`kidux-module-hello-web` is the same for a web application: hello's page
again, one `index.html` that `webapp/page.py` writes when the package is
built, with every language's page and words in it, so that it needs
nothing but itself; a link on it to a page on the internet, which the
policy keeps closed; *Save*, which keeps the page as a file, `hello.txt`
named in the child's language, made in the page and downloaded from its
`blob:` address where the child says in the file dialog, as Scratch saves
a project; and *Done*, which closes Chromium, and has the focus whenever
the page is shown. Chromium refuses to let a page close a window
with more than one page in its history, so after a link out and back
*Done* does nothing, and the bar's *Home* is the way out. A module made of
web pages is started by copying it. `kidux-module-basic` is the larger
example of such a page of Kidux's own: written by its `webapp/page.py`
the same way, with a guide in every language built from Markdown into it
beside a program it serves, wwwBASIC (basic.md). Its manifest names hello in
`recommended_before`: the same page, before its web one.

`kidux-module-hello` is the smallest module that exercises every part of
this contract: a manifest, an icon, its own translated words, one page of
content in two languages, a program that runs in its own directories, and a
launch. It exists so that the framework is tested against a module with
nothing else in it, and so that a new module can be started by copying it:

```
packages/kidux-module-hello/
  module.toml              the manifest
  icon.svg                 the tile's picture
  bin/kidux-module-hello   the program, installed to /usr/libexec
  content/en/hello.md      the page, in English, the source
  content/es/hello.md      its translation, with the English file's hash
  po/kidux-module-hello.pot, po/es.po    its words
  tests/test_module.py     the manifest reads, the words are complete
  debian/                  control, rules, changelog, copyright, source/format
```

To make `kidux-module-<id>` from it, copy the directory and then:

- **Rename** `hello` to the new id everywhere it names the module: the
  directory, `id`, `launch`, `i18n_domain` and the `po/` template in the
  manifest, the program's name in `bin/` and in `debian/rules`, the
  `DOMAIN` and the content path in the program, the package name in
  `debian/control`, `debian/changelog` (start at `0.1.0`, dated by `date
  -R`) and the lintian overrides' file and line, and the manifest's
  `version`, which is always the package's, and which the panel's Modules
  page shows beside the module's ages, without what follows a `+`; then
  `tests/project/module-fields.py --update` writes the new names into
  `debian/control`.
- **Replace** the icon (drawn like the avatars, branding/README.md), the
  content, the program, and the package's description, which is what an
  adult reads on the panel's *Modules* page before installing the module:
  its short description is `Kidux learning module: <Name>, <what it is>`,
  what an adult reads in apt, and its `XB-Kidux-` fields (section 3) are
  what the panel shows, in the machine's language (daemon.md section
  9). A module that runs a program already
  in Debian has no content, and its `debian/control` depends on that
  program; its manifest's `launch` names the program, or, when the program
  needs something set before it starts, a short starter of the module's
  own in `bin/`, installed to `/usr/libexec/kidux-module-<id>`, that sets
  it and `exec`s the program. `kidux-module-gcompris` is one: its starter
  answers GCompris's first-start questions, which a child who cannot read
  could not.
- **Keep** the rest: the build, the tests, the rule that the program reads
  its language from the session, writes only in the child's home and in the
  three directories the launcher gives it, and starts in a window
  (section 2).

Then `ci/i18n-extract.sh` makes the template and merges `po/es.po`, which
is translated by hand; `tests/project/content.py --update` records the
hashes of the translated content; and the package goes into
`ci/build-all.sh`'s list of packages built at once, after
`kidux-launcher`.
