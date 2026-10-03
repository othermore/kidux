# labwc on Kidux: what each piece does

`labwc` 0.8.3 (trixie) is the child's compositor (D58). This document is
what was found by trying it on the quick loop's machine, before anything of
Kidux's was built on it (phase-3-plan.md, step 3.19, part A), and what the
session, the launcher and the tests rest on because of it. The pictures
were taken at 1920x1080 in the machine's software rendering; the X11
softness is judged on the owner's MacBook (step 3.21).

## The configuration

- `labwc -C <dir> -s <command>` reads `rc.xml`, `menu.xml` and nothing
  else of the user's: `~/.config/labwc` is never read. `-s` runs the
  command through `/bin/sh`, as the child; it is `session-inner`, which
  starts the launcher. `labwc --exit` ends the session.
- `-c <file>` beside `-C <dir>` takes `rc.xml` from that file and the
  rest, `menu.xml` and `themerc-override`, from the directory; SIGHUP
  reads both again. Kidux's session gives it the directory's `rc.xml`
  with a `<libinput>` part put in before `</labwc_config>`.
- **Pointer and touchpad.** `<libinput>` has a `<device category="…">`
  for each kind: `touchpad`, `touch`, `non-touch` and `default`, which a
  device of a kind with no section of its own takes; a touchpad with a
  section takes nothing from `default`, so the pointer's speed goes in
  both. `<pointerSpeed>` is libinput's, -1 to 1, 0 its own;
  `<scrollFactor>` multiplies a device's scrolling, 1.0 by default, and a
  touchpad's two fingers scroll a page further than a child wants
  (labwc-config(5) of 0.8.3).
- **Keys.** Once `<keyboard>` defines a keybind and has no `<default />`,
  none of labwc's own are loaded: no terminal key, no root menu key, no
  close key. The configuration's are the only ones.
- **Mouse.** The same for `<mouse>`: without `<default />` only the
  configuration's mousebinds exist. So the kiosk has one, a press in a
  window focuses and raises it; the desk has the frame's (title drag
  moves, a double click maximises, the edges and corners resize, the
  iconify, maximise and close buttons do what they say) and no binding
  that shows a menu, so `menu.xml`, empty, is never reached. A binding
  in the `Frame` context (the whole window, client area included) that
  matches a press swallows it: labwc never passes that press to the
  program (`cursor.c`, `consumed_by_frame_context`). labwc's own
  configuration binds `Frame` only with Alt held for that reason, and
  Kidux's bind it not at all: a plain press is `Client`'s and
  `TitleBar`'s.
- **Window rules** match `identifier` (a Wayland window's `app_id`, an X11
  window's `WM_CLASS`), `title` and `type`, by glob. `type` is `dialog`
  for a Wayland window with a parent or a fixed size, `normal` otherwise,
  and an X11 window's `_NET_WM_WINDOW_TYPE`. `<windowRule identifier="*"
  type="normal" serverDecoration="no"><action name="Maximize"/>` makes
  every main window of a Wayland program a frameless window filling the
  room above the bar, and leaves a dialog floating, centred on its parent,
  above it: the kiosk. An X11 window takes no notice of
  `serverDecoration`, but the action `SetDecorations` with `decorations=
  "none"` and `forceSSD="yes"` takes its frame off, so the kiosk has that
  rule for every window, dialogs included; and one that says no
  `_NET_WM_WINDOW_TYPE`, a Tk one, is not `normal` to the rule, so the
  launcher maximises what the rule missed. (A GTK dialog made before its
  parent window is mapped has no parent, and is `normal`: a program's
  real dialogs have one; the test module that makes one waits for its
  window.)
- **A window that comes up fullscreen keeps a title bar.** labwc 0.8.3
  does not change a fullscreen window's decoration, and gives one taken
  out of fullscreen its frame back whatever a rule said;
  `<maximizedDecoration>`, which would take it off, is a later labwc's. So
  in the kiosk a program that asks for the whole screen when it starts,
  once the launcher has taken it back, has a title bar with a close
  button, which the kiosk's one binding for it makes work. Kidux's modules
  do not ask: `kidux-module-hello` starts in a window, and GCompris with
  `--window` (D60).
- **`skipTaskbar`** removes a window from the foreign-toplevel list: never
  set on anything the launcher has to see, its own window included.
- **Home.** `<keybind key="Super_L" onRelease="yes"><action name="ForEach">
  <query identifier="org.kidux.Launcher"/><then><action name="Focus"/>
  <action name="Raise"/></then></action></keybind>` brings the launcher's
  window forward with nothing of the launcher's involved: the kiosk's
  home. On the desk, where home minimises the windows and the launcher
  must remember which to bring back, Super is a signal to the launcher
  instead, as Alt+F4 is. A `ForEach` there with `<else><action
  name="Iconify"/></else>` does minimise every other window, but the
  launcher could not tell those from the ones the child minimised.
- **Placement.** `<placement><policy>cascade</policy>` places a new window
  further down and right of one already in view, and takes no notice of
  minimised windows. A window that comes up fullscreen has no natural
  geometry yet, and is placed by the policy when it leaves fullscreen;
  but when the program's own size reaches labwc before the request to
  leave, which a loaded machine makes likelier, that size is what is
  stored, and the window comes back at the top left at that size.
  Kidux's modules do not come up fullscreen (D60), so only the tests'
  robin shows it.
- **`XF86` keysyms** bind as any other (`key="XF86AudioRaiseVolume"`):
  labwc resolves the name with xkb, and a MacBook under `hid_apple` and a
  PC laptop send the same ones for brightness, keyboard light and sound.
  labwc also implements wlr-output-power-management, so `wlopm --off
  eDP-1` powers the panel off with everything else in place.
- **`Execute`** keybinds run a command as the child: `pkill -USR2 -f
  "^/usr/bin/python3 /usr/libexec/kidux-launcher"` reaches the launcher's
  own process, which is how Alt+F4 becomes the bar's *Close* (D45). By its
  command line, not `-x` and its name: the launcher runs itself again under
  `python3` to load the layer-shell library first, so its process is called
  `python3`.
- **Alt+Tab** is an `Execute` that signals the launcher (`pkill
  -RTMIN+1`, and `-RTMIN+2` for Alt+Shift+Tab), whose bar goes round the
  windows and lights the one it points at (D64). The bar learns that Alt
  is let go from the keyboard's state, which labwc sends every client,
  the one with the keyboard's focus or not
  (`broadcast_modifiers_to_unfocused_clients`), so it never takes the
  keyboard. A layer-shell surface that does, exclusively, stops labwc
  from focusing any window, even one asked for through foreign-toplevel,
  and hiding the surface does not give the keyboard back. `NextWindow`
  with `<windowSwitcher show="no">` shows nothing while it goes round,
  so a child cannot see where Alt+Tab goes.

## Frames

With `<decoration>server</decoration>` and `<titlebar><layout>
icon:iconify,max,close</layout>`, every program tried got labwc's frame,
with the three buttons working: GTK 4 (the canary, a dialog), Qt 6
(GCompris), Chromium (hello-web) and X11 through XWayland (a Tk window).
None drew a frame of its own. Nothing had to be set in a program's
environment for it.

## The bar and the scale

The launcher's bar, `gtk4-layer-shell` along the bottom, is drawn over
every window, and a maximised window, the launcher's included, fills the
room above it (the exclusive zone). `wlr-randr --output <name> --scale
<n>` changes the scale at once; an X11 window is drawn at
1 and enlarged with the rest.

## The foreign-toplevel protocol from Python

`python3-pywayland` 0.4.18 binds `wlr-foreign-toplevel-management-
unstable-v1` version 3 once its XML is turned into Python by
`pywayland.scanner.Protocol` with an import map naming `wl_seat`,
`wl_output` and `wl_surface` as the core protocol's, and the generated
`from ..wayland import` lines rewritten to `from pywayland.protocol.wayland
import` (the command-line scanner wants `pkg-config`, and puts the module
beside pywayland's own). With it: every window's `app_id`, `title` and
states (maximised, minimised, activated, fullscreen) after each `done`;
`parent`, a dialog's window; and `activate` (which also brings back a
minimised window), `set_minimized`, `set_maximized`, `unset_maximized`,
`unset_fullscreen` and `close` all work, on the launcher's own window too.
A short-lived client that calls `disconnect` crashes in libwayland on the
way out; a long-lived one never disconnects, and the launcher is one.

The `app_id`s: the canary `org.kidux.tests.Canary`, the robin
`org.kidux.tests.Robin`, GCompris `org.kde.gcompris`, Chromium
`chrome-127.0.0.1__<id>_-Default` unless given `--class`, a Tk window its
class name, a GTK window made without an application `python3`.

## The lock, the idle dimming, the end

Locking with modules open freezes the session and continuing brings every
window back as it was; the first key after continuing reaches the
compositor. `swayidle` runs under labwc (it uses `ext-idle-notify`).
After log-out nothing of the child's is left, XWayland included.

## Memory

With the launcher, GCompris, hello-web, a GTK window and an X11 window
open at 1920x1080 in software rendering: `labwc` 134 MB resident,
`Xwayland` 65 MB while an X11 program is open. XWayland starts with the
first X11 program and ends ten seconds after the last
(`xwaylandPersistence` no). The 2 GB machine had 787 MB available.

## The background

labwc draws none. The launcher's window, maximised under every other, is
the floor; `swaybg -c '#fff6e9'` runs under labwc for the moment the
launcher is started again.
