# Phase 4d plan — a mailbox of the child's own, a door to Gmail, and the keyboard's light with the lid

A child's first email, in two modules an adult chooses between by the
family's provider: **Mail**, Thunderbird with the account an adult gives
on the panel, for Gmail, Outlook, iCloud and any provider that speaks
IMAP; and **Gmail**, a door to Gmail's website, for a family that prefers
the website as it is, and for a child whose Google account is managed
with Family Link, which Google does not let sign in to Thunderbird. And
one fix the owner found on the MacBook: closing the lid turns the screen
off but leaves the keyboard lit. This plan is how. It follows phase-4c-plan.md's rules (section 3 there) and D93: a
commit per step, partial tests while building, the battery once at the
end, every user-facing word through i18n in both languages, a package's
new version at its first change and `~dev` builds of it until the owner
tries the work and says yes.

Section 4 records what the owner decided, on 2026-10-12 and, after
4.21, on 2026-10-15, which the steps follow.

## 1. Steps

| Step | What | Size |
|---|---|---|
| 4.21 | Found on the machine first: Thunderbird in a child's session, Gmail's hosts, the keyboard's light | M |
| 4.22 | Mail: Thunderbird as a module, the account from the panel, locked down | L |
| 4.23 | Gmail: a door to the website | S |
| 4.24 | The keyboard's light goes off with the lid, and comes back | S |
| 4.25 | Closing: the battery, the documents, the report | S |
| 4.26 | A bubble for a module's notices, in the child's screen | M |

## 2. The steps

### 4.21 — Found on the machine first

**Cause.** Three things this plan rests on are facts about Thunderbird,
Google and the MacBook, not about Kidux, and each was cheaper to try on
the test machine than to build around a guess. They were tried on the
quick loop's machine (`tests/run vm up 04`, `thunderbird` installed there
by hand), each program run from a child's session as a module runs it,
and on the MacBook for its light. What was found is below, and the steps
that follow are written from it.

**Thunderbird in a child's session** (Debian's 140.17 ESR):

1. **Its policies** are read from `/etc/thunderbird/policies/policies.json`
   (`browser.policies.applied` is true once a policy there takes). Version
   140 knows every policy step 4.22 names; the primary password's is
   `DisableMasterPasswordCreation`. `Preferences` takes, among others,
   prefs beginning `mail.`, `mailnews.`, `browser.`, `network.` and
   `signon.`, and can lock them.
2. **Its window** is `thunderbird`, drawn under Wayland, above the bar.
   It is up in about two seconds and holds about 370 MB with an empty
   mailbox.
3. **Its language** is the session's only with its language pack installed:
   without one, Thunderbird is in English for every child. Debian has one
   package a language, and `thunderbird-l10n-all` brings them all.
4. **An account seeded from `user.js`** comes up without Thunderbird's
   account setup, in the folder pane. Thunderbird connects to it at start
   only with `login_at_startup` and `check_new_mail` set on the incoming
   server. *Local Folders* has to be declared in `user.js` beside it, with
   its name, or Thunderbird makes a new one at every start: an account of
   type `none` of its own, named in the child's language.
   A `user.js` written afresh at every start puts the account list back,
   so that an account added by hand is gone at the next start.
5. **With no account in `user.js`**, only Local Folders, Thunderbird opens
   no setup window: it shows Local Folders' page, *Choose what to set up*,
   from which an account can be set up by hand, and which the next start
   forgets, as above. A bar along the bottom about Thunderbird's licence
   (*Know your rights*) is kept away with `mail.rights.version` 1.
6. **Links and attachments.** A link in a message, and an attachment of a
   kind Thunderbird does not know, offered *Choose another application…*, a
   chooser of any program on the machine. That door is closed with a
   `Handlers` policy that hands `http` and `https` to `/usr/bin/true`, so a
   link leads nowhere, and with `browser.download.forbid_open_with` and
   `network.protocol-handler.external-default` locked by the policy, so
   that an attachment offers only *Save File* and *Cancel*. It is saved in
   the folder `browser.download.dir` names, written in `user.js` from the
   child's `user-dirs.dirs` (D76): `/home/leo/Descargas` for Leo in Spanish.
   `mail.chat.enabled` locked off takes Chat out of the side bar.
7. **Google's sign-in from Thunderbird** (`authMethod` 10) opens Google's
   own window inside Thunderbird, in the child's language, with the address
   filled in. **A Family Link account cannot use it**: after the password,
   Google answers *Accounts managed with Family Link can't sign in here*.
   This is Google's rule, and nothing on the machine changes it. So Mail
   serves every account but a Family Link one, and Gmail (4.23) is the way
   for a Family Link child. The owner chose this on 2026-10-15
   (section 4, decision 7).
8. **A password account** was not tried: the owner has no IMAP account for
   the test, and tries one on the MacBook before the release.
9. **Mozilla's autoconfiguration database**
   (`https://autoconfig.thunderbird.net/v1.1/<domain>`) answers Gmail,
   Outlook, Hotmail, iCloud and Yahoo with their servers, `OAuth2` first
   for Google and Microsoft, and answers 404 for a domain it does not know.

**Gmail in Kidux's Chromium**, a throwaway module on the same machine:

1. **Signing in works**, with a Family Link account too: Google's page,
   in the child's language, takes the address, then the password, and
   asks no second step of a known account; the window goes on to the
   inbox. The session stays across closing the window and across logging
   out and in again, in the module's Chromium profile (D89).
2. **The address can be filled in from the URL**: Google's sign-in page,
   `https://accounts.google.com/ServiceLogin?service=mail&continue=…`, takes
   it as `Email=`, and with `Email=` empty it is the ordinary page with an
   empty field. So no page script is needed: the panel's `email` setting
   goes into the module's address.
3. **Signing in passes through the country's own Google**: on the way to
   the inbox Google calls `accounts.google.<the country's domain>`
   (`accounts.google.es` in Spain), and without it the sign-in stops on a
   blocked page. The country is the family's, so the module allows the
   `accounts.` host of every domain Google publishes as its own
   (`https://www.google.com/supported_domains`, 187 of them), and nothing
   else of those domains.
4. **Gmail's hosts**, from Chromium's net log over signing in, the inbox, a
   message with pictures, an attachment's preview, writing a message and
   signing out: `mail.google.com`, `accounts.google.com` and the country's
   `accounts.google.<domain>`, `apis.google.com`, `contacts.google.com`,
   `ogs.google.com` (the account's menu), `clients6.google.com` (new mail,
   contacts' suggestions), `ssl.gstatic.com`, `www.gstatic.com`,
   `fonts.gstatic.com`, `fonts.googleapis.com`, `lh3.google.com` and
   `lh3.googleusercontent.com` (pictures of people),
   `mail-attachment.googleusercontent.com` (an attachment's preview and its
   download) and `ci3` to `ci6.googleusercontent.com` (the pictures inside
   messages, which Google serves from these four). Left out, with all of
   Gmail working without them: `www.google.com`, which is Search, and only
   gave Gmail its icon and a script of Google's against abuse;
   `play.google.com`, which only took usage logs; `mail-ads.google.com`,
   the ads; `content.googleapis.com`, Drive's list of programs to open an
   attachment with; and the hosts Chromium calls by itself, which Kidux's
   policy keeps closed.

**The keyboard's light** on the owner's MacBook: the LED is
`/sys/class/leds/smc::kbd_backlight` (which `*kbd_backlight*` finds), at
most 255, in group `video` with mode 664, so the child's session sets it
to 0 and back; closing the lid leaves it as it is.

**Tests.** None of Kidux's: this step found facts. The accounts were typed
on the test machine only, and the machine was destroyed after.

### 4.22 — Mail: Thunderbird as a module

**Cause.** A child's first mailbox, with the account an adult gives and
nothing for the child to set up, break or add (section 4, decisions 1
to 4).

**The package** `kidux-module-mail`, as GCompris's (modules.md section
5): the manifest, the tile, its words, a program that starts Thunderbird
with the account in place, and Thunderbird's policies file. It depends
on `thunderbird` (140 ESR in trixie, Debian's own, with its security
updates) and on `thunderbird-l10n-all`, every language's pack, so that
Thunderbird speaks each child's language with no change to the package
when Kidux gains one (4.21); it ships nothing of Thunderbird's. Its name
is *Mail*, in Spanish *Correo*; its icon an envelope in the brand's style
(branding/README.md), drawn as the other modules' icons are.

**The manifest**:

```toml
id = "mail"
version = "0.1.0"
name = "Mail"
description = "A mailbox of the child's own, in Thunderbird, with the account an adult gives: Gmail, Outlook, iCloud or any provider. A Google account managed with Family Link cannot sign in to it; the Gmail module is for one."
min_age = 8
launch = { exec = "/usr/libexec/kidux-module-mail" }
app_ids = ["thunderbird"]
i18n_domain = "kidux-module-mail"
memory_max = "2G"

[[settings]]
key = "email"
kind = "text"
label = "Email address"
description = "The child's email address. Mail finds the provider's servers from it by itself."

[[settings]]
key = "name"
kind = "text"
label = "Name"
description = "The name the child's messages are sent as."

[[settings]]
key = "imap_host"
kind = "text"
label = "Incoming server"
description = "Only for a provider Mail cannot find by itself: its IMAP server, such as imap.example.org."

[[settings]]
key = "smtp_host"
kind = "text"
label = "Outgoing server"
description = "Only for a provider Mail cannot find by itself: its SMTP server, such as smtp.example.org."
```

No password among them (section 4, decision 2): the panel would hold a
secret nothing could use, since Thunderbird keeps passwords in a store
of its own that only it writes, and a Google or Microsoft account has
no password to give, only a sign-in.

**The program**, `/usr/libexec/kidux-module-mail`, Python, run by the
launcher as the child with the settings in `KIDUX_SETTING_<KEY>`
(D90):

1. **The profile** is `$XDG_CONFIG_HOME/thunderbird`, under the module's
   own configuration directory the launcher gives it,
   `~/.config/kidux/mail/` (D44), made with mode 0700. Thunderbird is
   started on it with `thunderbird --profile <dir> --no-remote`, so that
   no other profile of the child's is ever read.
2. **The servers**: the settings' `imap_host` and `smtp_host` when given,
   each a host, or a host and its port (`host:143` and `host:587` with
   STARTTLS, otherwise 993 and 465 with TLS), signed in to with a
   password; otherwise Mozilla's autoconfiguration database, the one Thunderbird's
   own setup uses, `https://autoconfig.thunderbird.net/v1.1/<domain>`,
   fetched with a short timeout and kept in the profile
   (`kidux-autoconfig.json`), so that a later start needs no network.
   Its XML gives the incoming server (type, host, port, socket type,
   authentication) and the outgoing one; `OAuth2` for Google and
   Microsoft, a password for the rest; the first of the database's
   incoming servers of type `imap`. Without an address, or with a domain
   the database does not know and no servers given, the program seeds no
   account: Thunderbird shows Local Folders' page, and what is set up by
   hand there is gone at the next start (4.21), so the guide says that
   the address, and the servers when Mail cannot find them, go on the
   panel.
3. **`user.js`**, written afresh at every start from the settings, so
   that whatever a child changes in *Account Settings* is back the next
   time (section 4, decision 4): one account, one identity, one incoming
   server, one outgoing server, and Local Folders beside them, named in
   the child's language through the module's catalogue (4.21), in the
   shape of

   ```
   user_pref("mail.accountmanager.accounts", "account1,account2");
   user_pref("mail.accountmanager.defaultaccount", "account1");
   user_pref("mail.account.account1.identities", "id1");
   user_pref("mail.account.account1.server", "server1");
   user_pref("mail.identity.id1.fullName", "<name>");
   user_pref("mail.identity.id1.useremail", "<email>");
   user_pref("mail.identity.id1.smtpServer", "smtp1");
   user_pref("mail.server.server1.type", "imap");
   user_pref("mail.server.server1.hostname", "<imap host>");
   user_pref("mail.server.server1.port", 993);
   user_pref("mail.server.server1.socketType", 3);
   user_pref("mail.server.server1.userName", "<email>");
   user_pref("mail.server.server1.authMethod", 3);   // 10 for OAuth2
   user_pref("mail.server.server1.name", "<email>");
   user_pref("mail.server.server1.login_at_startup", true);
   user_pref("mail.server.server1.check_new_mail", true);
   user_pref("mail.account.account2.server", "server2");
   user_pref("mail.accountmanager.localfoldersserver", "server2");
   user_pref("mail.server.server2.type", "none");
   user_pref("mail.server.server2.hostname", "Local Folders");
   user_pref("mail.server.server2.userName", "nobody");
   user_pref("mail.server.server2.name", "<Local Folders, translated>");
   user_pref("mail.smtpservers", "smtp1");
   user_pref("mail.smtp.defaultserver", "smtp1");
   user_pref("mail.smtpserver.smtp1.type", "smtp");
   user_pref("mail.smtpserver.smtp1.hostname", "<smtp host>");
   user_pref("mail.smtpserver.smtp1.port", 465);
   user_pref("mail.smtpserver.smtp1.try_ssl", 3);
   user_pref("mail.smtpserver.smtp1.username", "<email>");
   user_pref("mail.smtpserver.smtp1.authMethod", 3);
   ```

   and the prefs that keep Thunderbird quiet and small for a child: no
   start page (`mailnews.start_page.enabled` false), no offer of a new
   address (`mail.provider.enabled` false), no default-client question
   (`mail.shell.checkDefaultClient` false), no bar about the licence
   (`mail.rights.version` 1), no data reporting, and the download
   directory the child's Downloads folder in their language
   (`browser.download.dir` and `browser.download.folderList` 2, from
   `user-dirs.dirs`, D76). Without an account, only Local Folders and
   these. Nothing else is written
   into the profile: what Thunderbird keeps there, the password among it,
   is Thunderbird's.
4. **`--print`** writes the `user.js` it would make to standard output and
   starts nothing: what the unit tests and the acceptance test read.

**The policies**, `/etc/thunderbird/policies/policies.json`, a conffile
of the package (it binds every Thunderbird on the machine, and the
module's is the only one, as Chromium's policy is D36's): no application
updates (`DisableAppUpdate`, Debian's are the updates), no safe mode
(`DisableSafeMode`), no installing extensions (`InstallAddonsPermission`
with `Default` false, and `about:addons` blocked; not `ExtensionSettings`
with every extension blocked, since the language packs are extensions),
no developer tools, no `about:config`, `about:addons`, `about:profiles`
or `about:support`, no telemetry, no primary password a child could set
and forget (`DisableMasterPasswordCreation`), the password manager on and
offering to remember (`PasswordManagerEnabled`, `OfferToSaveLogins`),
links in messages leading nowhere (`Handlers`: `http` and `https` to
`/usr/bin/true`), and, locked through `Preferences`: no *Choose another
application* (`browser.download.forbid_open_with` true,
`network.protocol-handler.external-default` false), an attachment saved
in the download directory without being asked where
(`browser.download.useDownloadDir` true,
`browser.download.always_ask_before_handling_new_types` false), no
chat (`mail.chat.enabled` false), and never a notice of Thunderbird's
own, a window with no parent that the kiosk would show full screen: its
notices, a server that does not answer or new mail, go to the
desktop's notifications (`mail.biff.use_system_alert` true), which
Kidux's bubble shows (4.26). What a policy cannot lock, the rewritten
`user.js` puts back.

**The security of a shared machine**, as usual on Linux and nothing
more (section 4, decision 3): the profile is in the child's home, which
is the child's alone, under a directory of mode 0700; Thunderbird's
password store, `logins.json`, is encrypted with the key in that
profile's `key4.db`, so that another user of the machine, who cannot
read the home anyway, could not read it; nothing of it is held by the
daemon or shared between children. The daemon's rule that a secret
never reaches a child's session (D90) is for a secret the panel holds;
here the panel holds none, and the child's own mailbox password is the
child's, in the child's home, as every Linux mail client keeps it.

**The user guide's section** says what the adult does: install Mail,
switch it on for the child, give the address and the name in Mail's
*Settings* on the panel (and the servers only when Mail says it cannot
find them), then open Mail with the child the first time: for Gmail or
Outlook, Google's or Microsoft's own sign-in window appears, where the
adult signs in, with the second factor, once, and the account stays
signed in; for any other provider, Thunderbird asks the password once,
with *remember* ticked, and keeps it. Under thirteen, a Google account is
a Family Link one, which Google does not let sign in to Mail: the Gmail
module is for it. What a child can and cannot change. That links in
messages lead nowhere, and attachments are saved in the child's
Downloads.

**Tests.** Unit: the `user.js` from each kind of setting (an address
with servers given; an address whose domain the autoconfiguration
answers with a password provider, and one it answers with OAuth2, from
saved answers of the database; no address), the profile's mode, and the
policies file read as JSON with every key above. Acceptance: the module
installs through the daemon with Thunderbird, the policies file is in
place and whole, and `kidux-module-mail --print` as a child with the
settings in its environment gives the account
(`19-module-mail.sh`; the key's test, which has to be last, becomes
`20-no-key-no-archive.sh`, and `21-no-key-no-archive.sh` in 4.23).
Session (`34-module-mail.py`; the purge, which has to be last, becomes
`35-purge.py`, and `36-purge.py` in 4.23): an adult sets Leo's address, name and both servers
(`127.0.0.1`, so that nothing leaves the machine) from the command line;
Leo opens the tile; Thunderbird's window comes up above the bar, named
as the manifest says, with the account in its folder pane and no setup
window, its picture taken (`module-mail` in `tests/lib/doc-screenshots.txt`);
the password prompt, if one comes, dismissed with Escape; Alt+F4 closes
it; the profile is Leo's, 0700, with the `user.js` the settings make; Leo
logs out and the daemon removes the module. In every language.

**Documents.** The user guide's section, in both languages; the READMEs'
list of modules; modules.md section 5, a program module that configures
the program it runs; architecture.md's decision (section 4);
`tests/lib/doc-screenshots.txt`. The website's card (its picture, its
section's anchor in both languages, D94's words untouched) waits for its
picture: the site names only pictures that are in `docs/images/`, which
the release run alone writes (D93), and its project check stops the
battery over one that is not there. So the cards of Mail and Gmail are
one commit on a local branch, `site-mail-gmail`, which goes onto `main`
with the release's pictures, before the push.

### 4.23 — Gmail: a door to the website

**Cause.** A family that uses Gmail as a website, or a child under
thirteen with a Family Link account, which cannot sign in to Thunderbird
(4.21), gets Gmail as it is, as CodeCombat and Wikipedia are doors (D85,
D87).

**The package** `kidux-module-gmail`, as Wikipedia's: the manifest, the
tile (an envelope with a different colour, never Google's mark), its
words. Its address is Google's sign-in page for Gmail with the child's
address and language in it,
`https://accounts.google.com/ServiceLogin?service=mail&continue=https%3A%2F%2Fmail.google.com%2Fmail%2F&Email={email}&hl={lang}`,
which goes straight on to the inbox once the child is signed in (4.21);
`hosts` the ones 4.21 found, with the `accounts.` host of each of the 187
domains Google publishes as its own, written out in the manifest, with a
comment saying where the list comes from; `min_age = 8`,
`memory_max = "3G"`; the description saying it needs the internet and a
Google account, that it is the module for a Family Link account, that an
adult signs in with the child the first time, and that Kidux is not
connected with Google. Its window, opened on `accounts.google.com`, is
Chromium's `chrome-accounts.google.com__*`, which the launcher knows as
the module's from the address's host, as every door's.

One setting, the child's address:

```toml
[[settings]]
key = "email"
kind = "text"
label = "Email address"
description = "The child's Google account. Gmail's sign-in page opens with it filled in."
```

**A setting in a website's address.** `kidux-webapp` puts the value of
each of a module's settings, encoded for a URL, where its key stands in
braces in a `web` address, as it puts the language in `{lang}`; an empty
setting leaves an empty value, which Google's page takes as no address. A
secret never goes into an address: only the settings of kind `text`,
`integer`, `number` and `switch`. modules.md says so beside `{lang}`.

**Signing in** is Google's: the adult signs in with the child in the
module's window, with the second factor if Google asks for it; the
module's Chromium profile keeps the session (D89), and Google asks again
only when it chooses to. Nothing of the daemon's (the daemon could not
sign in to Google, and section 4, decision 5, does not ask it to).

**Tests.** Unit: the manifest reads as a door with its hosts and its
setting, the `accounts.` hosts among them; `kidux-webapp`'s address with
a setting, with an empty one, with one that needs encoding, and with a
secret left out. Acceptance (`20-module-gmail.sh`; the key's test becomes
`21-no-key-no-archive.sh`): as Wikipedia's, the policy allows its hosts
while it is installed and no longer after, and `kidux-webapp --print`
opens the sign-in page with the child's address and language in it.
Session (`35-module-gmail.py`; the purge becomes `36-purge.py`): an adult
sets Leo's address, a made-up one, from the command line; Leo opens the
tile and Google's sign-in page comes up above the bar with the address in
its field, its picture taken (`module-gmail`); nothing is typed into it;
Alt+F4, log out, removed. In every language. The address Chromium is given
is the acceptance test's to check: Chromium writes its own command line
over at 4096 bytes, and Gmail's list of hosts comes before it.

**Documents.** The user guide's section (the account, Family Link under
thirteen, the first sign-in with the adult, that the session stays, and
that the site's own questions about cookies are the site's); Mail's
section pointing a Family Link child here; the READMEs; modules.md (a
setting in a door's address); architecture.md's decision;
`tests/lib/doc-screenshots.txt`. The website's card and anchor go on the
local branch `site-mail-gmail` with Mail's (4.22).

### 4.24 — The keyboard's light goes off with the lid

**Cause.** On the MacBook, closing the lid turns the screen off and
locks the session (D61, D67), but the keyboard stays lit under the lid;
opening it should give back the light it had.

**Change.** `kidux.hardware` gains `keyboard_light_off()`, which reads the
keyboard's light (`keyboard_backlight`), remembers its level, in the
light's own steps, and sets it to 0, and `keyboard_light_back()`, which
sets the remembered level again and forgets it; both do nothing on a
machine without a keyboard light, and both touch the levels file of D61,
so that the corner's indicator follows. The level is remembered in
`/run/kidux-light/keyboard`, a directory `kidux-session` makes through
`tmpfiles.d`, root's, group `video`, mode 2770, and not in the session's
own runtime directory: a lid closed in a child's session locks it, and is
opened on the lock screen, which runs as `_greetd` and must find the
level to give it back; the child and `_greetd` are both in `video`. A
level already remembered is kept, since the screen may go off for the lid
and for being left alone at once; where it cannot be remembered, the
light is left on rather than turned off for good. The launcher's `lid.py`
calls the first when the lid closes, after the panel goes off, and the
second when it opens, before the panel comes on; `kidux-lid-watch` does
the same on the trusted screens, under `cage`. And `kidux-idle screen off`
and `screen on` do the same, so that a screen turned off for being left
alone does not leave a lit keyboard either, as the owner decided
(section 4, decision 12), except that `screen on` with the lid closed
leaves the light off, as it leaves the panel. The light is never put back to more than its
maximum, and a light that was already 0 stays 0.

**Tests.** Unit: `lid.py` with the screen and the light faked, closing
and opening, the lid's state at the start not a closing, a machine
without a light; `kidux.hardware`'s two functions against a fake `/sys`
and a fake directory to remember in, the level remembered, kept for a
second reason and forgotten, a light already off, one that cannot be
remembered. The test machines have no keyboard light, so the session
tests only check that nothing else changes. On the quick loop's machine,
once and by hand, a lid made through `uinput` and a light on a `tmpfs`
over `/sys/class/leds` take the whole way: the lid closed in Leo's
session, opened on the lock screen, and the screen left alone. The owner
tries it on the MacBook, by hand, at the end. kidux-launcher, kidux-session and
kidux-common take new versions.

**Documents.** session.md section 5 and launcher.md section 5, which say
what the lid and idleness do to the light; the user guide's section on a
laptop's keys and its lid, and on a session left alone, in both
languages; architecture.md, a decision refining D61. keys.md says nothing
of the lid.

### 4.25 — Closing

The battery, once, detached, on the last commit; the roadmap; the final
message: what was built, what was found in 4.21 and decided from it, how
the owner tries each module on the MacBook, and what the owner has to
do for the release (D93: the owner tries the work, says yes, and the
release, the push, the promotion and the public archive follow on their
word).

### 4.26 — A bubble for a module's notices

**Cause.** A program on Linux tells its user something through the
desktop's notifications (freedesktop.org's *Desktop Notifications*,
`org.freedesktop.Notifications` on the session's bus): Thunderbird a
server that does not answer, or new mail; any program something it has
done. A child's session had no one to show them, so Thunderbird showed its
own notice, a window of its own with no parent, which labwc maximised over
the whole screen and which neither Escape nor time closed; 4.22 kept it
away by silencing Thunderbird's notices, and so the reason a Family Link
mailbox stayed empty, Gmail's *IMAP access is not allowed for this
account*, showed nowhere. Kidux shows them itself now, as a bubble of its
own (section 4, decisions 8 to 11).

**Where.** In the launcher, which already draws the bar on
`gtk4-layer-shell` (1.0.4 in trixie) and speaks the child's language: it
owns `org.freedesktop.Notifications` on the child's session bus and draws
each notice as a bubble rising from the bar, above its right end, on the
overlay layer, over every module, taking no keyboard. So a bubble is only ever in
a child's session: the sign-in and lock screens run no launcher, and under
the lock the launcher is frozen with the session.

**A bubble** says who it is from, the module's name and tile when the
sender runs in a module's scope (its process's cgroup,
`kidux-module-<id>.scope`), the program's own name otherwise; the notice's
summary, and its text, plain. It has a close button; a click on it does
the notice's default action, when it has one, as Thunderbird's new mail
opens the message, and other actions are buttons with the program's own
words. It goes after eight seconds, or stays until it is closed when the
program marks it urgent or as never expiring, as an error is; several are
stacked, the newest nearest the bar. Never a sound: the server says it has
none, and takes no sound from a notice.

**The bell**, at the bar's right end, whatever is on screen: a button
that opens, above it, the last twenty notices that came, gone or not, the
newest first, each with who it is from, the time it came, its summary and
its text, so that a notice the child missed, or one an adult is asked
about, is read again; beside the bell, how many came since it was last
opened; *Clear* empties it (section 4, decision 13).
The launcher's own warnings that time is running out (launcher.md section
3) are bubbles from Kidux, with the mascot, staying until closed, each in
place of the one before; the bar keeps only the time left (decision 14).

**The server** answers `GetCapabilities` with `body` and `actions`,
`GetServerInformation` with Kidux's name and version, `Notify` with the
notice's number, replacing one when asked, `CloseNotification`, and sends
`NotificationClosed`, with why, and `ActionInvoked`. The journal says who
each notice is from and when it closes, never its words, which may be a
child's mail.

**Thunderbird** shows its notices through it: the policies no longer
silence them (`mail.suppressAlertsForTests` goes), and new mail, a
notice too, uses the desktop's notifications and never Thunderbird's own
window (`mail.biff.use_system_alert` locked true).

**Websites never notify** (section 4, decision 9): Chromium's policy
blocks every site's notifications (`DefaultNotificationsSetting` 2).

**Tests.** Unit, without a display: the server's answers, a notice's
number and its replacing, how long one stays, its actions, the module a
process belongs to from its cgroup, and the bell's history and count;
Chromium's policy. Session
(`34-module-mail.py`): Thunderbird's notice that 127.0.0.1 does not answer
comes up as a bubble from Mail, and as no window; a notice sent from Leo's
session with `gdbus`, urgent, stays until it is closed by its number; one
that is not goes by itself.

**Documents.** launcher.md, the bubble; modules.md, that a module tells
the child something through the desktop's notifications; the user guide,
the child's screen; architecture.md, a decision; the plan of 4.22 and its
section of the guide, which said Thunderbird's notices were silenced.

## 3. Rules for this plan

As phase-4c-plan.md section 3, and D93. No file, test or document holds a
real account: the owner's accounts for 4.21 are typed by hand on the
machine left up and nowhere else, and the machine is destroyed after.
Where 4.21 finds that something this plan expects is not so, the step is
rewritten to what is so before it is built, and the owner is told when
the difference changes what a module can do.

## 4. What the owner decided

Decided 2026-10-12 by the owner.

1. **Thunderbird is the mail client**, as a module called Mail, and no
   client of Kidux's own is written: it is the one client in Debian that
   signs in to Google and Microsoft by itself, without an application
   registered with either, and it works with every provider that speaks
   IMAP.
2. **The password is typed once in Thunderbird by the adult**, not held by
   the panel: Thunderbird keeps it, and Google and Microsoft accounts
   have no password to hold, only a sign-in.
3. **The security is Linux's usual for a shared machine**: the profile
   and its password store in the child's home, closed to every other
   user, as any mail client keeps them; nothing more and nothing less.
4. **The child cannot change what can be kept from changing**: the
   account is put back at every start, and Thunderbird's policies close
   what they can close.
5. **Gmail is a door module too**, for a family that wants the website,
   with the adult signing in with the child the first time.
6. **The keyboard's light goes off with the lid and comes back as it was.**

Decided 2026-10-15 by the owner, from what 4.21 found.

7. **Both modules, each for the accounts it can serve.** Google does not
   let a Family Link account sign in to Thunderbird. Mail is for every
   other account, Google's included; Gmail is the module for a Family
   Link child, and for a family that prefers the website. The modules'
   descriptions and the user guide say which to choose.

Decided 2026-10-15 by the owner, after the work of 4.21 to 4.24.

8. **Kidux shows a module's notices itself, as a bubble**, rather than a
   program's own window or silence: for Thunderbird, and for any module
   that tells the child something the same way. A bubble goes after eight
   seconds; an error, one its program marks urgent or never expiring,
   stays until it is closed.
9. **Websites never send notifications.**
10. **A notice never makes a sound.**
11. **A bubble is never shown on the sign-in or lock screens.**
12. **The keyboard's light goes off with the screen left alone too**, not
    only with the lid (4.24).

Decided 2026-10-16 by the owner, on the review of 4.26.

13. **The bubbles rise from the bar, and the bar keeps them.** A bubble
    stands on the bar at its right end, not in the screen's top corner,
    and a bell on the bar opens the notices that came, so that one that
    went by itself is read again.
14. **The warnings that time is running out are bubbles too**, from
    Kidux, and the bar keeps only the time left.
15. **A module installs and is removed in its own row of the Modules
    page**: the module being installed is among the installed ones from
    the moment Install is pressed, with its progress where its switches
    and buttons will be; Remove asks in the row; how it went is a toast,
    and nothing on the page moves.
16. **Removing a module purges what was installed for it alone** (D100).
17. **The page stays in the adult's hands while a module installs or is
    removed**: it scrolls, and Install and Remove pressed meanwhile wait
    their turn, each row saying so, and start one after the other. The
    question Remove asks takes the room of the row's switches and
    buttons and no wider, so that the page never changes width.
