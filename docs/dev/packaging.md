# Packaging and the archive

How a change in this repository becomes a package on a machine. Everything here
runs unprivileged except the one-time host setup.

## The shape of it

```
packages/<name>/          one Debian source package, with debian/ inside it
ci/build-package.sh       build one package in a clean chroot
ci/build-all.sh           check, then build all of them, most at once
ci/publish-local.sh       put what was built into the archive
ci/promote.sh             move what was tested from testing to stable
ci/archive/               the archive's configuration, ours, versioned here
ci/setup-dev-host.sh      the one privileged step, run once
ci/setup-ci-host.sh       the same, for a CI container, with a key of its own
ci/serve-archive.sh       the archive over HTTP without nginx, for CI
ci/i18n-extract.sh        collect translatable strings into the catalogues
ci/render-avatars.sh      look at the avatars
ci/render-branding.sh     render the logo and the mascot to PNG
ci/test-release.sh        build, publish, then every test, before a release
ci/vm/                    a throwaway Kidux machine to use, and its picture
.github/workflows/        continuous integration: the commands above, on GitHub
tests/run                 every test, or the kinds named: tests/README.md
tests/<kind>/             the tests themselves, one file each
build/                    everything the above produces; not in git
/srv/kidux-apt/           the archive itself; not in git, served by nginx
```

The archive's *configuration* is in the repository; the archive's *contents* are
not. `reprepro` keeps a database next to the packages that records what was
published when, and that has to survive a `git checkout` of any branch.

## Setting up a machine to build on

Once, as root:

```
sudo ci/setup-dev-host.sh
```

It creates `/srv/kidux-apt` owned by you, points nginx at it, puts you in the
`kvm` group so test VMs run at full speed, and lets your systemd linger, so
that a push set for the evening (`ci/push.sh --later`, D99) outlives your
session. Log out and back in afterwards for the group to take effect. It is
safe to run again.

Then the build chroot, which is a tarball rather than a `schroot` installation,
so that `sbuild` needs no root and CI runs the same command:

```
mmdebstrap --mode=unshare --variant=buildd trixie ~/.cache/sbuild/trixie-amd64.tar
```

Rebuild that tarball whenever it has drifted too far from current trixie.

## Building

```
ci/build-package.sh kidux-base      # one package
ci/build-all.sh                     # all of them
```

Results land in `build/`. `lintian` runs afterwards with `--fail-on
error,warning` and `--pedantic`, and a failure fails the build.

`ci/build-all.sh` builds the keyring and `kidux-common` first, one after
the other, since every other package installs `python3-kidux` to run its
tests; then the rest, four at a time (`KIDUX_BUILD_JOBS`), through
`ci/build-parallel.sh`, each with its log in `build/logs/<package>.log`,
the end of which it prints for a build that failed. Each build unpacks a
chroot of its own, and a module built from an upstream tarball adds
hundreds of megabytes to it: `ci/build-package.sh` has sbuild put them in
`/var/tmp/kidux-sbuild/`, on the disk (`KIDUX_TMPDIR`), not in `/tmp`,
a tmpfs in memory that the test machines need too; not under `build/`,
since the chroot's root, a user of sbuild's namespace, cannot enter a home
directory. A chroot a dead build leaves there belongs to that namespace's
users, and `unshare --map-auto --map-root-user rm -rf` removes it. Each
of those builds sees a copy of `build/`'s packages as they were when they
all started, so that none installs a package another is still writing. `tests/run reproducible` builds its two rounds the same
way.

`lintian` is run by the build script rather than by `sbuild`, on purpose:
`sbuild` reports a lintian failure in its log and still exits successfully, so a
package with real problems would pass CI unnoticed.

## Programs built at development time

Scratch, TurboWarp, ScratchJr's desktop port and Blockly Games are not in
trixie. Each is built from its own git repository with Node.js, and the
network to fetch what it depends on, which a package build does not have
(D68). So the program is built first, on the development machine, into a
tarball, and its package is built from the tarball, in the chroot, like any
other.

```
ci/build-upstream.sh kidux-module-scratch                 # build/upstream/<tarball>
ci/build-upstream.sh kidux-module-scratch --publish       # and a GitHub release
ci/build-upstream.sh kidux-module-scratch --from-source   # again, from its source alone
```

`packages/<package>/upstream.toml` says where the program comes from:

```toml
[upstream]
name = "scratch-gui"
repository = "https://github.com/scratchfoundation/scratch-editor"
commit = "<forty hex digits>"
version = "11.2.0+git20261001"      # the tarball's; the changelog's starts with it
node = "24.9.0"                     # a nodejs.org release; "" when the build needs none
build = "ci/upstream/scratch.sh"    # the build script
sha256 = "<the tarball's>"          # written by the first build
source_sha256 = "<its source's>"    # the same, for the source tarball (D71)
```

`ci/build-upstream.sh` runs the build script in a fresh
`build/upstream/work/<package>/`, with a home of its own and the Node.js
release named, which `ci/upstream/node.sh` downloads from nodejs.org into
`build/upstream/node/` once, checked against the sums published beside
it; the system's `node` is never used. The script fetches the commit,
builds, and packs the result with `ci/upstream/pack.sh`: one
top-level directory, sorted, owned by root, every time the commit's, so
that the same tree gives the same bytes. The tarball's SHA-256 goes into
`upstream.toml` the first time and is committed; a later build of the same
version that gives other bytes is an error, since a version's bytes never
change and a new build is a new version: the same commit built again with
a changed script is `<version>+build<n>`, as `15.2.0+build2`. `--publish`
puts the tarball in a release of this repository,
`upstream/<package>/<version>`, which is where every other machine gets
it: never in git.

Beside it goes the build's source (D71), `<package>_<version>.source.tar.xz`.
A build script fetches nothing itself: every repository and file goes
through `ci/upstream/fetch.sh`, which keeps a copy of each, the tree
without its history; npm's cache and the build's cache directory
(`XDG_CACHE_HOME`, where Electron's downloads go) are in the same place,
and `node.sh` keeps the Node.js archive there. The first build of a version packs all
of it, with the scripts of this repository that build it and a README
saying how, and records its SHA-256 as `source_sha256`. npm's cache holds
the times it was filled, so a later build's copy is not the same bytes:
the recorded one, published, is the version's source, and a later build
leaves it as it is. `--from-source` takes that tarball, from
`build/upstream/` or the release (`ci/fetch-upstream.sh <package>
--source`), and builds with npm offline in a network namespace of its own
(`unshare --net`), where nothing but the loopback answers; the result must
be the recorded tarball, byte for byte. Each source tarball is built from
that way before it is published. A script that has something else to keep,
such as the lock file npm wrote for a repository without one, puts it in
`$UPSTREAM_KEEP` and reads it back from `$UPSTREAM_KEPT`.

A program taken as files someone else built, with nothing to build, has no
repository and no commit: `repository` and `commit` are both empty, and
`tests/project/upstream.sh` accepts the pair only empty together. Its
build script fetches each file by its address through
`ci/upstream/fetch.sh`, checks it against a list of the package's own,
and writes the time its tarball is dated by into `$UPSTREAM_KEEP/time`,
which dates its source tarball too, there being no commit's time. PhET's
simulations are the one (`ci/upstream/simulations.sh`, reading
`packages/kidux-module-simulations/sims.toml`, which
`ci/upstream/simulations-versions.py` fills in by hand; phase-4f-plan.md,
4.30). The source tarball carries every `*.toml` of the package, the list
with `upstream.toml`.

`ci/build-package.sh` builds such a package from a staged copy of its
source, `build/staged/<package>/`, with the tarball, found in `build/upstream/`
or downloaded from its release by `ci/fetch-upstream.sh` and checked against
the recorded sum, unpacked into `upstream/` inside it; the package's
`debian/rules` installs from there. Nothing of the build reaches
`packages/`, and `.gitignore` keeps `packages/*/upstream/` out of git.
`tests/project/upstream.sh` checks every `upstream.toml`, and that a site's
check, `ci/upstream/check-site.py`, which fails on a built web site whose
files are referred to from the root rather than from the path
`kidux-webapps` serves it under, tells the two apart.

What the development machine needs for these builds, beyond what building
packages needs: `git`, `curl`, `xz-utils`, `tar`, `make`, `python3` and
`unshare` (util-linux), which it has. Nothing else is installed for them:
what a build needs is downloaded under `build/` and checked. And nothing a Kidux machine needs is
ever something only the development machine has: a module's `Depends` names
what its program needs, and the test machines, which start from Debian, are
the proof.

## Publishing

```
ci/publish-local.sh              # into the testing suite
```

Two suites, and the difference matters to a family:

- **`testing`** is where a package lands as soon as it builds.
- **`stable`** is what an installed machine follows and upgrades to unattended.
  Nothing reaches it that has not been installed from `testing` on a real
  machine first.

Which suite a package goes into is decided here, on the command line, never by
the package. Its `debian/changelog` says `trixie`, which is the Debian release it
was built against — a fact about the package. The suite is a fact about how far
it has got through our testing, which changes without the package changing.
`reprepro` warns about the mismatch and is told to expect it (D22).

A publish of the tree's own build first removes from the suite every
development build, a version ending `~dev.<time>` that `tests/run vm push`
published for trying a change ("Trying a change", below): reprepro keeps a
newer version over an older one without a word, so the machines would
otherwise install the try instead of the build.

Publishing always re-exports both suites, including one nothing has been put in
yet. To apt, a suite with no `Release` file is not empty but broken, and a
machine following `stable` would report the archive as unusable until the first
package was ever promoted.

## The build cache

A package is the same bytes whenever it is built from the same source, so a
build that would make the bytes already made is not done again.
`ci/build-key.py <package>` gives a build's key: a SHA-256 of every file of
the package (an upstream package's `upstream.toml` names its tarball's sum,
so the tarball is in it), the scripts that build it, the build chroot's
tarball, the distribution, and the key of each package of ours it builds
against. `ci/build-package.sh` keeps each package it builds, once lintian has
passed it, in `build/cache/<package>/<key>/`: the `.changes` and every file
it lists. A build whose key is there, from less than a week ago, copies
those files instead of building; the week is for what the key does not
cover, the Debian packages the chroot installs while building, which a
point release of trixie changes. A development build (`tests/run vm push`)
is never taken from the cache nor kept in it, and `KIDUX_BUILD_CACHE=0`
builds everything, for a release or when the cache is in doubt. The cache
is `build/`'s, so removing `build/cache/` empties it.

`tests/run reproducible` builds with the cache out of the way, and marks
each package it found reproducible in that package's cache entry: a package
whose key was shown to build identically twice less than a week ago is not
built twice again, and says so with the day it was shown. With nothing
changed since the last battery, the build stage copies every package and
the reproducibility stage builds none; a change to `kidux-common`, which
every Python package builds against, makes them all new keys.

## Reproducibility

```
tests/run reproducible              every package
tests/run reproducible kidux-base   one of them
```

Builds each package twice and refuses it if the two results differ by a single
byte. A version number is a promise about specific bytes: the archive refuses
to replace a published version with different content, and promoting from
testing to stable only means anything if what a family installs is what was
tested.

**A package's version is its newest changelog entry**, and nothing else may
say otherwise: a `pyproject.toml`, or the daemon's `VERSION`, which `Ping`
answers with, carries the same number. `tests/project/versions.sh` checks it.

**Take changelog dates from `ci/hours.py changelog-date <package>`, never
from your head.** `dpkg` clamps
every file's modification time to `SOURCE_DATE_EPOCH`, which it reads from the
newest `debian/changelog` entry — but it only clamps times that are *newer*
than that. A changelog dated in the future clamps nothing, so each build stamps
its own wall clock into the package and no two builds agree. That is how this
check earned its place.

The same rule has a second edge: a file *older* than the changelog's date keeps
its own time. In a fresh checkout every file is newer, but in a working copy a
file copied before the changelog entry was written is not, and the package then
depends on when that copy was made. `ci/build-package.sh` touches every file of
the package before building, so every time is clamped the same way in any
working copy.

## Promoting

```
ci/promote.sh                  everything in testing
ci/promote.sh kidux-base       one package
```

The full cycle for a change, then:

```
ci/test-release.sh <label>     the battery: every package built, the changed
                               ones as development builds, published into
                               testing and tested; the MacBook takes them too
                               (the owner tries the work, asks for any further
                               review, and says yes)
ci/test-release.sh <label> --release
                               the release: the versions themselves, built from
                               the bytes the reproducibility stage kept,
                               published into testing in place of the
                               development builds, every test run on them,
                               the guide's pictures written
ci/push.sh [--later]           then, each on the owner's word: the push, inside
                               the hours (below), now or at a timer's next chance
ci/promote.sh                  into stable
ci/publish-public.sh           and the public archive, inside the hours too;
                               ci/push.sh --then-publish does both after the push
```

A version made only of numbers is a release, and a release never changes
(D93): until the owner's yes every try, the battery's included, is a
development build of the version a package got at its first change, and
an error found is fixed within that version, so the numbers run on
without a gap. `--release` is refused on a tree with changes not
committed, so that a release is a commit, and unless a battery has passed
of that commit, or of an earlier one from which it differs only outside
what the packages are built from (`packages/`, the seed, the build
scripts; `build/releases/*/commit`), as after a test's own fault was fixed
and that test rerun alone with `--only`: the bytes tested are the bytes
built. A release publishes its versions to test them, and a version once
published never changes, so a release that fails costs the next number.

Promotion copies what is already in `testing` rather than publishing a fresh
build, so the bits a family gets are the bits that were tested, byte for byte.

**The hours.** Nothing of Kidux's reaches GitHub, or carries a time that is
read there, outside the hours it is seen working (D99, `ci/hours.py`):
Madrid's 19:00 to 02:00 around a weekday night, and all of Saturday and
Sunday, so Friday 19:00 to Monday 02:00 without a break. `ci/push.sh` is
the one way to push: inside the hours it dates the commits not yet on
`origin/main` again, the author's and the committer's dates alike, the
last at the push and each earlier one a minute before (closer when the
hours have just opened), the same trees, messages and author, and pushes;
outside them it refuses, or with `--later` sets a timer of the user's
systemd for the moment they open (`systemctl --user list-timers`,
`journalctl --user -u kidux-push-<time>`), which lives while the user has
a session or lingers (`sudo loginctl enable-linger`). `--then-publish`
runs `ci/promote.sh` and `ci/publish-public.sh` after the push, and
`ci/publish-public.sh` keeps to the hours by itself. A commit once pushed
never changes, so only the commits still to push are dated again, and as
the last step: after a release, the battery's record of its commit names
the one before the dating, which only matters to a `--release` run again.
A changelog's date, which the built package carries, comes from
`ci/hours.py changelog-date <package>`: the last moment inside the hours
not after now, and after the package's last entry; a date in the past is
safe for reproducibility (D23). A dated note in a document has no hour.

## The public archive

```
ci/publish-public.sh           the stable suite, to https://apt.kidux.org
ci/publish-public.sh --pack    packed only, into build/public-archive and build/kidux-apt.tar
```

A family's machine follows `https://apt.kidux.org`, suite `stable`: that is
what `kidux-apt-source` writes into `/etc/apt/sources.list.d/kidux.sources`,
and where the user guide's installation on Debian fetches the two bootstrap
packages from (D81, D82, D109). The testing suite is never public; it stays
on the development machine, for the machines that test.

The address is a web hosting of the project's own, OVHcloud's, serving the
folder `apt` of the hosting as the subdomain `apt.kidux.org`, over HTTPS
with a Let's Encrypt certificate the hosting renews. Its access logs are
why it exists: they say how many machines follow the archive and which
packages they fetch, which GitHub Pages never told. Its credentials live in
one file outside the repository on the release machine,
`~/.config/kidux/apt-hosting.netrc`, a netrc line (`machine <host> login
<user> password <password>`), mode 0600, read by the scripts and never
written anywhere else; `KIDUX_APT_HOSTING` names another file.

The public archive is the stable suite of the local one, copied whole:
`dists/stable/` with its signature, the packages its index names, and
`bootstrap/stable/`. `ci/publish-public.sh` packs them into
`build/public-archive`, checks each package against the index, and sends
them to the hosting over SFTP with `curl`, in an order a machine can fetch
from at any moment: the packages and the bootstrap packages first, then the
indexes, each uploaded under another name and renamed into place, and
`InRelease` last; the hosting's SFTP refuses to rename over a file, so the
old index is removed the instant before, and a machine that fetches in that
instant finds it missing and tries again later, never half written. Then
the packages no index names any more are removed from `pool/`. Afterwards
the script checks what the world sees: it fetches `InRelease` from
`https://apt.kidux.org`, verifies it with `gpgv` against the keyring the
packages ship, compares it byte for byte with the one just sent, and
fetches one package and compares its SHA256 with the index's. A difference
fails the script and says what differed.

While machines installed before `kidux-apt-source` 0.1.5 still follow
`https://kidux.org/apt`, the script then packs the same suite into one
tarball, sends it to the repository's `archive` release, and asks for the
site's workflow (website.md), which unpacks it under `apt/` beside the
pages after checking its signature against the keyring. Those machines move
to the new address at their next upgrade, which unattended-upgrades does
within a day of a release. GitHub Pages logs nothing, so the old address
goes on a rule rather than on a count: when the owner's known machines all
fetch from `apt.kidux.org` and a month has passed since that release, the
tarball, the release, the workflow's job and `ci/build-site.py --archive`
go (apt-archive-plan.md, A.5).

Nothing is signed on the hosting or on GitHub. The suite is signed on the
release machine when `ci/promote.sh` exports it, and what is published is
those bytes. The script refuses a stable suite that is not signed with the
key `kidux-archive-keyring` ships, or that holds a development build.

**What the logs count.** Every fetch from a Kidux machine carries
`User-Agent: Debian APT-HTTP/1.3 Kidux`, from
`/etc/apt/apt.conf.d/60kidux-user-agent` in `kidux-apt-source`: nothing of
the machine, so that one looks like another. A machine fetches `InRelease`
once a day, so the distinct addresses that fetched it on a day are the
machines following the archive that day, near enough; a `.deb` fetched is
an install or an upgrade of that package. *Share usage statistics*, on the panel's Advanced page and asked by the
first-run wizard, on unless an adult turns it off, adds an identifier the
daemon makes for that alone, random and of this machine's, in
`61kidux-statistics`; with it, machines are counted one by one rather than
by address. Nothing of a child's is in any of it, since the archive is
fetched by the machine, as root, at times a timer chooses.

```
ci/usage.py fetch              every day's access log not kept yet, up to yesterday
ci/usage.py report [--days N]  the machines per day, and the packages they downloaded
```

The hosting writes one access log a day for the space `kidux.org`, at
`https://logs.cluster131.hosting.ovh.net/kidux.org/osl/kidux.org-DD-MM-YYYY.log`,
behind the password of a logs user, about five minutes behind the requests;
how long it keeps them is not said, so `ci/usage.py fetch` keeps every day
it has not kept yet, gzipped, in `~/.local/share/kidux/usage/` on the
release machine, which also keeps the year of connection logs a hosting's
customer is asked to. The logs user's line is in the same netrc file as the
SFTP one. `report` reads only `apt.kidux.org`'s lines: a machine counts on a
day when it fetched `InRelease`, by its identifier or, without one, by its
address; an identifier that begins with sixteen zeros, or that
`ci/usage-test-ids.txt` lists, is a test machine's and never counts; other
apt clients, browsers and crawlers are counted apart. It shows the machines
by day, ISO week and month, with an estimate of them all: each address
without an identifier counts as the median number of machines the
identified ones show behind an address, which a school's many machines do
not pull up. And the places many machines come from over the last thirty
days, an address with three or more, or a range of near ones, a /24 or an
IPv6 /48, which may be a school or a centre, or only a provider's
neighbours.
`tests/project/usage.py` holds it to lines in the hosting's own shape.

The same counting runs on the hosting, as a page for the owner,
`https://apt.kidux.org/usage/`, behind a password its `.htaccess` asks
for. `ci/publish-usage.sh` puts it there: `usage.py`, its list of tests'
identifiers, the daily task `cron.php`, the logs user's line and the
page's password go to `kidux-usage/` in the account's home, which no site
serves, and the page, `index.php`, to `apt/usage/` (sources in
`ci/usage-site/`). Opening the page keeps every day's log not kept yet and
shows the numbers, today's so far among them, and links to explore: every
machine with an identifier, its first and last day, its addresses and how
often it changed address; every address, with the machines behind it and
its range; a machine's or an address's days one by one; every package
Kidux machines downloaded, with the machines that did and those on its
newest version, to see what is most used; a query of the
database, read-only, with examples; and the database's table as CSV. The
database, `usage.sqlite` beside the logs, is made again from the logs kept
at each look, a row a day, address, identifier, client, kind of request,
package and user agent, with how many requests, so that the logs stay what
it all comes from; the hosting's scheduled
task (*Tareas programadas - Cron*, `kidux-usage/cron.php`, daily) keeps
them on the days nobody opens it. The hosting's Python is 3.7, which
`usage.py` keeps to. Its two secrets on the release machine, outside the
repository: the logs user's line in `~/.config/kidux/apt-hosting.netrc`,
and the page's user and password as Apache reads them,
`~/.config/kidux/usage-page.htpasswd`, made with `openssl passwd -apr1`.

The source of what the archive holds is the repository itself, and for the
programs built at development time the source tarballs of their releases
(D71); the suite's own source packages are not copied.

So a release reaches a family in four commands, the last two new:

```
ci/test-release.sh <label>     everything built, published to testing and tested
ci/promote.sh                  into stable
ci/push.sh                     the tree it was built from, inside the hours
ci/publish-public.sh           stable, to kidux.org/apt
```

## Testing before a real machine

```
tests/run acceptance
```

Boots stock Debian under QEMU, installs the published packages the way an adult
would, and prints one line per check. The VM starts from an untouched image every
time and writes nothing back, so there is nothing to clean up and no way for one
run to poison the next.

The checks are the files in `tests/acceptance/`, which the VM fetches from the
host and runs in order; `tests/lib/seed/user-data` is the cloud-init that starts
it. Add a check there when a package starts promising something new.

The VM points the shipped apt source at `testing`, because this run is what
qualifies a package for `stable`. It edits the file the package installed rather
than writing one of its own, so the shipped file is what gets exercised.

The last two checks are the negative half: the keyring is removed and `apt
update` must then **fail**. Without them the rest would pass just as happily on
an archive anyone could write to.

Both VMs tell apt not to fetch Debian's source index or its translations. That
is about 17 MB of the 27 MB apt would otherwise pull through QEMU's emulated
network on every run, and it was most of the wait.

### Trying a change

```
tests/run unit kidux-greeter                 # its unit tests, from the tree
tests/run vm up                              # once: a session machine left up
tests/run vm push kidux-greeter              # after each change
tests/run vm test 13                         # or look at it over VNC
tests/run vm down
```

The quick loop (tests/README.md): a change tried in minutes on a machine
that already runs Kidux, the whole battery kept for before the work is
pushed (D72). `vm
push` builds each package named from a copy of its source whose changelog
gains an entry for `<version>~dev.<time>`, in `build/dev/<time>/`,
publishes that to the testing suite with `KIDUX_DEV_BUILD=1`, which keeps
the other development builds there, installs it on the machine left up, and
starts again what it runs. The version sorts before the tree's own build of
the same version and is never the same twice, so no published version ever
changes its bytes. The battery builds and publishes the packages changed in
a piece of work the same way, with `KIDUX_DEV_STAMP` (`ci/build-package.sh`,
`ci/devbuild.py`), into a directory of its run's own; the version itself is
built and published by the release run (D93), `ci/publish-local.sh`
without `KIDUX_DEV_BUILD`, which removes the development builds and puts
the version in their place on every machine.
A push of a version the archive already holds is refused, since a
development build of it would be older than the archive's (D77). `ci/promote.sh` refuses
while testing holds one. pyproject.toml gets the version as Python writes
one, `<version>.dev<time>`, which also sorts before the version. A package
that needs a version another is bumped to in the same work depends on it
with a tilde, `python3-kidux (>= 0.1.53~)`, which that version's
development builds satisfy as well as the version itself; a `Breaks` on
older versions is written `(<< <version>~)` the same way.

### The session, from outside the machine

```
tests/run session
```

A second VM, rebooted into Kidux and driven from outside through QEMU's
monitor: it types, presses the power button and photographs the screen. It
goes through the first-run wizard by keyboard, signs children in and out,
locks and unlocks, opens the adult panel, tries every door session.md
section 6 closes, and purges `kidux-session` at the end to prove the machine
comes back as Debian. session.md section 8 lists every check. Its pictures
land in `build/vm/session-NN-<screen>.png`, numbered in the order taken.

Its VM uses QEMU's standard VGA card. With no display attached, the virtio
card never completes a frame, and a Wayland client waits for one before
drawing its next: the screen would stay on its first frame until a key was
pressed.

### Before a release: everything, in one command

```
ci/test-release.sh [label]
```

The project checks, every package built with its tests and lintian,
publishing to `testing`, and then four stages at once: every package built
twice into the same bytes, the acceptance VM and the two session VMs, one
set up in Spanish and one in English. The four share nothing but the
archive, which is not written to until they are done, and the base image,
which the VMs only read; the rebuilds run under `nice`,
so that the VMs, whose tests wait on screens, come first. Each stage gets a
PASS or FAIL line with the minutes it took, and a log in
`build/releases/<label>/logs/`. The label defaults to the current commit.

Both VMs start from `build/vm/debian-13-kidux-deps.qcow2`, which
`tests/lib/warm-image.sh` makes from the stock cloud image: every Debian
package the archive's Kidux packages would bring, as they are brought on
a family's machine — the family with Debian's recommendations, as
`apt-get install kidux-base` brings them, the modules without, as the
daemon installs them — already installed and marked as installed for
them, and nothing of Kidux's own, so that each machine skips minutes of
downloads. It is made again whenever a dependency line in the archive or
the stock image changes. A release runs the battery cold, from the stock
image, as a family's machine starts:

```
KIDUX_VM_COLD=1 ci/test-release.sh <label>
```

so that a dependency a package forgot to declare, but which the warm image
happens to hold, is still caught. The `release` job on GitHub always runs
cold.

A stage that failed for a reason outside the code (a mirror down, a
machine that did not come up) is run again on its own, against what the
run built and published:

```
ci/test-release.sh <label> --only session      # or project, reproducible, acceptance
```

It builds nothing, so it tests byte for byte what the rest of the run
tested, and it refuses if the archive's testing suite, the packages'
sources or the machines' seed (`tests/lib/seed/`) are no longer what
`<label>` built and tested. Its verdict replaces that
stage's in `build/releases/<label>/verdicts`, marked as a rerun, and a
session rerun takes the pictures again.

Then the pictures. All of the session VM's are kept in
`build/releases/<label>/screens/` and compared with the previous run's by
`tests/lib/screenshot-diff.py`: `build/releases/<label>/report/index.html` shows
each screen before and now, with what changed in red. Whether a change is
right is for a person to judge; the report only makes sure nothing changed
unseen. The session tests run at the same time on two machines, one set up
in Spanish and one in English (`tests/run session` and `session-en`): every
test in Spanish, and in English the tests that photograph a screen the guide
shows, set the machine up, or check that every screen fits, so that every
screen of the guide is photographed in both languages and a longer English
word that no longer fits is caught, without checking twice what does not
depend on the language. When everything
passed, the pictures the user guide and the README use, listed in
`tests/lib/doc-screenshots.txt`, are copied to `docs/images/es/` from the Spanish
run and to `docs/images/en/` from the English one, so each document shows its
own language and never a screen that no longer looks like that; `git diff
--stat docs/images` then says which of them changed, to be committed with the
release.

## Continuous integration

`.github/workflows/tests.yml` runs this machine's own commands in a
`debian:trixie` container on GitHub's runners, so that a result there means
what it means here. Three jobs, by what they cost (D38):

| Job | Runs | When |
|---|---|---|
| `project` | `tests/run project` | every push and every pull request |
| `build` | `ci/build-all.sh`: every package with its unit tests and lintian | every pull request, and every push to a branch other than `main` |
| `release` | `ci/test-release.sh`, the test machines included | by hand (*Run workflow*), before a release |

The development machine is where the battery runs (D39); GitHub is a second
pair of eyes on a pull request, not the place tests live.

`ci/setup-ci-host.sh`, run as root in the container, is the counterpart of
`ci/setup-dev-host.sh`: the toolchain, a user `builder` to build and test as,
`/srv/kidux-apt`, the name `kidux.local`, `/dev/kvm` for the test machines,
the build chroot, and **a signing key made for that run alone**. The
archive's real key is never in CI and the workflow names no secret at all;
`tests/project/scripts.sh` fails if one ever does. The run's key reaches the
scripts through the environment:

```
KIDUX_SIGNING_KEY          the fingerprint reprepro signs with, instead of
                           the one in ci/archive/conf/distributions
KIDUX_ARCHIVE_PUBLIC_KEY   its public half: sbuild's extra repository trusts
                           it, and ci/publish-local.sh puts it beside the
                           archive as extra-key.pgp
```

The test machines append `extra-key.pgp` to the keyring the bootstrap
package installed, when the archive has one; on the development machine it
has none. `ci/serve-archive.sh` serves the archive on port 80 without nginx.

The chroot, the cloud image and the last run's pictures are cached between
runs, so the picture comparison has something to compare with. Every run
keeps its packages, and the `release` job its logs, pictures and report,
as the run's artifacts, which is where to look when it fails: the Actions
tab of the repository, since this machine has no access to GitHub's API.

## Using it

```
ci/vm/try.sh            # from the testing suite
ci/vm/try.sh stable     # from stable
```

Boots a throwaway machine that installs Kidux from the local archive, the way
a family's Debian machine would, restarts into it and shows the first-run
wizard. From there it is Kidux, to be used: the wizard, children, their
sessions, the lock screen and the panel, by keyboard and mouse.

Its screen is a VNC display on this machine only, port 5900, password
`kidux`. From the computer you work at, forward it over SSH to a local port
and open a VNC viewer on that; on macOS, Screen Sharing is one. The local
port is 5901 because macOS keeps 5900 for its own screen sharing:

```
ssh -N -L 5901:127.0.0.1:5900 <you>@kidux.local
open vnc://127.0.0.1:5901
```

Viewers that send characters rather than keys, macOS Screen Sharing among
them, are translated through a Spanish keymap, the keyboard to pick in the
wizard; `KIDUX_VM_KEYMAP=us` changes it. The terminal that ran `try.sh` is the
machine's serial console, with a root prompt for looking underneath, and
`ci/vm/screenshot.sh` takes a picture of the screen from another terminal.
`poweroff` at that prompt, or Ctrl-A then X, ends it; nothing is kept.

It exists because the question that matters about a screen, whether a
four-year-old could use it, is one no test can answer.

## The bootstrap problem

Nothing in Kidux can be verified until apt has our key, and the key cannot be
fetched from an archive apt does not yet trust. So two packages are installed by
hand, once. On a family's machine, from the public archive, over HTTPS, as the
user guide's section 2 says:

```
wget https://kidux.org/apt/bootstrap/stable/kidux-archive-keyring.deb
wget https://kidux.org/apt/bootstrap/stable/kidux-apt-source.deb
sudo apt install ./kidux-archive-keyring.deb ./kidux-apt-source.deb
sudo apt update && sudo apt install kidux-base
```

`bootstrap/<suite>/` always holds that suite's current pair under names without
a version, so these lines never go stale; `ci/archive/refresh-bootstrap.sh`
copies them there after every publish and every promotion.

They are two packages rather than one because a package that adds an apt source
has to say so in its name (D21). `kidux-apt-source` depends on the keyring, so
the trust is always in place before the source that relies on it.

A test machine, which is thrown away, installs the same pair from
`http://kidux.local/apt/bootstrap/testing/` and then turns the shipped source to
the development archive, address and suite, and adds the key testing is signed
with, which the archive publishes beside itself, to the keyring:

```
sed -i -e 's|^URIs: .*|URIs: http://kidux.local/apt|' \
    -e 's/^Suites: stable$/Suites: testing/' /etc/apt/sources.list.d/kidux.sources
curl -fsS http://kidux.local/apt/extra-key.pgp >> /usr/share/keyrings/kidux-archive-keyring.pgp
```

The development machine, which is kept, leaves both as shipped and follows
testing as a second source with a keyring of its own (rollout.md, section 3).

The installer image does all of it by itself.

## Translations

Kidux has one gettext domain, `kidux`, for everything it ships, so a word is
translated once and reads the same on the sign-in screen, the lock screen, the
launcher and the adult panel. The catalogues live in
`packages/kidux-common/po/`, because kidux-common is the package that installs
them, and the extractor reaches across every package to fill them.

After changing any user-visible string:

```
ci/i18n-extract.sh      collect the strings, merge into each catalogue
                        ... then translate what is new in po/es.po
tests/project/i18n.sh        confirm nothing was missed
```

`tests/project/i18n.sh` fails on four things: a catalogue template that no longer
matches the source, an untranslated or fuzzy entry, a catalogue that does not
compile, and a literal string handed straight to a widget without passing
through `_()`. It runs as part of `ci/build-all.sh`, so forgetting is loud
rather than silent.

Shared words go in `kidux/vocabulary.py` rather than being typed again in each
screen. A string belongs there when more than one program shows it, or when it
is a term the family learns; a sentence only one screen ever says belongs in
that screen.

A learning module is the one exception: it is installed and removed on its
own, so it brings its own words in its own domain, `kidux-module-<id>`, with
its catalogues in the package's `po/`. `ci/i18n-extract.sh` extracts each
from that package alone and `tests/project/i18n.sh` checks each as it checks
`kidux`'s.

English is the source language and has no catalogue, because an untranslated
string already is English. That is also the fallback when a catalogue is
missing: English on screen beats a traceback in front of a child.

## Module content

Lessons live in their module's package, `packages/kidux-module-<id>/content/<lang>/`
(modules.md, section 3). Every translated file records the
SHA-256 of the English file it was translated from, in its front matter, and
`tests/project/content.py` fails when that no longer matches.

A stale lesson is worse than a stale interface string. A wrong word is obvious;
a fluent Spanish explanation of the *previous* version of an exercise leaves a
child unable to do it and assuming they did not understand. After retranslating,
`tests/project/content.py --update` records the new hash.

The check is on content rather than timestamps, because a git checkout writes
every file with the current time and dates would report the whole project as
stale to anybody who cloned it.

## Conventions

- **Native packages** (`3.0 (native)`), versions starting at `0.1.0`. We are
  upstream; there is no separate upstream tarball to track.
- **`debhelper-compat (= 13)`**, `Standards-Version: 4.7.2`,
  `Rules-Requires-Root: no`.
- **Every package is removable.** A learning module an adult removes must leave
  nothing behind, and `kidux-session` in particular has to be removable as one
  unit, because that is what makes the kiosk hardening safe to try.
- **Package descriptions are read by adults, not by developers.** Say what
  installing it does to the machine, in the words someone setting up a computer
  for their child would use.
- **Python packages build with pybuild** and need `pybuild-plugin-pyproject` in
  their build dependencies. Their tests run during the build, inside the chroot,
  so a broken package cannot be built at all. `pyflakes3` runs alongside them;
  `ruff` is not in trixie.

## Signing

Each suite has its key (`ci/archive/conf/distributions`, D82).

- **`stable`** is signed with the archive's key, fingerprint
  `27E3FC17DBA9E4578268F8EEB3768AF190169C5E`. Its public part is the whole of
  `kidux-archive-keyring`: the one key a family's machine trusts.
- **`testing`** is signed with the development key, which signs unattended
  at every publish. Its public part is `ci/archive/development-key.pgp`,
  which `ci/publish-local.sh` puts beside the archive as `extra-key.pgp`
  for the machines that follow testing. No package ships it, so a family's
  machine never trusts it. In CI, both suites are signed with a key made
  for that run, published the same way.

`tests/project/archive-keys.py` holds the keyring to exactly the key stable
is signed with.

apt verifies the signature on the `Release` file, and `Signed-By` in
`kidux.sources` means it accepts nothing else. That, and not the transport,
is what makes the archive safe: the public one is served over HTTPS, the
development one over plain HTTP like any Debian mirror.

Both private keys are on the development machine, described in
[dev-environment.md](dev-environment.md), section 5.
