# Update watch plan — an update that restarts systemd is not an update that stopped

An update the adult panel installs runs in a unit of its own,
`kidux-update.service`, and the daemon follows it: it reads the job's
status file and asks systemd whether the unit still runs (daemon.md,
section 13). When systemd cannot be asked, the daemon takes the job for
stopped. An update that brings a new systemd makes systemd start itself
again half-way through, and for that moment it answers nothing: the daemon
then says *the update stopped before it finished* while the job is still
installing, lets children sign in under it, and refuses the next job as
`Busy` until the first one ends.

This plan makes the daemon believe that a job has stopped only when
systemd says so, and gives the tests an update that restarts systemd, so
that the fault is seen without waiting for Debian to publish one.

It follows phase-4c-plan.md's rules (section 3 there) and D93: a commit
per step, partial tests while building and never the battery, the package
at its next version and `~dev` builds of it until the owner says yes. Only
`kidux-daemon` changes.

## 1. What happens today

Found by the battery `phase-4h-2`, run cold on 2026-11-24
(`build/releases/phase-4h-2/logs/`).

- The stock Debian image the cold battery starts from is of 2026-10-16.
  On it, *Look for updates* finds 43 packages, systemd among them.
- `tests/acceptance/07-updates.py` and `tests/session/12-updates.py`, in
  both languages, install them through the daemon. The tests' own
  package reaches 1.1, and the machine's console shows systemd starting
  itself again (`systemd 257.13-1~deb13u1 running in system mode`). The
  daemon answers `failed`, *the update stopped before it finished*, while
  `kidux-update.service` is still loaded.
- What follows fails for that alone: the next jobs, a module removed and
  BASIC installed, are refused, since the unit's fixed name allows one
  job at a time.
- From a warm image, which holds Debian's packages of the day, the same
  tests find one package and pass.

Found on the quick loop's machine by step W1, on 2026-11-24, with the
daemon 0.3.39 and the tests' package's 1.1 given a `postinst` that runs
`systemctl daemon-reexec` and then waits ten seconds:

- The daemon answered `failed`, *the update stopped before it finished*,
  2.4 seconds after the start, while `kidux-update.service` was
  `active`. The job went on and ended eleven seconds later, `Deactivated
  successfully`, with 1.1 in place; its verdict was lost, since the
  daemon had deleted the status file when it gave its own. The audit
  trail says `update finished`, `failed`; the daemon's journal says
  nothing.
- systemd is away for about 0.4 seconds: the re-execution is asked for
  at 17:59:56.007 and the new systemd runs at 56.114. A call to systemd
  in flight then fails with `org.freedesktop.DBus.Error.NoReply`
  (*Message recipient disconnected from message bus without replying*)
  after 0.35 to 0.37 seconds, not after the call's own timeout; the next
  call, at once, is answered. Three clients asking without a pause, some
  9000 calls each over 25 seconds, met that one failure each, and no
  other error.
- systemd never answers `NoSuchUnit` for the running unit: before and
  after its re-execution it answers `active`. It answers `NoSuchUnit`
  before the job starts and once it has gone, `inactive` and then
  collected.
- So the fault is a race. The daemon asks every half second, and one of
  its questions in flight during those 0.4 seconds is enough: the first
  try met it, a second, with a 1.2 made the same way, did not and ended
  `updated`. The battery's update, 43 packages with systemd among them,
  met it in all three of its runs: acceptance, session and session-en.

Read from the code:

- `kiduxd/updates.py`, `Updates.poll`: with no verdict in the status file
  and `update_active()` false, the verdict is *the update stopped before
  it finished*.
- `kiduxd/machine.py`, `SystemMachine.update_active`: any failed call to
  systemd, `GetUnit` or the unit's `ActiveState`, is answered `False`.
  The same call fails in two different cases: systemd says there is no
  such unit, which is a job that ended; and systemd does not answer,
  which says nothing about the job.
- `daily_upgrade_state` answers `("", "")` on a failed call, so while
  Debian's daily upgrade restarts systemd, `Updates.installing()` says
  for a moment that nothing is installing, and a child who signs in at
  that moment is let in (D115).
- The calls are synchronous, with a timeout of ten seconds, from the
  daemon's main loop, every half second while a job runs.

A family's machine meets this when an adult presses *Install* on the
panel's System page and the update brings systemd. The update itself
finishes; the panel says it failed. The daily upgrade, which installs
most updates, is not followed through this job; its part is the moment
in which a child may sign in.

## 2. Steps

| Step | What | Size |
|---|---|---|
| W1 | Found on the machine first: an update that restarts systemd, what systemd answers meanwhile and for how long | S |
| W2 | The daemon: three answers from systemd, and a job stopped only when systemd says so | M |
| W3 | The tests: unit tests of the three answers, and the tests' own update restarts systemd | M |
| W4 | The documents, and closing | S |

W1 decides W2's details and is done first; nothing is committed before
it but this plan.

### W1 — Found on the machine first

On the machine left up (`tests/run vm up 11`, which leaves it where
`12-updates.py` starts), as root.

1. *An update that restarts systemd.* `kidux-as canary` makes the tests'
   package, 1.0 installed and 1.1 waiting. Its 1.1 is given by hand a
   `postinst` that does what systemd's own does when it is updated,
   `systemctl daemon-reexec`, and then waits ten seconds, so that the job
   is still running well after systemd is back. Then `kidux-as
   apply-updates`, as the tests run it.
2. *What the daemon says.* The answer of `apply-updates`, the audit
   trail's lines, and the daemon's journal.
3. *What systemd answers meanwhile.* From a shell, over the same seconds,
   `busctl call org.freedesktop.systemd1 /org/freedesktop/systemd1
   org.freedesktop.systemd1.Manager GetUnit s kidux-update.service` in a
   loop, a line each time with the time, the answer or the error's name,
   and how long the call took. Noted: the error's name while systemd is
   away (expected: no reply, or a name without an owner, and not
   `org.freedesktop.systemd1.NoSuchUnit`), whether the call fails at once
   or waits, and for how many seconds systemd is away.
4. *After it.* That the job ends with 1.1 in place, the unit gone and the
   status file's verdict `done:updated`.

If the fault does not show with the restart alone, it is looked for as
the battery found it: a machine from the stock image
(`KIDUX_VM_COLD=1`), Debian's own updates installed through the daemon,
the daemon's journal read. If the cause is another than section 1's, the
step stops and the owner is told.

If systemd answers `NoSuchUnit` for a unit that is running while it
starts itself again, the step stops and the designer is told, since W2's
rule then needs more than one answer (section 5).

**Found** is written into this plan's section 1, in place of *to be
confirmed*.

### W2 — The daemon

`kidux-daemon`, at its next version (section 3).

**`kiduxd/machine.py`.** What the daemon asks systemd about a unit has
three answers, not two:

- **running**: systemd answers, and the unit's `ActiveState` is one of
  `RUNNING`;
- **gone**: systemd answers that there is no such unit
  (`org.freedesktop.systemd1.NoSuchUnit`), or the unit's state is any
  other;
- **unknown**: the call failed in any other way: no reply, a timeout,
  systemd's name with no owner, the bus gone.

`_call` keeps the D-Bus error's name for whoever needs to tell them
apart. The question asked from the update's watch has a timeout short
enough not to hold the daemon's main loop while systemd is away: a
second, or what W1 finds is enough; the lock, the time and the sign-in
are answered from that loop.

**`kiduxd/updates.py`.** The `Runner` protocol gives the three answers
for the update's unit, and the daily upgrade's state with *unknown* told
apart from *no such unit*.

- `poll`: the verdict *the update stopped before it finished* is given
  only on **gone**, after the one more look at the status file that is
  there today. On **unknown** the job is still running: nothing is
  emitted, the watch goes on, and the next poll asks again. A verdict in
  the status file ends the job whatever systemd answers, as today.
- `resume`, after the daemon's own restart: a job with no verdict is
  watched on **running** and on **unknown** alike.
- `start`: `Busy` on **running**, as today. On **unknown** the start is
  tried, and fails as systemd makes it fail.
- `installing` and `make_up_daily`: while the daily upgrade's state is
  **unknown**, the answer is the last one systemd gave; a daily upgrade
  that was running is still running, and nothing is started.
- The daemon logs once per job, at warning, that systemd does not answer
  and the job is taken as still running, and once when it answers again.

No time limit is put on **unknown**: a systemd that never answers again
keeps the job *running*, and children at the waiting screen, until the
status file's verdict or a restart, as the fence on the daily upgrade
has none (daemon.md, section 13).

Nothing changes in `/usr/libexec/kidux-update`, in the D-Bus interface,
in the panel or in any word a person reads.

### W3 — The tests

**Unit**, `packages/kidux-daemon/tests/test_updates.py`, whose
`FakeRunner` gives the three answers:

- a job polled while systemd is **unknown** stays running: no
  `UpdateFinished`, no audit line, `installing()` true; when the status
  file then says `done:updated` the job ends `updated`;
- **unknown** and then **gone** with no verdict ends *the update stopped
  before it finished*, as **gone** alone does today;
- `resume` with a job in the file and systemd **unknown** watches it;
- `installing()` with the daily upgrade last seen running and its state
  **unknown** is true, and `make_up_daily` starts nothing;
- `start` while the unit is **running** is `Busy`.

`fake_daemon.py` and `test_time_and_lock.py`, which have runners of
their own, follow the protocol. If `machine.py` has tests against a
stand-in connection, the three answers are tested there by the error's
name; if it has none, none is made for this.

**On a machine.** `tests/lib/seed/tools/kidux-as canary` gives the 1.1
package the `postinst` of W1: `systemctl daemon-reexec`, then a wait of
a few seconds, with a comment that says why: an update that brings
systemd restarts it half-way, and the job must be followed to its end.
`tests/acceptance/07-updates.py` and `tests/session/12-updates.py` keep
their checks, which now hold over such an update; each gains a sentence
in its header, and 07 a check that the audit trail's *update finished*
is `ok`.

**Tried** with `tests/run unit kidux-daemon`, `tests/run project`,
`tests/run vm push kidux-daemon`, `tests/run vm test 12`, the same in
English, and the acceptance test 07 alone on the machine left up. Before
the fix, with the new `postinst`, test 12 fails as the battery's did:
that is run once and said in the report.

### W4 — The documents, and closing

- `docs/dev/daemon.md`, section 13, *Updates*: how the daemon knows that
  a job has ended. By the verdict in the status file; a unit systemd
  says is gone, with no verdict, is a job that stopped; while systemd
  does not answer, as when an update restarts systemd itself, the job is
  still running and is asked about again.
- `docs/dev/architecture.md`: D124 in the decision log, section 4's
  words.
- `docs/dev/README.md`: this plan among the plans, *built* at the end;
  phase-4h-plan.md is *built*.
- `docs/dev/roadmap.md`: a line where the updates are, ticked at the
  end.
- `tests/README.md` if it describes the tests' update.
- `debian/changelog`: *An update that restarts systemd is followed to
  its end, instead of being reported as stopped while it still runs.*

The user documents do not change: nothing a person sees or does is
different, except that the panel no longer says that such an update
failed.

Then the last message, for the owner, in Spanish: what was built, step
by step with its commit; what W1 found; and the prompt for the designer,
in English.

## 3. Packages and versions

Only `kidux-daemon`: `0.3.40`, dated by `ci/hours.py changelog-date
kidux-daemon`, after reading its changelog on `origin/main`;
`pyproject.toml` and `kiduxd/__init__.py` say the same
(`tests/project/versions.sh`). `tests/lib/seed/tools/kidux-as` is the
tests' own and has no version.

## 4. What was decided

By the owner, 2026-11-24: the daemon is mended before phase 4h is
released, and both are released together.

Taken by the plan, for the owner to overturn:

- **D124 — The daemon believes that an update's job has stopped only
  when systemd says so.** Asked about a unit, systemd answers that it
  runs, that it is gone, or nothing. The daemon read no answer as *gone*,
  so an update that restarted systemd, which every update of systemd
  does, was reported as stopped while it still ran, children could sign
  in under it, and the next job was refused. No answer now means *ask
  again*: the job ends by its own verdict, or when systemd says its unit
  is gone. The same holds for Debian's daily upgrade, whose last known
  state stands while systemd does not answer. No time limit: a child
  waiting is better than dpkg under a child's session.

## 5. What can go wrong

| What | What the plan does |
|---|---|
| The cause is not the one read from the code | W1 confirms it on a machine before anything is changed, and stops if it is another |
| systemd answers *no such unit* for a running unit while it starts itself again | W1 looks; if so it stops, and the rule becomes: *gone* is believed only when systemd has said it for several polls over a few seconds |
| The question to systemd waits ten seconds each time and holds the daemon's main loop while systemd is away | W1 measures how the call fails; W2 gives the watch's question a short timeout |
| systemd never answers again, and children stay at the waiting screen | Left so, by D124: the status file's verdict ends the job; a restart of the computer ends the rest |
| `systemctl daemon-reexec` in the tests' package disturbs the session tests' machine: the sign-in screen, a session | W1 tries it on the session machine before W3 writes it into the tests |
| The tests' update now lasts longer, and a test's wait is too short | The wait in the `postinst` is a few seconds; the tests' own limits are read in W3 |
| The other development machine has work on `kidux-daemon` | Its changelog on `origin/main` is read before the version is taken; the work starts with `git pull --rebase origin main` |
| Something is pushed, released or published before the owner's yes | Never: nothing is released as part of this plan |

## 6. After it

The designer reviews the build. Then, at the owner's word, one battery
run cold, the release run, the release's pictures committed, the branch
`phase-4h-site` rebased, tested and merged, and `ci/push.sh
--then-publish`: `kidux-daemon`, `kidux-module-kydux` and
`kidux-module-expedition-code` in one release.
