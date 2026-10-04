# Tests

Everything that checks Kidux is a file in one of the folders below, and
every file in them is a test. Adding a test is adding a file; the runners
find it by its place, and nothing else needs to know its name.

`tests/run` runs every test, or the kinds named (`tests/run project`,
`tests/run session`). `ci/test-release.sh` builds every package, publishes
them to the local archive's testing suite, runs `tests/run` and compares
every screen with the previous run (docs/dev/packaging.md, "Before a
release"). Building and publishing are not tests, and live in `ci/`;
everything that checks something and says PASS or FAIL lives here.

| Folder | What its tests check | Run by | One test is |
|---|---|---|---|
| `project/` | The repository itself: translations complete, nothing naming the developer's machine, lesson content in step, the logo copies current | `tests/run project`, before every build | an executable file; it prints PASS or FAIL lines and exits non-zero on a failure |
| `packages/<name>/tests/` | One package's code, without a machine: state machines, the daemon's rules, the time arithmetic | the package's own build, `ci/build-package.sh` | a `test_*.py` for pytest; they live with their package because its build runs them |
| (every package) | Each package builds twice into the same bytes | `tests/run reproducible` | nothing to add: every package in `packages/` is included |
| `acceptance/` | A stock Debian that installs the packages: the archive, the daemon, children, time and the lock on real logind sessions, updates through the daemon | `tests/run acceptance`, inside the VM | a `.sh` file sourced with `check "<what>" <command>`, or an executable that prints its own PASS or FAIL lines and exits with how many failed |
| `session/` | A machine rebooted into Kidux, driven from outside by keyboard: every screen, every door, the boot, in Spanish; `session-en` the same machine set up in English | `tests/run session`, `tests/run session-en` | a Python file with `run(machine)`, using `tests/lib/sessionlib.py` |

`lib/` is not tests: it is what the runners are made of. `lib/project.sh`,
`lib/reproducible.sh`, `lib/acceptance-vm.sh` and `lib/session-vm.py` run each
kind; `lib/unit.sh` and `lib/vm.py` are the quick loop below; `lib/base-image.sh` fetches the Debian cloud image, once, even when
both VMs ask together, and `lib/warm-image.sh` makes from it the image they
start from, with Kidux's Debian dependencies already installed
(docs/dev/packaging.md, "Before a release"); `lib/seed/` is the acceptance VM's cloud-init seed and the fixtures both
VMs use; `lib/sessionlib.py` is how session tests drive their machine;
`lib/screenshot-diff.py` compares two runs' pictures; and
`lib/doc-screenshots.txt` says which pictures the user guide, the README and
the website show, in each language. The guide's pictures of Debian's own
installer, `install-debian-*.png`, are not Kidux's screens and no test takes
them: they are from an installation of Debian 13.7 in a virtual machine, in
each language, ended with the guide's own lines against the public archive,
and are taken again by hand when Debian's installer changes.

## The order

Tests in `acceptance/` and `session/` run in the order of their names, and
share one machine, so each starts where the one before left it. Their names
start with a number for that reason: `09-child-session.py` expects the
children `04-family.py` made. A session test that returns `False` stops the
run, for a failure nothing after it could survive; any other result lets it
go on.

## The quick loop

A change is tried in minutes on a machine that already runs Kidux, and the
whole battery, which installs machines from nothing, runs in one go before
the work is pushed (CLAUDE.md; docs/dev/requirements.md, section 5).

1. **`tests/run unit [package…]`**: the packages' unit tests and pyflakes,
   from the tree, without building; every package in about ten seconds.
   The tests never read the machine they run on, so the answer is the
   build's.
2. **`tests/run vm up [NN]`**, once: the session machine from the warm
   image, Kidux installed from the archive's testing suite, the session
   tests run up to the one whose name starts `NN` (`04` when none is
   given: Kidux set up, its three children made, nobody signed in), and
   left up. Its screen is on VNC at `127.0.0.1:5901`, password `kidux`, on
   this machine only (from another computer, `ssh -N -L
   5901:127.0.0.1:5901 <you>@kidux.local` first). The machine is kept as a
   snapshot in `build/vm/snapshots/`, powered off after test `NN`: the next
   `vm up NN` starts from it in about a minute, takes the packages the
   archive has now and restarts if they changed anything, instead of
   installing Kidux and running the tests again. A change to those tests,
   to the seed or to the base image makes a new snapshot.
3. **`tests/run vm push <package>…`**, after each change: each package
   built from the tree as a development version, `<version>~dev.<time>`,
   published to the testing suite and installed on the machine, and what
   the package runs started again: the daemon for `kidux-daemon`, the
   sign-in screen for `kidux-greeter` when nobody is signed in, the web
   applications' server for `kidux-webapps`; `kidux-common` both of the
   first two. What cannot be started again under a child is said:
   the launcher takes the change at the next sign-in, a module the next
   time it is opened, `kidux-session` at a reboot. A package the machine
   does not have is published only, for the panel or apt to install.
4. **Look at it**, over VNC, or **`tests/run vm test NN`**: the session
   test whose name starts `NN`, against the machine as it is, as many
   times as it takes, its pictures numbered from 50; the machine has to be
   where the test expects it, since tests start where the one before left
   off. **`tests/run vm shot <name>`** photographs the screen into
   `build/vm/`, and **`tests/run vm ssh [command]`** is a shell on it as
   its administrator.
5. **`tests/run vm down`** powers it off and deletes its disk; until then
   a `tests/run session`, or the battery, refuses to start rather than run
   over it (`tests/run session --stop` is the same).

A development build never reaches a family: its version,
`<version>~dev.<time>`, sorts before the version itself (Debian's `~`),
which replaces it when it is published, after removing every development
build from the suite (ci/publish-local.sh), once the owner has tried the
work and said yes (D93); `ci/promote.sh` refuses while testing holds one.
The battery tests development builds too, of every package changed in the
work (ci/test-release.sh); the release run, `--release`, builds and tests
the versions themselves, and is the one that writes the guide's pictures
(D93). So the tree's version is always one the archive has not published: a package gets its version at its first change, and
`vm push` refuses a package the archive already holds at the tree's
version or above (D77). The owner's machine, which follows the testing suite, takes a pushed
package with `sudo apt update && sudo apt upgrade` (docs/dev/rollout.md,
section 5).

## Adding one

- **A rule about the repository:** an executable in `project/`.
- **A new behaviour of a package's code:** a `test_*.py` in that package's
  `tests/`. Its build will run it.
- **Something only an installed machine shows:** a file in `acceptance/`,
  numbered where it belongs.
- **Something only a machine running Kidux shows, a screen above all:** a
  file in `session/`, numbered where it belongs. Take a picture of every new
  screen with `machine.screenshot("<name>")`, and list the picture in
  `tests/lib/doc-screenshots.txt` if the user guide should show it.
  The battery runs every session test on a machine set up in Spanish, and
  on one set up in English (`tests/run session-en`, or `KIDUX_VM_LANGUAGE=en`
  for the quick loop) the tests that take a picture the guide shows, those
  that set the machine up and the one that says every screen fits, marked
  `EVERY_LANGUAGE = True` (`tests/lib/session-vm.py`; `KIDUX_VM_EVERY_TEST=1`
  runs them all). What depends on the language, a locale, a word, is read
  from `sessionlib.SPEAKS`, never written in the test.

A session test waits for what it stands for, never for a number of
seconds: `machine.shown(name, mark)` for a trusted screen, which logs
`drawn <name>` once it has painted one, counted from a `machine.mark()`
taken before the key, since the journal holds the whole boot (and
`machine.submit(text)` types, marks and presses Enter); `logged(tag,
text, before)` for any other line in the journal, counted the same way;
`launcher_shown(machine)` for the launcher; `machine.still()` for a
screen to finish drawing, which every `machine.screenshot()` does first;
and `machine.changes(machine.settled())` for a change nothing logs, such as
a dialog opening. A pause is left only where it stands for time itself: a
limit running out, the minutes to save work, or a door that must stay
shut for a while.

Every check says what it proves in the words of the behaviour, not of the
code: "a wrong password signs nobody in", not "test_auth_2".
