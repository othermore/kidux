# Test battery plan — making `ci/test-release.sh` faster

A plan, not a design document: what is to be built so that the battery takes
less of a working day, in the order it should be built, with what each step
has to prove. Steps marked done are built; the battery as it is now is
described in tests/README.md and ci/test-release.sh.

## 1. Where we start

Measured on 2026-09-26, on the development machine (8 cores, 15 GB, the VMs
on KVM), for one run of `ci/test-release.sh` with the warm image already
made (the `3.14` run, from the times its stage lines print):

| Stage | Minutes | What takes the time |
|---|---|---|
| build + publish | 4.8 | sbuild of two packages, then nine at once |
| test: project | <1 | |
| test: reproducible | 7.7, alongside the two below | every package built twice more, nine at once in each round |
| test: acceptance | 4.9, alongside | the warm image installing Kidux from the archive, then the checks, GCompris and Chromium among them |
| test: session | 19.4, alongside | the same install, a reboot, twenty-one tests driven by keyboard, a second reboot for GRUB, a purge and a third |
| screens and report | 1 | |

About 27 minutes: the three test stages run at once (B1), and the session
run is the whole of the wait after the build. A run whose archive has a new
dependency line makes the warm image again first, about four minutes more,
and a cold run, from the stock image, about five. Of the
session's minutes, five and a half are test 10 waiting for the minutes to
save work to run out, which is what it tests. The whole battery runs in
one go before the work is pushed and before anything is published (D72);
a change is tried in a minute or two with the quick loop (B7).

## 2. What must not change

- **Every run is whole, and the release run is cold.** Every run builds,
  publishes and installs every package on machines that have never seen
  Kidux. The runs before a plan step's commit start those machines from
  the warm image (B3), Debian with Kidux's Debian dependencies already
  installed; the run before a release starts them from the stock cloud
  image (`KIDUX_VM_COLD=1`), as a family's machine starts.
- **A green run means the same thing.** No stage is skipped by a run that
  claims to be the battery, and every commit of a plan step still needs the
  whole of it (the owner's decision, 2026-09-24: no shorter battery for
  commits). What is made faster is the battery itself.
- **Nothing is installed on the development machine** (D4): no cache daemon,
  no proxy. What is cached lives under `build/`.

## 3. The steps, in order

Sizes are relative effort. Each ends with `ci/test-release.sh` green,
measured (the logs' times, as in section 1), its numbers replacing the ones
in section 1, and a commit of its own. `packaging.md`'s "Before a release"
and `tests/README.md` describe what each step changes, in the present.

### B1 — The three test stages at once — S — **done 2026-09-25**

`ci/test-release.sh` runs *reproducible*, *acceptance* and *session* in
parallel once *publish* has succeeded (`stage` backgrounds each with its
own log and collects the three statuses with `wait`), and reports each
as today; *project* runs first, alone, since it is the quickest and
decides nothing else. The machine has the room: each VM takes 2 GB and
two cores, sbuild the rest.

What has to be true first, and the step checks it:

- The VMs share nothing under `build/vm/` that one writes and another
  reads: they already have separate console logs, seed directories and
  ports (8000, 8002 and 8003), but the acceptance VM copies `OVMF_VARS.fd` and
  the session VM `OVMF_VARS_session.fd`; keep it that way, and give every
  file a stage-specific name.
- The acceptance VM boots the base image with `-snapshot` and the session VM
  copies it to `session.qcow2`: both only read the base, so they may share
  it.
- The reproducible stage builds under `build/` too; its output directories
  must not collide with the VMs'.
- The archive is not republished while the VMs install from it: *publish*
  finishes before the three start.

Expected: about 27 minutes, the session run being the critical path.
Measured: 31 minutes; the session run takes 23.5 of them.

### B2 — Waits instead of pauses in the session tests — M — **done 2026-09-25**

Every `time.sleep(n)` that waited for the screen to be drawn is a wait on
the fact it stands for. The trusted screens log `drawn <name>` once a
screen is painted, besides `showing <name>` when they start to build it,
since building a page can take most of a second and a key pressed before
it is lost; `machine.mark()` counts the screens drawn so far and
`machine.shown(name, mark)` waits for one more, since the journal holds
the whole boot. `machine.submit(text)` types, marks and presses Enter.
Other facts come from the journal (`logged(tag, text, before)`,
`journal_count`), from the compositor's windows as the launcher sees
them (`launcher_shown`, `on_screen`, `windows`, `window_of`, through the
`kidux-toplevels` tool), from a session appearing or ending and from a
terminal switching. `machine.still()` waits until two frames a quarter of
a second apart are alike (a blinking text cursor allowed), and every
picture waits for it, so a picture is drawn whole without a fixed pause;
`machine.changes(machine.settled())` waits for a change nothing logs, a
dialog opening. A key press returns when QEMU's monitor answers, plus a child's
pace of 0.15 s, instead of 0.8 s. Pauses that stand for time itself stay:
a limit running out, the minutes to save work, a door that must stay
shut, and the Esc pressed about once a second through GRUB's hidden
second, since faster lands one in the firmware's; the GRUB pictures are
now checked, not only taken. The session run prints how long each test
took.

Measured: the session run 18.8 minutes, the whole battery
25. The waits also found a fault the pauses had hidden: a
lock screen told to stop while still starting could hold terminal 8 for
ninety seconds and make the next child's lock screen fail
(`kidux-locker@.service` now has `TimeoutStopSec=5`, session.md
section 4).

### B3 — A warm base image for the machines — M — **done 2026-09-25**

`tests/lib/warm-image.sh` makes `build/vm/debian-13-kidux-deps.qcow2`, an
overlay on the stock cloud image: it boots it once with the local archive
as a source, asks apt what installing every Kidux package in the testing
suite would bring — the family with Debian's recommendations, as
`apt-get install kidux-base` brings them, the modules without, as the
daemon installs them, so that a module's window opens on the image with
exactly what the panel's *Install* gives it — installs those of Debian's
(never Kidux's own, and with Kidux's conflicts respected, so no `foot`),
marks them as installed for a dependency, as installing Kidux would have,
removes the archive and its
key, updates, cleans cloud-init's state and shuts down: about four
minutes. The image is stamped with a hash of the stock image, of the
script and of every Depends, Pre-Depends, Recommends and Conflicts line
in the suite; a run whose stamp differs makes it again first, under a
lock, since both VMs ask at once. Both VMs boot it by default;
`KIDUX_VM_COLD=1`, which a release sets and GitHub's `release` job always
sets, boots the stock image as before (packaging.md, "Before a release").
Covering every package in the suite, not only the base, means a module's
Debian dependencies, GCompris's or Chromium's, are warm as soon as the
module is published.

Proven on the run that introduced it: the `b2` run, cold, and the `b3`
run, warm, give the same verdicts on the same tests. A dependency added to
a package makes a new stamp and a new image on the next run, and one a
package forgot to declare but the image holds is still caught by the cold
run before a release.

Measured: the session run's install from 231 seconds to 45, the session
run 15.7 minutes, the acceptance run 2.7, the whole battery
22.8.

### B4 — Rerunning one stage against the same build — S — **done 2026-09-25**

A stage that failed for a reason outside the code — a mirror down, the
cloud image's own `apt-daily` holding the dpkg lock, a VM that did not come
up — cost a whole run. `ci/test-release.sh <label> --only <stage>` reruns
`project`, `reproducible`, `acceptance` or `session` against what `<label>`
already built and published, and replaces that stage's line in the run's
`verdicts`, marked as a rerun; a session rerun takes the pictures and
compares them again. The build is not repeated, so the packages under test
are byte-for-byte the ones the report's other stages saw (D23): the run
records a hash of the archive's testing suite, of the packages' sources
and of the seed both machines are set up with (`tests/lib/seed/`) when it
publishes, and a rerun refuses when any has changed since.

Measured: the acceptance stage of `b4` rerun in 2.6 minutes, against 21
for the whole battery.

### B5 — The build itself — S — **done 2026-09-25**

`ci/build-all.sh` builds `kidux-archive-keyring` and `kidux-common` first,
one after the other, since every other build installs `python3-kidux` to
run its tests; then the rest, four at a time, through `ci/build-parallel.sh`,
each with its own log under `build/logs/`, waiting for all and saying how
each went. Each of those builds sees, through `KIDUX_EXTRA_PACKAGES`, a
copy of `build/`'s packages as they were when they started, so none
installs a package another is still writing. sbuild's chroot is a
tarball unpacked per build, so the builds share no other state. The
reproducible stage builds each of its two rounds the same way; the rounds
themselves cannot overlap, since both build from the same source
directories.

Measured: the build from 5.5 minutes to 2.7, the reproducible stage from
7.4 to 5.9, the whole battery from 22.8 to 21.4. The session run, beside
six rebuilds at once, slows from 15.7 minutes to 17.0 in its first tests;
the battery still gains.

### B6 — A machine left up is not run over — S — **done 2026-09-25**

`KIDUX_VM_STOP_AFTER` leaves a machine up and `tests/lib/session-one.py`
runs one test against it (tests/README.md). `tests/run session` refuses to
start while that machine's monitor socket answers, and says how to reach
it or stop it; `tests/run session --stop` powers it off, stops the seed
server the run left with it, and deletes its disk, which every hand test
used to end with by hand. No minutes off the battery, but no run lost to a
machine forgotten up.

The steps were built in the order B1, B2, B3, B5, B4, B6. The battery went
from about 45 minutes to 21 (section 1): the three test stages at once,
the session run's waits and its warm machine, and most packages built at
once. It is now the session run, at 17 minutes, and inside it test 10,
which waits six and a half minutes for a limit and the minutes to save work
to run out, that set the pace.

### B7 — The quick loop: a change tried in minutes — M — **done 2026-09-26**

A change is tried on a machine that already runs Kidux, by updating the
package it is in, and looked at by hand or with the one test that covers
it; the whole battery runs before the work is pushed (D72). `tests/run`
takes two more
words (tests/README.md, "The quick loop"):

1. **`tests/run unit [package…]`** (`tests/lib/unit.sh`) runs the
   packages' unit tests and pyflakes straight from the tree, with the
   tree's `kidux-common` first on `PYTHONPATH`, what each package's build
   runs in its chroot, without the build. The tests read nothing of the
   machine they run on (the daemon's keep the update job's status file in
   their own directory, and a module's reads no catalogue the machine has
   installed), so a machine that runs Kidux answers as the chroot does.
2. **`tests/run vm up [NN]`** (`tests/lib/vm.py`) runs the session tests
   up to the one whose name starts `NN`, `04` when none is given (Kidux
   set up, its three children made, nobody signed in), and leaves the
   machine up, its screen on VNC at `127.0.0.1:5901` with the password
   `kidux` (`KIDUX_VM_VNC` in sessionlib, unset for the battery).
3. **`tests/run vm push <package>…`** builds each package from a copy of
   its source whose changelog gains `<version>~dev.<time to the second>`,
   in `build/dev/<time>/` (`KIDUX_SOURCE_DIR` and `KIDUX_BUILD_DIR` for
   `ci/build-package.sh`), publishes it to the testing suite with
   `KIDUX_DEV_BUILD=1`, installs on the machine left up the binaries it
   has, and starts again what they run: the daemon for `kidux-daemon`
   and `kidux-common`, greetd for `kidux-greeter` and `kidux-common` when
   no child is signed in, the web applications' server for
   `kidux-webapps`; for the launcher, a module and `kidux-session` it says
   when the change arrives. A time, not a counter, makes the version: it
   is never the same twice even after the development builds are
   removed, so no published version ever changes its bytes.
4. **`tests/run vm test NN`**, **`vm shot <name>`**, **`vm ssh
   [command]`** and **`vm down`**: one session test against the machine,
   a picture of its screen, a shell on it, and the end of it.
5. **The battery tests what it built.** reprepro keeps a newer version over
   an older one without a word, so `ci/publish-local.sh`, publishing
   anything but a development build, first removes every `~dev.` version
   from the suite; `ci/promote.sh` refuses while testing holds one. The
   rerun fingerprint of `ci/test-release.sh` reads `packages/` from its
   second level, where the sources are, not the `.dsc` and tarballs each
   build leaves at its top.
6. **Documents.** tests/README.md "The quick loop", packaging.md
   "Trying a change" and "Publishing", rollout.md section 5 "Taking a
   change" (how the MacBook, following the same suite, takes a pushed
   package, and what each package needs afterwards), requirements.md
   section 5.

**Tests.** `tests/project/quick-loop.py`: a development version sorts above
the tree's build of the same version and below the next, a later push above
an earlier, its changelog entry is one dpkg reads, what each package
restarts, and `tests/run vm` refusing a push without a package, of the
archive's key, and an unknown word.

Measured on its own commit: `tests/run unit`, every package, 9 seconds;
`vm up`, 1.5 minutes from the warm image; `vm push kidux-greeter`, 31
seconds from the command to the sign-in screen drawn again with the new
build; `vm push kidux-common kidux-daemon`, 69 seconds; `vm test 05`, 15
seconds.

## 4. What stays as it is

- The order and the state-sharing of the session tests: a machine driven by
  keyboard from one screen to the next is what makes the run mean something,
  and splitting it into independent machines would multiply the installs it
  is meant to save.
- GitHub runs the whole battery only when asked (D39).
