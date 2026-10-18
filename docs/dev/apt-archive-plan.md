# APT archive plan — the stable suite on a server of Kidux's own

A family's machine fetches Kidux from `https://kidux.org/apt`, which GitHub
Pages serves from the site's own files (D82). GitHub Pages keeps no log of
who fetched what, so nobody knows how many machines follow the archive, nor
which modules they install. This plan moves the public archive to a web
hosting of the project's own, `https://apt.kidux.org` on OVHcloud, whose
server logs answer both questions without identifying a family, and leaves
GitHub Pages to the website alone. It follows D93: a package gets its next
version at its first change, the work stays in `~dev` builds until the
owner tries it, and the release is one battery and one `--release`.

## 1. What to check first

Before any step, on the hosting's own panel, since each is a fact of the
plan the hosting has to hold:

- The hosting serves a subdomain from a folder of its own (a *multisite*
  entry, `apt.kidux.org` to `apt/`), with its own Let's Encrypt
  certificate, and `kidux.org`'s DNS can give that name to the hosting
  while `kidux.org` itself stays on GitHub Pages. The DNS zone lives where
  the domain is registered; the record is a `CNAME` for `apt`.
- A file of a few hundred megabytes is served whole, without a limit per
  file or per request: ScratchJr's package is about 380 MB.
- The server's raw access logs can be downloaded, with the client's
  address, the date, the path, the status and the `User-Agent` of each
  request, and for how long the hosting keeps them.
- Files reach it over SFTP, by a user and password or a key. With SSH as
  well, `rsync` does the mirroring; with SFTP alone, `lftp mirror`.
  Either is in trixie.

## 2. Steps

| Step | What | Size |
|---|---|---|
| A.1 | The hosting: the subdomain, its certificate, the `apt/` folder and the credentials in a file outside the repository | S |
| A.2 | `ci/publish-public.sh` mirrors the stable suite to the hosting, in an order a machine can fetch from at any moment, and checks what it published | M |
| A.3 | `kidux-apt-source` names the new address, and tells the server it is Kidux | S |
| A.4 | Both addresses serve stable until every machine has moved; then GitHub Pages stops serving `apt/` and the site's workflow is decoupled from the archive | M |
| A.5 | `ci/usage.py`: what the logs say, in a few numbers | M |
| A.6 | The documents: packaging.md, architecture.md and its decision, layout.md, rollout.md, the user guide's words on updates, the website's | S |

### A.1 The hosting

The credentials live in one file the owner keeps outside the repository,
`~/.config/kidux/apt-hosting`, mode 0600, with the host, the user, the
password or the key's path and the remote folder, and nothing of it ever
appears in a command line, a log or a commit: the scripts read the file.
The same goes for the OVH account itself. Only the release machine, the
one with the production key, holds this file (D82): the public archive is
published from where stable is signed.

### A.2 Publishing

`ci/publish-public.sh` keeps its refusals: not outside the hours (D99),
not a suite the keyring's key did not sign, not one holding a `~dev`
build. It then mirrors `build/public-archive`, the stable suite as D82
packs it today, to the hosting:

1. `pool/` first: every package the indexes name, new ones added, nothing
   removed yet.
2. `dists/stable/` next, each index copied under a temporary name and
   renamed into place, `InRelease` last: a machine fetching in the middle
   sees either the old suite whole or the new one whole, and never an index
   naming a package that is not there yet.
3. Then the packages no index names any more are deleted from `pool/`.

Afterwards it checks what the world sees: fetches
`https://apt.kidux.org/dists/stable/InRelease`, verifies it with `gpgv`
against `kidux-archive-keyring.pgp`, compares it byte for byte with the
local one, and fetches one package the index names and compares its
SHA256. A difference fails the script and says what differed.

`ci/push.sh --then-publish` keeps working as it does: promote, then
publish.

### A.3 The source on a family's machine

`packages/kidux-archive-keyring/sources/kidux.sources` names
`https://apt.kidux.org`; the suite, the component and `Signed-By` do not
change, so the key a machine trusts is the same. The package gets its next
version.

`kidux-apt-source` also installs `/etc/apt/apt.conf.d/60kidux-user-agent`:

```
Acquire::http::User-Agent "Debian APT-HTTP/1.3 Kidux";
```

so that the logs tell a Kidux machine from any other client that fetches
the archive, with nothing of the machine in it: no version, no name, no
identifier. The counting in A.5 needs nothing more.

### A.4 Moving every machine

A machine installed before this change still names `https://kidux.org/apt`
until it upgrades `kidux-apt-source` from there, which unattended-upgrades
does within a day of the release (kidux-base's `60kidux-unattended-upgrades`).
So both addresses serve the same stable suite for a while: the script
publishes to the hosting and, as today, to the `archive` release that the
site's workflow unpacks. GitHub Pages cannot redirect `apt/` to the new
address in a way apt follows, so the old address simply keeps serving.

The old address stops when the logs of the new one show every machine that
followed the old one, or after a fixed time the owner sets (the number of
machines is small and known to the owner). Then:

- `ci/publish-public.sh` loses the tarball and the GitHub release;
- `.github/workflows/site.yml` loses the job that downloads the archive and
  the refusal to publish without it, and `ci/build-site.py` its `--archive`
  option;
- the `archive` release on GitHub is deleted.

### A.5 What the logs say

A machine fetches `InRelease` once a day (apt's daily timer), so the number
of distinct addresses that fetched it with the Kidux `User-Agent` on a day
is the number of machines following the archive that day, near enough: a
household behind one address counts once, an address that changes counts
twice. A `.deb` fetched is an install or an upgrade of that package, so
`pool/` fetches say which modules families install and how fast a release
reaches them.

`ci/usage.py` downloads the raw logs with the credentials of A.1 and
prints, for a range of dates: machines per day, fetches of each package by
version, and the share of clients that are not Kidux (mirrors, crawlers).
It keeps nothing: the logs stay on the hosting for as long as the hosting
keeps them, and the script's output is numbers, not addresses. Nothing of a
child's is in any of it: the archive is fetched by the machine, by root, at
times a timer chooses.

### A.6 The documents

- `docs/dev/packaging.md`, "The public archive": the hosting, the mirror
  order, the checks, `ci/usage.py`.
- `docs/dev/architecture.md`: the overview line on where a family's machine
  fetches from, and a decision in the log: the stable suite is public at
  `apt.kidux.org`, on a hosting of the project's own, for the usage its
  logs give; it supersedes D82's address and leaves D82's key as it is.
- `docs/dev/layout.md`, `docs/dev/rollout.md`, `docs/dev/website.md`: where
  they name the archive's address or the site's workflow.
- The user guide (both languages) and the README: the sentence that says
  where updates come from, and one that says the archive's server logs
  each fetch, with the machine's address and no more, for counting. The
  website says the same in its privacy words (D83, D94 cover the site's
  own counting; this is the archive's).

## 3. After it: the licence

The owner intends to move Kidux from the Business Source License 1.1 (D78)
to the GNU General Public License, version 3 or later, once the archive is
the project's own. It is a separate piece of work and the owner's decision;
what it touches, so that it is one commit and one release:

- `LICENSE`, and `debian/copyright` of every package, `Files: *` from
  `BUSL-1.1` to `GPL-3.0-or-later`, each package at its next version
  (D93), so it is a release of every package;
- the licence paragraphs of `README.md` and `README.es.md`, the licence
  words of `site/en.toml` and `site/es.toml`, which `tests/project/site.py`
  holds to the same keys, and `docs/dev/website.md`;
- `CLAUDE.md`'s licence section, and a decision in the log superseding D78,
  with the rationale: the archive's logs give the project what the licence
  was there to give, a sight of who uses Kidux;
- the four-year clause goes with BUSL, so the sentence about it goes from
  every document that has it.

The name and the penguin stay outside the licence either way.
