# Requirements

## 1. Vision

A Debian-based operating system that anyone can install on a modest or old computer
to make it a child's first computer. It boots into a safe, restricted kiosk mode by
default and lets an adult enable learning modules progressively from a control panel
protected by a password. It is bilingual (English and Spanish) from the first release
and built so that any further language is a translation, not a development task.

## 2. User profiles

- **Child (end user):** a limited session with no access to system settings; sees only
  the modules an adult has enabled. Several children can share one machine, each with
  their own account, password, language and progress.
- **Adult (administrator):** a mother, father, grandparent, teacher or any other adult
  responsible for the machine. Enters a password-protected management mode to enable or
  disable modules, add children, set how much time each child may use the computer,
  update the system, and later adjust web browsing restrictions and review progress.
  This is not a separate desktop session: it is a panel reached from the sign-in or
  lock screen.

## 3. Functional requirements

### 3.1 Sign-in and sessions
- The machine boots into a sign-in screen showing each child's avatar. There is no
  automatic login.
- Each child has their own account and their own password, and their own language,
  keyboard, avatar and settings.
- Children take turns by one logging out and the next logging in.
- The adult password is never typed inside a child's session. It is only ever accepted
  on the sign-in screen and on the lock screen, which a child's session can neither
  reach nor imitate.

### 3.2 Restricted mode (kiosk)
- The child's session opens straight into the module launcher, with a bar to move
  between the modules that are open; several may be open at once, and the files a
  child makes in one are there for the others. No terminal, file manager or system
  settings are reachable.
- Dangerous key combinations (virtual terminal switching, session kill, magic SysRq,
  Ctrl+Alt+Del) are disabled.
- A child can never reach anything their own account is not allowed to reach. The
  restriction is enforced by the system itself, not only by the launcher.
- The child can power the machine off and on without help.

### 3.3 Access control and time limits
- Each child is in one of three modes, chosen by an adult: **unlimited**, a **daily
  limit** in minutes, or **adult-authorised**, where an adult grants time case by case.
- Unlimited and daily-limit access apply on the days of the week an adult chooses,
  every day unless they choose otherwise. On the other days the child has only the
  time an adult gives that day.
- Time counts while the session is unlocked, whether or not the child is actually using
  the computer, and stops while the session is locked. The daily allowance resets in
  the early morning rather than at midnight, so an evening session is not cut in half.
- Extra time given by an adult is a credit that is only spent by use. Under a daily
  limit it expires with the day; under adult-authorised access it lasts until it is
  used.
- The child is warned, in good time, before their time runs out.
- **When the time runs out the session is locked, never closed.** Nothing the child was
  doing is lost. From the lock screen an adult can give more time, unlock the machine
  briefly so the child can save their work, or log the child out; the child can carry
  on when they have time again.
- The child can lock the session themselves at any moment, and that is the normal way
  to step away without spending time.
- Pressing the power button always brings up the lock screen instead of switching the
  machine off, so an adult always reaches a genuine screen before typing a password.
- Time already spent survives a restart, a power cut and a crash.

### 3.4 Adult panel
- Reached from the sign-in screen or from the lock screen with the adult password. It
  never opens inside a child's session.
- The adult password is free text chosen by the family: no minimum length, no
  digits-only rule. The panel advises on how strong it is but never refuses a choice,
  and never locks anyone out after failed attempts. Every attempt is recorded.
- Create and remove children; set each child's name, avatar, password, language and
  keyboard.
- Set each child's access mode, daily minutes and days of the week, and grant extra
  time.
- Enable or disable modules per child.
- Install available updates with one action.
- Set each child's time left for today, zero included.
- An *Advanced* section on the System page for the settings that depend on
  the machine's hardware — Chromium's flags for its graphics first — each with
  a default that works on most machines and a plain explanation, so that
  whoever installs Kidux on their own computer can make it work there
  without touching a file.
- Closing the panel locks it again; it cannot be left open by accident.
- (Future) configure web browsing restriction levels.
- (Future) view each child's activity and progress per module.

### 3.5 Module framework
- One common way to install, enable, launch and isolate every learning module; an
  enabled or disabled module never affects another one.
- Every module (Scratch, micro:bit, the Python course, …) is an independent unit that
  an adult can install, enable, disable or uninstall on its own, even when several
  modules share internal infrastructure such as the local web-app server.
- Each module declares: name, icon, recommended age range, the modules best done
  before it, dependencies and its translation catalog. The age range and the modules
  first are advice the panel shows, never a rule. Whether a module opens the web is what the module is, and
  an adult enables it or not.
- Modules are added as packages without changing the core system.

### 3.6 Modules, first wave
- **Early learning:** GCompris activities for the youngest children.
- **Typing:** a guided typing course for children.
- **Scratch:** the official Scratch 3 editor, served locally and working offline.
- **Electronics with micro:bit:** several guided, progressive projects (light an LED,
  sensors, radio, …) with the official MakeCode (blocks) and micro:bit Python
  editors served locally and working offline, including their simulators.
- **CodeCombat:** optional online module (real Python/JavaScript, free first world,
  subscription for the rest) for families who want it.
- **AI learning:** guided projects in which the child configures and uses AI agents
  in a controlled and safe way through an adult-managed gateway.
- **Python:** our own course in a real editor (Thonny): turtle graphics, then games
  with Pygame Zero, then micro:bit; progressive projects with automatic feedback. This
  is the main road from blocks to real Python.

### 3.7 Future modules (out of scope now, but the framework must allow them)
- **Graded web browsing:** unrestricted, site allow-list, or category block-list,
  chosen by an adult.
- **Linux system administration:** an educational module on the terminal and basic
  administration.

## 4. Non-functional requirements

- **Public distribution:** a downloadable ISO with a graphical, translated installer
  that an adult can complete without Linux knowledge, on UEFI and legacy BIOS machines.
- **Upgradable without data loss:** security updates are automatic; feature updates
  and Debian major-version upgrades are offered from the panel; a reinstall from the
  ISO can keep all children's data and the adults' configuration. User data lives on
  its own partition.
- **Lightness:** runs on any 64-bit x86 computer from about 2008 with 2 GB of RAM
  (4 GB recommended) and 32 GB of disk.
- **Reproducibility:** everything on the installed system comes from Debian packages
  or from packages built from this repository; the image is produced by versioned
  `live-build` scripts, never by cloning a disk.
- **Security and isolation:** the child cannot escalate privileges or leave the kiosk;
  changing what a child may do requires the adult password, which is only ever accepted
  on a screen the child's session cannot imitate; modules run isolated from each
  other.
- **Internationalization:** English and Spanish shipped together with full parity in
  interface, installer, content and documentation; every user-visible string goes
  through the i18n layer; adding a language requires only translation files.
- **Accessibility:** contrast, text size and input targets suitable for young
  children.
- **Identity:** Kidux's logo is large on the screens that welcome someone,
  the first start and the sign-in screen, and small in a corner of every
  other screen where it does not get in the way of what the screen is for,
  so that whoever sits down knows what computer this is.
- **Maintainability:** the whole system (image, packages, modules, panel, content)
  lives in this repository with a documented history.

## 5. Development environment

- **Development agent:** Claude Code installed on the Debian development server, using
  the existing claude.ai subscription, reached over SSH from the main Mac; VS Code with
  Remote-SSH as the editor. See
  [dev-environment.md](dev-environment.md).
- **Development and test server:** Debian 13 on a MacBook Pro Retina 15" (mid-2015,
  MacBookPro11,5), which is also the owner's children's daily computer, so the
  project is used by real children from the first usable phase. See
  [install-debian-macbookpro-2015.md](install-debian-macbookpro-2015.md).
- **Version control:** this GitHub repository, private for now.
- **A change is tried without reinstalling anything.** A machine that runs
  Kidux — the test machine left up, the throwaway machine of `ci/vm/try.sh`,
  or the MacBook, which follows its own package archive — takes a changed
  package as an update and restarts only what that package runs, and the
  change is looked at by hand or with the one test that covers it, in
  minutes. The whole battery, which installs a machine from nothing, runs
  in one go before the work is pushed and before anything is published,
  not for every try (D72). See `docs/dev/test-battery-plan.md`, step B7.
- **Image build:** `live-build` configuration in `image/`, independent of the
  development server's installed system; built in CI.

## 6. Out of scope (for now)

- Web browsing module with restrictions.
- Linux system administration module.
- Languages beyond English and Spanish (the architecture supports them; content and
  translations are not planned yet).
- Cloud sync of progress or online user accounts.
- 32-bit (i386) hardware: Debian 13 no longer provides an installer or kernel for it.
