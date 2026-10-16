# Phase 4d plan — a mailbox of the child's own, a door to Gmail, and the keyboard's light with the lid

A child's first email, in two modules an adult chooses between by the
family's provider: **Mail**, Thunderbird with the account an adult gives
on the panel, for Gmail, Outlook, iCloud and any provider that speaks
IMAP; and **Gmail**, a door to Gmail's website, for a family that prefers
the website as it is. And one fix the owner found on the MacBook: closing
the lid turns the screen off but leaves the keyboard lit. This plan is
how. It follows phase-4c-plan.md's rules (section 3 there) and D93: a
commit per step, partial tests while building, the battery once at the
end, every user-facing word through i18n in both languages, a package's
new version at its first change and `~dev` builds of it until the owner
tries the work and says yes.

Section 4 records what the owner decided on 2026-10-12, which the steps
follow.

## 1. Steps

| Step | What | Size |
|---|---|---|
| 4.21 | Found on the machine first: Thunderbird in a child's session, Gmail's hosts, the keyboard's light | M |
| 4.22 | Mail: Thunderbird as a module, the account from the panel, locked down | L |
| 4.23 | Gmail: a door to the website | S |
| 4.24 | The keyboard's light goes off with the lid, and comes back | S |
| 4.25 | Closing: the battery, the documents, the report | S |

## 2. The steps

### 4.21 — Found on the machine first

**Cause.** Three things this plan rests on are facts about Thunderbird,
Google and the MacBook, not about Kidux, and each is cheaper to try on
the test machine than to build around a guess. Nothing of 4.22 to 4.24
is written until these are known; what is found goes into the steps
below, and into the documents, as facts.

**Thunderbird in a child's session**, on the quick loop's machine
(`tests/run vm up 04`, `apt-get install thunderbird` there by hand), run
from a child's session as a module would run it, with
`XDG_CONFIG_HOME` set as the launcher sets it (launcher.md section 5):

1. **The policies file Debian's Thunderbird reads**: expected
   `/etc/thunderbird/policies/policies.json`, as Debian's Firefox reads
   `/etc/firefox-esr/policies/`; confirmed with a policy that shows
   (`DisableAppUpdate`, then *Help → About*), or found in
   `dpkg -L thunderbird` and the package's patches. Which policies 140 ESR
   knows (the Thunderbird policy templates of that version), of the list
   in 4.22, and whether `Preferences` accepts `mail.*` prefs.
2. **Its window's name under labwc**: the `app_id` the launcher sees
   (`toplevels:` in the launcher's log), expected `thunderbird`; and
   that it draws under Wayland (`MOZ_ENABLE_WAYLAND=1` is set by
   kidux-session) rather than through XWayland.
3. **An account seeded from `user.js`**: a profile made by hand with the
   prefs of 4.22 for an IMAP account on a made-up host, and whether
   Thunderbird starts on that account without its account setup, with
   the folder pane showing it; then a change made by hand in *Account
   Settings* and whether a fresh `user.js` at the next start reverts it.
   Also what Thunderbird does when `user.js` names no account: its setup
   window, which is what a child sees when no address was given.
4. **The password, once**: with a real IMAP account of the owner's, typed
   by hand on the machine and never written to any file (phase-4c-plan.md
   section 3), whether Thunderbird asks for the password at the first
   connection with *Use Password Manager to remember this password*
   offered, keeps it across restarts, and whether
   `DisableMasterPasswordCreation` keeps the primary password out of a
   child's reach.
5. **Gmail with OAuth**: with a Google account the owner gives for the
   try, typed by hand and never stored, whether Thunderbird's own sign-in
   to Google (`authMethod` 10, `oauth2`) opens Google's window inside the
   session, takes the second factor, and keeps the grant across restarts;
   and, if the owner can make one, **a Family Link account** (a child
   under 13): whether Google lets it authorise Thunderbird, with the
   parent's approval or not at all. If it cannot, the Mail module still
   serves every other account, and the Gmail module (4.23) is the way for
   a Family Link child: the user guide says so.
6. **Links and attachments**: where a link in a message goes (expected:
   Thunderbird asks the system for a browser, which is Chromium walled
   by the policy of D36 to the installed modules' hosts, which is a door
   this plan closes: a link must lead nowhere, as in every module, through
   a `Handlers` policy or a handler that does nothing, found here); and
   where an attachment is saved (`DefaultDownloadDirectory` or
   `browser.download.dir`, to the child's Downloads folder in their
   language, D76).
7. **Memory and start time** on the test machine, for `memory_max` and for
   the session test's patience.

**Gmail's hosts**, as 4.12 found CodeCombat's: Chromium's net log over
Gmail's front page, the sign-in, the inbox, opening a message, writing
one, an attachment, and signing out, from a `kidux-webapp` window; the
hosts that are Gmail's, each named as narrowly as the manifest's `hosts`
allows (`mail.google.com`, `accounts.google.com`, `ssl.gstatic.com` and
the like, never `google.com` whole, which would open Search, Drive and
Docs too), and the ones left out, with why. Also whether Google's sign-in
page takes the address from the URL (`login_hint`, `Email`, the account
chooser) so that the panel's `email` setting can fill it, and whether
Google's sign-in works at all in a Chromium under a managed policy with
`BrowserSignin` off (D36).

**The keyboard's light** on the owner's MacBook, by hand: the LED's name
under `/sys/class/leds/` (`kidux.hardware.keyboard_backlight` looks for
`*kbd_backlight*`), that `brightnessctl` can set it to 0 and back as the
child (group `video`, D61), and whether closing the lid changes it by
itself at all today (it does not, the owner found). Done by the owner at
the agent's request, since the test machines have no keyboard light.

**Tests.** None of Kidux's: this step finds facts. **Documents.** The
facts go into this plan's steps, replacing the expectations above.

### 4.22 — Mail: Thunderbird as a module

**Cause.** A child's first mailbox, with the account an adult gives and
nothing for the child to set up, break or add (section 4, decisions 1
to 4).

**The package** `kidux-module-mail`, as GCompris's (modules.md section
5): the manifest, the tile, its words, a program that starts Thunderbird
with the account in place, and Thunderbird's policies file. It depends
on `thunderbird` (140 ESR in trixie, Debian's own, with its security
updates), and ships nothing of Thunderbird's. Its name is *Mail*, in
Spanish *Correo*; its icon an envelope in the brand's style
(branding/README.md), drawn as the other modules' icons are.

**The manifest**:

```toml
id = "mail"
version = "0.1.0"
name = "Mail"
description = "A mailbox of the child's own, in Thunderbird, with the account an adult gives: Gmail, Outlook, iCloud or any provider."
min_age = 8
launch = { exec = "/usr/libexec/kidux-module-mail" }
app_ids = ["thunderbird"]              # as 4.21 found it
i18n_domain = "kidux-module-mail"
memory_max = "3G"                      # as 4.21 found it

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
2. **The servers**: the settings' `imap_host` and `smtp_host` when given;
   otherwise Mozilla's autoconfiguration database, the one Thunderbird's
   own setup uses, `https://autoconfig.thunderbird.net/v1.1/<domain>`,
   fetched with a short timeout and kept in the profile
   (`kidux-autoconfig.json`), so that a later start needs no network.
   Its XML gives the incoming server (type, host, port, socket type,
   authentication) and the outgoing one; `OAuth2` for Google and
   Microsoft, a password for the rest. Without an address, or with a
   domain the database does not know and no servers given, the program
   seeds no account and Thunderbird opens its own setup, which the guide
   says is the adult's to answer.
3. **`user.js`**, written afresh at every start from the settings, so
   that whatever a child changes in *Account Settings* is back the next
   time (section 4, decision 4): one account, one identity, one incoming
   server, one outgoing server, as 4.21 found the prefs to be, in the
   shape of

   ```
   user_pref("mail.accountmanager.accounts", "account1");
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
   user_pref("mail.smtpservers", "smtp1");
   user_pref("mail.smtp.defaultserver", "smtp1");
   user_pref("mail.smtpserver.smtp1.hostname", "<smtp host>");
   user_pref("mail.smtpserver.smtp1.port", 465);
   user_pref("mail.smtpserver.smtp1.try_ssl", 3);
   user_pref("mail.smtpserver.smtp1.username", "<email>");
   user_pref("mail.smtpserver.smtp1.authMethod", 3);
   ```

   and the prefs that keep Thunderbird quiet and small for a child: no
   start page (`mailnews.start_page.enabled` false), no offer of a new
   address (`mail.provider.enabled` false), no default-client question
   (`mail.shell.checkDefaultClient` false), no data reporting, no
   *What's new*, the three-pane view, and the download directory the
   child's Downloads folder in their language (`browser.download.dir`,
   from `user-dirs.dirs`, D76), as 4.21 found. Nothing else is written
   into the profile: what Thunderbird keeps there, the password among it,
   is Thunderbird's.
4. **`--print`** writes the `user.js` it would make to standard output and
   starts nothing: what the unit tests and the acceptance test read.

**The policies**, `/etc/thunderbird/policies/policies.json`, a conffile
of the package (the path as 4.21 found it; it binds every Thunderbird on
the machine, and the module's is the only one, as Chromium's policy is
D36's): no application updates (`DisableAppUpdate`, Debian's are the
updates), no extensions and no installing any (`ExtensionSettings`
`"*": blocked`, `InstallAddonsPermission`), no developer tools, no
`about:config`, `about:addons`, `about:profiles` or `about:support`, no
telemetry, no primary password a child could set and forget
(`DisableMasterPasswordCreation`), the password manager on and offering
to remember (`PasswordManagerEnabled`, `OfferToSaveLogins`), links in
messages leading nowhere (the way 4.21 found), and the download
directory where `user.js` says. What a policy cannot lock, the
rewritten `user.js` puts back.

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
a Family Link one, and what 4.21 found about it. What a child can and
cannot change. That links in messages lead nowhere, and attachments are
saved in the child's Downloads.

**Tests.** Unit: the `user.js` from each kind of setting (an address
with servers given; an address whose domain the autoconfiguration
answers with a password provider, and one it answers with OAuth2, from
saved answers of the database; no address), the profile's mode, and the
policies file read as JSON with every key above. Acceptance: the module
installs through the daemon with Thunderbird, the policies file is in
place and whole, and `kidux-module-mail --print` as a child with the
settings in its environment gives the account. Session
(`34-module-mail.py`): an adult sets Leo's address, name and both servers
(`127.0.0.1`, so that nothing leaves the machine) from the command line;
Leo opens the tile; Thunderbird's window comes up above the bar, named
as the manifest says, with the account in its folder pane and no setup
window, its picture taken (`module-mail` in `tests/lib/doc-screenshots.txt`);
the password prompt, if one comes, dismissed with Escape; Alt+F4 closes
it; the profile is Leo's, 0700, with the `user.js` the settings make; Leo
logs out and the daemon removes the module. In every language.

**Documents.** The user guide's section, in both languages; the READMEs'
list of modules; the website's modules (a card with its picture, its
section's anchor in both languages, D94's words untouched); modules.md
section 5, a program module that configures the program it runs;
architecture.md's decision (section 4); `tests/lib/doc-screenshots.txt`.

### 4.23 — Gmail: a door to the website

**Cause.** A family that uses Gmail as a website, or a child under
thirteen with a Family Link account that cannot authorise Thunderbird,
gets Gmail as it is, as CodeCombat and Wikipedia are doors (D85, D87).

**The package** `kidux-module-gmail`, as Wikipedia's: the manifest, the
tile (an envelope with a different colour, never Google's mark), its
words. `launch = { web = "https://mail.google.com/" }`, `hosts` the ones
4.21 found, each as narrow as the rule allows, `min_age = 8`,
`memory_max = "3G"`, the description saying it needs the internet and a
Google account, that an adult signs in with the child the first time,
and that Kidux is not connected with Google.

**Signing in** is Google's: the adult signs in with the child in the
module's window, with the second factor, and leaves *don't ask again on
this device* on; the module's Chromium profile keeps the session (D89),
and Google asks again only when it chooses to. Nothing of the daemon's
(the daemon could not sign in to Google, and section 4, decision 5, does
not ask it to). If 4.21 found that Google's sign-in page takes the
address from the URL, the manifest declares an `email` setting and the
module's `page_script` fills it in, with the non-secret settings handed
to page scripts as `window.KIDUX.settings` (a small change to
`kidux-webapp`'s `told()`, documented in modules.md); if it did not,
there is no setting.

**Tests.** Unit: the manifest reads as a door with its hosts. Acceptance:
as Wikipedia's, the policy allows its hosts while it is installed and no
longer after. Session (`35-module-gmail.py`): Leo opens the tile and
Google's sign-in page comes up above the bar, its picture taken
(`module-gmail`); nothing is typed into it; Alt+F4, log out, removed. In
every language.

**Documents.** The user guide's section (the account, Family Link under
thirteen, the first sign-in with the adult, that the session stays, and
that the site's own questions about cookies are the site's); the READMEs;
the website's card and anchor; architecture.md's decision.

### 4.24 — The keyboard's light goes off with the lid

**Cause.** On the MacBook, closing the lid turns the screen off and
locks the session (D61, D67), but the keyboard stays lit under the lid;
opening it should give back the light it had.

**Change.** `kidux.hardware` gains `keyboard_light_off()`, which reads the
keyboard's light (`keyboard_backlight`), remembers its percentage in the
session's runtime directory (`$XDG_RUNTIME_DIR/kidux/keyboard-light`,
beside the levels file of D61) and sets it to 0, and
`keyboard_light_back()`, which sets the remembered percentage again and
forgets it; both do nothing on a machine without a keyboard light, and
both touch the levels file, so that the corner's indicator follows. The
launcher's `lid.py` calls the first when the lid closes, after the panel
goes off, and the second when it opens, before the panel comes on;
`kidux-lid-watch` does the same on the trusted screens, under `cage`.
And `kidux-idle screen off` and `screen on` do the same, so that a
screen turned off for being left alone does not leave a lit keyboard
either; the owner may strike this last part out. The light is never put
back to more than it was, and a light that was already 0 stays 0.

**Tests.** Unit: `lid.py` with the screen and the light faked, closing
and opening, the lid's state at the start not a closing, a machine
without a light; `kidux.hardware`'s two functions against a fake `/sys`
and a fake runtime directory, the level remembered and forgotten. The
test machines have no keyboard light, so the session tests only check
that the launcher's log says nothing wrong; the owner tries it on the
MacBook, by hand, at the end. kidux-launcher, kidux-session and
kidux-common take new versions.

**Documents.** session.md section 5 and launcher.md section 5, which say
today that brightness and the light are left alone; keys.md if it says
so; architecture.md, a decision refining D61.

### 4.25 — Closing

The battery, once, detached, on the last commit; the roadmap; the final
message: what was built, what was found in 4.21 and decided from it, how
the owner tries each module on the MacBook, and what the owner has to
do for the release (D93: the owner tries the work, says yes, and the
release, the push, the promotion and the public archive follow on their
word).

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
