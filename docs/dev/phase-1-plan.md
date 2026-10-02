# Phase 1 plan — Base system, access control and i18n foundation

Working plan for roadmap phase 1. Written 2026-09-22 against the state of the
development server (`kidux`, Debian 13.7, `/` 74 GB + `/home` 391 GB, 16 GB RAM,
KVM available) and the trixie archive on that date.

This document is a plan, not a decision record. Decisions taken while executing it go
to the decision log in [architecture.md](architecture.md).

## 1. Where we are

Phase 0 is complete:

- [x] Debian 13 installed on the MacBook Pro 2015 (`kidux`), partitioned as the
      architecture requires: separate `/` and `/home`.
- [x] SSH from the Mac, VS Code Remote-SSH, Claude Code authenticated on the server.
- [x] Public product name: **Kidux**, from *kid* + *tux*; see D19 in
      `architecture.md`.
- [x] The GitHub repository is `othermore/kidux`.

Steps 9.0 to 9.5 are done. `kidux` builds and signs packages, and a stock Debian VM
turns into a machine following the Kidux archive by installing them, in the language
each child is given. With `kidux-session` installed it boots through its own GRUB
entry into greetd with every door of session.md section 6 shut, a child's session
runs the launcher, and the power button locks it. How any of that is run is in
[packaging.md](packaging.md); the toolchain and the signing key are in
[dev-environment.md](dev-environment.md), section 5.

Steps 9.6a, 9.6b, 9.7 and 9.10 are done: the sign-in and lock screens, the
first-run wizard, the adult panel, the child's launcher and the boot splash,
every one used by keyboard in a VM by `tests/run session`, and the look of
every screen settled with the owner (greeter.md section 8, D30).
`ci/test-release.sh` runs every test in `tests/` and compares every screen
with the previous run; the owner has used the result himself through
`ci/vm/try.sh`. Step 9.7b made the panel a set of forms, one screen per
page, as the owner asked after using it, and put the logo on every screen;
step 9.8 put updates on the panel's system page.

Step 9.9 runs the same checks on GitHub Actions (D38), and step 9.12
brought every document in line with the built system. What remains of
phase 1 is 9.11, the rollout on `kidux`, which waits for the owner at the
keyboard and blocks nothing else (D31): phase 3 starts on the VM now
([phase-3-plan.md](phase-3-plan.md)).

## 2. Vocabulary

Four screens. Two of them are **trusted**: they run as the system user `_greetd` on
their own virtual terminal, out of reach of anything a child can run. The other two run
as the child.

| Screen | Runs as | What it is |
|---|---|---|
| **Sign-in screen** (the *greeter*) | `_greetd`, trusted | What the machine boots into. The children's avatars; each child enters with **their own password**. Depending on the child's access mode it starts their session, asks an adult to authorise it, or explains that the time is spent. Has the "Adult" button that opens the panel. |
| **Lock screen** (the *locker*) | `_greetd`, trusted | Appears over a running session when time is up, when the child presses "Lock", or when anyone presses the power button. The session underneath is frozen, not ended. Offers: *Continue* (child's password, if they have time), *Adult* (adult password: give time, unlock briefly to save, or log the child out), *Log out*, *Turn off*. |
| **Launcher** | the child | The child's screen once inside, and the only application their session runs: name, clock, remaining time, the grid of tiles for the modules enabled for them, a **Lock** button and a **Log out** button. A child opens and closes modules here all day and is never asked for a password. |
| **Panel** | `_greetd`, trusted | The adult's configuration screen, reached from the sign-in screen or the lock screen with the adult password. Three pages: Children, Modules, System. Modal: while it is open nothing else is reachable, and leaving it re-locks. |

Two rules that follow:

- **The adult password is only ever typed on a trusted screen.** Never inside a
  child's session, because everything inside that session runs as the child, and a
  child who can run code (phase 6 gives them Python on purpose) could show a fake
  prompt and capture it.
- **The adult password gates changing what a child may do; the child's own password
  gates being that child; neither is ever needed to use a module that is already
  enabled inside an allowed session.**

## 3. Definition of done for phase 1

On a machine running plain Debian 13 with our apt repository configured:

```
apt install kidux-base && reboot
```

produces a computer that:

1. Boots into the sign-in screen: no desktop, no terminal, no Debian text or logo
   after the firmware screen.
2. Cannot be left: no shell, no virtual-terminal switching, no SysRq, no Ctrl+Alt+Del,
   no GRUB editing without a password, and nothing reachable that the child's Unix
   user is not allowed to reach — that user is the security boundary (D17).
3. Gives every child their own account, password, avatar, language and keyboard; a
   child logs out and a sibling logs in.
4. Enforces one of three access modes per child — unlimited, daily limit, or
   adult-authorised time — with warnings before time runs out and a trusted lock
   screen when it does, from which an adult can give more time, let the child save,
   or log them out, and the child can continue tomorrow.
5. Shows an "Adult" button on the trusted screens that opens a panel where an adult
   can create and remove children, set each child's language, keyboard, password,
   avatar and access mode, toggle module switches, and trigger a system update.
6. Speaks Spanish or English per child, with no string hard-coded anywhere, both
   locales generated, and both catalogs complete.
7. Keeps everything it knows in `/home/.kidux/`, so reinstalling the system
   partition restores the same configuration *and* the same time accounting.
8. Was built entirely from this repository by a script that CI can run.

Not in phase 1: the ISO (phase 2), real modules and the module launch path (phase 3).
Phase 1 ships the framework's state, access control and UI, with an empty module list.

## 4. Decisions taken before starting

| # | Decision | Rationale |
|---|---|---|
| D1 | **Python 3 + PyGObject** for every component we write. | GTK4 4.18 and libadwaita 1.7 are in trixie with GObject introspection; `dh-python` packaging is standard; gettext is native. Iteration speed matters more than 0.3 s of start-up on the target hardware. Revisit only if measurements on a 2008 machine say otherwise. |
| D2 | **Local apt repository first.** `reprepro` on `kidux`, served by nginx on the LAN; GitHub Pages publishing moves to phase 2. | The GitHub repository is private, so Pages is not available; nothing about the package format or the client configuration changes when the archive later moves to a public URL. |
| D4 | **Test the kiosk and the hardening in a QEMU/KVM VM before installing on `kidux`.** | `kidux` is also the family's daily machine and the development server. A hardening mistake must not cost a USB recovery. |
| D5 | **An adult password, not a PIN.** Free-form text, no minimum length, no digits-only rule. | Forcing digits stops adults from using something they can actually remember. How strong it is, is the family's call; the panel advises and never blocks. |
| D6 | **The adult panel is modal, lives only on trusted screens, and dies on exit.** `Unlock(password)` gives a token that lives exactly as long as the panel is open. | The panel blocks the whole screen, so it cannot be left open unnoticed. It runs as `_greetd`, never inside the child's session (see section 7). |
| D7 | **"Exit to desktop" (`labwc`) is out of phase 1.** | A compositor is not a desktop: it would pull a launcher, a panel, a terminal, a file manager and a screen lock onto every installed machine, plus a second session type to harden. Configuration never needed it — that is what the panel is for. Revisit when a real adult asks. |
| D8 | **The adult is called "Adult" ("Adulto"), never "parent".** | Mothers, fathers, grandparents and teachers all use the same machine; "Adult" fits all of them and a six-year-old reads it without help. Applies to every user-visible string and the public documents. The D-Bus interface keeps the name `Parental1`: "parental controls" is the established term and the API is never seen by a user. |
| D9 | **Every child has their own password. Switching child is "one logs out, the other logs in".** | Gives every child real separation and makes the sign-in screen the single place where access rules are applied. |
| D10 | **The machine boots into our own greeter.** `greetd` runs `cage -- kidux-greeter`; the child's password is their **Unix** password and `greetd` does the PAM conversation. | Authentication that starts a session must be the system's, not ours, and the sign-in screen is then the single place where access rules are applied. |
| D11 | **Three access modes per child: `unlimited`, `daily`, `manual`.** Enforced by `kidux-daemon`, never by anything running as the child. | Enforcement lives in the privileged service because anything the child's session owns, the child can eventually kill. |
| D12 | **Time up = warn, then lock. A session is never ended by the system on its own.** Warnings at 10, 5 and 1 minute, then the trusted lock screen appears and the session is frozen underneath. From there an adult can give more time, unlock for a few minutes so the child can save, or log the child out; the child can continue when they have time again (tomorrow, in `daily` mode), or log out or turn off themselves. | Unsaved work is never destroyed by a timer, and a `daily` child who leaves the session locked overnight simply continues the next day. |
| D13 | **The daily counter counts wall-clock time while the session is unlocked**, no idle detection, reset at 04:00 local time. Locked time does not count. | Simple to implement and to explain to a child. The consequence must be said out loud to families: leaving the session unlocked over dinner spends the day's time. The launcher's "Lock" button is prominent for exactly this reason. |
| D14 | **Granted time is a bank, spent only by use.** In `manual` mode a grant lasts until it is spent, across sessions and days. In `daily` mode an extra grant is for today only and is lost at the 04:00 rollover. | What an adult gives should not evaporate because a child logged out early; but a daily limit is a daily limit. |
| D15 | **No lock-out on the adult password.** Every attempt is audited; nothing is delayed or blocked. | Choosing a password children cannot guess or see is the adult's responsibility. Because the password is only typed on trusted screens (D6), no child process can attempt it at all; only someone at the keyboard can. |
| D16 | **The power button and Ctrl+Alt+Escape always bring up the trusted lock screen**, handled by the daemon reading the input devices directly, not by the compositor. | This is the "secure attention" rule that makes D6 hold in practice: an adult presses the power button *before* typing their password, and whatever screen appears is real, because nothing the child runs can stop the daemon from switching to it. It also means the power button can never turn the machine off without a screen that asks. |
| D17 | **The child's Unix user is the security boundary, not the launcher.** Everything the child's uid can do, assume the child will do. | Phase 6 hands children arbitrary code execution by design (Python in Thonny), and any file write into the home directory is a potential foothold. The kiosk is a user-experience boundary; the privilege boundary is enforced by the kernel, PAM, polkit and the daemon. |

| D18 | **Accounts are named by whoever installs; our packages depend on groups, never on names.** The Adult of the interface is a password, not a Unix account (D6, D7). The administrator account is created by the installer under a name the family chooses. The only fixed identities are the system groups `kidux-admin` and `kidux-children` and the `_greetd` user. `kidux-firstboot.service` adds every human account that is in `sudo` to `kidux-admin`. | Shipping a fixed name such as `parent` would publish half a credential on every installation and gain nothing, since the installer asks for a name anyway. Depending on groups is what makes the packages work on a machine we have never seen. Adding the administrator at first boot rather than in `postinst` is required because during an image build that account does not exist yet; it cannot help a child, because the daemon never puts a child in `sudo`. |

These go to the decision log in `architecture.md` as the first action of step 9.0.
D5 and D8 also rename "PIN" and "parent" throughout the public documents; D10, D12,
D16 and D18 rewrite architecture sections 4 and 5. See step 9.0.

## 5. Packages built in this phase

Architecture section 3 lists the package set. Phase 1 builds seven source
packages, in the order `ci/build-all.sh` builds them:

| Package | Contents |
|---|---|
| `kidux-archive-keyring` | Our signing key in `/usr/share/keyrings/`, and the binary `kidux-apt-source` with the deb822 `/etc/apt/sources.list.d/kidux.sources` (D21). |
| `kidux-common` | Python library `kidux`: paths, state file I/O, i18n, the audit trail, the D-Bus client, the shared vocabulary, the avatars, the logo and the mascot. |
| `kidux-daemon` | System D-Bus service, polkit actions, first-boot unit, adult password, children, access policy, time accounting, the lock/unlock machinery and the secure-attention keys. |
| `kidux-greeter` | The sign-in screen, the lock screen (`--lock`), the first-run wizard and the adult panel: one program, run as `_greetd`. |
| `kidux-launcher` | The child's screen. |
| `kidux-session` | `greetd` configuration, the session wrapper, the locker service, `cage`, `wlr-randr`, `swayidle`, the boot splash, GRUB, and every hardening drop-in (logind, sysctl, sshd, getty, Ctrl+Alt+Delete, polkit rules). Split out so hardening can be installed, inspected and removed as one unit, which is what makes it safe to test. |
| `kidux-base` | Metapackage depending on the above plus kernel, firmware, fonts, `locales` with both locales generated, `unattended-upgrades` configured for our suite. |

All are Debian **native** packages (`3.0 (native)`), since we are upstream.
Source lives in `packages/<name>/` with `debian/` inside it; each package's
version is its newest changelog entry (packaging.md).

## 6. On-disk contract

Everything the daemon owns lives under `/home/.kidux/`, root-owned, group
`kidux-admin`, mode `0750`:

```
/home/.kidux/
  config.toml                 schema version, default language and keyboard (used by
                              the trusted screens), display scale, reset hour
  adults.toml                 argon2id adult password hash, GRUB recovery password
  state/
    audit.log                 every privileged action, every grant, every attempt
  children/
    <user>/
      profile.toml            display name, language, keyboard, age, avatar
      access.toml             mode, daily_minutes, granted bank (D14)
      usage.toml              last date seen, seconds used today, session state
      modules.toml            enabled = ["hello"]
```

Rules:

- The daemon is the only writer. No child can read the directory.
- `usage.toml` is flushed every 30 seconds while a session is unlocked, so a power
  cut, a crash or a deliberate reboot cannot reset a child's daily counter.
- Every file carries `schema_version`; the daemon refuses to start on a newer schema
  and migrates older ones on first boot.
- Written atomically (`tempfile` + `os.replace`).
- The child's password is **not** here: it is their Unix password, in `/etc/shadow`,
  set by the daemon through `chpasswd` (D10).
- The child's own work stays in `/home/<child>/`, untouched by us.

## 7. D-Bus API, version 1

Bus name `org.kidux.Daemon1` on the **system** bus, object `/org/kidux/Daemon1`.

**Security model.** Three gates, by purpose:

1. *PAM, through `greetd`*, decides who may start a session. The child's password is
   their Unix password; we never re-implement login (D10). Verified on trixie:
   `/etc/pam.d/greetd` includes `login`, which has no `pam_shells`, and `greetd` runs
   the session command through `sh -c`, so a child's `/usr/sbin/nologin` shell blocks
   terminals without blocking the graphical session. `login` also carries
   `pam_faildelay` (3 s per failed attempt) for free.
2. *polkit* decides which Unix users may call what. Members of `kidux-admin` may call
   everything. `_greetd` (the trusted screens) may call everything the greeter,
   locker, panel and wizard need. A member of `kidux-children` may call **only**
   `Access1.Usage` and `Modules1.List` about themselves, `Access1.Lock`, and
   `System1.Shutdown` / `Reboot`. Note that `kidux-admin` is *not* a polkit
   administrator group (that is `sudo`, per `50-default.rules`); our rules grant the
   daemon's actions explicitly, and no child is ever in `sudo`.
3. *The adult password* gates every change of configuration and every grant of time.
   `Unlock(password)` returns a token bound to the caller's unique bus name and uid,
   revoked by `Lock()`, by the panel closing or by the caller disconnecting (D6).
   Every privileged method takes that token as its first argument.

| Interface | Methods |
|---|---|
| `org.kidux.Daemon1` | `Ping() → s`, `GetConfig() → a{sv}` (default language and keyboard, display scale, reset hour, setup and language-chosen flags), `SetConfig(s token, a{sv} changes)`, property `Version`, signal `AttentionRequested(s source)` (the power button or Ctrl+Alt+Escape pressed while no child session exists) |
| `.Parental1` | `IsPasswordSet() → b`, `Unlock(s password) → s token`, `Lock(s token)`, `SetPassword(s token, s new_password)`, `GetRecoveryPassword(s token) → s` |
| `.Children1` | `List() → aa{sv}`, `Create(s token, s username, s display_name, s language, s keyboard, s avatar, s password)`, `Delete(s token, s username, b keep_home)`, `SetProfile(s token, s username, a{sv} changes)`, `SetChildPassword(s token, s username, s password)`, signal `ChildrenChanged()` |
| `.Access1` | `GetPolicy(s username) → a{sv}`, `SetPolicy(s token, s username, a{sv} policy)`, `Grant(s token, s username, u minutes)`, `CheckAccess(s username) → (s state, i seconds_available)` (`allowed`, `needs_adult`, `blocked` or `updating`), `AuthoriseSession(s adult_password, s username, u minutes) → b`, `GrantExtraTime(s adult_password, s username, u minutes) → b`, `Usage(s username) → (u used_today, i available)`, `Lock()`, `UnlockForSaving(s adult_password, u minutes) → b`, `ContinueSession(s username, s password) → b`, `EndSession(s username, s password) → b`, signals `TimeWarning(s username, u seconds_left)`, `Locked(s username, s reason)`, `Unlocked(s username)` |
| `.Modules1` | `List(s username) → aa{sv}`, `SetEnabled(s token, s username, s module_id, b enabled)`, signal `ModulesChanged(s username)` |
| `.System1` | `Shutdown()`, `Reboot()`, `CheckUpdates(s token)`, `ApplyUpdates(s token)`, `UpdateState() → (s job, d fraction, s package, s outcome, s detail, as packages)`, signals `UpdatesChecked(u count, as packages, s error)`, `UpdateProgress(d fraction, s package)`, `UpdateFinished(s outcome, s detail)` |

daemon.md is the design and is right where the two disagree; this table is
the summary.

Notes:

- `CheckAccess` returns `state` ∈ `allowed`, `needs_adult`, `blocked`, with the
  seconds the child may use now (or −1 for unlimited). The greeter calls it *after*
  the child's password is accepted, so a wrong password and a spent limit are never
  confused in the interface.
- Methods that take a password are callable only by `_greetd` (gate 2); the daemon
  never logs the password argument, only the outcome.
- `ContinueSession` and `EndSession` accept either the child's own password
  (verified through PAM by the daemon) or the adult password.
- `Shutdown` and `Reboot` need nothing: a child may always turn the computer off.
  Updates are only ever applied from the trusted screens while no child session
  exists, which is the only safe moment to replace what a session runs.
- `Modules1.List` returns one `{id, enabled}` per installed module, sorted
  by id, `enabled` for that child (daemon.md section 9); installing and
  removing modules is phase 3's step 3.4 ([phase-3-plan.md](phase-3-plan.md)).

Adult password rules (D5, D15): any non-empty string, argon2id (`python3-argon2`), no
lock-out, every attempt audited with its outcome. The panel shows a non-blocking
strength hint.

## 8. Access control, in detail

Per-child policy in `access.toml`:

```toml
schema_version = 1
mode = "daily"          # "unlimited" | "daily" | "manual"
daily_minutes = 60      # mode = "daily"
granted_seconds = 0     # the bank (D14): manual grants, or today's extra in daily mode
```

| Mode | At the sign-in screen | During the session |
|---|---|---|
| `unlimited` | Child's password, in. | Nothing to enforce. |
| `daily` | Child's password; the daemon computes today's remaining minutes plus today's extra grant. With time available, in. With none, the screen says so and offers "Ask an adult for more time": adult password plus minutes, added to today's bank only. | Warnings at 10, 5 and 1 minute; then lock (D12). |
| `manual` | Child's password; if the bank is empty, the screen asks for the adult password and a number of minutes. No adult, no session. If the bank still holds time from an earlier grant, in. | Same, against the bank. Whatever is not spent stays in the bank for another day. |

**The lock screen, step by step.** When time runs out, when the child presses "Lock",
or when someone presses the power button or Ctrl+Alt+Escape (D16), the daemon:

1. Starts `kidux-locker@<child>.service`: `cage` with `kidux-greeter --lock <child>` on
   virtual terminal 8, as `_greetd`, with a logind session of its own (the unit uses
   `PAMName=` and `TTYPath=`, the same mechanism `cage`'s own documentation gives for
   running it as a service).
2. Switches to that terminal (`org.freedesktop.login1.Seat.SwitchTo`). The child's
   compositor loses the display and the input devices; logind revokes them, the
   compositor cannot refuse.
3. Freezes the child's session scope (`systemctl freeze session-N.scope`), so nothing
   of the child's keeps running — no scripts, no music, no counting.
4. Stops the child's clock.

On *Continue* (child's password, time available), on *UnlockForSaving* (adult
password, a few minutes that are not charged to the child) or on a grant: thaw the
scope, switch back to terminal 7, restart the clock, stop the locker. On *Log out*
(child's or adult password) or *Turn off*: terminate the session (the launcher already
warned about unsaved work when the time warnings appeared), then let `greetd` show the
sign-in screen, or power off.

Enforcement facts that matter:

- **The daemon, not the launcher, holds the clock.** It learns about sessions from
  `systemd-logind` signals, so it keeps counting even if the launcher is killed.
- **The child cannot switch back to their session.** `/dev/tty*` is root-only, so the
  raw ioctl path is closed; and the polkit action `org.freedesktop.login1.chvt`, whose
  trixie default *allows* an inactive session to activate itself, is explicitly denied
  to `kidux-children` in our rules.
- **Rebooting does not reset anything** (`usage.toml` flushed every 30 s).
- **The day rolls over only when the calendar date is later** than the last one
  recorded in `usage.toml`; a clock that moves backwards never resets a counter, and a
  jump of more than one day in either direction is written to the audit log. Session
  and in-session accounting use the monotonic clock, so a clock change during a
  session changes nothing. A child cannot change the clock inside Linux
  (`timedate1.set-time` requires an administrator); a BIOS clock is what the firmware
  password in the install guide is for.
- **The day rolls over at 04:00**, not midnight, so an evening session is not cut in
  half by the calendar.
- **Grants are logged**, so an adult can see that they gave three extra half-hours
  this week.

## 9. Work plan

Each step ends in something installable and testable. Sizes are relative effort.

### 9.0 — Toolchain and phase-0 closure — S — **done 2026-09-22**

- Record D1–D17 in `architecture.md`; add `kidux-archive-keyring`, `kidux-common`
  and `kidux-session` to its package list; rewrite section 5 for D9–D17 and section
  4 for the new state files.
- Rename "PIN" → "adult password" and "parent" → "adult" (D5, D8) across `CLAUDE.md`,
  `architecture.md` and both halves of every public document: `README`,
  `REQUIREMENTS`, `ROADMAP`, `docs/en|es/install-guide.md`, each pair in one commit.
  The install guides currently promise a "4–8 digit PIN"; that wording goes.
- Add the access modes, the lock screen and the power-button rule to
  `REQUIREMENTS.md`/`.es.md` (new sections 3.1, 3.3 and 3.4): they are functional
  requirements.
- Install on `kidux`: `build-essential devscripts debhelper dh-python python3-all
  lintian sbuild mmdebstrap reprepro gnupg nginx qemu-system-x86 ovmf python3-pytest
  python3-dbusmock pamtester`.
- Build chroot with `mmdebstrap --mode=unshare --variant=buildd trixie` into
  `~/.cache/sbuild/trixie-amd64.tar` and use `sbuild --chroot-mode=unshare`: no root,
  no `schroot`, the same command in CI.
- Create the development signing key (ed25519), which signs the testing suite;
  its public part is `ci/archive/development-key.pgp`. The private key stays on
  `kidux` with an off-machine backup. The stable suite is signed with another
  key, the one `kidux-archive-keyring` holds (packaging.md, "Signing").
- Create the swap file the architecture asks for; this machine has none.

**Acceptance:** `sbuild --chroot-mode=unshare -d trixie` builds Debian's `hello`
source package.

### 9.1 — Packaging skeleton, local archive, `kidux-base` — M — **done 2026-09-22**

- `packages/` layout, `ci/build-package.sh`, `ci/build-all.sh`, `ci/publish-local.sh`.
- `reprepro` configuration in `ci/archive/`, suites `testing` and `stable`, component
  `main`, architectures `amd64 source`; root `/srv/kidux-apt`, nginx at
  `http://kidux.local/apt`.
- `kidux-archive-keyring`, and a real `kidux-base` whose `postinst` makes sure
  every shipped locale (`en_US.UTF-8`, `es_ES.UTF-8`) is in `/etc/locale.gen` and
  runs `locale-gen` — this machine only has `en_US` generated — and whose
  `unattended-upgrades` drop-in adds our `stable` suite to `Origins-Pattern`.

**Acceptance:** on a throwaway trixie VM, installing the keyring by hand then
`apt update && apt install kidux-base` works with the signature verified,
`locale -a` lists both locales, and `lintian` reports no errors.

### 9.2 — `kidux-common` and the i18n foundation — M — **done 2026-09-22**

- Python package `kidux`: `paths`, `state` (TOML via `tomllib` + `python3-tomli-w`,
  atomic writes, schema versions), `i18n`, `log`, `client`, `widgets`, and the
  shipped avatar set (SVG).
- `po/kidux/` with `kidux.pot` and `es.po`. English is the source language and has
  no catalog; Spanish is updated in the same commit as any string change.
- `ci/i18n-extract.sh` (xgettext over Python and `.ui` files) and `tests/project/i18n.sh`,
  which fails on untranslated or fuzzy entries, on a stale POT, and on a user-visible
  string that never passes through `_()`.
- `tests/project/content.py` for each module's `content/<lang>/`: every Spanish file carries the
  `source_sha256` of its English counterpart in its front matter; the linter fails on
  a missing file or a stale hash. Content-based, so a `git` checkout cannot produce a
  false failure the way file dates would.
- Linting with `pyflakes3` from trixie (`ruff` is not in the archive).

**Acceptance:** `pytest` green; `LANG=es_ES.UTF-8 python3 -c "from kidux.i18n import
_; print(_('Adult'))"` prints "Adulto"; `tests/project/i18n.sh` fails when a string is
added without translating it.

### 9.3 — `kidux-daemon`, core — M — **done 2026-09-22**

The design is [daemon.md](daemon.md); this is the order to build it in. Each
item ends green before the next starts, and each is its own commit.

1. Source package `kidux-daemon`, Python package `kiduxd`, `debian/` with the
   groups created in `postinst`, the unit of daemon.md section 14, the D-Bus
   policy and activation files, `/etc/pam.d/kidux`, and
   `data/org.kidux.Daemon1.xml` with every interface of section 7 including
   `GetConfig` and `AttentionRequested`. Builds and passes `lintian` with a
   daemon that only answers `Ping`.
2. `adults.py` and `tokens.py` (daemon.md sections 4, 5), unit-tested:
   hashing, verify, rehash, token issue, rebinding to another connection,
   expiry, revocation on name loss.
3. `gate.py` (section 2): polkit through dbusmock's `polkitd` template, and
   every one of the daemon's own checks as a test that tries to break it —
   a child asking about another child, a token from another connection, a
   `Delete` aimed at the administrator.
4. `children.py` (section 6) with `FakeAccounts` in tests and `SystemAccounts`
   in production: create, the rollback when a step fails, delete refused while
   a session is active, delete, profile changes, password change.
5. `firstboot.py` and `kidux-firstboot.service` (section 12).
6. `system.py`: `Shutdown` and `Reboot` through logind.

**Acceptance:** the integration suite of daemon.md section 17 is green for
everything above; in the VM, `busctl` from the administrator's SSH session
unlocks, creates a child and deletes it, `pamtester login <child> authenticate`
accepts the password that was set, and the audit log shows every step. The
package is published to `testing` and the acceptance run still passes.

### 9.4 — `kidux-daemon`, access control, time and the lock — L — **done 2026-09-22**

The part with the most ways to be quietly wrong, so it is its own step.
daemon.md sections 7, 8, 10 and 11.

1. `access.py` as pure functions over a fake clock, with every scenario listed
   in daemon.md section 7 as a test, **before** any of it is wired to D-Bus.
   Nothing else in this step starts until this is green.
2. `sessions.py` (section 8): logind tracking through dbusmock's `logind`
   template; the clock starts on `SessionNew`, stops on `SessionRemoved`, the
   30-second tick flushes, and a daemon restart resumes from `usage.toml`.
3. `CheckAccess`, `Usage`, `AuthoriseSession`, `GrantExtraTime`, `SetPolicy`,
   `GetPolicy` on the bus, with `TimeWarning` firing at each threshold once.
4. `locker.py` (section 10) against dbusmock's `systemd` and `logind`: the
   exact call order on lock and on unlock, and the fallback to `Terminate`
   when `SwitchTo` does not take. Ships `kidux-locker@.service` and its PAM
   file as part of `kidux-session` (9.5), so this item lands the daemon's half
   and 9.5 lands the unit.
5. `ContinueSession`, `UnlockForSaving` with its re-lock timer, `EndSession`,
   `Lock`, all audited.
6. `attention.py` (section 11) with a fake evdev device in tests: `KEY_POWER`
   locks, Ctrl+Alt+Escape locks, no session means `AttentionRequested`.
7. The adversarial VM run from daemon.md section 17, scripted in `ci/vm/`.

**Acceptance:** the scripted VM run passes end to end and the audit log read
back from it holds every event in order: warned, locked, granted, continued,
locked by request, continued the next day with a fresh allowance.

### 9.5 — `kidux-session`: greetd, cage, the locker unit and hardening — M — **done 2026-09-23**

The design is [session.md](session.md).

- The package: greetd pointed at Kidux's own configuration, the child's
  session wrapper, the lock screen's unit and PAM file, idle, and every door
  of session.md section 6 as a packaged file.
- GRUB (section 7): `09_kidux` and `90-kidux.cfg`.
- `tests/run session`: a machine of its own for the run, rebooted into
  Kidux and driven from outside — SSH for the administrator, the QEMU monitor
  for keys, the power button and pictures of the screen. A stand-in greeter
  signs a child in through greetd's IPC until the real one exists.
- Purging the package and rebooting gives Debian back; the run ends with it,
  which is also the proof that its Ctrl+Alt+F2 check can fail.
- `kidux-base` does not depend on `kidux-session` until `kidux-greeter`
  exists: without it greetd would restart a missing greeter forever.

**Acceptance:** session.md section 8, every step green in one command, and
`tests/run reproducible` green for every package. The two adversarial checks
of 9.4 that need keys pressed from outside the VM run here too: the power
button locks a child's session, and polkit refuses a child `chvt`.

### Running unattended

Every remaining step, and every step of the phases after this one, is built
without the owner present. Three rules apply:

- **Nothing is installed on `kidux` itself.** Every test runs in the VM (D4).
  Step 9.11 waits for the owner, at the keyboard.
- **The cycle is the cycle.** `ci/test-release.sh` (build, publish to
  testing, every test in `tests/`, every screen compared), then the commit,
  for every step; `ci/promote.sh` only when the owner says so. A step that
  cannot reach green is left as uncommitted work with a note in the commit
  message of the last green step saying exactly what failed, and the next
  step is not started on top of it.
- **What the screens look like is the owner's call.** Every step that adds a
  screen builds it in the look of greeter.md section 8, ends with pictures of
  it from `tests/run session`, and puts the pictures the user guide needs in
  `docs/images/` through `tests/lib/doc-screenshots.txt`. The owner looks at
  them, in the report or through `ci/vm/try.sh`, and says what to change.

### 9.6a — `kidux-greeter`: sign-in and lock screens — M — **done 2026-09-23**

The design is [greeter.md](greeter.md); how the screens look is its section 8.

- Avatar grid of all children, an "Adult" button and a power button. The keyboard
  layout and language come from `config.toml` until a child is chosen; tapping an
  avatar switches the screen to that child's language, so two siblings with different
  languages each see their own.
- Child password entry; on success, `CheckAccess` decides what happens next:
  `allowed` → start the session through the `greetd` IPC socket, then **exit** — the
  greeter must terminate for `greetd` to start the session, and `cage` exits with it;
  `needs_adult` → adult password plus minutes; `blocked` → "Your time for today is
  finished", with "Ask an adult for more time".
- `--lock <child>` mode: the same binary as the lock screen of section 8, with
  Continue, Adult, Log out, Turn off.
- Start-up is wrapped: any exception shows a minimal screen with "Turn off" and
  "Try again" rather than exiting, so `greetd` never sees a crash loop.
- Friendly, blame-free wording throughout: nothing here is the child's fault.

**Acceptance:** all three modes reach a session or a clear explanation, in both
languages, with no route that leaves a child stuck at a screen with no way forward;
the lock screen appears on the power button while a session runs and the session
continues intact afterwards.

### 9.6b — Panel and first-run wizard — M — **done 2026-09-23**

The design is [panel.md](panel.md). On the daemon's side: `SetConfig`,
`GetRecoveryPassword` and `Grant`, a client method for every call the panel
makes, and the adult password checked before PAM on the lock screen. The
panel's update action waits for step 9.8.

- **Panel** (after `Unlock`, from the sign-in or lock screen), three pages: *Children*
  (add, remove, name, avatar, language, keyboard, password, **access mode, daily
  minutes and the bank**, grant time), *Modules* (per-child switches; in phase 1 a
  placeholder explaining that modules arrive in phase 3), *System* (version, update
  check and apply with progress, GRUB recovery password, change the adult password,
  default language and keyboard, display scale). Modal; leaving re-locks (D6).
- **First-run wizard** when the daemon reports no adult password: choose the
  machine's default language and keyboard, set the adult password, create the first
  child with avatar, password and access mode. This is what makes a fresh install
  usable, and it lives here because a fresh install has no child to open a launcher
  for.

**Acceptance:** from a fresh install, an adult reaches a working child account without
a terminal, in either language.

### 9.7 — `kidux-launcher` — M — **done 2026-09-23**

The design is [launcher.md](launcher.md). `kidux-session` changes with it:
`session-inner` runs the launcher in the loop of launcher.md section 4, and
`greetd.toml` sets `source_profile = false`, so that nothing a child writes in
their own home directory changes how their session starts. A child's
`~/.profile` is theirs to write (D17); it must not be a way to replace the
launcher with something else, even as themselves.

- Large clock, child's name and avatar, the remaining time when the mode has a limit,
  the module grid read from `/usr/share/kidux/modules/*.toml` (empty in phase 1, so
  a friendly empty state), a prominent **Lock** button (D13), a **Log out** button
  with a "save your work first" confirmation, and a power button that simply calls
  `Access1.Lock` (the trusted lock screen has the real "Turn off").
- The 10/5/1-minute warnings as unobtrusive toasts saying to save; at zero the daemon
  locks, and the launcher has nothing to draw — the lock screen is not its job.
- **Accessibility and style:** every screen fits 1280x800 whole (D30), high
  contrast, full keyboard navigation, no text baked into images, and sizes in
  logical pixels, so the display scale makes them larger on a dense screen.
- **i18n:** every string through `_()`; `es.po` updated in the same commit.

**Acceptance:** the launcher survives the daemon restarting under it, and a locked
session resumes exactly where it was, including a module that was open.

### 9.7b — The panel as forms — M — **done 2026-09-24**

The panel is for adults, and the owner, having used it, wants it dense: one
screen per thing, where every option is changed in place, instead of a
sequence of screens each asking one question (D37). The children's screens
keep their look; the panel keeps the colours and the typeface and drops the
size.

1. **The look of the adult screens.** A second stylesheet class in `view.py`
   for the panel: 16 px text, 40 px buttons and rows, libadwaita's own
   widgets where they fit (`Adw.PreferencesGroup`, `Adw.EntryRow`,
   `Adw.PasswordEntryRow`, `Adw.ComboRow`, `Gtk.CheckButton` groups,
   `Gtk.Switch`), Kidux's colours over them. D30 holds: every page fits
   1280x800 whole, and `13-every-screen-fits.py` keeps checking it. Full
   keyboard use: Tab between fields, Enter saves, Escape closes without
   saving.
2. **Children.** One page: the children in a row of small pictures at the
   top, the selected one marked, *Add a child* at its end; below, the
   selected child's form, all of it at once:
   - name, an entry;
   - picture, the avatars in a row of small pictures, the current one
     marked;
   - language, a drop-down of the shipped languages; the keyboard follows
     it (panel.md section 3);
   - password, two entries, empty, changed only when both are filled;
   - how they may use the computer: the three modes as radio buttons, the
     daily minutes as a drop-down beside the daily one;
   - time today: used and left, as words, and *Give time*: 15, 30, 60
     minutes, acting at once, with the notice;
   - *Save* and *Remove*. *Save* sends every changed field in one go, one
     daemon call per field, and shows one notice; a field the daemon
     refuses is marked in place with the daemon's sentence and the rest is
     kept. *Remove* asks once, on the same page, with *Keep their files*
     as the alternative, and is a sentence rather than a button while the
     child has a session.
   *Add a child* is the same form, empty, with *Add* in place of *Save*:
   `Children1.Create` then `Access1.SetPolicy`, and the new child selected.
3. **The first-run wizard** keeps its steps for what needs them, language,
   keyboard and the adult password, and then shows the same child form for
   the first child, so that a machine's first child is added exactly as
   every later one.
4. **System.** One page: the version; *Look for updates* (step 9.8); the
   recovery password behind *Show*; the adult password change as three
   entries and *Save*; language and keyboard as two drop-downs, saved at
   once with the *applies at next start* notice; the display scale as
   radio buttons.
5. **Modules.** Stays a sentence until phase 3, whose step 3.1 builds it as
   one table: modules down, children across, a switch in each cell.
6. **`panel.py`.** The state machine loses the step screens
   (`panel_child_name`, `_picture`, `_language`, `_password`, `_access`,
   `_remove`, `panel_password`, `panel_language`, `panel_keyboard`,
   `new_child_*`): a page answers with everything its form needs, and one
   `save_child(username, changes)` and one `add_child(fields)` do the work;
   `ChildForm` goes. `PANEL_ACTIONS` and `WIZARD_ACTIONS` shrink to match,
   and the rule that every screen has a way forward still holds and is
   still tested.
7. **Tests.** Unit: `test_panel.py` rewritten for the forms: every field
   saved through the call the table in panel.md names, a refused field
   marked and the others kept, *Add* creating and selecting, the wizard's
   child step being the same form. Session: `03-first-start.py` fills the
   first child's form by keyboard; `09-child-session.py`'s panel visit
   selects a child, changes their picture and gives time from the one
   page; pictures `panel-children`, `panel-child` (the form) and
   `panel-system` replace the ones of the step screens in
   `tests/lib/doc-screenshots.txt`, and the user guide's section 8 and the
   first-start section say what the screen now is, in both languages.
8. **The logo on every screen** (greeter.md section 8 item 10): large on
   the wizard's first step and on *Choose*, as now; small in the bottom
   middle of every other screen of the greeter, the lock screen and the
   panel, where the launcher already has it, drawn by the same `_logo` in
   the frame that every screen shares, so that a new screen gets it
   without asking. `13-every-screen-fits.py` keeps every page whole with
   it, and the pictures of the run show it.
9. **Documents, same commit:** panel.md sections 2, 3 and 8, greeter.md
   section 8 item 8, `docs/images/`.

**Acceptance:** an adult adds a child, changes every one of their settings,
gives them time and removes them without leaving the *Children* page, by
keyboard alone as well as by mouse; every panel page fits 1280x800 and
shows the logo; the session run green.

### 9.8 — `System1` updates — M — **done 2026-09-24**

The panel's *System* page gets *Look for updates* and *Install*, so an adult
keeps the machine current without a terminal. daemon.md section 13 is the
design; this is the order to build it in, and what each item has to prove.

**How it works, in one paragraph.** The daemon never runs apt itself: its
unit has no network and a read-only system (section 14), and an update can
replace and restart the daemon half-way through. So every apt job runs in a
transient system unit, `kidux-update.service`, started through systemd's
`StartTransientUnit` and running `/usr/libexec/kidux-update <check|apply>`,
a script shipped by `kidux-daemon`. The script writes apt's own progress
(`APT::Status-Fd`) and its verdict to `/run/kidux/update.status`; the daemon
watches that file and turns it into signals. If the daemon is restarted by
the update, it finds the unit still running and the file still there when it
comes back, and carries on watching. The panel listens for the signals on
the bus name, so it survives the restart too; only its token dies with the
daemon, and the next thing the adult does asks for the password again.

1. **The script**, `bin/kidux-update`, tested with a fake apt on `PATH`:
   - `check`: `apt-get update`, then `apt-get -s dist-upgrade`, and writes
     `kidux:checked:<count>:<pkg1,pkg2,...>` or `kidux:failed:<one line>`.
   - `apply`: `dpkg --configure -a` (a power cut mid-update leaves dpkg to
     finish first), then `apt-get -y dist-upgrade` with
     `DEBIAN_FRONTEND=noninteractive`, `-o Dpkg::Options::=--force-confdef
     -o Dpkg::Options::=--force-confold` and `-o DPkg::Lock::Timeout=600` (so
     an `unattended-upgrades` run already holding the lock is waited for, not
     fought), `-o APT::Status-Fd=3` with fd 3 appended to the status file;
     then `kidux:done:updated`, `kidux:done:up-to-date`,
     `kidux:done:restart-needed` (when `/run/reboot-required` exists) or
     `kidux:failed:<one line>`.
   - It refuses to start while another `kidux-update` is running (the unit
     name is fixed, so systemd refuses for it: `Busy`).
2. **`updates.py`** in the daemon, pure: parses the status file into
   `(fraction, package)` from `pmstatus:` and `dlstatus:` lines, and the job
   state machine `idle → checking → applying → done/failed`. Every line
   format apt writes has a test.
3. **The daemon side.** `RuntimeDirectory=kidux` on `kidux-daemon.service`,
   so `/run/kidux` exists and is the daemon's to clean. `machine.py` gains
   `start_transient(name, argv)` and `unit_active(name)`. New methods, all
   `manage` class, all audited (`update check`, `update started`, `update
   finished` with the outcome):
   - `System1.CheckUpdates(token)`: starts `check`; refuses `Busy` while a
     job runs. Answers by signal: `UpdatesChecked(u count, as packages, s
     error)`.
   - `System1.ApplyUpdates(token)`: refuses `SessionActive` while any child
     session exists, locked or not (dpkg replacing the launcher or a module
     under a frozen session), and `Busy` while a job runs. Signals
     `UpdateProgress(d fraction, s package)` as the file grows and
     `UpdateFinished(s outcome, s detail)` at the end, outcome one of
     `updated`, `up-to-date`, `restart-needed`, `failed`.
   - `System1.UpdateState() → (s job, d fraction, s package, s outcome,
     s detail, as packages)`, `screens` class: the job, `idle`, `checking`
     or `applying`, and the last job's outcome, which the panel asks once a
     second while a job runs.
   - On start, if `/run/kidux/update.status` exists: the unit still active
     means keep watching; inactive means emit the verdict the file holds,
     once, and delete the file.
   - `Busy` is a new error name (daemon.md section 3).
4. **The panel.** *System* page: *Look for updates* → *Looking…* → either
   *Everything is up to date* or *N updates* with *Install*; then a progress
   bar with the package being installed; then *Done*, or *Restart to finish*
   with *Restart now* (`System1.Reboot`, which is safe: no child session
   exists), or the failure sentence with *Try again*. While a child has a
   session, *Install* is replaced by the sentence panel.md section 3 already
   promises. Strings in `words.py`, Spanish in `es.po`.
5. **Tests.**
   - Unit: item 2 entire; the refusals (`Busy`, `SessionActive`, a missing
     token); the reattach after a restart, with the file present and a fake
     machine saying the unit is active or not.
   - Integration, dbusmock `systemd`: `ApplyUpdates` calls
     `StartTransientUnit` with the unit name and the argv; a status file the
     test appends to drives `UpdateProgress`; the last line drives
     `UpdateFinished`.
   - Acceptance, `tests/acceptance/07-updates.py`, before 09 removes the
     archive key, on real apt: the test makes a package to
     update *without touching the real archive*: it builds
     `kidux-test-canary` 1.0 and 1.1 inside the VM with `dpkg-deb`, installs
     1.0, publishes 1.1 in a local file repository (`dpkg-scanpackages`, a
     `deb [trusted=yes] file:/var/tmp/canary ./` source), and `check-updates`
     now says one, named; `apply-updates` ends `updated` and `dpkg -s` shows
     1.1; with the child's session of `05-time-and-lock.py` open,
     `apply-updates` is refused with `SessionActive`; the audit trail holds
     the three lines.
   - Session, in `09-child-session.py`'s panel visit or a file of its own:
     *Look for updates* from the panel with pictures `panel-updates-none`,
     and, after the same canary is prepared over SSH, `panel-updates-found`,
     `panel-updates-progress` and `panel-updates-done`. The user guide's
     section 10 shows the found and done pictures
     (`tests/lib/doc-screenshots.txt`).
6. **Documents, same commit:** daemon.md sections 3, 13 and 14; panel.md
   section 3; the user guide section 10 in both languages; roadmap phase 1
   *Update action* ticked.

**Acceptance:** the acceptance and session runs above green;
`ci/test-release.sh` green; an update that restarts the daemon leaves the
panel showing its progress and finishing, and the audit trail complete.

### 9.9 — Continuous integration — M — **built 2026-09-24; its proof runs are read in the Actions tab**

GitHub Actions runs this machine's own commands, in a `debian:trixie`
container: `.github/workflows/tests.yml`, described in packaging.md,
"Continuous integration". Nothing is published from CI (D2): promotion stays
on the development machine, and GitHub Pages is phase 2.

**The jobs** (D38): `project`, `tests/run project`, on every push and pull
request; `build`, `ci/build-all.sh` with every package's unit tests and
lintian, on every pull request and every push to a branch other than
`main`; `release`, `ci/test-release.sh` whole with both test machines, by
hand, before a release (D39). The repository is private and its minutes are
few, and the development machine runs the whole battery before every commit
of a step anyway.

**What CI can never hold.** The archive signing key. `ci/setup-ci-host.sh`
makes a key for the run, `KIDUX_SIGNING_KEY` and `KIDUX_ARCHIVE_PUBLIC_KEY`
hand it to the publishing scripts and to sbuild, the archive carries its
public half as `extra-key.pgp`, and the test machines append that to the
keyring the bootstrap package installed. The workflow names no secret, and
`tests/project/scripts.sh` fails if one ever does.

**Checked here:** the scripts parse; a workflow with a secret fails the
check; publishing with a run's own key signs the archive with it and leaves
`ci/archive/conf` alone, and a keyring holding both keys verifies both
archives; the identity check also refuses the address of the change's
author, which is what it has to find in CI, where the machine is nobody's.
The development machine has no access to GitHub's API, so what the runs
themselves say is read in the repository's Actions tab.

**Acceptance:** a push to a branch that breaks a translation, a lintian
rule, or that names the author's address under `ci/`, fails; the three
branches `ci-proof-translation`, `ci-proof-lintian` and `ci-proof-identity`
are pushed for exactly that, and their runs are read in the Actions tab.

### 9.10 — VM test harness — S — **done 2026-09-23**

Built along the way rather than at the end, because every step from 9.1 needed
it: `tests/run acceptance` (a clean Debian installs the packages and checks
them from inside, including the access-control run of 9.4 on real logind
sessions), `tests/run session` (a machine rebooted into Kidux and driven
from outside, 9.5), `ci/vm/try.sh` (a Kidux machine to use, over VNC) and
`ci/vm/screenshot.sh`. All boot Debian's own cloud image under QEMU/KVM with
OVMF; pictures come from QEMU's monitor rather than from inside the
compositor. Phase 2 replaces them with the ISO smoke test.

Every test is a file in `tests/`, by kind (`tests/README.md`): the project's
own checks, each package's unit tests, the acceptance VM's checks and the
session VM's scenarios, one file each, run in order. The session scenarios
cover the first-run wizard, the panel, the launcher, time running out, unlock
to save, Ctrl+Alt+Escape, the daemon away, the idle return, a child's
`~/.profile`, the boot splash, and that the logo and mascot are actually on
screen. `ci/test-release.sh` runs all of it and compares every screen with the
previous run. What CI will run is the same command, step 9.9.

### 9.11 — Roll out on `kidux` — S

The runbook is [rollout.md](rollout.md), done by the owner at the keyboard,
whenever he chooses: it blocks nothing (D31), because the children's daily
use waits for phase 3's first module in any case. Install `kidux-base` from
the local `testing` suite, keeping the administrator account and SSH intact,
and verify the definition of done on real hardware: the Retina scale, the
AMD GPU path, and, the part no VM can prove, that switching between the
child's terminal and the lock screen works on the `radeon` driver. Retire the
interim lid watcher.

### 9.12 — Documentation — S — **done 2026-09-24**

A pass over every document against the built system, at the end of the
phase, with nothing left "to be written when it exists" for anything that
exists:

- `architecture.md`: sections 3, 4 and 5 say what the packages, the state
  directory and the session model are; the decision log holds D1 to D31 and
  whatever 9.8 and 9.9 add.
- `daemon.md`, `session.md`, `greeter.md`, `panel.md`, `launcher.md`,
  `packaging.md`, `layout.md`, `tests/README.md`: every file, unit, path and
  command they name exists under that name, checked by reading them next to
  `git ls-files` and an installed VM.
- The user guide, in both languages: every screen has its picture from the
  last green run (`tests/lib/doc-screenshots.txt`), the three access modes,
  the rule that unlocked time counts even with nobody at the keyboard, and
  the rule "press the power button before typing your password" are said
  plainly, and sections 2 and 9 stay empty until phase 2 and phase 3 fill
  them.
- `README.md` and `README.es.md` in step with the guide.
- `roadmap.md`: phase 1 ticked, and the order of phases 2 and 3 as D31 says.

**Acceptance:** `tests/run project` green (translations, content, scripts,
versions, branding), and a reading of each document against the machine
finds nothing that is not there.

## 10. Risks

| Risk | Mitigation |
|---|---|
| Hardening locks the family out of their own machine. | VM first (D4); SSH untouched; `kidux-session` removable as one package; the GRUB recovery password is written to `/home/.kidux/` before hardening is applied. |
| Time limits are the feature a child will attack hardest. | Enforcement in the daemon, sessions tracked through logind, counter flushed every 30 s, no clock access, `chvt` denied, `ptrace` restricted, no shell, no SSH; every grant audited. Step 9.4 tests each attack explicitly. |
| A child with code execution fakes an adult prompt. | The adult password is only ever typed on trusted screens (D6), and the power button always reaches a real one (D16). The install guide teaches the rule. |
| Switching virtual terminals between two compositors misbehaves on some GPU. | Standard logind mechanism (every "switch user" on a desktop does it); verified on `radeon` in 9.11; if a driver fails, the fallback is to end the session at time-up, which loses only comfort, not safety. |
| D13 means a session left unlocked over dinner spends the day's time. | Accepted deliberately; the launcher shows remaining time and a prominent "Lock"; the install guide says it plainly. |
| No lock-out on the adult password (D15). | Only someone at the keyboard can try; every attempt is audited; the panel's strength hint. Accepted by the owner. |
| `greetd` stops after five greeter crashes. | `StartLimitIntervalSec=0` drop-in and a greeter that never exits on an exception. |
| A child powers off while the owner builds over SSH (`power-off-multiple-sessions` is allowed by default). | Correct on a family machine; on the dev machine, `systemd-inhibit` around long builds. |
| Retina panel unreadable at 2880x1800. | `wlr-randr --scale` in the session wrapper and the locker unit; layout driven by scale. |
| `cage` 0.2 and `sway` 1.10, both on `wlroots` 0.18, on GCN 1.0 (`radeon`). | Step 9.11 on the real GPU; the install guide already documents the `amdgpu` fallback. |
| Phase 1 grew: a greeter, a lock screen and an access-control engine. | If it needs shortening, ship `unlimited` first: 9.6a alone already allows dogfooding; `daily` and `manual` fill in behind the same hooks. |
