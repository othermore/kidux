# Phase 4c plan — settings an adult gives a module, CodeCombat signed in, a way back, and the pointer's speed

The owner's tries on the MacBook asked for four things the framework does
not have: settings an adult gives a module for each child (to turn off
BASIC's *Type it in for me*, and to give CodeCombat a child's account); a
CodeCombat that signs in by itself, in the child's language, and opens
where the playing starts; a way back and forward in a module that is a
door to a website; and a pointer and a two-finger scroll that are not too
fast on a MacBook's touchpad. This plan is how. It follows
phase-4b-plan.md's rules (section 3 there): a commit per step, partial
tests while building, the battery once at the end, every user-facing word
through i18n in both languages, a package's new version at its first
change and `~dev` builds of it until the owner confirms it (D93).

Section 4 records what the owner decided on 2026-10-03, which the steps
follow.

## 1. Steps

| Step | What | Size |
|---|---|---|
| 4.16 | Settings a module declares and an adult sets for each child; BASIC's *Type it in for me* the first | L |
| 4.17 | CodeCombat signs in by itself, with the child's account, in the child's language, at the play screen | M |
| 4.18 | A bar with Back and Forward over a website module's pages | S |
| 4.19 | The pointer's speed and the touchpad's scroll, set on the panel's Advanced page | M |
| 4.20 | Closing: the battery, the documents, the report | S |

## 2. The steps

### 4.16 — Module settings, per child

**Cause.** An adult wants BASIC's listings typed by the child, and a
child's CodeCombat account given once, not typed every time.

**The manifest** (`kidux.modules`, kidux-common): each module declares
its own settings and their kinds, and nothing outside the module lists
them; Kidux knows only the kinds. A list of tables,

```toml
[[settings]]
key = "type_in"                 # [a-z][a-z0-9_]{0,31}
kind = "switch"                 # switch | integer | number | text | secret
label = "Type it in for me"     # English, translated through i18n_domain
description = "A button under each program of the guide types it into the editor."
                                # what it does, required, translated the same way
default = true                  # of the kind; text and secret default to ""
min = 0                         # integer and number only, optional
max = 10                        # integer and number only, optional
```

read into `Module.settings`, a tuple of a small dataclass; a setting
whose table is wrong, which does not say what it does in a
`description`, or whose default is not of its kind, is dropped with a
line in the log, as `app_ids` is. The panel shows each setting's label
and, under it, its description, both in the adult's language.

**Where they are kept** (kidux-daemon): per child, in the child's state
directory the daemon already keeps, root's alone (`modules.toml`, a table
per module), so that a child can neither read another's nor change their
own. New D-Bus methods: `ModuleSettings(token, child, module)` and
`SetModuleSetting(token, child, module, key, value)` for the panel, with
the adult's token; and `MyModuleSettings(module)` for the child's own
session, which the daemon answers only for the caller's own uid and only
with every kind but a secret: a secret never reaches the child's
session (section 4, decision 1). Removing a module keeps its settings, as
it keeps its folders (D89).

**The panel** (kidux-greeter): on the Modules page, an installed module
that declares settings has *Settings* at the end of its row, before
*Remove*. It opens a page of its own: one column per child, the module's
settings down, a switch, a text box or a password box where they meet,
each saved when changed, as the module switches are: a switch for a
switch, a number box with its limits for an integer or a number, a text
box for text, and a password box for a secret, shown as dots and never
read back into it. The daemon refuses a value not of the setting's kind
or outside its limits, and the panel says so.

**Into the module** (kidux-launcher, kidux-webapps): the launcher asks
`MyModuleSettings` when a tile is opened and passes each as
`KIDUX_SETTING_<KEY>` in the module's scope; `kidux-webapp` adds them
to a web application's address, `?lang=es&type_in=0`, which is how
BASIC's page reads them.

**BASIC**: `type_in`, a switch, on by default. Off, the page draws no
*Type it in for me* button, and the guide's sentences about the button,
which a new convention `::: type-in` … `:::` marks, are not shown.

**Tests.** The reader's (a good `settings`, a wrong one dropped); the
daemon's (kept per child, a child cannot read another's, secrets never
in `MyModuleSettings`, an adult's token needed to set); the panel's (the
row's *Settings*, the page, saving); the launcher's (the environment);
`kidux-webapp`'s (the address); BASIC's (the page without the buttons
and the marked sentences when `type_in=0`). Session: a new test switches
BASIC's *Type it in for me* off for Leo and finds no button on the page.

**Documents.** modules.md section 1 (`settings`) and section 4; panel.md;
daemon.md (the methods); the user guide's panel section and BASIC's;
architecture.md, a decision for module settings.

### 4.17 — CodeCombat, signed in

**Cause.** A child should not have to type an email and a password, nor
change the site's language, nor find the play screen.

**The settings**: `email` (text) and `password` (secret), per child.

**How it starts.** `kidux-webapp` opens a page of the module's own first,
served by `kidux-webapps`: *Connecting to CodeCombat…*, in the child's
language, with the mascot. Meanwhile it signs in (section 4, decision 1), sets the
account's language to the child's, and then takes the window to the
play screen, `https://codecombat.com/play`. Chromium is started with
`--remote-debugging-pipe`, a pipe only `kidux-webapp` holds, never a
port: through it `kidux-webapp` gives Chromium the session's cookies and
moves the window to the site. The daemon already refuses that flag among
the machine's own. The pipe needs the policy's
`DeveloperToolsAvailability` at 1, and the tools' own pages stay blocked
by its `URLBlocklist` (D91).

**Signing in** is the daemon's (section 4, decision 1): it keeps the
password, root's alone, asks CodeCombat for a session over HTTPS when
the child's `kidux-webapp` asks it to through a new method,
`Modules1.SignIn(module)`, answered only for the caller's own uid, and
returns the session's cookie and nothing else. The daemon's unit opens no
internet socket, so the request runs in a transient unit of its own, a
dynamic user with no homes, given the account on its standard input.
CodeCombat refuses a request that does not say what sends it, so it says
`Kidux (https://kidux.org)`. What it sends where is
data in the module's manifest, not code: a `[sign_in]` table with the
`https://` address, which must be on one of the module's `hosts`, the
body to send with `{email}` and `{password}` where the settings go, and
the names of the cookies to hand back. The daemon makes that one
request and runs nothing of the module's, so that it knows nothing of
CodeCombat and no module's code runs as root.

**Setting the language and going to play** is a script of the module's,
`sign-in.js`, which `kidux-webapp` runs in the site's first page once
the cookies are in: it asks who is signed in and stores the child's
language in that account.

**When it cannot**: a wrong email or password, no internet, the site not
answering, no account set. The page says which, in a sentence a child
reads (*I could not sign in to CodeCombat. Ask an adult to check your
account.*), with *Try again*; nothing of the site is shown. No account set
says that the easiest is for an adult to put it on the panel, and offers
*Sign in myself*, which opens the site's own sign-in page, `manual` in
the manifest.

**Found on the machine first**, with the net log and the owner's test
account, never written to any file: the address CodeCombat signs in at,
what it answers to a good and a wrong password, the cookie it sets, how
its language is stored, and that `/play` opens the campaign signed in.
If signing in needs anything but an HTTPS request with the email and the
password (a captcha, a token from a page), the step stops and the owner
is told, with the options.

**Tests.** Unit: the start's states and the words of each failure, with
the site faked; the pipe's messages. Session: with no account set, the
front page as today. The quick loop: with the owner's test account,
typed into the panel by hand, the play screen in Spanish.

**Documents.** The user guide's CodeCombat section (the adult gives the
account on the panel); modules.md, a website module that signs in;
architecture.md's decision.

### 4.18 — Back and Forward on Wikipedia

**Cause.** An application window has no buttons to go back; a child does
not know Alt+Left.

**Change.** Something of the Wikipedia module's own (section 4, decision
4): its manifest names a script of its own, `page_script`, which
`kidux-webapp` starts Chromium with `--remote-debugging-pipe` to add to
every page the module shows, as 4.17's pipe; any other module may do the
same when it needs to. Wikipedia's script is a slim bar along the top
with *Back* and *Forward*, in the child's language and the brand's colours,
which go through the window's history and are dimmed where there is
nowhere to go. The bar pushes the page down by its own height rather
than covering it. Web applications Kidux serves itself, BASIC or
Scratch, get none: their pages have their own buttons.

**Considered and not chosen**: a bar for every website module, which
CodeCombat, with its own buttons, does not need; Back and Forward on the
launcher's bar, which would need the launcher to reach into another
program's window;
a Chromium extension, which every policy of D36 keeps closed.

**Tests.** Unit: the script the bar is, and its words. Session:
`33-module-wikipedia.py` goes back with the bar's *Back*, by keyboard,
where it now presses Alt+Left.

**Documents.** The user guide's introduction to section 9 and the
Wikipedia section.

### 4.19 — The pointer's speed and the touchpad's scroll

**Cause.** On the MacBook the two-finger scroll is too fast.

**Change.** The panel's *Advanced* page gains two settings for the
machine: *Pointer speed* (slower … faster, five steps) and *Scrolling
with two fingers* (slower … faster, five steps), applied when the next
session starts, so that the owner tries them on the MacBook and keeps
the one that feels right. The daemon keeps them in its configuration
and writes `/etc/kidux/input.xml`; the session puts them, at every start
of a child's session, in the `<libinput>` part of the `rc.xml` it gives
labwc with `-c`, written afresh in a directory of its own, beside Kidux's
configuration directory, `-C` (`pointerSpeed`, and `scrollFactor` for the
touchpad category), which labwc 0.8.3, in trixie, reads. The trusted
screens run under `cage`, which takes no such settings, and keep
libinput's own. The middle step is today's speed for the
pointer; for the touchpad's scroll, half of today's (section 4,
decision 3).

**Tests.** Unit: the daemon's settings and the file it writes; the
session's `rc.xml` with and without them. Session: the Advanced page's
picture with the two settings.

**Documents.** The user guide's Advanced section; session.md;
labwc-notes.md.

### 4.20 — Closing

The battery, once, detached; the pictures; the roadmap; the final
message: what was built, how to try each part on the MacBook, and
whether to push.

## 3. Rules for this plan

As phase-4b-plan.md section 3. In addition: no file, test or document
holds a real account; the owner's test account is typed by hand on the
machine left up and nowhere else.

## 4. What the owner decided

Decided 2026-10-03 by the owner.

1. **A child's CodeCombat password stays with the daemon**, which signs
   in and hands the child's session only the cookie that results: the
   password never reaches the child's session.
2. **Each module declares its own settings and their kinds**, a switch,
   an integer, a number, a text or a secret, and there is no central list
   of settings; *Type it in for me* is BASIC's alone.
3. **The touchpad's scroll defaults to half of today's**, and the owner
   tunes it on the panel on the MacBook once it is there.
4. **Back and Forward are the Wikipedia module's own**, not every website
   module's; another module may do the same when it needs to.
