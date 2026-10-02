# Phase 3 plan — The module framework and the first module

Working plan for roadmap phase 3, built before phase 2 (D31). It is written
so that each step can be built unattended, on the VM, by the cycle of
phase-1-plan.md "Running unattended": `ci/test-release.sh` green, then the
commit, for every step.

This document is a plan, not a decision record. The decisions it rests on
are D32 to D36 in [architecture.md](architecture.md); the contract a module
is written to is [modules.md](modules.md), and this plan changes that
document where it says so.

## 1. Where we start

Steps 3.1 to 3.7 are built: the daemon lists modules and switches them
per child, the panel has its *Modules* page, the launcher shows a tile per
enabled module and opens it in a scope of its own, and the child's session
runs under `labwc`, where every open module fills the room above the
launcher's bar, or has a window of its own for a child with windows, and
the bar along the bottom takes the child between them. The
tests' stand-in modules, the canary and the robin, go through all of it.
`kidux-module-hello`, the reference module, installs from the archive
and is what a new module is copied from. An adult installs and removes a
module from the panel's *Modules* page, through the daemon's update job.
GCompris is the first real module, and `kidux-webapps` with
`kidux-module-hello-web` opens modules made of web pages in a Chromium
window held to a server on the machine. Step 3.8, the owner's first hand
test at the MacBook, is done, and what it found is built in steps 3.9 to
3.15 (D45 to D53): every module closes from the bar, the modules on offer
speak the machine's language, the display scale is automatic, an adult
sets a child's time left, Chromium's flags for a machine are an advanced
setting, and windows are a setting of the child. Steps 3.17 and 3.18 give
a child's time to the days of the week an adult ticks (D54), and have
every module say who it is for, its ages and the modules best done first
(D55). Steps 3.19 and 3.20 put the child's session on `labwc`, with
XWayland on (D58, D59), and give a child with windows a desk where every
window is in view at once, in labwc's frame (D57). What is left of the
phase is the owner's hand tests, steps 3.16 and 3.21.

## 2. Definition of done

On a machine running Kidux:

1. An adult installs a learning module from the panel's *Modules* page,
   from the list the archive offers, and removes it the same way; both
   refused, with a sentence, while a child has a session.
2. An adult switches each installed module on or off for each child.
3. A child sees a tile for each module switched on for them, with its name
   in their language, opens it by tapping or by keyboard, uses it, opens
   another beside it, moves between them and the launcher with the bar or
   the keyboard, and finds in one module the files they made in another.
4. A module is a closed door or an open one by what it is: an adult
   decides which a child may open, and nothing else about the network.
5. The lock screen over an open module, and continuing afterwards, leaves
   the module exactly where it was; logging out ends the module with the
   session.
6. `kidux-module-hello` exercises every part of the contract with nothing
   else in it, and `kidux-module-gcompris` is the first real module.
7. The children of the owner use the MacBook daily, with GCompris.
8. Every part above is checked by `ci/test-release.sh`.

## 3. Decisions

Recorded in the decision log; summarised here because every step refers to
them.

- **D32 — A module runs in a systemd user scope.** The launcher starts
  each module with `systemd-run --user --scope --unit=kidux-module-<id>
  --collect` under the child's user manager, which logind already starts
  for a session of class `user`; the scope is what lets the launcher end a
  module cleanly, cap its memory, and lets a module outlive a launcher
  crash, so that the child's work is not lost when the launcher is started
  again. (The network namespace D32 first had went with D42.)
- **D33 — Installing and removing a module goes through the daemon and the
  update job runner of step 9.8**, as `kidux-update install <package>` and
  `kidux-update remove <package>`, refused with `SessionActive` while any
  child session exists: dpkg never replaces what a session may be running.
  Enabling and disabling are state, `modules.toml`, and need no job.
- **D34 — The daemon says which modules exist and which are enabled; the
  screens read the manifests themselves.** `Modules1.List(username)`
  returns every installed manifest's `id` with `enabled` for that child.
  Manifest reading moves to `kidux.modules` in `kidux-common`, used by the
  daemon (what is installed), the launcher (tiles) and the panel (switches),
  so there is one reader. A module's `name` and `description` are English
  strings in the manifest, translated through the module's own gettext
  domain, which the module package installs.
- **D35 — Every child's session has PipeWire.** `kidux-session` depends on
  `pipewire-audio`, whose user units start with the child's user manager;
  there is no system-wide sound server. GCompris speaks.
- **D36 — Web-application modules are confined by Chromium's policy, not by
  a network namespace.** `kidux-webapps` serves `/usr/share/kidux/webapps/`
  on `127.0.0.1` as a system user, and a Chromium profile per module
  per child is allowed that origin and nothing else through the managed
  policy in `/etc/chromium/policies/managed/`: a web application is a
  closed door by that policy, whatever the machine's connection.
- **D40 — The lock freezes the child's user manager with their session**,
  since the modules' scopes live there, and thaws it before the session
  ends, the machine powers off or the daemon stops.
- **D42 — The child's home is shared by every module, there is no
  sandbox, and the manifest says nothing about the network.** A file made
  in one module is there for the next; a module's own settings, data and
  cache are the only things that are its own; whether a module opens the
  web is what the module is, and the adult switches it on or not.
- **D43 — Several modules at once: `sway` is the child's compositor, and
  the launcher draws the bar.** Each module on a workspace of its own, the
  launcher on the first, a bar along the bottom with Home, the open
  modules, the time left and Lock, Super and Alt+Tab on the keyboard.
  `cage` stays for the trusted screens. Step 3.3.
- **D45 — Every module closes from the launcher's bar: asked first,
  forced as the emergency.** A close button on the bar for the module on
  screen; it asks the module to close, and ends it by force only when it
  does not go, after asking the child. Step 3.9.
- **D46 — Windows are a setting of the child, and a module may require
  them.** Modules that can be moved, resized, put fullscreen and opened
  several at once, for the children an adult switches it on for; a
  manifest may require it. Before the first real web module, phase 4.
- **D47 — A module carries its name and description in every language in
  its package's control fields.** `XB-Kidux-Name-<lang>` and
  `XB-Kidux-Description-<lang>`, read by the daemon's catalogue. Step
  3.10.
- **D48 — Kidux answers GCompris's first-start questions and leaves its
  downloads on; the module's description says it needs the internet.**
  Step 3.11.
- **D49 — One display scale for every screen, chosen by the adult, and
  the room a larger screen has is used.** The sign-in screen and the
  child's session share the one scale, from a finer set of choices;
  every screen fits 1280x800 whole and uses the room of a larger one.
  Step 3.12.
- **D50 — The adult sets a child's time left for today, zero included.**
  Step 3.13.
- **D51 — Chromium's drawing on a machine's graphics is settled on the
  machine, through a file of flags Kidux reads.** Step 3.14.
- **D52 — The settings that depend on a machine's hardware are on the
  panel's System page, under *Advanced*, Chromium's flags first.** The
  daemon keeps them and writes the file; the panel is the one way in.
  Step 3.14.

- **D54 — A child's time is for the days of the week an adult ticks.**
  Seven boxes on the child's page, all ticked for a new child; on a day
  not ticked the child is blocked at sign-in as when their time is spent,
  and an adult's grant still lets them in. Step 3.17.
- **D55 — A module says who it is for: an age range, and the modules
  best done first.** `min_age`, `max_age` and `recommended_before` in the
  manifest, carried in the package's fields for a module not installed,
  shown on the panel's Modules page. Step 3.18.
- **D56 — The automatic scale leaves room to spare, 1600x960, and the
  System page says what it comes to on this screen.** Step 3.12.
- **D57 — With windows on, a child's modules share one desk: every
  window in view at once, with a frame and its buttons, and the bar as
  the taskbar.** Step 3.20.
- **D58 — labwc replaces sway as the child's compositor, and XWayland is
  on.** Frames with buttons for every program, real minimise, the
  foreign-toplevel protocol in place of sway's socket, two configurations
  (kiosk and desk); X11 programs of one child see one another; X11
  windows soft on a high-density screen, so Wayland modules are
  preferred. Step 3.19.
- **D59 — The whole sizes are the preferred ones, and the panel marks
  the others and says why.** Step 3.19.

## 4. What changes in the contract (modules.md)

- The manifest gains `name` and `description`, English, translated through
  `i18n_domain`; `icon.svg` beside the manifest is the tile's picture, so
  that no icon theme is needed and the tile is the same on every machine.
- `launch = { exec = "..." }` names a program on the machine; the launcher
  runs it as D32 says. `launch = { webapp = "<id>" }` waits for step 3.7.
- A module's own settings, data and cache go under `~/.config/kidux/<id>/`,
  `~/.local/share/kidux/<id>/` and `~/.cache/kidux/<id>/`, which the
  launcher creates before the first start and passes as the XDG variables,
  so that removing the module removes them and no other's; the child's
  work goes in the child's home, shared by every module (D42).
- The reference module's content lives in its package,
  `packages/kidux-module-hello/content/<lang>/`, and
  `tests/project/content.py` checks it from the first commit that adds it
  (step 3.4 changes modules.md section 3 to say so).

## 5. Work plan

Each step ends installable, tested by `ci/test-release.sh`, and committed.
Sizes are relative effort. The rules of phase-1-plan.md "Running unattended"
apply to every step, and so do these, which every step of this phase needs:

- **Versions.** A published version's bytes never change (D23): every
  package a step touches gets a new version in its `debian/changelog`, dated
  by `date -R`, and the package's `VERSION` where it keeps one. `kidux-greeter`
  and `kidux-launcher` depend on `python3-kidux (>= <the version that adds
  what they use>)`, so that a machine never runs a screen against an older
  library.
- **Where the tests go.** Unit tests beside the code (`packages/<name>/tests/`).
  Acceptance checks are new `kidux-as` commands (`tests/lib/seed/tools/kidux-as`)
  called from a numbered file in `tests/acceptance/`. Session checks are
  numbered files in `tests/session/`, run in name order, and the purge test
  (`<NN>-purge.py`) has to stay last: a step that adds one renames the purge
  test to the number after its own. In `tests/acceptance/`,
  `19-no-key-no-archive.sh` stays last the same way, since it breaks the
  machine's archive on purpose; the numbers before it are free for new
  checks. Every picture the user guide shows is listed in
  `tests/lib/doc-screenshots.txt`. The session tests reach a control by
  counting Tab stops from a known one, so a control added to a row that
  other tests cross (the rows that give time, the panel's tab bar, the
  children's row) changes every count that crosses it: grep the tests for
  the row before running the battery, not after.
- **The stand-in modules of the tests** live in `tests/lib/seed/modules/canary/`
  (`module.toml`, `icon.svg` and the program `run`) and, from step 3.3,
  `robin/`, its twin in another colour; the test that needs one copies it
  to `/usr/share/kidux/modules/<id>/` over SSH with `sessionlib.copy`, as
  `01-install.py` copies `kidux-as`, and removes it when it is done, so
  the picture of an empty launcher stays the empty one.
- **Looking inside a child's session.** `KIDUX_VM_STOP_AFTER=NN tests/run
  session` leaves the machine up after test NN, and
  `tests/lib/session-one.py` runs one test file against it
  (tests/README.md). `sessionlib.windows()` lists every window as the
  launcher sees it through labwc's foreign-toplevel protocol, and
  `on_screen()` says whose is in use; the launcher logs `toplevels:` each
  time they change; `labwc -d` in `kidux-session` with its stderr sent to
  a file shows every device and window labwc sees, and a client run with
  `WAYLAND_DEBUG=1` shows every event it is sent, which is how the lost
  first key of step 3.3 was found.
- **Documents.** Each step changes the developer document of the part it
  builds (daemon.md, launcher.md, panel.md, modules.md) so that it describes
  what is built, in the present, and adds its strings to the catalogues
  (`po/kidux.pot` and `po/es.po` of the package, `tests/project/i18n.sh`
  keeps them complete). The user guide's section 9 says what each module
  is as it arrives, in both languages.

### 3.1 — `kidux.modules`, `Modules1` for real, and the tiles — M — **done 2026-09-24**

1. **`kidux.modules`** in `kidux-common` (`packages/kidux-common/kidux/modules.py`),
   the one reader of D34. `MODULES_DIR = paths.DATA_ROOT / "modules"`; the
   id rule of today's `kidux_launcher/modules.py` (`[a-z][a-z0-9-]{0,31}`).
   `Module`, frozen: `id`, `name`, `description`, `icon` (the path of
   `icon.svg` beside the manifest, or `""` when there is none),
   `launch` (the dict), `i18n_domain` (default
   `kidux-module-<id>`), `min_age`, `max_age` (`0` when absent),
   `memory_max` (the string, default `"2G"`). `read(id, root=MODULES_DIR) →
   Module | None`: `None`, with one `log.warning`, when the directory or the
   file is missing, the TOML does not parse, `id` differs from the directory,
   `name` is missing, or `launch` has neither a string `exec` nor a string
   `webapp`. `installed(root=MODULES_DIR) → list[Module]`: every directory
   under `root` whose manifest reads, sorted by id. `name_in(module,
   language)` and `description_in(module, language)`: `gettext.translation(
   module.i18n_domain, languages=[language], fallback=True).gettext(text)`,
   so a module without a catalogue shows its English. `kidux_launcher/
   modules.py` goes; the launcher and the daemon import this, and
   `python3-kidux` grows no dependency. Unit tests against a directory of
   manifests: a good one, one with a bad id, one without `name`, one whose
   `launch` is a string, one that is not TOML, an empty directory; and the
   two translators with a domain that has no catalogue.
2. **The daemon.** `Modules1.List(username) → aa{sv}`: `[{id, enabled}]`
   for every module of `installed()`, in that order, `enabled` from the
   child's `modules.toml` (the file's `enabled = ["id", ...]` list; the
   state layer already versions it, `kidux.state`); the gate as today
   (`require_self`, then `require_child`). `Modules1.SetEnabled(token,
   username, id, enabled)`: `InvalidArgument` when `read(id)` is `None`;
   otherwise the list gains or loses the id, the file is written, the audit
   line is `module enabled` or `module disabled` with `child` and `module`,
   and `ModulesChanged(username)` is emitted; setting what is already set
   is not an error and writes nothing. An id in the file that is no longer
   installed is left there and never listed: removing a package must not
   rewrite every child's file, and putting it back restores the switch.
   daemon.md gains a section *Modules* between *Sessions* and *The lock*
   saying exactly this, and phase-1-plan.md's API table lists the real
   return values.
3. **The launcher.** `view.py` draws the middle from `Modules1.List` and
   `kidux.modules`: a `Gtk.FlowBox` inside a `Gtk.ScrolledWindow`, one
   `Gtk.FlowBoxChild` per enabled module holding the icon (the SVG through
   librsvg, as the mascot is drawn, 128 px, the mascot itself when the
   module has no icon) over the name in the child's language, six to a row
   at 1280 px, the rows scrolling when there are more (launcher.md section
   6 for the sizes and the focus ring). A module `List` names whose manifest
   no longer reads gets no tile. `ModulesChanged` for this child redraws
   the middle; `NOTHING_YET` with the mascot stays what an empty list shows.
   Activating a tile only logs until step 3.2, and the tile is drawn with
   that step's `open` in mind: the FlowBox's `child-activated` handler,
   `_open`, is the one place. Tab reaches the tiles as one stop from *Lock*
   backwards; the arrows move between them.
   launcher.md section 5 says how the tiles are drawn.
4. **The panel.** The *Modules* page as panel.md says: a `.kidux-adult`
   form with one `Gtk.Grid`: the installed modules down, each row its name
   and description in the machine's language (`name_in`, `description_in`)
   and, across, one `Gtk.Switch` per child under the child's name, the
   switch reading `Modules1.List(child)`. Flipping a switch calls
   `SetEnabled` at once and shows the *Saved* notice, or the daemon's
   sentence and the switch put back. With nothing installed the page keeps
   today's sentence and adds *An adult can add modules from this page*
   (step 3.5 makes it true; until then it is one sentence, not a button).
   `panel.py` gains `set_module(username, module_id, enabled)` and the page
   answers with `modules` (id, name, description, per-child enabled) in its
   form data; `PANEL_ACTIONS["panel_modules"]` grows to match and the
   way-forward test keeps passing.
5. **Sound.** `kidux-session` depends on `pipewire-audio` (D35);
   `session-inner` needs nothing: the user manager starts PipeWire's
   sockets. The session test checks that `pw-cli info 0` answers as the
   child, on the socket in their `$XDG_RUNTIME_DIR` (`runuser -u leo -- env
   XDG_RUNTIME_DIR=/run/user/<uid> pw-cli info 0`, over SSH as root).

**Tests.** Unit: `kidux.modules` entire; the daemon's `List` and
`SetEnabled` rules, including a sibling's id from a child, an uninstalled id,
an enabled id whose package is gone, and setting what is already set;
`test_panel.py` for the page and `set_module`. Acceptance
(`08-modules.sh`, the key test renamed `09-no-key-no-archive.sh`): the
test fetches the canary's manifest and icon from the seed into
`/usr/share/kidux/modules/canary/`, `kidux-as modules marta` prints `canary
off`, `kidux-as enable marta canary on` then prints `canary on` and the
audit line exists, `kidux-as enable marta nothing on` is refused with
`InvalidArgument`, `kidux-as modules marta` as the child lists their own
and `child-sibling` is refused a new sibling's, and with the files gone the
module is no longer listed and its id stays in the child's file. Session
(`15-modules.py`, the purge test renamed `16-purge.py`): with the manifest
copied over SSH, the panel's *Modules* page shows it with a switch per
child; the switch turned on for Leo by keyboard (picture `panel-modules`);
Leo's launcher shows the tile (picture `launcher-tile`); off again from the
panel over the lock screen, and the launcher, open all along, shows the
mascot again; the page with a module on it fits and was drawn, which
`15-modules.py` checks itself since it runs after `13-every-screen-fits.py`.

**Acceptance:** the runs above green; `tests/run reproducible` green; the
pictures `panel-modules` and `launcher-tile` listed in
`tests/lib/doc-screenshots.txt` as `panel-modules.png` and
`launcher-tile.png`, for the user guide's sections 8 and 5.

### 3.2 — Launching, and the sandbox — M — **done 2026-09-24**

1. **`kidux_launcher/launch.py`**: `command(module, home) → list[str]`, a
   pure function from a `Module` and the child's home to the argv the
   launcher runs; the argv is the one launcher.md section 5 shows, and the
   test asserts the whole of it (D32, D42): a scope with the manifest's
   memory cap and the module's three XDG directories, no sandbox. The
   scope, not the launcher's life, is what ends a module, so a launcher
   that crashes leaves the child's work open. `launch = { webapp }` raises
   `NotImplementedError` until the web-application step, and the launcher
   shows the sentence of item 2 for it. `kidux-launcher` depends on
   `systemd`.
2. **The launcher** creates the three directories (mode 0700) before the
   first start, runs the command with `Gio.Subprocess` (`stdout` and
   `stderr` inherited, so that a module's complaints land in the session's
   journal), and remembers the scope's name while it runs; with
   `--scope`, `systemd-run` runs the program itself, so the subprocess is
   the module and watching it end is watching the module end. A module
   that fails to start (the program missing,
   `systemd-run` refused, exit status other than 0 within two seconds)
   shows *That did not open. An adult can look at it.* as a notice over the
   tiles and logs the command and the status.
3. **The session's end.** Logging out ends the session and its
   compositor, and with it every window a module had; the module's scope
   then ends with the user manager (`UserStopDelaySec`). The module's
   scope is under the child's user manager, not the
   session's scope, so the lock freezes the user manager too (D40): the
   daemon's `FreezeUnit` and `ThawUnit` take `user@<uid>.service` after and
   before the session's scope, and both units are thawed before the machine
   powers off or the daemon stops, since systemd refuses to stop a frozen
   unit.
4. **The stand-in module for the tests**, `tests/lib/seed/modules/canary/`:
   the manifest with `launch = { exec =
   "/usr/share/kidux/modules/canary/run" }`, and `run`, a Python 3 GTK 4
   program that opens a window filling the screen with the text *canary*
   in a large label, writes `$XDG_DATA_HOME/opened` with the outcome of
   `urllib.request.urlopen("http://10.0.2.2/", timeout=3)` (the archive's
   web server; `reached`, or the exception's class name), and stays open
   until it is ended. It is what the session tests open.

**Tests.** Unit: item 1, every branch. Session (`16-module-open.py`, the
purge test renamed `17-purge.py`): Leo opens the canary by keyboard (Tab
to the tile, Enter), its window is on the screen (picture `module-open`,
mostly the label's colour); `systemctl --user is-active` as Leo, over
SSH, shows `kidux-module-canary.scope` active; the module's three
directories exist, mode 0700, and its `opened` note names its data
directory; the note it writes in Leo's home is there for every module;
it reaches the host as any program of the child's does; the power button
locks over it, `user@<uid>.service` is frozen, and *Continue* brings the
same window back (picture `module-after-lock`); `kill <launcher pid>`
leaves the scope active and the module on the screen; the module ending
gives the launcher back with the tile; opened again, the lock screen's
*Log out* ends the session and the module with it. Step 3.3 rewrites this
test for several modules at once. Acceptance: nothing new.

**Acceptance:** the session run green, and the launcher.md acceptance of
plan step 9.7 that waited for a module, "a locked session resumes exactly
where it was, including a module that was open", now proven.

### 3.3 — Several modules at once: `sway`, and the launcher's bar — L — **done 2026-09-25**

The child's session moves from `cage` to `sway` (D43), and the launcher
gains the bar that makes several open modules usable. Proven on the test
machine before this step was written: sway starts under greetd's session
with the launcher in it exactly as cage did, two windows tile side by side,
a layer-shell bar from GTK 4 stays on top and keeps its room, `swaymsg`
and `python3-i3ipc` move windows between workspaces, and `bindsym
--release Super_L` and `Alt+Tab` switch them. What did not work on the way
and this step must get right: the layer-shell library must be in the
process before GTK opens its display (`LD_PRELOAD`, item 2); a lone
`bindsym Mod4` does nothing, it has to be `--release Super_L`; a module
that asks for fullscreen gets it from sway unless the launcher takes it
back; `bar { mode invisible }` still starts a `swaybar`, so the
configuration has no `bar` block at all.

1. **`kidux-session`.**
   - `Depends: sway (>= 1.10), xdg-user-dirs` beside `cage`, which the
     trusted screens keep; `Conflicts: foot, wmenu`, the terminal and the
     menu sway recommends, since nothing a person types is installed on a
     child's computer (session.md section 1).
   - `/usr/share/kidux/sway.conf`, packaged, root-owned, read-only to the
     child:
     ```
     xwayland disable
     default_border none
     default_floating_border none
     smart_borders off
     focus_follows_mouse no
     titlebar_border_thickness 0
     titlebar_padding 0
     assign [app_id="org.kidux.Launcher"] workspace number 1
     bindsym --release Super_L workspace number 1
     bindsym Alt+Tab workspace next_on_output
     bindsym Alt+Shift+Tab workspace prev_on_output
     exec /usr/lib/kidux/session-inner --keep-running /usr/libexec/kidux-launcher
     ```
     No `bar` block, no other binding, no `include`. The keyboard layout
     comes from `XKB_DEFAULT_LAYOUT` in the environment, which sway reads
     as cage did; the scale is set by `session-inner` through `wlr-randr`,
     which sway serves as cage did.
   - `kidux-session` `exec`s `sway -c /usr/share/kidux/sway.conf` in place
     of `cage`; the environment it exports stays.
   - `session-inner` runs `xdg-user-dirs-update` once before the launcher,
     so that the child's home has its usual folders in the child's
     language, where modules save the child's work (D42); and when its
     loop ends it runs `swaymsg exit` in place of killing `$PPID`, which is
     how the session ends.
   - session.md: sections 1 and 3 describe this; section 6's table gains
     the rows for sway (no bindings but three, no XWayland, no terminal
     installed, the IPC socket reachable by the child's processes runs
     things as the child and nothing more; virtual-terminal keys refused by
     logind's `chvt` denial as before, which `05-doors.py` keeps proving).
2. **The launcher**, which is now the child's desktop.
   - `kidux_launcher/sway.py`: the compositor behind a protocol, the real
     one on `i3ipc.Connection()` (`python3-i3ipc`, `SWAYSOCK` from the
     environment): `windows()` as `(container id, pid, app_id, workspace)`
     from the tree's leaves; `on(event, handler)` for `window` and
     `workspace` events on a thread, delivered to the main loop with
     `GLib.idle_add`; `move(container, workspace)`, `show(workspace)`,
     `unfullscreen(container)`, `exit()` as `swaymsg` commands. A fake
     for the tests.
   - `kidux_launcher/desk.py`: the policy, no GTK. A window belongs to
     the module whose scope its pid is in, read from `/proc/<pid>/cgroup`
     (`kidux-module-<id>.scope`); the first window of a module gets the
     lowest free workspace from 2 and the module keeps it while any
     window of its is open; every later window of the same module goes to
     that workspace (a dialog sway floats stays where it is); a window
     that turns fullscreen is told `fullscreen disable` at once, since the
     bar must stay reachable and a module that wants the whole screen has
     it minus the bar; a window of no module (there should be none) is
     left alone and logged. Opening a module from a tile: if it has a
     workspace, `show` it; else start it (launch.py as it is) and show its
     workspace when its first window comes. At start, the modules
     `launch.running()` finds and their windows are mapped the same way,
     so a launcher started again after a crash has the bar right; the
     wait behind a module of step 3.2 goes.
   - `kidux_launcher/bar.py`: a second `Gtk.Window` of the same
     application, a layer-shell surface on the bottom edge, layer top,
     exclusive zone its own height (56 px at scale 1, the launcher's
     button height), keyboard interactivity none: *Home* (the mascot,
     small), one button per open module with its icon at 32 px and its
     name, in the order they were opened, the one on screen marked, *Home*
     when it is the launcher; then, while a module is on screen, the time
     left in the words of `model.py`, the launcher's warning banner when
     there is one, and *Lock*, since that is what the child is looking at
     (on the launcher they are on its own page). Tapping a module's button
     shows its workspace; *Home* shows workspace 1. The
     bar is drawn in the launcher's colours (launcher.md section 8), a
     shade darker than the page so it reads as a bar.
   - `gtk4-layer-shell` (1.0 in trixie, `gir1.2-gtk4layershell-1.0` and
     `libgtk4-layer-shell0`, both in `Depends`) must be loaded before GTK
     opens its display: `main.py` checks `LD_PRELOAD` and, when the
     library is not in it, re-executes itself with
     `LD_PRELOAD=libgtk4-layer-shell.so.0` once; `Gio.SubprocessLauncher`
     with `LD_PRELOAD` unset starts the modules, so they do not inherit
     it. The tests' `launcher_pid()` pattern keeps matching.
   - Tiles stay sensitive while modules are open; the home page keeps its
     Lock, Log out and Turn off. `session-inner`'s loop and the exit
     statuses stay as launcher.md section 4 says.
   - launcher.md sections 1, 2, 4, 5, 6 and 8 describe the launcher as it
     now is; architecture.md section 5 already does.
3. **The tests' second stand-in module**, `tests/lib/seed/modules/robin/`:
   the canary's files with `id = "robin"`, `name = "Robin"`, and `run`
   drawing its window in another colour (`#3a86ff`), so that two modules
   can be open at once in the tests; both programs also list the files of
   the child's home in their `opened` note, so that a test can see one
   module's file from the other.
4. **The user guide**, section 5, in both languages: the bar, several
   modules at once, Home and the keys, with the pictures below.

**Tests.** Unit: `sway.py`'s parsing of a tree and of `/proc/<pid>/cgroup`
against saved samples, and `desk.py` against the fake: first window gets
a free workspace, later windows follow, fullscreen refused, a launcher
started with modules already running maps them. Session:
`09-child-session.py`'s pictures of the launcher gain the bar (its colour
checks move up by the bar's height; look at every box that names the
bottom of the screen); `15-modules.py` unchanged in what it proves;
`16-module-open.py` rewritten: Leo opens the canary, which appears on its
own workspace filling the screen above the bar (picture `module-open`;
yellow above the bar, the bar below); the canary asked for fullscreen and
did not get it (`swaymsg -t get_tree` shows `fullscreen_mode` 0); Super
brings the launcher back (picture `launcher-with-module-open`, the bar
listing the canary); the robin opens beside it on a third workspace;
Alt+Tab goes round the three (picture `module-two-open`); the canary's
note is in Leo's home and the robin sees it; the lock and continuing
bring the same workspace back; killing the launcher brings it back on
workspace 1 with both modules in the bar; ending the canary removes it
from the bar; logging out from the lock screen ends everything. Acceptance:
`kidux-session`'s conflicts hold (`dpkg -l foot wmenu` finds nothing) and
`sway.conf` is root's, mode 0644. `13-every-screen-fits.py` stays green.

**Acceptance:** the runs above green; `launcher.png` in the guide shows
the bar; the two new pictures listed in `tests/lib/doc-screenshots.txt`.

### 3.4 — `kidux-module-hello` — S — **done 2026-09-25**

The smallest package that exercises every part of the contract, and the
template for the next one (modules.md section 5). It saves nothing of the
child's, so it needs no folder; its window is one more on the bar.

1. **The package**, `packages/kidux-module-hello/`, native format,
   `debhelper-compat 13`, `Rules-Requires-Root: no`, built by
   `ci/build-all.sh` after `kidux-launcher` and checked like every other
   package (packaging.md). `Depends: python3, python3-gi, gir1.2-gtk-4.0,
   gir1.2-rsvg-2.0, python3-kidux (>= 0.1.18), fonts-sil-andika`; the
   description is the sentence an adult reads on the panel's page in step
   3.5, written for them (packaging.md, "Conventions"). It installs:
   - `/usr/share/kidux/modules/hello/module.toml`: `id = "hello"`,
     `version`, `name = "Hello"`, `description = "A first page to read,
     and a button to press."`, `min_age = 4`, `max_age = 8`,
     `launch = { exec = "/usr/libexec/kidux-module-hello" }`,
     `i18n_domain = "kidux-module-hello"`, `memory_max = "1G"`; and
     `icon.svg` beside it, drawn like the avatars (branding/README.md), a
     waving hand on the module's own colour, no text in it.
   - `/usr/libexec/kidux-module-hello`, GTK 4 in Python: one window,
     in the child's language, showing the page
     `/usr/share/kidux/modules/hello/content/<lang>/hello.md` as text (the
     Markdown read as plain paragraphs, the heading in the title size of
     greeter.md section 8), the mascot beside it drawn as the launcher
     draws it (`kidux.paths.MASCOT`, librsvg), and one button, *Done*,
     which closes the window; Escape does the same. The language is
     `LANG`'s, through `kidux.i18n.translations`-style lookup of
     `content/<lang>/`, falling back to `en` when there is no directory for
     it. `GSETTINGS_BACKEND=memory` arrives from the session. It writes
     `$XDG_DATA_HOME/opened`, a line with the date (`date -I` style, from
     `datetime`), so that there is one file a test can look for.
   - `content/<lang>/hello.md`, installed to `/usr/share/kidux/modules/
     hello/content/<lang>/`: `en/hello.md`, the source, one heading and
     three short paragraphs for a child who is starting to read; `es/
     hello.md`, its translation, with the `source_sha256` front matter
     `tests/project/content.py` checks. The content lives in the package
     because `dpkg-source` packs only the package's directory; modules.md
     section 3 changes in this step to say so: `packages/kidux-module-
     <id>/content/<lang>/`, and `tests/project/content.py` walks every
     `packages/kidux-module-*/content` as one module directory each (the
     script already takes a module directory as its unit; `tests/lib/
     project.sh` passes them).
   - `po/kidux-module-hello.pot` and `po/es.po` for the domain
     `kidux-module-hello`, holding `name`, `description` and every string
     the program shows (*Done*, the window title); compiled by the package
     into `/usr/share/locale/es/LC_MESSAGES/kidux-module-hello.mo`.
     `ci/i18n-extract.sh` learns a second kind of catalogue: every
     `packages/kidux-module-*/po/` is its own domain, extracted from that
     package alone, and `tests/project/i18n.sh` checks each as it checks
     `kidux`'s (template matches the source, `es` complete, `es` compiles).
2. **modules.md section 5** says how to copy the package into a new module,
   file by file: what to rename (the id, in the manifest, the paths, the
   domain, the unit), what to replace (the icon, the content, the program),
   what to leave.

**Tests.** Unit, in the package: the manifest reads through
`kidux.modules.read` and has the fields above; the catalogue is complete.
Project: `content.py` and `i18n.sh` cover the package. Acceptance
(`10-module-hello.sh`, before `09-no-key-no-archive.sh` is renamed to `11-`
— it stays last): `apt-get install kidux-module-hello` from the archive;
`kidux-as modules marta` lists `hello off`; the manifest, the icon, the
program and both content directories exist; `apt-get purge` leaves nothing
under `/usr/share/kidux/modules/hello` and nothing of the domain under
`/usr/share/locale`. Session (`17-module-hello.py`, the purge test renamed
`18-purge.py`): with the package installed from the archive over SSH
(`apt-get install`, not a copy: the acceptance of the package is that
`apt` puts it where the launcher looks), switched on for Leo with
`kidux-as`, Leo opens it by keyboard as the canary is opened; the window
is in Spanish (picture `module-hello`); `$XDG_DATA_HOME/opened` exists
under `~leo/.local/share/kidux/hello/`; *Done* by keyboard (Enter, the
button has the focus) closes it and the launcher is back; the package is
purged at the end and the tile is gone. The user guide's section 9 gets
its first paragraph, in both languages, with that picture; the README's
*Learning modules* section waits for GCompris.

### 3.5 — Installing and removing from the panel — M — **done 2026-09-25**

The security of this step is that an adult's click never runs anything but
`apt` on a package whose name the daemon made from an id it validated, and
never while a child's session could be running what apt replaces.

1. **The daemon.**
   - `Modules1.Available() → aa{sv}`: every `kidux-module-*` package the
     archive offers, as `{id, name, description, installed, version}`,
     from the lists apt already has and no network: `apt-cache search
     --names-only '^kidux-module-'` gives `<package> - <short
     description>` per line, and `dpkg-query -W -f '${Package} ${Version}
     ${db:Status-Status}\n' 'kidux-module-*'` which are installed. `id`
     is the package name after `kidux-module-`, kept only when it matches
     `kidux.modules.ID`; `name` is the manifest's `name_in` the machine's
     language when the package is installed, else the `<Name>` of the
     short description (item 3), else the id with its first letter
     capitalised; `description` is the rest of the short description;
     `installed` and `version` from dpkg. Gate: the `screens` class, no token to look.
     The lists are as fresh as the last `System1.CheckUpdates`, which the
     panel's page runs on demand (item 2); a machine whose sources have no
     Kidux archive answers an empty list, and the panel says so. The
     parsing is a pure function of the two outputs, `kiduxd/catalogue.py`,
     tested against saved samples.
   - `Modules1.Install(token, id)` and `Modules1.Remove(token, id)`: the
     token first; then the id must match `kidux.modules.ID` or it is
     `InvalidArgument` — never a package name from the caller; the daemon
     makes `kidux-module-<id>` itself. `SessionActive` while any child
     session of class `user` exists, locked or not (the same check as
     `ApplyUpdates`: dpkg never replaces what a session may be running,
     and under sway a module's windows live as long as the session);
     `Busy` while a job runs. Then the job runner of daemon.md section 13:
     `Updates.start` takes a package for the new kinds, and the transient
     unit runs `/usr/libexec/kidux-update install kidux-module-<id>` or
     `remove kidux-module-<id>` (`Machine.start_update(kind, package)`;
     `kiduxd/updates.py`'s `JOBS` gains `install: installing` and `remove:
     removing`, the verdict lines `done:installed` and `done:removed`, and
     the status `package`).
   - `kidux-update install <package>` and `remove <package>`: the name
     must match `^kidux-module-[a-z][a-z0-9-]{0,31}$` or the verdict is
     `failed:not a module`, checked again in the script because it runs
     as root. `install` is `dpkg --configure -a`, `apt-get update`, then
     `apt-get install -y --no-install-recommends <package>`, with the
     lock timeout, the status descriptor and the configuration-file
     options `apply` uses; `remove` is `apt-get purge -y <package>`. A
     purge leaves nothing of the module's own files on the system; what
     the module depended on (GCompris itself, say) stays installed, since
     `autoremove` cannot be held to one package's dependencies and could
     take something an administrator wanted, and the children's own files
     under their homes stay theirs. The verdict is `done:installed`,
     `done:removed` or `failed:<apt's last E: line>`.
   - The job's progress and end go on the signals and `UpdateState` an
     update has: `UpdateProgress(fraction, package)` while it runs, then
     `UpdateFinished(outcome, detail)` with outcome `installed`, `removed`
     or `failed`, and `UpdateState`'s `job` is `installing` or `removing`
     with the package in `package`. When it ends, `ModulesChanged("")`,
     for every launcher and panel, and the audit line `module installed`
     or `module removed` with `module` and `outcome`; the daemon's
     `resume` after a restart of its own reports a module job as it
     reports an update.
   - `kidux-as modules-available`, `install <id>` and `remove <id>` for
     the acceptance tests, modelled on `check-updates` and `apply-updates`:
     they wait for `UpdateFinished` and print its outcome.
2. **The panel.** The *Modules* page (panel.md section 8) becomes two
   parts of one form:
   - **Installed**, the grid of step 3.1 with, at the end of each module's
     row, *Remove*; it asks once, on the page, as removing a child does
     (*Remove <name>? The children's own files stay.* with *Remove* and
     *Cancel*). The tab order of a row is its switches, then *Remove*, so
     the page still opens on the first module's first switch.
   - **Add modules**, under it: one row per module `Available` lists and
     the grid does not, its name, its description and *Install*; *Look
     for modules*, which calls `System1.CheckUpdates` (allowed with
     children signed in) and redraws the list when `UpdatesChecked`
     arrives; with nothing to add, *Every module the archive offers is
     installed.*, and with no archive, *This computer has no source of
     modules.*
   - While a job runs, the page shows the bar and the package as the
     system page does, polling `UpdateState` once a second (`panel.py`
     shares `_update_state` and `poll_updates` with the system page), and
     ends with *Installed.* or *Removed.* or the failure's sentence in the
     notice. With a child signed in, *Install* and *Remove* answer
     *Children are signed in. Modules can be installed and removed once
     they have logged out.* `PANEL_ACTIONS["panel_modules"]` grows
     (`install_module`, `ask_remove_module`, `remove_module`,
     `look_for_modules`, `poll_modules`) and the way-forward test keeps
     passing. The page must still fit 1280x800 with three modules and
     three children: rows stay one line high, and the list scrolls inside
     the page before the page does.
3. **The package descriptions** of every module are what the adult reads
   on that page: the short description is `Kidux learning module: <Name>,
   <what it is, for the adult>` and the panel shows it without the prefix.
   `kidux-module-hello`'s already reads that way; a new module's is
   written for the adult who is deciding whether to add it.

**Tests.** Unit: `catalogue.py` against saved `apt-cache search` and
`dpkg-query` output (a package installed, one not, one whose name is not
a valid id, an empty archive); `Install`/`Remove` refusing a bad id
(`../hello`, `Hello`, `kidux-module-hello`), a missing token, a session
open, a running job, and the exact `start_update` call; `updates.py`
reading the new job kinds and verdicts; `kidux-update`'s name check in
`tests/project/module-jobs.sh` (calls with every kind of bad name against
a status file in a temporary directory); the panel's page and its five
actions against the fake daemon. Acceptance (`10-module-hello.sh`
grows): `kidux-as modules-available` lists `hello` not installed;
`kidux-as install hello` ends `installed` and the manifest exists;
`kidux-as remove hello` ends `removed` and it is gone; `install ../hello`
is `InvalidArgument`; both are refused with `SessionActive` while the
test child's session of `05-time-and-lock.py`'s kind is open. Session
(`17-module-hello.py` grows at the front): with nobody signed in, the
panel's Modules page installs hello by keyboard (pictures
`panel-modules-available`, `panel-modules-installing`, `panel-modules-installed`),
then the rest of the test as it is, and at the end, back on the panel,
*Remove* purges it and the page shows it under *Add modules* again. The
tile's disappearance while Leo is signed in stays as it is. The user
guide's section 8 says how modules are added and removed, in both
languages, with `panel-modules-available.png`.

**Acceptance:** the runs above green; `tests/lib/doc-screenshots.txt`
lists the new picture.

### 3.6 — `kidux-module-gcompris` — S — **done 2026-09-25**

The first real module, with no content of its own. What is known about
GCompris 25.0 in trixie: `gcompris-qt` is a Qt 6 program, installed as
`/usr/games/gcompris-qt`, and does not depend on `qt6-wayland`, which is
the Qt platform plugin a Wayland session needs (there is no XWayland in a
child's session, so without it GCompris cannot open a window);
`gcompris-qt-data` (79 MB) holds the activities but not the voices or the
word images, which GCompris downloads itself, into its data directory,
when the machine has a connection and its automatic downloads are on; and
the first time it starts it asks two questions in writing, a welcome and
whether to download, which a child who cannot read cannot answer.

1. **The package**, `packages/kidux-module-gcompris/`, copied from hello as
   modules.md section 5 says, with no `content/`: `Depends: gcompris-qt,
   gcompris-qt-data, qt6-wayland`, `memory_max = "3G"`, `min_age = 2`,
   `max_age = 10`, `launch = { exec = "/usr/libexec/kidux-module-gcompris"
   }`, `name = "GCompris"`,
   `description = "Over a hundred activities: reading, counting, colours,
   the keyboard and the mouse."`, translated in `po/es.po`; `icon.svg`
   drawn in the avatars' style, blocks with a letter and a number on the
   module's own colour, since the tile is Kidux's and not GCompris's logo.
   Its short description, for the panel: *Kidux learning module:
   GCompris, over a hundred activities for ages two to ten*.
2. **How it runs.** GCompris takes its language from the locale, which the
   session sets from the child's; its configuration goes under the
   module's `XDG_CONFIG_HOME` and what it downloads under its
   `XDG_DATA_HOME`, so removing the module removes them and nothing else;
   it asks for the whole screen and the launcher gives it the screen minus
   the bar (D43). `/usr/libexec/kidux-module-gcompris`, a short shell
   program, starts it: before the first start of each child it writes
   GCompris's configuration with the welcome seen, automatic downloads
   on and the version last run set to the installed one, so that GCompris
   opens on its menu and fetches the voices for the child's language by
   itself with a connection; a configuration already there is never
   touched. Then it `exec`s `/usr/games/gcompris-qt`. Checked on the test
   machine: GCompris draws under sway with the machine's software
   rendering, comes up in Spanish for Leo, and is a client of the
   PipeWire in his session.
3. **The user guide's section 9** gets GCompris, in both languages, as the
   manual of the finished thing: what it is, that the voices arrive on
   their own with a connection, and the picture. The README's *Learning
   modules* section, in both languages, says GCompris is the first and
   shows the picture.

**Tests.** Acceptance (`10-module-hello.sh` gains a second half, or
`11-module-gcompris.sh` with the key test renamed `12-`): installs from
the archive with `qt6-wayland` among what it brings, the manifest is
listed, purge leaves nothing under `/usr/share/kidux/modules/gcompris`.
Session (`18-module-gcompris.py`, the purge test renamed `19-`): installed
with apt over SSH and switched on for Leo; Leo opens it by keyboard; its
window is on a workspace of its own and not fullscreen (picture
`module-gcompris`, the one the guide and the README show); the process's
environment carries Leo's language and the module's three directories;
PipeWire shows a client of GCompris's (`pw-cli list-objects Client` as
Leo, run with a timeout); it opens on its menu, which the picture waits
for, with its first questions answered; the lock and continuing bring the
same process back; the lock screen's *Log out* ends it; purged at the
end. The module's unit tests run the starter program with `true` in
place of GCompris.

### 3.7 — `kidux-webapps` — M — **done 2026-09-25**

Infrastructure for the modules of phase 4 (Scratch, MakeCode, the micro:bit
Python Editor), and the second reference module that proves it. It is
here because the framework is not complete without it.

1. **`packages/kidux-webapps/`.**
   - `kidux-webapps.service`, a system unit with `DynamicUser=yes`,
     `ProtectSystem=strict`, `ProtectHome=yes`, `PrivateNetwork=no`, no
     capabilities, running `/usr/libexec/kidux-webapps`, a Python 3 static
     server of our own on `http.server` (threaded): it binds
     `127.0.0.1:8123` only, serves files under `/usr/share/kidux/webapps/`
     and nothing else — every path is resolved and must stay under that
     directory, `..` and symlinks out of it are `403`, a directory serves
     its `index.html` or `404`, there are no listings — with the content
     type from the extension and `Cache-Control: no-store`. Unit tests
     against a temporary tree: the good path, `/`, `/../etc/passwd`, an
     encoded `..`, a symlink out, a missing file.
   - The Chromium policy, `/etc/chromium/policies/managed/kidux.json`:
     `URLBlocklist ["*"]`, `URLAllowlist ["127.0.0.1:8123"]`,
     `BrowserSignin 0`, `SyncDisabled true`, `ExtensionInstallBlocklist
     ["*"]`, `DeveloperToolsAvailability 2`, `IncognitoModeAvailability 1`,
     `PasswordManagerEnabled false`, `DownloadRestrictions 3`,
     `DefaultBrowserSettingEnabled false`, `MetricsReportingEnabled
     false`, `BackgroundModeEnabled false`, `PromptForDownloadLocation
     false`, `HomepageLocation "http://127.0.0.1:8123/"`,
     `AllowFileSelectionDialogs false` (a file dialog is a way into the
     child's files), `PrintingEnabled false`, `DefaultSearchProviderEnabled
     false`, and, since trying it showed them, `TranslateEnabled false`,
     `BrowserGuestModeEnabled false`, `BrowserAddPersonEnabled false`. A web
     application is a closed door by this policy (D36): a link to
     anywhere else is blocked by Chromium itself, whatever the machine's
     connection.
   - `/usr/libexec/kidux-webapp <id>`, which the launcher runs for
     `launch = { webapp = "<id>" }` (`launch.command` gains the branch and
     its test; the argv is the scope of D32 around `kidux-webapp <id>`):
     Chromium 153 as `chromium --ozone-platform=wayland --no-first-run
     --no-default-browser-check --disable-session-crashed-bubble
     --password-store=basic --user-data-dir=$XDG_CONFIG_HOME/chromium
     --lang=<the language of LANG> --app=http://127.0.0.1:8123/<id>/?lang=<the
     language>`: an application window, with no tabs and no address bar,
     one window above Kidux's bar (D44). Not `--kiosk`, tried first, which
     hides Chromium's bars only while its window is fullscreen, which the
     launcher never allows (D43). The id is checked against
     `kidux.modules.ID` before it goes anywhere near a URL. `Depends:
     chromium, python3, python3-kidux`; Chromium is 300 MB, which the guide
     says. Chromium moves its browser process into a systemd scope of its
     own when it starts, so the launcher knows its window by its children,
     which stay in the module's scope (launcher.md section 5, D44).
2. **`kidux-module-hello-web`**, `packages/kidux-module-hello-web/`: the
   manifest with `launch = { webapp = "hello-web" }`, `memory_max = "3G"`
   (Chromium's), `Depends: kidux-webapps`; one page under
   `webapp/index.html`, installed to `/usr/share/kidux/webapps/hello-web/`,
   that shows the same three paragraphs as hello in the language the
   query string names, English when it names none, from
   `content/<lang>/hello.md` embedded into the page at build time by a
   short script in `debian/rules` (so `tests/project/content.py` checks the
   translation as it checks hello's), its words through its own catalogue
   (`webapp/page.py`, which `ci/i18n-extract.sh` reads); a link on it to
   `https://www.debian.org/`, which the policy blocks, and whose place
   Chromium fills with its own "blocked" page, named after the address;
   and a *Done* button that calls `window.close()`, and has the focus
   whenever the page is shown. Chromium refuses `window.close()` to a
   window with more than one page in its history, so after a link out and
   back, the bar's *Home* is what leaves it. Its icon, a globe drawn in
   the avatars' style.
3. **Documents.** modules.md section 1 says what a web-application module
   is now that one exists; section 5 says what hello-web is the template
   for; architecture.md section 6 already describes the shape. The user
   guide's section 9 gets hello-web in one paragraph, both languages.

**Tests.** Unit: the server, the argv of `kidux-webapp` for a good and a
bad id, `launch.command` for a webapp. Acceptance (`12-webapps.sh`, the
key test renamed `13-`): `kidux-webapps` and `kidux-module-hello-web`
install from the archive; `curl` to `/hello-web/` answers `200`, to `/`,
`/../`, `/hello-web/../../etc/passwd` and `/nothing/` `403` or `404`; the
policy file is root's; nothing listens on any address but `127.0.0.1`
(`ss -ltn`). Session (`19-module-hello-web.py`, the purge test renamed
`20-`): the tile for Leo, Chromium showing the page in Spanish on its own
workspace (picture `module-hello-web`), its title the page's heading,
its command line an application window with the module's own profile;
lock and continue, *Done* by keyboard closes it; opened again with Enter,
the link is blocked (the window's title is the address, not the site's)
and back is the page; log out ends it; purged at the end. Chromium under
software rendering is slow to start: the waits are a minute and a half.

### 3.8 — The children start — S

The owner's step, at the MacBook: what no test machine can try, before
the children do. Step 9.11 first (rollout.md), if it has not happened.
Then, in order, and each answered in the owner's notes:

1. From the panel, *Look for modules*, then *Install* on GCompris and on
   hello-web: the page while the job runs, and its notice at the end.
   Switch each on for each child; *Remove* asks first. The Modules page
   fits and reads well on the Retina panel at scale 2. The modules on
   offer are described in English until they are installed: whether that
   is acceptable for now is the first open question below.
2. As a child: the tile, GCompris on its own workspace above the bar, its
   first sound, its voices arriving in Spanish once an activity asks for
   them; the bar's buttons under the trackpad and a mouse; ⌘ pressed alone
   goes home; Alt+Tab goes round; the lock over GCompris and continuing;
   the first key after continuing reaches GCompris; time running out
   over GCompris, and the lock screen's *Unlock to save work*.
3. Hello, opened and closed with the trackpad only, as the youngest child
   would.
4. Hello-web: the page in Spanish in Chromium's window, above the bar,
   *Done* closing it; opened again, the link to the internet, Chromium's
   own "blocked" page in its place, back; and then *Done*, which does
   nothing, and the bar's *Home*, which leaves the window open on its
   workspace. Then every way out of the window a keyboard offers, one
   after another, each noted with what it opened: Ctrl+N, Ctrl+T,
   Ctrl+Shift+N, Ctrl+O, Ctrl+S, Ctrl+P, Ctrl+U, Ctrl+H, Ctrl+J, Ctrl+F,
   F1, F11, F12, Ctrl+Shift+I, Alt+F4, Alt+Home, a right click, and a
   long press on the link. Whatever opens must stay on the module's
   workspace, show nothing but Chromium's own pages, and close with
   Ctrl+W; anything else is a bug.
5. GCompris on the GPU: smooth, and the fan quiet. Its own downloads
   (voices, words, background music, which the module's starter turns on)
   arriving on the family's connection, and their size.
6. Two modules open at once, the bar between them, and the files a child
   saves in one showing in the other.

What the children then do with it, and what the owner sees them try, is
the input to phase 4. From here on every phase is dogfooded at home.

Steps 3.5, 3.6 and 3.7 are built and reviewed, and step 3.8 has
happened: what it found is steps 3.9 to 3.15, built unattended in that
order, each with its battery green and its own commit, then reviewed;
step 3.16 is the owner's second hand test, and phase 4 starts after it.

### 3.9 — Close from the bar — M — **done 2026-09-26**

D45. The launcher's bar has *Close* for the module on screen (a cross and
the word; a screen reader hears *Close <name>*), and Alt+F4 does the same
by keyboard: `sway.conf` binds it to `nop kidux-close`, which runs nothing
of sway's, and the launcher hears the binding on sway's IPC. Every module
is closed the same way.

1. **Asked first.** Close sends each of the module's windows sway's
   `kill`, the `xdg_toplevel` close request a window manager's close
   button sends: a program with nothing to save goes at once; one with
   unsaved work asks its own question, as it would anywhere. Chromium
   closes its application window this way whatever its history.
2. **Forced as the emergency.** A module still open ten seconds later
   (`CLOSE_SECONDS`) is overdue, and the bar asks, on that module's screen,
   *<name> has not closed. It may have something to save.*, with *Cancel*,
   which leaves it and forgets the request, and *Close it anyway*, which
   stops its scope (`launch.stop`). While it asks, the question takes the
   place of the time, the warning and *Close*, so that *Lock* still fits
   on a 1280-pixel screen. Close pressed again while the bar asks is
   *Close it anyway*; before the wait is over, it asks the module again.
   Nothing is forced without that question. The policy is `desk.py`'s,
   with no GTK in it.
3. **Documents.** launcher.md section 5 (the bar, the desk's closing) and
   section 7, session.md sections 3, 6 and 8, the user guide's section on
   the child's screen, both languages, with the question's picture.

**Tests.** Unit (`test_desk.py`, `test_launch.py`): every window of the
module on screen asked and no other's, nothing on home, a module that goes
when asked never asked about, one still open after the wait asked about
and not ended, *Cancel* keeping it, *Close it anyway* and a second Close
while asked ending its scope, a second Close before the wait asking again,
the question gone when the module closes after all, and the scope stopped
with `systemctl --user stop`. Session: in `16-module-open.py`, Alt+F4
closes the canary, which goes when asked; the robin, whose window now
refuses a close request as a program with unsaved work would, is asked
about on the bar ten seconds later (picture `launcher-close-question`),
and Alt+F4 again ends it; in `19-module-hello-web.py`, after the link,
when *Done* can no longer close Chromium, Alt+F4 does. *Cancel* and *Close
it anyway* are the pointer's, which the session tests, driven by keyboard,
do not press; the unit tests hold them to the same policy.

### 3.10 — Modules in every language before they are installed — S — **done 2026-09-26**

D47. Each module's `debian/control` carries, in its binary paragraph,
`XB-Kidux-Name-<lang>` and `XB-Kidux-Description-<lang>` for English and
each language it has a catalogue for: the manifest's `name` and
`description` and their translations. `tests/project/module-fields.py`
fails when they differ, so they cannot drift, and `--update` writes them.
`kiduxd/catalogue.py` reads the archive's records with `apt-cache search
--names-only --full '^kidux-module-'`, one call as before, and gives each
module not installed its name and description in the machine's language,
then English, then its short description; `Modules1.Available()` carries
them and the panel shows them. hello, gcompris and hello-web have the
fields. `kidux-as` prints each offered module's name, and gains
`get-config` and `set-config` for the machine's settings.

**Tests.** Unit: the catalogue with fields in both languages, in one, in
none, an installed module named by its manifest, the machine's language
from its locale. Project: `module-fields.py`. Acceptance
(`10-module-hello.sh`): `kidux-as modules-available` names hello *Hello*
on an English machine and *Hola* on a Spanish one, the machine's language
put back as it was. Session (`17-module-hello.py`): the Modules page, on
the Spanish machine, offers hello as *Hola* (picture
`panel-modules-available`).

### 3.11 — GCompris says it needs the internet — S — **done 2026-09-26**

D48. GCompris's description, in `module.toml` and so in its package's
fields of 3.10, in both languages, ends *It needs the internet at first,
to fetch its voices.*: GCompris downloads its voices, words and music
itself the first times an activity asks for them. The user guide's
section 9 says the same, and that the panel says so before it is
installed. "Always" instead of "at first" if the owner's use at home shows
it downloads on every start (step 3.16).

**Tests.** `tests/project/module-fields.py` keeps the package's fields and
the manifest's words in step, and `tests/project/i18n.sh` the Spanish;
nothing on a machine.

### 3.12 — One scale for every screen, and room on a big one — M — **done 2026-09-26**

D49, D53. What the owner saw on the MacBook — the adult panel far too
small, the child's desktop cramped — was not a screen that ignored the
scale: `cage` 0.2.0 implements `wlr-output-management` as `sway` does, and
the scale reaches both. The MacBook's scale had never been changed from 1,
on a 2880x1800 panel.

1. **Automatic until chosen** (D53). A machine's `display_scale` is 0,
   automatic, until an adult chooses one: `session-inner` sets, on each
   output, the largest quarter at which the output's current mode still
   leaves the mode roomy, 1600x960, never less than 1
   (`kidux.screen.automatic_scale`, and `python3 -m kidux.screen <mode>`
   for the shell; D56), under `cage` and under `sway` alike; 1.75 on the
   MacBook. `session-inner` exports the mode as `KIDUX_SCREEN_MODE`. A scale `wlr-randr` refuses is logged
   with what it said, instead of swallowed. The daemon takes 0 or 1 to 3.
2. **Finer choices.** The System page offers *Automatic (175 %)*, the
   percentage being what automatic comes to on this screen (D56), then
   100, 125, 150, 175, 200, 250 and 300 %.
3. **Room on a big screen.** Every screen still fits 1280x800 whole (D30).
   On a screen with 1600x960 logical pixels or more (`kidux.screen.roomy`)
   the screens keep their size and the room is space, as the owner put it
   (D53); the greeter's and the launcher's windows are marked
   `kidux-roomy`, and the launcher puts eight tiles to a row instead of
   six. Each program logs `screen <width>x<height>` when it starts.
4. **The quick loop's machine** can have a larger screen
   (`KIDUX_VM_SCREEN=1920x1200`), for looking at a roomy screen by hand;
   the battery's is the card's own 1280x800.
5. **Documents.** session.md section 3, greeter.md section 7, panel.md
   (the System page's choices), daemon.md section 15, rollout.md section 4
   (automatic on the MacBook, and a machine's saved 1 staying 1 until
   *Automatic (175 %)* is chosen), the user guide's System page, both
   languages; D53 and D56 in the decision log.

**Tests.** Unit: the automatic scale for 1280x800, 1366x768, 1920x1080,
2560x1600, 2880x1800 and 3840x2160; what is roomy; the scale automatic on
the daemon until set, and 0 accepted. Session (`20-scale.py`, the purge
test renamed `21-`): the scale set to 2 through the daemon, the sign-in
screen under `cage` logs 640x400 and Leo's launcher under `sway` 640x400
(pictures `sign-in-scale-2`, `launcher-scale-2`); 1.25 gives 1024x640; and
automatic, on this 1280x800 machine, 1280x800 again.

### 3.13 — The adult sets the time left — S — **done 2026-09-26**

D50. `Access1.SetTimeLeft(token, username, minutes)` (MANAGE; 0 to
`MAX_MINUTES`; `InvalidArgument` for a child with no limit, for whom it
means nothing) leaves exactly `minutes` for today: `access.set_left`, a
pure function beside `grant`, keeps what was used today as it was and
makes the difference a grant, negative when time is taken away, which in
daily mode goes with the day as every daily grant does; in manual mode it
is the bank. A session that is up is charged first, so the minutes are
what it has from then on, and at zero the timekeeper's next tick, a tenth
of a second later, locks it as when its time runs out by itself. Audited
as `time set`. The panel's page for a child keeps its row on one line at
1280 pixels: *Used today*, *Give more time: 15 30 60*, and *Left today* with
a number from 0, which starts at what the child has left, and *Set*; the
number of the adult's own that gave time is gone, since setting what is
left does the same and more. For a child with no limit the row says *No
time limit*, and *Set* answers *This child has no time limit.* `kidux-as`
gains `set-time-left <child> <minutes>`.

**Tests.** Unit: `set_left` in both modes, zero, above the day's
allowance, what was taken away back the next day, no limit refused, the
range; `SetTimeLeft` on the bus, checked, audited; a session up set to
zero locked at once and what it used unchanged; set to two minutes,
locked two minutes later; the panel's action and its answer for a child
with no limit. Acceptance (`05-time-and-lock.py`): set to 5, `Usage` says
about 300 seconds; set to 0 with the child's session up, the session is
locked at once. Session (`10-time-runs-out.py`): Tim has an hour a day and
his time left is set to none while he is signed in: the time-up lock
screen comes up at once, instead of after a minute of waiting (picture
`time-is-up`); the rest of the test stays. The row itself is in the
picture of the panel's page for a child (`panel-child`).

### 3.14 — Advanced settings: Chromium's flags for this machine — M — **done 2026-09-26**

D51, D52. The settings that depend on the machine's hardware are reached
from the panel's System page, under *Advanced*; Chromium's flags are the
first.

1. **The daemon keeps them.** `chromium_flags` is one of the machine's
   settings (`kiduxd/advanced.py`): at most 20 flags, each `--name` or
   `--name=value`, lower-case name, no spaces or control characters, at
   most 200 characters, blank ones dropped, and none of the flags that
   would take a web module out of Kidux's hold (another page or profile,
   the remote-debugging doors, extensions, the sandbox or the web's rules
   off, a proxy or a resolver of its own); anything else is
   `InvalidArgument` and nothing changes. Saved, they are written to
   `/etc/kidux/chromium-flags` (`paths.CHROMIUM_FLAGS`), root's and 0644,
   one a line, and the file removed when there are none.
2. **The program reads them.** `kidux-webapp` adds the file's lines that
   start with `--` after Kidux's own flags, so that one there wins over
   Kidux's for the same thing, and says what it left out;
   `kidux-webapp --print <id>` prints the command line instead of running
   it. Nothing ships in the file.
3. **The panel.** The System page has no room left at 1280x800 for a
   section, so its last row is *Advanced* with a button, *Chromium's
   options*, to a page of its own, `panel_advanced`, under the same tabs:
   *Only if something does not work on this computer*, the options as
   several lines of text with a sentence on what they are for, and *Save*,
   which says *Saved.* or, when the daemon refuses one, what an option must
   be, keeping what was typed. The words in both languages. `kidux-as
   set-config chromium_flags '<a JSON list>'`.
4. **The trial on the MacBook**, in rollout.md section 5, done in the
   panel, one option at a time: `--disable-gpu-compositing`, then
   `--disable-gpu`, then `--use-gl=angle` with `--use-angle=gl`, then
   `--disable-features=WaylandLinuxDrmSyncobj`; what draws cleanly is what
   the owner reports in 3.16, and the review decides whether it becomes
   Kidux's own default.
5. **Documents.** daemon.md section 15, panel.md, modules.md section 4,
   rollout.md section 5, the user guide's System page, both languages,
   with the page's picture.

**Tests.** Unit: the daemon's checks (good lists, a flag without `--`,
with a space, capitals, two flags on one line, too many, too long, each
refused flag), the file one a line and 0644, none no file, a refused list
changing nothing, the setting needing the adult; `kidux-webapp`'s command
line with the machine's flags after Kidux's, the file read one a line and
a bad line left out and said, no file no flags, `--print`; the panel's
page and its two answers. Acceptance (`12-webapps.sh`): a flag set
through the daemon is in the file, root's and 0644, and at the end of
`kidux-webapp --print hello-web` run as a child; none is no file; `--app`
is refused. Session (`12-updates.py`): a flag set from the command line
before the panel opened, *Chromium's options* on the System page by
keyboard shows it (picture `panel-system-advanced`), and *Save* there keeps
it, audited, in the file.

### 3.15 — Windows — L — **done 2026-09-26**

D46. A child's desktop is either the one it was — every module filling
the room above the bar — or one of windows the child moves, resizes and
puts fullscreen, several open at once. Which, is a setting of the child;
a module may say it needs the second.

1. **The setting.** `windows` in the child's profile, a boolean, off for
   a new child: `Children1.SetProfile` validates it and `Children1.List`
   carries it. The panel's page for a child, and its *Add a child*, have a
   *Windows* switch with what it does on the same row; the wizard does not
   ask. `kidux-as set-profile <child> windows on|off`.
2. **The manifest.** `needs_windows = true` in `module.toml`
   (`kidux.modules.Module.needs_windows`, false for anything else). The
   launcher shows no tile for such a module to a child without windows;
   the panel's Modules page says *Needs windows* after its description,
   and that child's switch for it is off and cannot be switched on.
3. **The session knows.** The sign-in screen adds `KIDUX_WINDOWS=1` to the
   environment of a child with windows, and the launcher reads it; a
   change applies at the next sign-in, which the switch's row says.
4. **The launcher's policy with windows on** (`desk.py`): every module
   still has its own workspace, and the bar, Home, Alt+Tab, Super and
   *Close* work as before. Each window a module opens is floated once, when
   first seen, with a title bar to move it by and edges to resize it by,
   at four fifths of the room above the bar, centred, and each later one of
   the same module 40 pixels further down and right; one opened on another
   workspace goes to its module's first. A window that comes up in
   fullscreen, as GCompris and the canary do, opens as a window: out of
   fullscreen first, placed on the next change `sway` reports (placed at
   once, trying it showed, it went back where it came up); one larger than
   the room, as such a program makes itself on leaving fullscreen, is put
   back at four fifths. Fullscreen asked for afterwards is the child's. A
   dialog `sway` floats itself is left as `sway` put it. The page for a
   child has one row to spare at 1280x800, which *Windows* takes: the
   minutes a day go on the same row as the mode they belong to. The title bars are
   `sway.conf`'s: Andika, ink on cream, cream on ink for the window in use.
   With windows off nothing changes.
5. **Documents.** launcher.md section 5, modules.md section 2, panel.md,
   daemon.md section 6, greeter.md section 5, session.md sections 3 and 4;
   the user guide's page on children, both languages, with a picture.

**Tests.** Unit: the profile's `windows` through the daemon; `needs_windows`
read; the sign-in screen's environment for a child with windows; the
desk with windows on (floated on its workspace, a later window a step on
and placed once, one opened elsewhere moved to its module, one that came up
in fullscreen taken out of it and then placed, one larger than the room
made smaller and one within it left alone, fullscreen asked for afterwards
kept, a floating dialog left) and off (nothing floats); each window's size
and its workspace's room read from sway's tree; the float command;
the panel's switch saved, for an existing and for a new child, and the
Modules page's rows. Session (`21-windows.py`, the purge test renamed
`22-`): Leo with windows on, his page on the panel (picture
`panel-child-windows`); the canary floating with a title bar, at four
fifths of the width, centred, on its workspace (picture
`windows-canary`); the robin floating on the next; a window that asks for
the whole screen keeps it (picture `windows-fullscreen`) and Super still
goes home; Alt+F4 still closes; logging out ends them; with windows off,
the robin's manifest saying `needs_windows`, Leo's tiles are the canary's
alone, which fills the room above the bar as ever.

### 3.16 — The owner tries again — S

The owner's second hand test at the MacBook, after 3.9 to 3.18 are
reviewed: step 3.8's list again, and then *Automatic (175 %)* chosen on
the System page (the MacBook keeps the 1 it was given until then) and
every screen at 1.75, roomy, and 2 and 2.25 tried to see it all larger; a child's time
left set to 1 minute and the time-is-up screen a minute later; Close and
Alt+F4 on every module, and the question ten seconds later on one that
does not go; the trial of 3.14, with the line that draws hello-web
cleanly reported; windows switched on for one child, and that child
moving, resizing and putting fullscreen the modules, and back to the
launcher; today unticked for a child, the day-off screen and an adult's
grant, and ticked again; the ages and *Recommended before:* on the
Modules page; the list of Chromium's options on the Advanced page. What
it finds is fixed before phase 4.

### 3.17 — The days of the week — M — **done 2026-09-27**

D54. A child with a set time each day, or with no limit, has it on the
days an adult ticks; the other days the computer is not theirs, unless an
adult gives time.

1. **The rule** (`kiduxd/access.py`). `Policy` gains `days`: seven
   booleans, Monday first, all true unless set, and all true for a file
   written before there were days; `validate_policy` takes `days` as a
   list of seven booleans and nothing else, and `as_document` writes it to
   `access.toml`. `available(policy, usage, weekday)`,
   `check_access(policy, usage, weekday)` and `set_left(policy, usage,
   weekday, minutes)` take the accounting day's weekday, `weekday_of(usage)`,
   `last_day`'s once the day is rolled (a clock set back keeps the later
   day, as the counters do). On a day not ticked, `daily` and `unlimited`
   have what an adult gave that day, `max(0, granted_seconds −
   seconds_used_today)`, as if the day's allowance were none; so an adult's
   grant, from the panel or the lock or sign-in screen, still works that
   day, and `set_left` sets from none, in unlimited mode too. A grant in
   `unlimited` mode goes with the day, as one in `daily` mode does, since it
   only counts on a day off. `manual` is by grant anyway, and its days are
   not asked. `check_access` on a day not ticked with nothing left answers
   `("day_off", 0)`, a fourth state, so the sign-in screen can say why. At
   the reset hour, a session that runs into a day not ticked has nothing
   left at the next tick, and locks `time_up`. `allowance(policy,
   weekday)` is what the three share: the daily minutes, none on a day
   off, None with no limit. `grant` takes the usage and the weekday too,
   and always gives its minutes: below what was used today, as after the
   allowance was cut or on a day unticked after use, it covers the
   difference first, so that a grant from the sign-in or lock screen on
   such a day lets the child in for its minutes.
2. **The daemon.** `Access1.GetPolicy` carries `days`; `SetPolicy` takes
   it and keeps the days as they were when it is left out; the audit of
   `policy set` names the days as a string of seven digits, `1111100`.
   `CheckAccess` may answer `day_off`. A list of booleans travels as `ab`
   both ways (`bus.to_variant_value`, `client._variants`). daemon.md
   section 7.
3. **The sign-in screen.** `day_off` is the `blocked` screen with a
   notice of its own, *The computer is not for you today. An adult can
   give you time.* (`vocabulary.NOT_TODAY`; the child's picture and name
   are above it, and the other notices speak to the child too), and the
   same *Ask an adult for more time* under it, which leads to the adult's
   grant as it does when the time is spent.
4. **The panel.** Under *How may they use the computer?* a row *Days*
   with seven `Gtk.CheckButton`s, *Mon* to *Sun* (`words.DAYS` and
   `words.WEEKDAYS`, translated: *Lun* … *Dom*), sensitive for the daily and
   unlimited modes, saved with the policy: `fields()["access"]` is
   `"<mode>:<minutes>:<seven digits>"`, which `parse_access` and
   `access_of` read and write (a value without days is every day), and
   `Access1.SetPolicy` gets `days`. The page for a child fits 1280x800
   (`13-every-screen-fits.py`) with the child's form's rows 8 pixels apart
   instead of the other forms' 10; the *Windows* sentence on one line would
   have widened every field of the form. The wizard's first child keeps
   every day: the wizard does not show the row.
5. **The rest.** `kidux-as set-policy <child> <mode> <minutes> [<seven
   digits>]` and `kidux-as check-access <child>`;
   `kidux.client.set_policy` takes `days`; the launcher's time text is
   unchanged (a child signed in is on a ticked day or on a grant).
6. **Documents.** daemon.md section 7 (the policy and the fourth state),
   greeter.md (the sign-in screen's states), panel.md (the row and the
   field's format), the user guide's sections on the sign-in screen, time
   and the panel's child page, both languages, with the picture `day-off`,
   the README's list of modes ("on which days of the week"), and D54 in the
   decision log.

**Tests.** Unit (`test_access.py`): the weekday of the accounting day
across four in the morning; a day not ticked gives nothing in daily and
unlimited modes and `day_off`; a grant that day gives its minutes, is
spent, and goes with the day; a grant after the allowance was cut below
what was used, or on a day unticked after the morning's use, gives its
whole minutes (`test_time_and_lock.py` too, from the lock screen); manual mode ignores days; the roll into a
day not ticked; the time left set on a day off from none; `validate_policy`
with seven booleans and with six, eight, a string, or numbers; a file
without days has every day. `test_time_and_lock.py`: `SetPolicy` with days
round-trips through `GetPolicy`, is audited with the digits, and days left
out are kept; `CheckAccess` says `day_off`; `AuthoriseSession` lets the
child in that day; a session up at the reset hour into a day not ticked is
locked `time_up`. `test_bus.py`: the days over the real bus. The greeter's
flow on `day_off`; the panel's `parse_access` and `access_of` with days and
without, and the days saved with the policy. Acceptance
(`05-time-and-lock.py`): with today unticked `check-access` is `day_off`,
the audit names the days, and a grant lets the child in. Session
(`08-time-spent.py`): Leo's days set from the command line to all but
today and his time left to none, his picture on the sign-in screen gives
the day-off screen (picture `day-off`), *Back*; on the panel his page
shows the boxes (in `panel-child`), today's box ticked by keyboard and
*Save* puts the day back, and he signs in.

### 3.18 — Who a module is for: ages, and what to do first — S — **done 2026-09-27**

D55. The manifest's `min_age` and `max_age` are shown at last, and a
module may name the modules best done before it.

1. **The manifest** (modules.md section 1). `recommended_before`, a list
   of module ids, optional; `kidux.modules.read` keeps the strings that
   match `ID` and drops the rest with a line in the log, and a value that
   is not a list gives none, logged too; `Module.recommended_before` is a
   tuple, empty when absent. hello-web's manifest names hello.
2. **The package's fields** (D47, step 3.10). `XB-Kidux-Ages`, from
   `min_age` and `max_age` as `4-8`, `2-` or `-10`, absent when neither
   is set; `XB-Kidux-Before`, the ids separated by spaces, absent when
   none. `tests/project/module-fields.py` writes and checks them with the
   names; the lintian override already covers `Kidux-*`.
3. **The daemon** (`kiduxd/catalogue.py`). `Modules1.Available()` entries
   gain `min_age` and `max_age` (0 for none) and `before` (a list of
   ids), from the fields for a module not installed (`catalogue.ages` and
   `catalogue.before`, a field that does not read giving none) and from the
   manifest for one installed: the service's `installed_of(id)` gives the
   installed manifest's name, ages and ids. daemon.md section 9.
4. **The panel.** `_about_module` says, smaller, beside the module's
   name: *Ages 4 to 8* (`words.AGES_FROM_TO`, and `AGES_FROM`, `AGES_TO`
   for one bound), and under the name, as small, on a line of its own
   only when the module names any, *Recommended before: Hola*
   (`words.FIRST`), the recommended modules' names in the machine's
   language where they are installed or on offer, their ids otherwise
   (`panel.modules` works them out as `first`). Both in the installed grid
   and in *Add modules*. The ages beside the name, and the description
   wrapping at 56
   characters instead of 40, because the Modules page has to keep fitting
   1280x800: with a module installed, three on offer and *Saved.*
   (`15-modules.py`), with the three on offer and the bar of an install
   (`17-module-hello.py`), and with the three installed (tried on the
   quick loop's machine).
5. **The rest.** `kidux-as modules-available` prints the ages and the
   modules first after the version: `hello available - 4-8 - Hola`.
6. **Documents.** modules.md sections 1, 3 and 5, daemon.md section 9,
   panel.md, the user guide's section on the panel's Modules page, both
   languages, and D55 in the decision log.

**Tests.** Unit: `read` with a good list, ids that are not ones, and a
value that is not a list; the catalogue with ages and before fields and
without, an installed module's from its manifest, and `ages` for each
form and for ones that do not read; the panel's rows and offers with
their ages and their modules first by name. Project: `module-fields.py`.
Acceptance (`10-module-hello.sh`): `kidux-as modules-available` prints
hello's ages, and hello-web with hello first. Session
(`17-module-hello.py`): the Modules page offers hello for ages 4 to 8, and
hello-web after hello (picture `panel-modules-available`), and fits the
screen.

### 3.19 — `labwc` in the kiosk, and XWayland — XL — **done 2026-09-27**

D58, D59. The child's compositor is `labwc`; for the child without windows
nothing changes on screen, and XWayland is on, with an X11 stand-in module
in the tests.

**A. The gate.** Tried on the quick loop's machine before anything of the
launcher was rewritten, each point photographed, and written down in
`docs/dev/labwc-notes.md`: labwc read only from `-C`; no default keys or
mouse bindings without `<default />`; labwc's frame, with iconify,
maximise and close working, on GTK 4, Qt 6 (GCompris), Chromium and an X11
Tk window alike; the window rules and what `type` matches; the bar and its
exclusive zone; the scale by `wlr-randr`, X11 enlarged with the rest;
every request of the foreign-toplevel protocol from `python3-pywayland`,
the launcher's own window included; `ForEach` for home; the lock,
continuing and the first key after it, the idle dimming, and nothing left
after log-out; memory; `swaybg`. What it changed of this plan: Super is
labwc's own `ForEach` on the launcher's window, not a signal; Alt+F4 is
`pkill -USR2 -f "^/usr/bin/python3 /usr/libexec/kidux-launcher"`, since
the launcher runs itself again under `python3` and `-x` does not find it;
Alt+Tab is labwc's `NextWindow`, the window used before, not a round of
the modules in order; Chromium takes no notice of `--class` for its
Wayland `app_id`, which is `chrome-127.0.0.1__<id>_-Default`, so a web
application's is a pattern the manifest reader adds and `kidux-webapp` is
unchanged; GCompris's is `org.kde.gcompris`; an X11 window's frame goes
only with `SetDecorations`; and a window that comes up fullscreen gets a
title bar back when it is taken out of it, which labwc 0.8 does whatever a
rule says, so Kidux's modules do not ask for fullscreen and GCompris
starts with `--window`.

**B. The session** (`kidux-session`). `Depends: labwc (>= 0.8), xwayland,
swaybg, swayidle` in place of `sway`; the same `Conflicts`.
`kidux-session` execs `labwc -C /usr/share/kidux/labwc/kiosk` (or `desk`
with `KIDUX_WINDOWS=1`) `-s "session-inner --keep-running
kidux-launcher"`; each directory has `rc.xml`, an empty `menu.xml` and a
`themerc-override` with Kidux's colours, root's, where no theme of the
child's reaches. The kiosk: four keys (Super home by `ForEach`, Alt+Tab and
Alt+Shift+Tab `NextWindow` and `PreviousWindow` with the switcher hidden,
Alt+F4 the signal), a press focusing and raising a window and the close
button of a title bar as its mouse bindings, every `normal` window
maximised by a rule, and a second rule, `serverDecoration="no"` with
`SetDecorations` `none`, so that no window has a frame, an X11 one
included. The desk (for step 3.15's windows until 3.20): the same
keys, labwc's frame with iconify, maximise and close and its mouse
bindings, cascade, and the launcher's window maximised without a frame.
XWayland on, `<xwaylandPersistence>no`. `session-inner` starts `swaybg -c
'#fff6e9'` and ends the session with `labwc --exit`.

**C. The launcher.** `sway.py` is gone; `compositor.py` speaks
`wlr-foreign-toplevel-management-unstable-v1` through `python3-pywayland`
(and `python3-cffi-backend`, which pywayland needs and does not declare),
its Python made from the XML at build (`protocol/generate.py`, the
scanner called directly with an import map), read in GLib's main loop on
the compositor's socket, with no thread: `Toplevels`, pure, builds the
list from the events; `Labwc` feeds it and sends `activate`, `close`,
`set_minimized`, `set_maximized` and `unset_fullscreen`; Alt+F4's signal
through `GLib.unix_signal_add`. The manifest gains `app_ids`, globs, a
web application's added by the reader (`kidux.modules.claims`); hello's is
`org.kidux.modules.Hello`, GCompris's `org.kde.gcompris`. `desk.py` works
on windows instead of workspaces: whose each is (manifest, parent, the
module waiting for its first window, or a stranger), the module on screen
from the active window, home the launcher's; in the kiosk fullscreen taken
back and a main window maximised again; with windows, fullscreen taken
back once. The launcher logs `toplevels:` and `on screen:` on every
change. A launcher started again after a crash shows home, since labwc
brings every new window forward, with the open modules in its bar in the
order labwc lists them.

**D. The X11 stand-in module** (`tests/lib/seed/modules/x11-canary/`), a
Tk window with `WM_CLASS` `x11-canary`, and `python3-tk` installed for it
by its test.

**E. The System page** (D59): the sizes that are not whole marked
`125 %*` (`panel.size_label`, `words.NOT_PREFERRED_MARK`), automatic too
(`words.AUTOMATIC` is `Automatic ({size})`), and `words.SCALE_NOTE` under
the list; the form's rows 8 pixels apart so that the page fits 1280x800.

**F. Documents.** session.md sections 1, 3, 5, 8 and the test list,
launcher.md sections 1, 2, 4, 5 and 7, modules.md sections 1 and 2
(`app_ids`; X11 programs allowed, soft at a marked size), panel.md, layout.md,
daemon.md, rollout.md, test-battery-plan.md, architecture.md sections 1, 3,
5 and 6, the user guide's child's screen (Alt+Tab), *Windows* and System
page, both languages, `labwc-notes.md`, and D58 and D59 in the log.

**Tests.** Unit: `compositor.py`'s `Toplevels` from scripted events;
`desk.py` against a compositor that only remembers (whose each window is,
home, tiles, closing, the kiosk and windows); `kidux.modules` with
`app_ids`; the panel's `size_label`. Session, through the `kidux-toplevels`
tool (installed like `kidux-as` by `01-install.py`), which lists windows
as the launcher sees them and can ask for fullscreen, minimise or
activate: `09-child-session.py` checks the kiosk configuration;
`16-module-open.py` the room above the bar by colour, a click reaching the
module, Alt+Tab back and forth, the lock, the launcher's crash coming back home, a module's tile
bringing it forward, and Alt+F4; `17` to `19` their modules by module and
maximised; `21-windows.py` the desk configuration, the canary in labwc's
frame (ink along its title), fullscreen asked for afterwards kept, Super
and Alt+F4; `22-x11.py` (new) the X11 canary through XWayland, as Leo,
filling the room, a click reaching it, back after the lock, closed by Alt+F4, XWayland ending by
itself, nothing left after log-out; the purge is `23-purge.py`.

### 3.20 — The desk: every window at once — M — **done 2026-09-27**

D57. For a child with windows, on `labwc` (3.19): the modules' windows
all on one desk, each in `labwc`'s frame with its buttons, and the bar
listing them.

1. **The desk configuration** (`/usr/share/kidux/labwc/desk/rc.xml`,
   from 3.19): labwc's frame with iconify, maximise and close and its
   mouse bindings, cascade; the launcher's window maximised, without a
   frame and `ToggleAlwaysOnBottom`, the desk's floor under every window.
2. **Home on the desk.** Brought forward over the windows, the launcher's
   window would cover them all (3.19's test saw the robin opened from home
   over it and the canary under it): so it stays under them, and home
   shows the desk instead, every module's main window minimised and the
   launcher's in use. Super on the desk is a signal to the launcher,
   `pkill -USR1` found as for Alt+F4, and both it and the bar's Home are
   `desk.home`, which minimises them through the protocol and remembers
   them. Leaving home by a tile or a window's button on the bar brings
   them back, the one asked for in front: labwc places a new window as if
   the minimised ones were not there, so a module opened from home would
   come up exactly over the one before. A window the child minimised
   stays so.
3. **The bar as the taskbar** (`bar.py`, `desk.py`, `view.py`). With
   windows on, one button per main window instead of one per module: the
   module's icon and the window's title (`desk.title_of`: the module's name
   when it has none, cut to 24 characters), the window in use marked, a
   minimised one faded (`kidux-minimised`); a button activates its window,
   back from minimised (`desk.raise_window`); the buttons scroll past 560
   pixels. The desk tells the bar of every change of a window's title or
   state, not only of the modules open. *Close* as ever, on the module of
   the window in use. Minimise and maximise are the frame's.
4. **Fullscreen** asked for by a program is the child's, the bar under it;
   Super shows the desk.
5. **Copy and paste** between windows is Wayland's own, and XWayland's
   between an X11 program and the others; the guide says so, and the
   owner tries it in 3.21. No session test: nothing in the test machine
   can type into two programs and read a third's clipboard reliably
   enough to be worth it.
6. **`needs_windows`** unchanged (D46).
7. **Documents.** launcher.md sections 5 and 7, session.md section 3,
   the user guide's paragraph on *Windows*, both languages, with the
   picture `windows-desk`, the README's line on windows, D57 in the log as
   it stands.

**Tests.** Unit (`test_desk.py`): home on the desk minimising every main
window and no dialog, and in the kiosk nothing; leaving home by a tile
or the bar bringing back what home put away, and not what the child
minimised; the bar's windows, a
button bringing one back, the launcher's own window not raised that way;
the bar hearing of a window minimised; `title_of`. Session
(`21-windows.py`): Leo with windows opens the robin, which asks for the
whole screen and opens as a window; Super shows the desk, the robin
minimised and on the bar (picture `windows-home`); the canary opens from
its tile in labwc's frame, placed further down and right, the robin back
as home is left, both in view at once (picture `windows-desk`); the robin
minimised leaves the screen and stays on the bar (picture
`windows-minimised`), and its tile brings it back; maximised, it fills the
room above the bar (picture `windows-maximised`) and a click reaches it;
fullscreen asked for
afterwards kept, Super, Alt+F4; without windows, a module that needs them
has no tile and the canary fills the room. The `kidux-toplevels` tool
gains `maximize`.

### 3.21 — The owner tries labwc — S

The owner's third hand test at the MacBook, after 3.19 and 3.20 are
reviewed, with 3.16's list first if it has not been done: the kiosk
exactly as before for a child without windows (GCompris, hello, hello-web,
Close, Alt+F4, the lock); the desk for a child with windows: frames with
their buttons on GCompris, hello-web and the canary, minimise from the
frame and back from the bar, maximise, two windows side by side, copy
from one and paste into another; the X11 canary at *Automatic (175 %\*)*,
at 200 % and at 100 %, and whether the softness at 175 % is tolerable for
an occasional X11 module or the marked sizes should be avoided on this
machine; the System page's marks and note. What it finds is fixed
before phase 4, and the choice of Thonny or a Wayland editor for phase 6
takes the X11 result into account.

### 3.22 — A laptop's keys and its corner — M — **done 2026-09-28**

D61. What the first hand test of labwc on the MacBook asked for and is
built here: the machine's own keys for the screen, the keyboard's light
and the sound; a corner of the child's screen that shows them, and the
battery; the lid powering the panel off; the keys written where the child
sees them; and an X11 stand-in that shows blur.

**A. What the machine has** (`kidux.hardware`, kidux-common): a battery
(`/sys/class/power_supply`, the machine's own, not a peripheral's), the
screen's backlight (`/sys/class/backlight`, the panel's own before the
firmware's), the keyboard's light (`/sys/class/leds/*kbd_backlight*`), the
lid (input devices whose `capabilities/sw` has bit 0), whether the machine
is a Mac (DMI) and whether its function keys want fn (`hid_apple`'s
`fnmode`), and the sound through `wpctl` (`get-volume`, `set-volume`,
`set-mute` on the default sink). Levels are set through `brightnessctl`,
which asks logind. Every reading takes the root it reads under, so the
tests are directories of files: the MacBook's and a desktop's.

**B. The corner** (`status.py`, kidux-launcher): top right of the child's
screen, after the time left: the sound, the keyboard's light and the
screen's brightness as buttons with an icon and a percentage that open a
vertical slider, the sound's with a *Mute* toggle; the battery as an icon
and a percentage. Each only when the machine has it; read again every
five seconds and after the child moves a slider. The launcher logs
`hardware: battery=… backlight=… keyboard=… lid=… mac=… fn=… audio=…`
once, which the session tests read.

**C. The keys** (`kidux-keys`, kidux-launcher; both `rc.xml`,
kidux-session): `XF86MonBrightnessUp/Down`, `XF86KbdBrightnessUp/Down`,
`XF86AudioRaiseVolume/LowerVolume/Mute` run `kidux-keys brightness|
keyboard|volume up|down|mute` as the child: a step of ten, the screen
never under five per cent, a step while muted unmuting first, nothing on
a machine without the thing. keys.md says why one binding serves a Mac
and a PC, and how a keyboard that sends something else is added.

**D. The lid** (`lid.py`, kidux-launcher; `70-kidux-switches.rules`,
kidux-session): a udev rule makes every input switch readable; the
launcher reads the lid switch in GLib's loop (`EVIOCGSW` for the state at
start, the events after) and powers the machine's own panel (`eDP-*`,
`LVDS-*`, `DSI-*`, or the only output) off and on through `wlopm`.
Brightness is untouched, so `swayidle`'s dimming and the lid never fight;
logind keeps ignoring the lid.

**E. The keys written** (`bar.py`, `desk.py`): Home says `⌘` or `Win`,
Close `Alt+(fn)F4` or `Alt+F4`, and the module or window Alt+Tab would go
to, the one in use before the one in use now, which the desk tracks from
the activations it sees, says `Alt+Tab`; small beside the name, and as
the tooltip. The launcher logs `keys: home=… close=… next=…` once.

**F. The X11 stand-in** (`tests/lib/seed/modules/x11-canary/run`): under
its name, text in DejaVu Sans, Serif and Mono at 9 to 18 points and a
drawing of one-pixel lines and a checkerboard, to judge the blur by.

**G. Documents.** launcher.md sections 2, 5 and 7; session.md sections
3, 5, 6 and 8; keys.md (new); labwc-notes.md; rollout.md's lid row; the
user guide's child-session section, both languages; D61.

**Tests.** Unit: `kidux.hardware` on the two directories (battery, a
mouse's battery ignored, backlight preference, keyboard light, lid,
steps, `wpctl`'s answer, lid events from bytes, fn and the key names);
`desk.previous` and the bar hearing when Alt+Tab's target changes.
Acceptance (`02-install.sh`): both configurations bind the seven keysyms
to `kidux-keys`, `kidux-keys` runs and does nothing on the test machine,
the udev rule is in place. Session: `09-child-session.py` reads the
launcher's `hardware:` line (nothing of a laptop's, no Mac) and its
`keys:` line (`Win`, `Alt+F4`, `Alt+Tab`). What no machine of the tests
can try, a real key, a slider on a real backlight, the lid, is step
3.21's on the MacBook.

### 3.23 — What the hand test asked for: the network, the versions, Chromium's language, the trusted screens' keys — L — **done 2026-09-28**

D61 for the trusted screens; the rest is the owner's list of 2026-09-28.
Built by Opus 5.5, each part with its battery green and its own commit,
reviewed afterwards. Every part has the same shape: the daemon or the
program, its unit tests, the panel or screen with its words in both
languages (`ci/i18n-extract.sh`, no fuzzy entry left), the session or
acceptance test with its picture where a screen changes, the developer
document that describes the piece, the user guide in both languages, and
the version bumps of every package touched, dated with `date -R`.

**1. The network page** (kidux-daemon, kidux-greeter, kidux-common,
kidux-base). D62. The adult panel gets a fourth page, *Network*, after
*System*, for the adult who wants to see and fix the connection; the daemon
an interface, `Network1` (`kiduxd/network.py`, daemon.md section 16), every
method adults only, with the panel's token. `GetNetwork` answers a
summary, the interfaces and the Wi-Fi networks: the interfaces from `ip -j
addr` (every one but the loopback with a device or an IPv4 address), the
gateway from `ip -j route`, and, when NetworkManager runs, which it manages
(`nmcli -t device status`) and the networks in reach (`nmcli -t device wifi
list --rescan no`); a Wi-Fi it does not manage, `ifupdown`'s, is named by
`wpa_cli status` and its signal read from `/proc/net/wireless`. `Check`
scans, waiting for the scan to end, and pings the gateway once; the
daemon's unit may not open an
internet socket, so the ping runs in a transient unit as a dynamic user
(`systemd-run`). `ConnectWifi` checks the network is in reach and its
password what its security takes, then joins it with a saved connection
when there is one and no new password, or writes a connection file of
NetworkManager's own, root's and 0600, for the whole machine, loads it and
brings it up with a wait of 40 seconds: the password is on no command line
and in no audit line, a failed join takes the new file away again, and
`Secrets were required` is a wrong password. `ForgetWifi` deletes every
saved connection to the network. Each is a job in a thread, one at a time,
and the page asks `GetNetwork` once a second while one runs. The page:
each connection on a line, the router's answer, *Look again* (which the
page does by itself when it opens), and, when NetworkManager manages the
Wi-Fi, the networks in reach with *Connect*, the password asked in place,
and *Forget*, which asks once; a note that the children's modules may lose
their connection for a moment, since the page is not refused while a child
is signed in; a Wi-Fi `ifupdown` set up shown read-only, with the user
guide's way to hand it over. NetworkManager and `wpasupplicant` become
dependencies of `kidux-base`, `iproute2` and `iputils-ping` of
`kidux-daemon`. The panel's Network tab comes after System, so the session
tests that walk back from the first child's name to a tab count one more.
Unit: the parsers on real outputs of the test machine and the MacBook
(`tests/samples/network/`), the security kinds, the passwords, the
connection file, every job against a machine that answers as nmcli does;
the daemon's calls adults only and the password never audited; the page's
flows against a fake daemon. Session (`23-network.py`, the purge now
`24-purge.py`): two simulated radios (`mac80211_hwsim`), an access point
with a password on one (`hostapd`, `dnsmasq`), and, from the panel by
keyboard, the page, a wrong password said and not kept, the right one
joining in a file of root's, 0600, and Forget; picture `panel-network`.

**2. The versions** (kidux-daemon, kidux-greeter, kidux-common).
`System1.Versions()`, the `screens` class (daemon.md section 13): every
Kidux package dpkg has installed, `kidux-*` and `python3-kidux`, and its
version, from `dpkg-query -W`. The System page's *Version* row says
`kidux-base`'s, and under it, in the small letters the ages use, one line
of each part's, named in the adult's language: *service* (kidux-daemon),
*session*, *child's screen* (kidux-launcher), *sign-in screen*
(kidux-greeter), *common parts* (python3-kidux) and *web modules*
(kidux-webapps); after an update the row is what changes. *Choose* and the
lock screen say *Kidux 0.2.3* small under the logo. The Modules page
writes each installed module's version beside its ages (its manifest's
`version`, now read into `kidux.modules.Module`), and each module on offer
the archive's (`offered_version`, from the record `apt-cache search
--full` prints). Both languages. Unit: the daemon's answer from a
`dpkg-query` output, a package only configured left out, dpkg unreadable;
the version on the sign-in screen and none when the daemon cannot say;
the System page's parts; the manifest's version; the archive's version of
a module on offer. The pictures of the sign-in screen, the System page and
the Modules page change.

**3. Chromium in the child's language** (kidux-webapps). Chromium's own
words, its blocked page, its history, its dialogs, are in
`chromium-l10n`, which Debian ships apart: without it Chromium has only
English, whatever `--lang` says. `kidux-webapps` depends on it;
`kidux-webapp` already passes `--lang=<language>` from the session's
locale. Acceptance (`12-webapps.sh`): `chromium-l10n` installed with the
package, its Spanish there, `--lang=es` in `kidux-webapp --print hello-web`
under a Spanish locale. Session (`19-module-hello-web.py`): `--lang=es` on
Chromium's command line and its Spanish translation mapped in the browser
process (`/proc/<pid>/maps`), which is how Chromium shows it has loaded
it.

**4. Chromium's options, as a list** (kidux-greeter, kidux-common). The
Advanced page's explanation is one sentence and then the options as a list,
`words.CHROMIUM_OPTION_LIST`: each in monospace, selectable to copy into
the box, with what it does beside it: `--disable-gpu-compositing`,
Chromium puts the page together itself, the likeliest cure;
`--disable-gpu`, nothing on the graphics card, slower; `--use-gl=angle`
with `--use-angle=gl`, another way of drawing, the two lines together;
`--disable-features=WaylandLinuxDrmSyncobj`, the newer way of handing
pictures to the screen, turned off. The options are Chromium's and never
translated, their meanings are. The page still fits 1280x800 whole, which
`13-every-screen-fits.py` holds it to; both languages; picture
`panel-system-advanced`.

**5. The trusted screens' keys and lid** (kidux-greeter, kidux-session,
kidux-common, kidux-launcher). Under `cage` no configuration binds keys:
the sign-in screen and the lock screen answer the `XF86` keysyms of
keys.md themselves, in the window's key handler, before anything else
(`kidux_greeter/laptop.py`, a table and one function, no GTK), through
`kidux.hardware.key`, which `kidux-keys` now calls too: one place for what
each key does. The lid on those screens: `session-inner` under `cage`
starts `/usr/lib/kidux/kidux-lid-watch` beside the screen, which reads the
lid switch through `kidux.hardware` (its outputs from `wlr-randr`,
`hardware.panel_outputs` choosing the laptop's own, which the launcher's
lid now uses too) and runs `wlr-randr --output <panel> --off` and `--on`;
it ends when the screen's process, its parent, is gone, and on a machine
without a lid logs so and ends. Under `labwc` the launcher does it (3.22)
and `session-inner` starts no watcher. Unit: the key table against a fake
hardware and against `hardware.KEYS`; `hardware.key` stepping each level
through `brightnessctl` and `wpctl` as a machine answers, the floor, a
machine without the things; the panel among `wlr-randr`'s and `wlopm`'s
outputs. Session (`02-boot.py`): the watcher started under `cage` with the
sign-in screen, and on the test machine, which has no lid, saying so.

**5b. The udev rule on upgrade** (kidux-session). `70-kidux-switches.rules`
applies to devices as udev sees them, so a machine upgraded without a
reboot keeps its lid switch at the old mode until `udevadm trigger` runs:
`kidux-session`'s `postinst` runs `udevadm control --reload-rules` and
`udevadm trigger --subsystem-match=input --action=change` when udev is
running (`/run/udev`), and ignores their failure. Acceptance
(`02-install.sh`): after the install, every `ID_INPUT_SWITCH` device under
`/dev/input` is mode 0644; the test machine has none, and the check says
how many it found.

**6. Documents.** panel.md (the Network page, the versions, the Advanced
page), daemon.md (Network1, the versions), greeter.md (the keys, the
version line), session.md (the watcher), modules.md (the version shown),
installer.md or install guide (NetworkManager), the user guide's panel
section, both languages, and the roadmap's lines. D61 already covers the
trusted screens' keys; the network page is a decision of its own, D62,
in the log: NetworkManager as Kidux's network stack, the page adults
only, `ifupdown` machines read-only.

**What can go wrong, and what to do.** `nmcli` absent or NetworkManager
stopped: the page shows the facts from `ip` and the sentence, never an
error. A Wi-Fi interface managed by `ifupdown`: read-only, as above. The
test machine's wired card is `systemd-networkd`'s, which NetworkManager
leaves alone: its facts come from `ip`, and the session test brings a
Wi-Fi of its own (`mac80211_hwsim`). `ping` blocked or slow: the thread
and the one-second timeout; the page says *did not answer*. A password
with spaces or quotes: it goes into the connection file through GLib's
key file writer, which escapes it, and on no command line. Chromium's
`--lang` ignored when `chromium-l10n` is missing: the dependency. The
greeter's `key-pressed` for `XF86` keys never arriving under `cage`:
`cage` forwards every key it does not bind, and binds none but
Ctrl+Alt+F*n*; if a key does not arrive, `libinput debug-events` says
whether the kernel sent it (keys.md). A machine whose `dpkg-query` lacks
a package: the line omits it. The panel's fourth tab not fitting at
1280x800: the tabs are short words, four fit; the picture proves it.

### 3.24 — What the second hand test found: the keyboard light, the corner everywhere and at once, the network page's ten seconds, the scale that goes, Alt+Tab home — M — **done 2026-09-29**

The owner's hand test of 2026-09-29 on the MacBook, with 3.23 installed.
Every finding has its cause found on the machine before this is written;
each part below says the cause, the change, its tests and its documents.
Built by Opus 5.5, in the order written, each part with its battery green
and its own commit, every package touched bumped with `date -R`, both
user guides in the same commit, nothing installed on the development
machine, nothing pushed.

**What the machine says.** `brightnessctl` in trixie (0.5.1-3.1) is built
without logind: it writes `/sys` itself, and its own udev rule
(`90-brightnessctl.rules`) hands a backlight's `brightness` to group
`video` and a LED's to group `input`. A child is in `video` (D61,
`accounts.CHILD_GROUPS`) and rightly not in `input`, which reads every
keyboard; so the screen's backlight works and the keyboard's light,
`/sys/class/leds/smc::kbd_backlight/brightness`, `root input 0664`, is
refused, silently: `hardware._run` drops the program's stderr. `_greetd`
is in no group at all, so on the trusted screens even the backlight is
refused. The daemon names an `ifupdown` Wi-Fi with `wpa_cli`, whose reply
comes to a socket it binds under `/tmp`; the daemon's unit has
`PrivateTmp=yes`, so `wpa_supplicant` cannot reach that socket, `wpa_cli`
waits its ten seconds for a reply that never comes, and the greeter's
call, whose timeout is also ten seconds (`kidux.client.DEFAULT_TIMEOUT_MS`),
gives up first: *Something went wrong*. The corner's label is set only by
the five-second refresh, so a slider's value shows seconds late and a key's
change later still. When one module is open, Alt+Tab goes to the
launcher, which the desk knows (`previous()` is `HOME`) and the bar writes
nowhere. The trusted screens' scale is set by `session-inner` the instant `cage`
starts, with one `wlr-randr --scale` per output; `cage` refuses a
configuration that comes while it is still bringing the output up, and
`wlr-randr` says *failed to apply configuration*, which the MacBook's
journal (`journalctl -t kidux-session`) shows for 1.75 on `eDP-1` at most
starts of the sign-in screen: the screen stays at 1, and every screen of
the greeter looks small.

**A. The network page in a second** (kidux-daemon). `network.py` never
runs `wpa_cli`: an unmanaged Wi-Fi is named by `iw dev <name> link`
(nl80211, `AF_NETLINK`, which the unit allows; `iw` 6.9 in trixie, a
dependency of `kidux-daemon`), its `SSID: <name>` line parsed by
`iw_network`, the signal from `/proc/net/wireless` as now. daemon.md
section 14 gets the rule this teaches: no program the daemon runs may
wait for an answer through `/tmp`. Unit: `iw`'s output on the MacBook
(`tests/samples/network/macbook-iw-link.txt`, scrubbed as the others),
the MacBook test naming the network from it, and `read()` never calling
`wpa_cli`. Session (`23-network.py`, after *Forget*;
the acceptance machine's cloud kernel has no `mac80211_hwsim`): the
simulated radio handed to `wpa_supplicant` started by hand with its
socket under `/run`, as `ifupdown` runs a Wi-Fi, NetworkManager told
`managed no`; then `kidux-as network` (a new command of the tests' helper:
unlock, `GetNetwork`, print each interface's name, kind, address and
network) answers within five seconds and names the network. This is the
MacBook's case on the test machine, and the check that `GetNetwork` fits
the greeter's timeout.

**B. The keyboard light, and every failure said** (kidux-session,
kidux-common). `91-kidux-keyboard-light.rules` in kidux-session, after
brightnessctl's own: `ACTION=="add|change", SUBSYSTEM=="leds",
KERNEL=="*kbd_backlight*"` runs `chgrp video` and `chmod g+w` on
`/sys/class/leds/%k/brightness`, so the keyboard's light is `video`'s as
the backlight is; the `postinst` triggers `--subsystem-match=leds` as it
triggers the switches, so an upgrade takes effect at once. The same
`postinst` adds `_greetd` to `video` (`adduser --quiet _greetd video`
when the user exists), since the trusted screens run the keys themselves
(3.23) and greeter.md already says the user is there: now it is.
`hardware._run`, which runs a program that changes something, logs its
failure at warning with its name and its stderr, one line, so that the
journal says *brightnessctl: Can't modify brightness: Permission denied*
rather than nothing; `_output`, which reads every few seconds, stays
quiet. Unit: a
program that fails is logged (a `sh -c` that writes to stderr and exits
1, read through `caplog`). Acceptance (`02-install.sh`): the rule is in
place; after `udevadm trigger --subsystem-match=leds --action=change`,
every `/sys/class/leds/*kbd_backlight*/brightness` is group `video` (the
test machine has none, and the check says how many it found); `_greetd`
is in `video`. Documents: session.md sections 1 and 5, greeter.md, D61
extended with the group.

**C. The corner at once** (kidux-launcher, kidux-common). `_Slider` sets
its own label as its value changes, before `on_value` runs, and the
refresh leaves a slider whose popover is open alone (its value is the
child's hand, not the machine's). A key's change reaches the corner
without waiting for the refresh: `hardware.key` touches
`$XDG_RUNTIME_DIR/kidux/levels` when it has changed a level (the
directory made if missing; nothing when `XDG_RUNTIME_DIR` is unset), and
the corner watches that file with `Gio.FileMonitor` and refreshes on any
event, at most once per 200 ms. Under labwc `kidux-keys` runs as the
child, so the file is the child's own; under cage the greeter calls
`hardware.key` itself and refreshes its corner directly as well. No
package has GTK unit tests, since the build has no display, so what needs
no GTK is tested alone: the levels file, and that a key touches it only
when it changed something, and not without the variable. Session
(`09-child-session.py`): the corner has made its directory in the child's
runtime directory, to watch it; the test machine has nothing a key can
change. Documents: launcher.md section 2, keys.md.

**D. The corner on the trusted screens** (kidux-common, kidux-greeter,
kidux-launcher). `status.py` moves to `kidux.corner` in kidux-common
(GTK 4, taking the translate callable and the `/sys` root as now), its
words to `kidux.vocabulary` (*Battery*, *Screen brightness*, *Keyboard
light*, *Volume*, *Mute*, *Muted*), and the launcher imports it. The
greeter draws the same corner top right on every screen of its own, the
sign-in screen, the password, the lock screen, the adult screens and the
panel's pages, in a `Gtk.Overlay` over the page's top right, taking no
room from it; made once and moved from page to page, since it watches a
file and reads the machine on a timer, and made again only when the
language changes; showing what the machine has
as the launcher does: on `_greetd`'s session the sound is absent when
`wpctl` finds no output, and everything is absent on the test machine,
so no picture changes there; every screen still fits 1280x800
(`13-every-screen-fits.py`). The greeter's own key handler (3.23)
refreshes the corner after `hardware.key`. Session (`02-boot.py`): the
sign-in screen's corner logs the machine's `hardware:` line, nothing of a
laptop's on the test machine; the overlay's path, which that empty corner
never takes, run by hand on the test machine with a fake battery and
backlight. Documents: greeter.md, launcher.md section 2, panel.md, the
user guide's sign-in and lock sections in both languages, D61 extended.

**E. The scale, every time** (kidux-session). `session-inner` sets each
output's scale again, every 250 ms for up to five seconds, while
`wlr-randr` refuses it, and a listing without a `current` mode is asked
again the same way; it logs how many tries a scale took when it took more
than one, and the refusal itself only when it gives up, so that a small
screen has one line in `journalctl -t kidux-session` saying why. Session
(`20-scale.py`): the sign-in screen restarted five times at scale 2, each
time logging `screen 640x400`: a race that shows in one start of many
shows here. Documents: session.md section 2.

**F. Alt+Tab written on Home** (kidux-launcher). When the window Alt+Tab
goes to is the launcher's own (`desk.previous()` is `HOME`, the case of
one module open), the bar writes both keys on Home, `⌘ Alt+Tab` or `Win
Alt+Tab`, and takes the second away when another window becomes the
previous; `show_modules` and `show_windows` alike. Unit: the bar with
`previous=HOME` hints Home; with a module, that module and not Home.
Session (`16-module-open.py`): with one module open the bar's Home hint
says Alt+Tab (read from the launcher's `keys:` and `bar:` lines or the
accessible label). Documents: launcher.md section 5, D61 unchanged.

**G. The X11 stand-in sized to its text** (`tests/lib/seed/modules/
x11-canary/run`): no fixed geometry, so Tk sizes the window to the
samples and the drawing, which the owner could not see in a 640x400
window; `22-x11.py` still finds it maximised by labwc's rule.

**Found on the way.** Debian's new kernels gave the test machine five
updates, whose names took three lines on the System page and pushed it
past 1280x800: the updates' row now takes two lines at most, the rest in
its tooltip (panel.md).

**Tests.** Every part's, above; `ci/i18n-extract.sh` for the words that
move; the pictures of the greeter's screens do not change on the test
machine, which has nothing for the corner to show. Both user guides say,
in the sections on the sign-in screen and the lock screen, that the
corner is there too on a laptop.

**Risks.** `chgrp` from a udev `RUN` on a `/sys` path: it is what
brightnessctl's own rule does through its helper, and the acceptance
check reads the result. A LED renamed by the kernel: the `KERNEL` match
takes any `*kbd_backlight*`, as `kidux.hardware` does. `iw` printing
`Not connected.` for an interface that is up with no network: an empty
name, as now. The corner's file monitor on a runtime directory that is
not there: the launcher makes the directory at start, and the monitor
watches the directory's entry. The scale's retries making the trusted screens
slower to appear: nothing waits when the first try is taken, and the
refused one is taken a quarter of a second later.

### 3.25 — What does not fit scrolls, and shows it — S — **done 2026-09-29**

D63, the owner's, before the second hand test's fixes are tried: no screen
can be drawn for every number of children, modules or updates, nor every
screen size and scale, so what does not fit must scroll and show it. What
was there: the greeter's middle and the launcher's scrolled up and down
only, with GTK's overlay scrollbar, hidden until the pointer moves (at a
scale of 2 the sign-in screen's children were cut with nothing to say
so), and not sideways, so a Modules page with more children than its
width would have been cut on the right; the bar's buttons scrolled with no
sign at all; and the Network page showed six networks at most.

**The area** (kidux-common): `kidux.scroll.scroller`, a `Gtk.ScrolledWindow`
scrolling both ways where needed, with its scrollbar drawn always
(`overlay-scrolling` off), and `kidux.scroll.CSS`: the scrollbar in Kidux's
browns, 14 pixels wide, and a shade along each edge beyond which there is
more (GTK's `undershoot` nodes). `watch` calls back when an area does not
fit, for the logs; `more`, which needs no GTK, says whether there is more
before and after what is shown.

**The screens.** The greeter's middle and the launcher's are such areas,
and each logs `does not fit: <n> pixels tall` or `wide`, once each way; the
box of Chromium's options keeps its three lines and scrolls inside itself;
the Network page lists every network in reach. The bar's buttons, which
have no room for a scrollbar, get an arrow either side while they do not
all fit, the one at an end faded, each moving them along, and bring the
button of what is in use into view; both are set once GTK has laid the bar
out, 100 ms after it changes, since neither can be while it does. While the
bar asks whether to close a module, the buttons and their arrows step
aside, as the time and *Close* do, so that *Lock* stays whole.

**Tests.** Unit: `more` on an adjustment's numbers. Session (`20-scale.py`):
at a scale of 2 the sign-in screen and the child's are too tall, log so,
and draw their scrollbar (its colour on the right edge of the picture).
The bar's arrows, which no session test fills enough windows for, tried on
the test machine by hand: the real bar with nine modules, both arrows,
the one at the start faded, the one in use brought into view, and none
with two. `16-module-open.py`: *Lock* whole on the bar while it asks
(its blue where its left end belongs), which the first run of this step
found pushed off the screen by the arrows. Test 13 still holds every
screen to 1280x800 at a scale of 1.

### 3.26 — Reviewed: the corner compact on a narrow screen, what group `video` opens, the manuals plainly written — S — **done 2026-09-29**

The review of 3.24 and 3.25 by Fable 5.1, with the owner's two asks of
2026-09-29 on the documents.

**The corner on a narrow screen** (kidux-common, kidux-greeter,
kidux-launcher). The greeter's corner lies over the page, so on a screen
narrower than the full corner and the page's centred top content side by
side, the panel's tabs at 300 % on the MacBook (960 logical pixels), it
covered the last tab. Under 1200 logical pixels
(`kidux.screen.compact_corner`, tested on the widths that matter) the
corner is compact, icons without percentages, in both programs, and the
launcher cuts the child's name, which may be 64 characters, to 24 with an
ellipsis, so that the clock keeps its room. The corner's log line ends in
`compact` when it is. Tried on the test machine with a battery the kernel
fakes (`test_power`): the corner over the real sign-in screen, full at
1280 and compact at 640.

**What group `video` opens** (documents). session.md's doors table names
it: the console's framebuffer, the DRM card nodes as a client, and a
webcam where there is one; D61 points there.

**The manuals, plainly written** (documents). The README, in both
languages, says a child can have windows and describes what a child sees
in plain sentences; the user guide, in both languages, is rewritten for
reading: shorter sentences, one idea a paragraph, lists where things are
listed, and each page of the panel under a heading of its own. The
sections keep their numbers, which the screens' words and the developer
documents refer to, and every picture stays where it was.

### 3.27 — What the third hand test found: a laptop's keys on the trusted screens, the scale when the panel closes, the bar's room, Alt+Tab round the bar — M — **done 2026-09-29**

The owner's hand test of 2026-09-29 on the MacBook, with 3.26 installed,
and their ask to fix it directly. Each part below says the cause, the
change, its tests and its documents; each is its own commit with its
battery green.

**Plymouth's label plugin** (kidux-session). At every kernel update
initramfs-tools' Plymouth hook warned that `label-pango.so` was missing:
it copies that plugin for every theme but Debian's own. kidux-session
depends on `plymouth-label`, and `02-boot.py` finds the plugin in the
initramfs.

**A laptop's keys on the trusted screens** (kidux-greeter). The volume,
keyboard-light and brightness keys did nothing on the sign-in, lock and
adult screens, though they worked in a child's session. The greeter
matched the keys by the names xkb gives them, `XF86MonBrightnessUp`, and
GTK 4 names them without the prefix, `MonBrightnessUp`, so no key ever
matched. `laptop.KEYSYMS` is keyed by the keysym's number, and each key
answered is logged, `laptop key: volume up`. Tests: unit, on the numbers
and on a key that is not one; `02-boot.py` sends the volume key to the
sign-in screen and reads the log line.

**The scale when the panel closes** (kidux-greeter). A new size, language
or keyboard, set from the panel on the sign-in screen, applied only after
a child had signed in and out, since the screen takes them when it
starts. Closing the panel on the sign-in screen after such a change
starts the greeter again, which `greetd` does at once, so the adult sees
it applied; the panel says *Saved. It applies when you close the panel.*
On the lock screen, which must not start again over a child's session,
it waits for the next start, as it says. Tests: unit, on what each
screen says and on the panel's close ending the greeter only after a
change and only on the sign-in screen.

**The bar's room** (kidux-common, kidux-launcher; D64). The keys written
beside the bar's buttons (D61) and *51 minutes left* took the room of
the modules' buttons. The keys are the buttons' tooltips. The time left
is an hourglass and `00:51` (`Model.time_clock`, `timeleft.py`), the
sentence on hover and in a popover on a tap, on the bar and on the
child's screen alike; the hourglass is kidux-common's
(`paths.HOURGLASS`). The modules' buttons take all the room between
*Home* and the time left, and scroll past it as before (D63). Tests:
unit, on the clock's text; the session tests' pictures.

**Alt+Tab round the bar** (kidux-launcher, kidux-session; D64). labwc's
`NextWindow` with its switcher hidden went between the last two windows
with nothing shown, so a child held Alt and saw nowhere to go. labwc
sends the launcher a signal for Alt+Tab and one for Alt+Shift+Tab
(`SIGRTMIN+1`, `+2`); each is a step round the launcher's window and
every module's main one, in the order they were last in use
(`desk.switch`); the bar lights the button of the one pointed at and
follows the keyboard's state, which labwc sends every program, until Alt
is let go, which goes there (`desk.switch_done`). The bar never takes the
keyboard to hear Alt let go: while a layer-shell window holds it, labwc
brings no window forward, and hiding the window does not give it back
(labwc-notes.md). Tests: unit, on the round's order, a
launcher started again, and one window; `16-module-open.py` holds Alt
down and presses Tab twice on a keyboard of the machine's own
(`tests/lib/keyboard.py`, through uinput, since QEMU's `sendkey` lets
Alt go at the next key), and finds the launcher lit on the bar, then the
canary, the robin still on screen, and Alt let go going to the canary.

### 3.28 — The pictures in each language — S — **done 2026-09-30**

D65, the owner's, 2026-09-29: the English user guide and README showed the
Spanish screens, and the README showed only GCompris.

**Two runs.** `sessionlib.LANGUAGE` (`KIDUX_VM_LANGUAGE`, Spanish by
default) sets the machine up in that language: the wizard's choice, and
what the tests expect of it, `sessionlib.LANGUAGES` (locale, keyboard, the
hello modules' words, Chromium's translation). A run in English has its own
disk, ports and pictures (`session-en-NN-<screen>.png`), so
`tests/run session-en` runs beside `tests/run session`, and the battery runs
both with the other test stages.

**The pictures.** The battery copies each language's to
`docs/images/es/` and `docs/images/en/`; each guide and README shows its
own. The comparison report names an English picture `en/<screen>`. The
README shows the sign-in screen, a child's screen with a module open, the
adult panel and GCompris.

**Tests.** The English run itself, every session test in English; the
battery, both.

### 3.29 — Alt+Tab goes round the modules in the bar's order, Home out of it — S — **done 2026-09-30**

The owner's fourth hand test, 2026-09-30, on the round of step 3.27 (D66).

**Cause.** The round goes through the windows in the order they were last
in use, the launcher's window among them, so a child holding Alt cannot
tell where the next Tab goes, and gets sent home by a key that is for the
modules. The owner wants what the bar shows: left to right, from the one
after the one on screen, the last wrapping to the first; Home is not a
module, and the key for Home is Super.

**Change** (kidux-launcher).
- `desk.py`. `switch(step)` builds the round, when it begins, from the
  bar's order: for a child without windows, the main window of each
  module in `self.modules`, which is the order the bar shows (a module with
  several main windows contributes the one in use if any, else its
  first; a module with no window yet contributes nothing); for a child with
  windows, the main windows of `self.windows`, in the compositor's order,
  which is the bar's. The launcher's window is never in it. The position
  is the index of the window in use when it is in the round; when it is
  not (the launcher's window, a stranger's), a step forward starts at the
  first, a step backward at the last. The target is `round[(position +
  step) % len(round)]`; when it is the window in use, or the round is empty,
  `switch` returns None and the launcher logs `switch: nowhere`. The rest
  of the round (`_round`, `switch_done`) is as it is. `next_in_bar()`
  returns what one Alt+Tab would go to now, by the same rule, for the bar's
  tooltip: a module's id, a window's number on the desk, or None.
  `previous()`, `previous_window()` and `_recent` go, and their tests with
  them.
- `view.py`: `show_modules(…, next=self._desk.next_in_bar())` and
  `show_windows(…, next=…)` replace `previous`/`previous_home`; `switch`
  logs `switch: nowhere` when `desk.switch` returns None.
- `bar.py`: `_alt_tab(target)` sets Home's tooltip to the home key alone,
  always; the button whose `kidux_key` is `target` gets the `Alt+Tab`
  tooltip; the log line `alt-tab: <module id | window number | none>` when
  it changes. The module docstring and the constants' comments say the
  bar's order.

**Tests.** Unit (`test_desk.py`): with canary and robin opened in that
order, on robin the round is canary then robin; on canary, robin then
canary; on the launcher, the first is canary and a step back is robin;
with canary alone and on it, `switch` is None; with canary alone and on
the launcher, canary; `next_in_bar` the same, and None with one module on
it; on the desk the order is the compositor's. Session
`16-module-open.py`: *with one module open, on it, Alt+Tab goes nowhere*
(`switch: nowhere` logged, the canary still on screen); *from Home it goes
to the canary* (Super first, then Alt+Tab, `switched: canary`); with both
open and the robin on screen, a quick Alt+Tab goes to the canary and
another back to the robin; Alt held with two Tabs lights the canary and
then the robin, and Alt let go stays on the robin; Alt+Shift+Tab goes to
the canary. The check `alt-tab: home` goes; `alt-tab: canary` on Home and
`alt-tab: none` on the canary alone are what the log shows.

**Documents.** keys.md's row (the tooltip is the next module's, Home says
its own key only), launcher.md section 5, the user guides' *The keyboard*
in both languages (the sentence about Home saying Alt+Tab goes), D64
marked in part, D66 added.

**Done when.** Test 16 passes in both languages with the new checks.

### 3.30 — A session left alone locks, the screen turns off, the lid locks; the minutes an adult's setting — M — **done 2026-09-30**

The owner's fourth hand test, 2026-09-30 (D67): a child walks away and
the session stays open, spending the day's time and open to anyone.

**Cause.** `swayidle` in each session sets the backlight to zero after
five minutes and nothing more (session.md section 5, D13: idle never
locks). A backlight is a laptop's; a desktop's screen never goes off.
Closing the lid powers the panel off and locks nothing. The adult panel
closes after five minutes of its own, and its token dies after fifteen
(D26), two numbers nobody set.

**Change.**

*Settings* (kidux-daemon, kidux-common). `idle_lock_minutes` (default 5,
1 to 120) and `screen_off_minutes` (default 10, 1 to 240) are in
`config.py`'s `DEFAULTS` and `Config`, and there is no setting of the
panel's own timeout: the panel follows the first; both are in `SETTABLE`, checked as integers in their range (`InvalidArgument`
otherwise), and in `GetConfig`. `Tokens` is made with
`idle_lock_minutes * 60` and takes the new value when `SetConfig` changes
it (`tokens.set_timeout`). `Access1.LockFor(s reason)`, gated `SELF` like
`Lock`, locks the caller's own session for `idle` or `lid` (any other
reason is `InvalidArgument`), with the reason in the audit line and in the
`Locked` signal; a lock for `idle` is refused (`NoSession`, "the session
was continued a moment ago") when the session was unlocked less than
`IDLE_LOCK_GRACE_SECONDS = 10` ago, which is a frozen timer speaking, not
a child who has gone. `kidux.client` gains `request_lock_for(reason)`;
the launcher's `daemon.py` `lock_for(reason)`.

*The sessions* (kidux-session). `session-inner` no longer runs
`swayidle` itself; it runs `/usr/lib/kidux/kidux-idle watch` in the
background, for the trusted screens and for the child's session alike,
with `KIDUX_IDLE_SCREEN=wlopm` for the child's session (labwc has
wlr-output-power-management) and `wlr-randr` for the trusted screens
(cage has not; the lid watcher already turns outputs off that way). The
greeter (`flow.py`) passes a child's session `KIDUX_IDLE_LOCK_SECONDS`
and `KIDUX_SCREEN_OFF_SECONDS`, the settings in seconds;
`greeter-session` gives the trusted screens `KIDUX_SCREEN_OFF_SECONDS`
and `KIDUX_IDLE_LOCK_SECONDS=0`. `kidux-idle`, a Python program in
`packages/kidux-session/bin/` installed beside `kidux-lid-watch`, logs
to the journal as `kidux-idle`, and does three things:
- `watch`: runs `swayidle -w` with `timeout <lock> "kidux-idle lock"`
  when the lock seconds are more than 0, `timeout <off> "kidux-idle screen
  off"` and `resume "kidux-idle screen on"` when the screen-off seconds
  are, **only while this screen's terminal is the active one**: it reads
  its own from `XDG_VTNR` and the active one from
  `/sys/class/tty/tty0/active`, every two seconds; when the active
  terminal is another, `swayidle` is killed and nothing fires; when it
  becomes this one again, or when the clock says the process was frozen
  (more than ten seconds between two looks), `swayidle` is started afresh,
  so that the count begins when the session comes to the front and a
  timer that expired under the lock screen never fires on thaw, and
  `kidux-idle screen on` runs, so that a session coming to the front is
  on a screen that is on. It logs `swayidle started (tty7, lock 300 s,
  screen off 600 s)`, `swayidle stopped: tty8 is active`, and ends when
  its parent does.
- `lock`: `Access1.LockFor("idle")` through `kidux.client`, as the child;
  the answer logged, `lock: asked` or `lock: refused: <why>`.
- `screen off` and `screen on`: `wlopm --off '*'` / `--on '*'`, or
  `wlr-randr --output <each> --off` / `--on` for every output the
  compositor lists; logged `screen off (tty7)`, `screen on (tty7)`.
  Brightness is left alone; the `brightnessctl --save/--restore` dimming
  goes, and with it session.md's sentence that a dark screen is still an
  unlocked session.
`kidux-session` depends on `wlopm` as well as `wlr-randr`, and on the
`python3-kidux` with `request_lock_for`.

*The lid* (kidux-launcher). `Lid(devices, set_screen, on_closed=None)`:
closing calls `on_closed()` before the screen goes off; the launcher
passes `lambda: self._daemon.lock_for("lid")`, with the daemon's errors
logged and nothing else done, as its Lock button does. The trusted
screens' watcher is unchanged: on the lock screen a closed lid powers the
panel off, and an open one powers it on.

*The panel* (kidux-greeter). The System page, after the size row: a row
*Lock a child's screen, and close this panel, after* [spin 1–120] *minutes
without a touch* with a *Set* button, and a row *Turn the screen off
after* [spin 1–240] *minutes without a touch* with its own; the actions
`set_idle_lock` and `set_screen_off` (`SetConfig`, then the page with
`words.SAVED`); the values in the screen's data. Every panel screen
carries `idle_seconds` in its data, and the view's `_idle_method` reads it
for the panel instead of `PANEL_IDLE_SECONDS`, which goes; the sign-in
screen's own minute (`IDLE_SECONDS`) stays. The change applies to the
panel at once and to a session the next time it starts.

**Tests.**
- Unit, daemon: the two settings' defaults, ranges and refusals; `LockFor`
  for `idle` and `lid`, the audit reason, the refusal within the grace
  seconds after an unlock and its acceptance after; the tokens' timeout
  following the setting. Unit, greeter: the System page's data and the
  two actions; `_idle_method` reading `idle_seconds`. Unit, launcher: a
  `Lid` whose `on_closed` is called once per close and not on open. Unit,
  session: `kidux-idle`'s decision table (own terminal, active terminal,
  a frozen gap → start, stop, nothing), with `swayidle` and the clock
  faked.
- Acceptance `05-time-and-lock.py` or a new `kidux-as` command
  `child-lock-for <reason>`: a child locks their session for `lid`; for
  `idle` right after a continue is refused; `set-config idle_lock_minutes
  0` and `500` are refused, `3` is read back.
- Session `24-idle-lock.py`, the purge test renamed to `25`: as the
  administrator, `set-config idle_lock_minutes 1` and `screen_off_minutes
  2`; Leo signs in; a minute without a key locks the session (the lock
  screen drawn, `active_terminal()` is `tty8`, the audit line says
  `idle`); a minute more and the greeter's `kidux-idle` logs `screen off
  (tty8)`, while its count of that line during the child's minute is
  what it was before (the guard held); a picture, `screen-off`, taken and
  described in the report line for what a screen dump shows then; a key,
  `screen on (tty8)` and the lock screen; the adult continues
  (`lock_screen_adult` and the continue path test 16 uses); fifteen
  seconds later the session is still unlocked on `tty7` (no second lock
  on thaw); the child's `kidux-idle` has logged `swayidle started` twice;
  the settings back to 5 and 10; log out.
- The panel's rows appear in `panel-system.png` of test 13 without a
  change to it.

**Traps.**
- `cage` has no wlr-output-power-management: `wlopm` fails there, which is
  why the trusted screens use `wlr-randr --off`, as the lid watcher does;
  a screen turned off that way comes back with `--on` on the first key,
  and cage survives having no output, which the lid already proved.
- The whole session, `kidux-idle` included, is frozen under the lock
  screen; the clock gap is how it knows on thaw.
- A module that plays by itself with nobody touching anything is locked
  like any other after the minutes; the guide says so.
- The session tests' longest stretch without a key is under four minutes
  (GCompris's first screen); the rule in phase-4-plan.md section 3 keeps
  it so.

**Documents.** session.md section 5 rewritten (idle: the lock and the
screen; the lid), daemon.md (the settings, `LockFor`, the tokens),
panel.md (System page rows; *Leaving* says the panel closes after the
lock's minutes), launcher.md section 5 (the lid locks), rollout.md's
hardware table row for idling, the user guides' *A laptop's own keys and
its lid*, *Files, locking and logging out*, section 7 (the screen off on
the lock screen), section 8 *Opening and closing it* and *System*, both
languages; the README's *What an adult decides* gains the minutes; D13,
D26 marked in part, D67 added.

**Done when.** Test 24 passes in both languages, and the owner's lid test
on the MacBook locks.

## 6. Risks

| Risk | Mitigation |
|---|---|
| `systemd-run --user` finds no user manager inside a child's session. | logind starts `user@<uid>` for every session of class `user`, and phase 1's sessions already have one (daemon.md section 8 sees it as a second, `manager` session); step 3.2's first test is exactly this. |
| GCompris under `labwc` on Wayland, on the `radeon` machine. | Qt on Wayland is what the session already sets (`QT_QPA_PLATFORM`); the VM proves the window, step 9.11 proves the GPU. |
| GCompris needs files it downloads: voices, words, background music. | `gcompris-qt-data` is checked on the VM in step 3.6 before the manifest is written; what it lacks is packaged, or downloaded by GCompris itself on a machine with a connection. |
| A module's window that floats (a dialog) or that asks for fullscreen escapes the bar. | The launcher takes fullscreen back at once and a dialog floats over its own window (step 3.19); `16-module-open.py` checks the first with the robin. |
| A compositor that gets the screen back after the lock screen sets its input devices up on the first event, and that event, a key, never reaches the window (wlroots 0.18 resumes libinput without reading its queue). | The daemon wakes the input devices with a udev change event once the child's session has the screen back (daemon.md section 10); `15-modules.py` presses a key right after continuing. |
| A child's process asks the compositor, through the foreign-toplevel protocol, to close or show another program's window. | Every such program is the child's own, which is nothing a child cannot do already (D17); session.md's table says so. |
| A module keeps running after log-out and keeps counting for nothing. | `KillUserProcesses=yes` and the scope under the user manager; the session test checks nothing of the child's survives. |
| GCompris does not draw under labwc on the test machine's software rendering, or a Qt program cannot open a window at all. | `qt6-wayland` in the module's dependencies, since `gcompris-qt` does not bring it and Kidux's modules do not rely on XWayland; `QT_QUICK_BACKEND=software` through a wrapper if the VM needs it (step 3.6); the real GPU is step 3.8's. |
| Chromium takes too much of the test machine's 2 GB, or is too slow on software rendering for the session test. | `memory_max = "3G"` in web-application manifests; waits of 60 seconds in the test; if it still cannot run there, 3.7 is left for the owner's machine and the plan says so. |
| A module installed from the panel is not in apt's lists because they are stale. | `kidux-update install` runs `apt-get update` first; the page's *Look for modules* refreshes the list on demand. |
| Chromium's application window finds a way out (a file dialog, a link, a new window). | The managed policy of D36, and a session test that tries the link; anything the test cannot try is the owner's, at the keyboard, in 3.7. |
| The archive's list of available modules is empty on a family machine without our archive. | `Available` says so with a sentence; the ISO of phase 2 ships every module pre-installed (architecture.md section 6). |
