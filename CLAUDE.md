# Kidux — project conventions

Read this before touching anything. These rules come from the project owner and are
not negotiable.

## Language rules

- **Code, comments, identifiers, commit messages, issues, PRs and development docs:
  English only**, even though the owner talks to Claude in Spanish. Reply to the owner
  in Spanish.
- **Two kinds of documentation and a website, and nothing in between.**
  - **User documentation**, for the adult who runs a Kidux machine: `README.md`
    with `README.es.md`, and `docs/en/<name>.md` with `docs/es/<name>.md`, the same
    file names, always in sync; when you change one, change the other in the same
    commit. Their screenshots are in `docs/images/en/` and `docs/images/es/`, each
    document showing its own language's. It is written as the
    finished product's manual and presentation: static and definitive, never as
    something under construction. What does not exist yet gets an empty section,
    not a description of a plan; the one exception is Kidux's own image, which
    the documents say is coming, with what installing from it will be (D81).
  - **The website**, `site/`, is the product's shop window, in the same two
    languages: its page once, `site/page.html`, and its words in
    `site/<language>.toml`, the same keys in each, which `tests/project/site.py`
    holds them to. It says only what is true of Kidux today, in few words, and
    never more than the licence does (`docs/dev/website.md`).
  - **Developer documentation**, English only, in `docs/dev/`: the requirements,
    the roadmap, the architecture and its decision log, how each part works, how
    to make a module, the plans. `branding/README.md` is the style guide.
- **Everything user-facing in the product goes through the i18n layer.** Never
  hard-code a UI string, lesson text, icon label or error message. Ship Spanish and
  English from day one; adding a language must never require a code change.
  See `docs/dev/architecture.md`, section "Internationalization".

## Documents describe the present, not the past

- **Public documents and plans say what is true now.** No "it used to be called X",
  no "this supersedes the earlier decision", no "changed after review", no
  "previously we planned Y". A reader wants the current state, not its history.
  This covers `README`, `docs/en/`, `docs/es/`, and every document and plan in
  `docs/dev/`.
- **The single exception is the decision log in `docs/dev/architecture.md`.** A log is
  meant to hold history: it records each decision with its rationale, and an entry that
  a later one overturns stays, marked as superseded. Nowhere else does.
- **Code comments describe the code, not its edit history.** Never write "changed
  because X", "was Y before", "removed the old approach", "fixed after the review" or
  a dated changelog in a source file. Why a change was made belongs in the commit
  message; why the code is the way it is, when that is not obvious, belongs in a
  comment written in the present tense. The same goes for `debian/changelog`: it lists
  released changes, not the reasoning behind them.
- Everywhere else, when you rewrite something, delete what it replaced instead of
  annotating it. If the reason still matters, it belongs in the commit message or the
  decision log.

## Licence

- Kidux's own code, images and documents are free software under the **GNU
  General Public License, version 3 or later** (`LICENSE`, D110): anyone may
  use, read, change and pass on the code, a family and an organisation alike,
  with no licence to ask for. Every `debian/copyright` says `GPL-3.0-or-later`
  for `Files: *`, and the program a module packages keeps its own licence,
  named there too. The name and the penguin are outside the licence.

## What the project is

A Debian-based distribution for a child's first computer: a locked kiosk launcher for
the child, a password-protected adult panel that unlocks learning modules, built to be
publicly installable on old 64-bit hardware and upgradable without losing data.
The technical design and every decision taken so far are in `docs/dev/architecture.md`.
Keep that file the single source of truth for design decisions; add to its decision log
instead of scattering decisions across chats.

## Working agreements

- Debian 13 "trixie" is the base. Prefer packages in trixie; package everything else
  ourselves as `.deb`. No Flatpak (documented plan B only).
- Every learning module is an independent package an adult can install, enable,
  disable or remove on its own, even when modules share infrastructure.
- Everything that ends up on a user's machine must be reproducible from this repo:
  `.deb` packages in `packages/`, image config in `image/`. Never hand-edit a built
  system and call it done.
- **Partial tests while developing, the whole battery only for a release.**
  While a change is made, test only what it touches, on the machine left up,
  with nothing installed from scratch: its unit tests, `tests/run vm up NN`,
  `vm push <package>` for a changed package, `vm test NN` for its session test,
  and its acceptance test. The whole battery is never run while developing,
  nor at the end of a piece of work: the owner first tries the work by hand
  (their acceptance test), then asks for a release, and only then does the
  whole battery run, once, just before the release. A battery whose only
  failures are a test's own fault, not the product's, needs no second run:
  fix the test and run it alone.
- **Fundamental: a version made only of numbers is a release (D93).** A
  release never changes: once a version is published, its bytes are final,
  and the next change to that package goes under the next number. So a
  package gets its next version at its first change in a piece of work,
  dated by `ci/hours.py changelog-date`, and all the work stays in that number as `~dev`
  builds: `tests/run vm push` and the battery build `<version>~dev.<time>`,
  which Debian sorts before `<version>`, so the numbers run on without a
  gap, since no number is spent on a try. The release itself is built and
  published only when every test has passed, the owner has tried the work
  and said yes, and the further review the owner asks for, when they ask
  for one, is done: `ci/test-release.sh <label> --release`, which refuses
  to run unless a battery has passed of that very commit, or of one it
  differs from only outside the packages' sources (a fixed test, a
  document), since a release publishes its versions to test them; then
  the push, `ci/promote.sh` and `ci/publish-public.sh`, each on the
  owner's word.
  Nothing is released as part of developing or testing, and nothing goes
  to GitHub before the owner's yes. A push of a version the archive
  already holds is refused (D77).
- **The battery, `ci/test-release.sh`**: every check, every package built and
  built again identically, the packages changed in the work published as `~dev`
  builds and installed on the VMs, and every screen photographed in Spanish and in
  English and compared with the previous run. Look at its report
  (`build/releases/<label>/report/index.html`). **The guide's pictures come
  from the release run alone**, `--release`, which writes them into
  `docs/images/es/` and `docs/images/en/`: a battery run never touches them,
  since a `~dev` version shows on the screens. They are committed before the
  push. A new screen or behaviour gets its check in `tests/run session` in the
  same commit, and its picture listed in `tests/lib/doc-screenshots.txt` if the
  guide shows it.
- Commits: imperative subject line in English, body explains why. Commit only when
  the owner asks. They are authored as `othermore <info@kidux.org>`, the
  repository's own `git config`, never with a personal address (D80).
- **Never write a timestamp from memory.** A `debian/changelog` date comes from
  `ci/hours.py changelog-date <package>`, a dated note from `date -I`. A
  changelog dated in the future breaks build reproducibility, because `dpkg`
  only clamps file times that are newer than `SOURCE_DATE_EPOCH` (D23);
  `tests/run reproducible` catches it. A date in the past is safe.
- **GitHub only in the evening and at the weekend (D99).** Nothing is pushed,
  released or run on GitHub outside Madrid's 19:00 to 02:00 on a weekday and
  the whole weekend. `ci/push.sh` is the one way to push: it dates the
  commits not yet on GitHub inside those hours and pushes; outside them,
  `ci/push.sh --later` sets a timer for the hours' next opening, and
  `--then-publish` has the timer promote and publish after the push, so
  that nobody waits up for it. Never `git push` by hand, never rewrite a
  commit already on GitHub.
- **More than one development machine.** Each has its own archive, test
  machines and `~dev` builds; `main` on GitHub is the only thing they share.
  Start a piece of work with `git pull --rebase origin main`, and before
  bumping a package read its changelog on `origin/main`, since the other
  machine's unpushed work is invisible; the owner says which machine works
  on which package. Push from any of them with `ci/push.sh`, which refuses
  until `origin/main` is behind. A release, the promotion and the public
  archive happen only on the machine that holds the production key and the
  archive whose `stable` goes public, from a tree that holds everything on
  `origin/main`.
- Before proposing a technology, check it is in trixie (`qa.debian.org/madison.php`)
  or has a maintained Linux build, and note the version in the docs.
