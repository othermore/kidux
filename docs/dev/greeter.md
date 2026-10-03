# kidux-greeter

The sign-in screen and the lock screen: the two screens a child sees before and
between sessions, and the only two places an adult ever types the adult
password (D6). One program, `kidux-greeter`, run by greetd on terminal 7 as the
sign-in screen and by `kidux-locker@.service` on terminal 8 as the lock screen
(`--lock <child>`), always as `_greetd`, always under `cage`.

This document fixes the behaviour. How it looks is the owner's decision, set
out in section 8; nothing about the behaviour depends on it.

## 1. Shape

Two halves, so the half with the decisions can be tested without a screen:

```
kidux_greeter/
  flow.py       the state machine: which screen, what happens on each answer
  panel.py      the adult panel's and the first-run wizard's (panel.md)
  screen.py     what a state machine hands the view
  words.py      the sentences only these two screens say
  greetd.py     greetd's IPC: create, authenticate, start, cancel
  daemon.py     the calls it makes to kidux-daemon, behind a protocol
  laptop.py     a laptop's keys for the screen, its keyboard's light and
                the sound, which these screens answer themselves
  view.py       GTK 4 + libadwaita: draws what flow.py says, reports taps
  main.py       wiring, and the guard that never lets it crash (section 6)
```

`flow.py` knows nothing about GTK. It is given events — a child's avatar
tapped, a password submitted, a signal from the daemon — and answers with the
screen to show and the data to show on it. The tests drive it with a fake
daemon and a fake greetd, the way the daemon's own tests drive `access.py`.

Source package `kidux-greeter`, which `kidux-session` depends on.

Under `cage` no configuration binds a key, so every key reaches these
screens, and they answer a laptop's own keys for the screen's brightness,
its keyboard's light and the sound themselves (`laptop.py`, D61): the same
`XF86` keysyms a child's session binds in labwc (keys.md), matched by
their number, not by the name GTK gives them, through the same
`kidux.hardware.key`, before anything else looks at the key. The sign-in
screen's user, `_greetd`, is in `video`, which `kidux-session`'s
`postinst` gives it, and which `brightnessctl` needs to write the
backlight and the keyboard's light (session.md section 5); the sound there
may have no output, and then the key does nothing. `kidux-greeter`
depends on `brightnessctl` and `wireplumber`, the programs
`kidux.hardware.key` runs. The lid, on these screens, is
`kidux-lid-watch`'s (session.md section 5).

Over the top right of every screen, the sign-in screen, the password, the
lock screen, the adult's screens and the panel's pages, is the corner the
child's screen has (`kidux.corner`, D61): the battery, and the screen's
brightness, the keyboard's light and the sound as buttons with a slider,
each only when the machine has it. It is made once and kept across the
screens, since it watches a file and reads the machine on a timer, and
made again only when the language changes; it lies over the page in a
`Gtk.Overlay`, taking no room from it, so every screen still fits
1280x800, and on a machine with nothing to show there is nothing over the
page at all. On a screen narrower than 1200 logical pixels
(`kidux.screen.compact_corner`), where the full corner, about 380 pixels
wide, would reach the panel's tabs or the clock, it is compact: the icons
alone, the sliders still under them. It logs `hardware: …` as the
launcher's does, `compact` at the end when it is. A laptop's key here
refreshes it at once.

Every screen is the same frame: its content centred in the middle, and a
bottom row for Back, Turn off and the like. Every screen fits 1280x800
whole (section 8). Where one does not, on a smaller screen, at a larger
scale or with more than it was drawn for, the middle scrolls, down and
sideways, while the bottom row stays in view, and shows it (`kidux.scroll`,
D63): a scrollbar drawn for as long as there is more, and a shade along the
edge that has more. The greeter logs `the <screen> screen does not fit:
<n> pixels tall` (or `wide`), once each way. The box of Chromium's options
keeps its three lines and scrolls inside itself the same way.

## 2. The sign-in screen

```
                  starting ──(daemon unreachable)──▶ waiting ─┐
                     │                                  ▲     │ retry
                     │ no adult password yet            └─────┘
                     ├──────────────────────────▶ first-run wizard (panel.md)
                     ▼
     ┌────────────▶ choose ──── Adult ──────────▶ adult password ──▶ panel (panel.md)
     │                │  └───── power ──────────▶ power
     │                │ avatar
     │                ▼
     │            password ──(wrong)──▶ password, with "try again"
     │                │ right
     │                ▼
     │          CheckAccess
     │     allowed │   needs_adult │   blocked, day_off
     │             │               ▼         ▼
     │             │        adult grants ◀── time spent ("an adult can
     │             │           │ yes          give me more time")
     │             ▼           ▼
     │        start session, exit
     └──────────── Back / timeout ─────────── (from any child screen)
```

**Choose.** Every child's avatar and name, from `Children1.List`, in the
machine's default language and keyboard (`GetConfig`). An *Adult* button and a
*Turn off* button, each with a picture as well as a word, because the people
using this screen include children who cannot read yet.

**Password.** Tapping an avatar switches the whole screen to that child's
language before anything else happens, so two siblings with different
languages each meet their own. The keyboard layout stays the machine's (D29).
The child's picture and name, large, and a password field. When the password
is submitted, greetd is asked to `create_session` for the child, and its
`auth_message` of type `secret` is answered with what was typed.

- Wrong password: greetd says so after PAM's own three-second delay
  (`pam_faildelay`), and the screen says *That password is not right. Try
  again.* — never *wrong username or password*, never anything that sounds
  like the child did something bad. The field is cleared; the child is still
  on their own screen.
- Right password: greetd has authenticated but not started anything. Now,
  and only now, `CheckAccess(child)` decides (D10, daemon.md section 7). A
  wrong password and a spent allowance are therefore never the same message.

**Allowed.** `start_session` with the child's environment (D24):
`KIDUX_LANGUAGE`, `XKB_DEFAULT_LAYOUT`, `KIDUX_DISPLAY_SCALE`,
`KIDUX_AVATAR`, `KIDUX_WINDOWS=1` for a child with windows (D46), and command
`/usr/libexec/kidux-session`. Then the greeter **exits**: greetd starts the
session only once the greeter is gone, and `cage` ends with it.

**Needs adult** (`manual` mode, empty bank). *Ask an adult to unlock the
computer for you.* An adult types the adult password here — on the trusted
screen, which is the whole point — and picks how long: 15, 30 or 60 minutes,
or another number, with the child's time left (`Usage`) in view, so that the
adult knows what the child has and what they will have. `AuthoriseSession`;
then `CheckAccess` again, which now says `allowed`.

**Updating** (an update being installed, daemon.md section 13): the waiting
screen, saying so, which tries again by itself.

**Blocked** (`daily` mode, spent). *You have used all your time for today.
You can use it again tomorrow.* with a button *Ask an adult for more time*,
which leads to the same adult screen. On a day of the week an adult has not
ticked for the child (`day_off`, D54) the same screen says *The computer is
not for you today. An adult can give you time.*, and the button leads to
the same grant.

Escape is *Back* on every screen that has a *Back*, so everything works from
a keyboard without counting Tab presses.

Leaving any child screen — *Back*, or a minute without a touch — cancels the
greetd session (`cancel_session`) and returns to *Choose*, in the default
language again.

**Power.** *Turn off* and *Restart*, each asking once more ("Turn off the
computer?"), then `System1.Shutdown` or `Reboot`. The daemon's
`AttentionRequested` signal — the power button pressed with nobody signed in
— opens this same screen, so the power button never turns the machine off
without a screen that asks (D16).

**Adult.** The adult password, then the panel (panel.md). Leaving the panel
locks it at once (`Parental1.Lock`) rather than leaving the token to expire
(D26).

*Back* is in the bottom-left corner of every screen that has it, where
*Adult* is on *Choose*, and *Turn off* is in the bottom-right corner.

**Waiting.** If the daemon cannot be reached, *The computer is still
starting up. Wait a moment and try again.*, retrying on its own every few
seconds. The machine is always usable enough to turn off from here.

## 3. The lock screen

`kidux-greeter --lock <child>`, on terminal 8 over the child's frozen session.
In the child's language, because it is the child who is sitting in front of
it.

What it says depends on why it is up, which it learns from
`Access1.Usage(child)`: no time left means *Time is up*; time left means the
child or an adult locked it.

| Button | Asks for | Calls | Then |
|---|---|---|---|
| Continue | the child's password | `ContinueSession` | the daemon unlocks, the lock screen is stopped |
| Adult | the adult password, then one of three | `GrantExtraTime` then `ContinueSession`, `UnlockForSaving`, `EndSession` | unlocked, unlocked for a few minutes, or logged out |
| Log out | the child's password | `EndSession` | the session ends, the sign-in screen returns |
| Turn off | a confirmation | `System1.Shutdown` | |

The daemon's grant unlocks by itself only a session locked because its time
ran out. Locked by the power button or the *Lock* button, the session would
stay locked with more time on it, so after a grant the lock screen continues
it with the adult's password, which `ContinueSession` accepts.

`ContinueSession` with no time left answers `NoTimeLeft`, and the screen says
the day's time is used up and offers the adult route instead of the password
again.

Nothing on the lock screen ever needs the lock screen to close itself: the
daemon stops `kidux-locker@.service` when the session is unlocked or ends, and
the program is simply killed.

## 4. Languages at run time

`kidux.i18n` sets up one language when it is imported, which is right for the
launcher and wrong here: the sign-in screen changes language when a child is
tapped. So the greeter uses `kidux.i18n.translations(language)`, which returns
the catalogue for one language, keeps the current screen's, and redraws with
it. Every visible string still goes through the shared catalogue, and
`tests/project/i18n.sh` still refuses one that does not.

The words the lock screen and the panel share with it — *Try again*, *Back*,
*Restart*, *Turn off the computer?*, *Ask an adult for more time*, *How
long?*, and "{count} minutes" with its plural — are in `kidux.vocabulary`.
The sentences only these two screens say are in `kidux_greeter/words.py`.

## 5. What the daemon is asked

All as `_greetd`, which polkit's `screens` action allows (daemon.md section 2):

`GetConfig`, `IsPasswordSet`, `Children1.List`, `Access1.CheckAccess`,
`AuthoriseSession`, `GrantExtraTime`, `UnlockForSaving`, `ContinueSession`,
`EndSession`, `Usage`, `Parental1.Unlock`, `System1.Shutdown`, `Reboot`, and
the signals `AttentionRequested` and `ChildrenChanged` (redraw *Choose*).

## 6. Never a crash loop

greetd restarts a greeter that exits, and `kidux-session` has taken away the
limit on how often (session.md section 2). A greeter that crashes at start
would therefore flash forever. So `main.py` wraps everything: any exception
after the window exists shows a plain screen with *Try again* and *Turn off*;
any exception before it exists is logged and followed by a short sleep before
exiting, so a broken installation costs a restart every few seconds rather
than a busy loop. The sign-in screen exits on purpose in one case only:
after `start_session` succeeded.

## 7. Testing

- **flow.py**, unit tests with a fake daemon and a fake greetd: every arrow
  in section 2's diagram and every row of section 3's table, in both
  languages, plus the rule that matters most — there is no state a child can
  reach from which no button leads anywhere.
- **greetd.py** against a fake socket speaking greetd's framing: create,
  a wrong password, a right one, start, cancel.
- **The machine**: `tests/run session` (session.md section 8) uses both
  screens the way a child does, by keyboard — Enter on the picture that has
  the focus, the password typed key by key through QEMU's `sendkey` — and
  takes a picture of every screen on the way: choose, password, wrong
  password, the lock screen and its password, time spent, and the adult
  giving time. The pictures are what the owner reviews. The screen logs
  `showing <name>` when it starts to build a screen and `drawn <name>` once
  it has been painted, and the tests wait for the second before they press
  a key or take a picture.
- **What cannot be tested without a screen**: `view.py` and `main.py` need
  GTK and a display, so the machine run is their test.

## 8. The look

Settled with the owner; `view.py` applies it, and the launcher follows it.

1. **Typeface: Andika** (`fonts-sil-andika`, 6.200 in trixie), SIL's font
   designed for beginning readers: a single-storey *a*, and *I*, *l* and *1*
   that cannot be mistaken for one another.
2. **Size: everything fits 1280x800 whole**, in logical pixels, a common
   size for a laptop about ten years old, and one display scale, the
   machine's, reaches every screen (D49), automatic until an adult chooses
   one (D53, D56): the development MacBook's 2880x1800 panel, automatic, is
   1645x1028 at 1.75, roomy. Text is 20 px,
   titles 30 px, buttons at least 64 px tall, avatars 128 px, or 96 px where
   a screen shows more than the one child. The launcher keeps its bars
   smaller still, because the room between them belongs to the modules.
   `tests/session/13-every-screen-fits.py` fails if any screen the run shows
   has to scroll, but for the panel's pages of settings that grow, Advanced
   and a module's settings, which scroll where they do not fit (D92). On a screen with room to spare, 1600x960 logical pixels
   or more (`kidux.screen.roomy`), the screens keep their size and the room
   is space (D53); the window is marked `kidux-roomy`, and the launcher puts
   eight tiles to a row instead of six. Each program logs `screen
   <width>x<height>` when it starts.
3. **Colour:** a light, warm background, and each child's button tinted with
   the background colour of their own avatar, so the picture and the colour
   say the same thing.
4. **Choose:** the avatars centred, four to a row; *Adult* bottom-left,
   *Turn off* bottom-right, both small enough not to compete with the
   children.
5. **A clock on the sign-in screen**, large, top-centre, so a child can see it
   is not time yet.
6. **The words** in `packages/kidux-common/po/es.po` are corrected as the owner
   meets them while using the machine.
7. **The mouse pointer** stays: `cage` shows it in the middle of the screen,
   and a child with a mouse needs it.
8. **The adult panel** is dense, a form per page (D37, panel.md section 8),
   with *Give more time* above a child's form, since giving time is what an
   adult most often opens it for; the focus starts in the form, so an Enter
   pressed out of habit gives nobody time.
9. **A notice** is up to 60 characters wide, so a short sentence such as
   *That password is not right. Try again.* stays on one line.
10. **The logo** is large on the screens that welcome someone, the wizard's
    first step and *Choose*, and small in the bottom middle of every other
    screen of the greeter, the lock screen, the panel and the launcher,
    between the corner buttons, so that no screen is without it and it
    never covers what the screen is for. On *Choose* and the lock screen,
    *Kidux 0.2.3*, small, under it: `kidux-base`'s version, from
    `System1.Versions`, what an adult reads to know an update arrived.
