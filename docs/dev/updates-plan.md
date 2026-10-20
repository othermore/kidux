# Updates: the daily upgrade keeps out of a child's session

The one fault found in how Kidux updates itself, and the work that puts it
right. Nothing else about updates changes: no notice on the sign-in screen,
no search of the machine's own; those are the roadmap's, for later.

## 1. What Kidux does today

Two ways in, one rule, and the rule kept by one of them.

- **Debian's `unattended-upgrades`**, which `kidux-base` depends on and
  configures (`apt/60kidux-unattended-upgrades`) to accept Debian's
  security updates and everything in Kidux's `stable` suite. Debian's own
  timers run it: `apt-daily.timer` refreshes the package lists at 06:00
  and 18:00 plus a random delay of up to twelve hours, and
  `apt-daily-upgrade.timer` installs what the lists know at 06:00 plus up
  to an hour. Both are persistent: a machine that was off when they were
  due runs them soon after it starts. It never reboots on its own.
- **The adult panel's System page**: *Look for updates* and *Install*,
  through the daemon's `kidux-update` unit (daemon.md, section 13).
  *Install* is refused with `SessionActive` while any child has a session,
  and while it runs the daemon answers `updating` to a child who signs in,
  whom the sign-in screen then holds on its waiting screen
  (`Access1_CheckAccess`, `flow.py`).

The rule, which the user guide states, is that an update never changes
anything under a running child's session: dpkg must not replace the
launcher or a module while a child uses it. The panel's way keeps it.
Debian's daily upgrade does not look: it runs under a child's session as
readily as under none, and a child may sign in while it runs. A machine
turned on in the afternoon, whose persistent timer fires within the hour
and whose child signs in meanwhile, is the common case.

## 2. The fix

The daily upgrade stays Debian's; Kidux fences it the way it fences its
own, in both directions.

1. **It does not start under a child's session.** `kidux-base` ships a
   drop-in for `apt-daily-upgrade.service`,
   `/usr/lib/systemd/system/apt-daily-upgrade.service.d/kidux.conf`, with
   `ExecCondition=/usr/libexec/kidux-no-child-session`: a small script,
   also `kidux-base`'s, that exits 0 when no session belongs to a user of
   the group `kidux-children` (`loginctl list-sessions --json`, each
   session's user looked up in the group) and 1 otherwise. systemd then
   skips the service quietly, with no failure, and the timer counts the
   day as run.
2. **No child signs in while it runs.** `Access1_CheckAccess` answers
   `updating` while `apt-daily-upgrade.service` is active, as it does
   while its own `kidux-update` unit applies: the daemon asks systemd for
   the unit's `ActiveState` over the bus (it already talks to the manager
   for its transient units). The sign-in screen needs nothing new: its
   waiting screen says *Updating* and tries again by itself.
3. **A skipped run is made up.** When the last child session ends, the
   daemon starts `apt-daily-upgrade.service` if the service's last run
   was skipped by the condition since the timer last fired, so that a
   machine busy at 06:00 still gets its updates that day. The daemon
   starts the unit through the manager's `StartUnit`, as it starts its
   transient ones; `ExecCondition` is checked again, so a child who
   signed back in meanwhile is safe. Starting the unit is the daemon's,
   not the script's: the script knows nothing of sessions ending.
4. **Nothing else moves.** `apt-daily.timer`, which only refreshes lists,
   is left alone. `kidux-update apply` already waits up to ten minutes
   for apt's lock in case the daily upgrade holds it.

## 3. Packages and versions

- `kidux-base`: the drop-in and `kidux-no-child-session`, and its own
  unit test of the script with a stand-in `loginctl`. Next version
  `0.2.7`, so the screens say *Kidux 0.2.7*.
- `kidux-daemon`: the `updating` answer for the daily unit, the start on
  the last logout, with their tests. Next version `0.3.38`.
- `kidux-greeter`: nothing; `vocabulary.UPDATING` is there.
- Both versions at the work's first change, dated by `ci/hours.py
  changelog-date`; `~dev` builds until the release (D93).

## 4. Tests

- Unit: the script says no with a child's session and yes without, with
  a `loginctl` of the test's own; the daemon answers `updating` while the
  daily unit is active and starts it when the last child logs out after a
  skipped run.
- Session (`tests/session/12-updates.py`, or a test beside it): with Leo
  signed in, `systemctl start apt-daily-upgrade.service` ends skipped, the
  journal saying the condition failed, and nothing is installed; a child
  signing in while a stand-in `apt-daily-upgrade.service` runs (a drop-in
  of the test's own that sleeps) sees the waiting screen and gets in when
  it ends; after Leo logs out, the daemon starts the service and the
  update the test staged is installed.
- Acceptance (`tests/acceptance/02-install.sh` or `07-updates.py`): the
  drop-in is in place and names the condition.

## 5. Documents

- `docs/dev/daemon.md`, section 13: the two directions of the fence, the
  daily unit among what `updating` covers, the start on logout.
- `docs/dev/architecture.md`: D115, the daily upgrade fenced as the
  panel's install is, refining the security-updates row of the table.
- `docs/en/user-guide.md` and `docs/es/user-guide.md`, section 10: the
  sentence that updates never interrupt a child stays, now true of both
  ways; a line that a child who signs in during an update waits for it.
