# Developer documentation

Everything about how Kidux is built and how it works inside. English only.
What an adult or a child needs is in the [user guide](../en/user-guide.md)
instead, in English and Spanish.

## Start here

- [requirements.md](requirements.md): what the system must do, for whom, and
  what is out of scope.
- [architecture.md](architecture.md): the technical design, and the
  **decision log** at its end, which is the one place where the history of a
  decision is kept. Every non-obvious choice has a number there, and code and
  documents refer to decisions by that number.
- [roadmap.md](roadmap.md): the phases, in order, and what is done.
- [layout.md](layout.md): where everything is, in the repository and on an
  installed machine.
- [../../CLAUDE.md](../../CLAUDE.md): the project's conventions, for people
  and for the coding agent alike.

## How it works

- [daemon.md](daemon.md): `kidux-daemon`, the one privileged process: who may
  call what, the adult password, children, time, the lock.
- [session.md](session.md): `kidux-session`: how the machine boots into the
  sign-in screen, the child's session, the lock screen's terminal, and every
  door that is closed.
- [keys.md](keys.md): the keys a child's session binds, why a MacBook's and a
  PC's are the same, and how a keyboard that sends something else is added.
- [greeter.md](greeter.md): `kidux-greeter`, the sign-in screen and the lock
  screen.
- [panel.md](panel.md): the adult panel and the first-run wizard.
- [launcher.md](launcher.md): `kidux-launcher`, the child's screen.
- [installer.md](installer.md): the installable image and the installer, as
  designed.
- [modules.md](modules.md): what a learning module is and how to make one.
- [website.md](website.md): the website, what it says, how it is built and
  published, and where a donation goes.

## Building, testing, shipping

- [packaging.md](packaging.md): how a change here becomes a package on a
  machine: building, the archive, reproducibility, promoting, the VM tests.
- [../../tests/README.md](../../tests/README.md): every kind of test, where
  each lives, how they run, and how to add one.
- [dev-environment.md](dev-environment.md): the editor, the coding agent and
  the machine they run on.
- [install-debian-macbookpro-2015.md](install-debian-macbookpro-2015.md):
  the development and test server.
- [rollout.md](rollout.md): putting Kidux onto that server, which is also a
  family's machine.
- [../../branding/README.md](../../branding/README.md): the logo, the mascot,
  the colours and the type.

## Plans

- [phase-1-plan.md](phase-1-plan.md): the base system, step by step, built.
- [phase-3-plan.md](phase-3-plan.md): the module framework, the first
  modules and what the hand tests at home ask for, built before the ISO
  (D31).
- [phase-4-plan.md](phase-4-plan.md): the content modules, typing and the
  Scratch family first, and how a program that is not in Debian is built
  and packaged, built.
- [phase-4b-plan.md](phase-4b-plan.md): the current plan: the website's
  visits behind a cookie notice, BASIC with its guide, and
  modules that are a door to one website, CodeCombat and Wikipedia.
- [test-battery-plan.md](test-battery-plan.md): making `ci/test-release.sh`
  faster without making it mean less.

A plan describes what is to be built and is rewritten as things are built;
a design document describes what exists. Neither keeps history: that belongs
to the decision log and to the commit messages.
