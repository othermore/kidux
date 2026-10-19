# APT archive plan — the stable suite on a server of Kidux's own

A family's machine fetches Kidux from `https://apt.kidux.org`, the folder
`apt` of the project's OVHcloud web hosting, whose server logs say how many
machines follow the archive and which modules they install without
identifying a family (D109; packaging.md, "The public archive"). This plan
is how it was built and what is left of it. It follows D93: a package gets
its next version at its first change, the work stays in `~dev` builds until
the battery has passed, and the release is one battery and one `--release`.

## 1. Steps

| Step | What | State |
|---|---|---|
| A.1 | The hosting: the subdomain, its certificate, the `apt/` folder and the credentials in a file outside the repository | built |
| A.2 | `ci/publish-public.sh` mirrors the stable suite to the hosting, in an order a machine can fetch from at any moment, and checks what it published | built |
| A.3 | `kidux-apt-source` names the new address, and tells the server it is Kidux | built |
| A.4 | *Share usage statistics*: a switch on the panel's Advanced page and a question of the first-run wizard, on by default, which adds an identifier of the machine's own to every fetch | built |
| A.5 | Both addresses serve stable until every machine has moved; then GitHub Pages stops serving `apt/` and the site's workflow is decoupled from the archive | the old address still serves |
| A.6 | `ci/usage.py`: what the logs say, in a few numbers; every day's log kept; a page for the owner on the hosting, `apt.kidux.org/usage/`, behind a password | built; the hosting's daily task to set in its panel |

### A.1 The hosting

The hosting serves the folder `apt` as `apt.kidux.org` (OVHcloud's *Mis
sitios*), with *Registros separados* on, so that the subdomain has log files
of its own, and a Let's Encrypt certificate the hosting issues and renews.
Files reach it over SFTP, with one credentials file on the release machine,
`~/.config/kidux/apt-hosting.netrc`, mode 0600, that nothing prints, passes
on a command line or commits. The hosting's git integration is not used
(D109).

### A.2 Publishing

`ci/publish-public.sh`, as packaging.md describes it: pack, send `pool/`
and `bootstrap/`, send the indexes with `InRelease` last, remove what no
index names, check what the address serves with `gpgv` and by comparison,
then the old address.

### A.3 The source on a family's machine

`kidux.sources` names `https://apt.kidux.org`; the suite, the component and
`Signed-By` are unchanged, so the key a machine trusts is the same.
`60kidux-user-agent` gives every fetch `User-Agent: Debian APT-HTTP/1.3
Kidux`, with nothing of the machine in it.

### A.4 Share usage statistics

The daemon keeps `apt_statistics` in `config.toml`, on by default, and
with it, once made, `apt_statistics_id`, a random identifier of this
machine's for this alone, never the system's `machine-id`. With it on, the daemon
writes `/etc/apt/apt.conf.d/61kidux-statistics`, a `User-Agent` with the
identifier appended; turning it off removes the file, and the identifier
stays, so that turning it on again counts the same machine. The panel's
Advanced page has the switch with a sentence on what is shared and what is
not; the first-run wizard asks the same question, so that an adult decides
at the start, and may turn it off there. The user guide's section 10 says what the server records.

### A.5 Moving every machine

A machine installed before `kidux-apt-source` 0.1.5 names
`https://kidux.org/apt` until its next upgrade, which unattended-upgrades
does within a day of a release. So both addresses serve the same stable
suite: the script publishes to the hosting and, as before, to the `archive`
release the site's workflow unpacks. GitHub Pages keeps no log, so nothing
says when the last machine has left the old address; the new one's logs
say which machines have arrived. The old address goes when the owner's
known machines all fetch from `apt.kidux.org` and a month has passed since
the release that moved them, long enough for any machine that is switched
on now and then:

- `ci/publish-public.sh` loses the tarball and the GitHub release;
- `.github/workflows/site.yml` loses the job that downloads the archive and
  the refusal to publish without it, and `ci/build-site.py` its `--archive`
  option;
- the `archive` release on GitHub is deleted;
- packaging.md, website.md and D109's documents say so.

### A.6 What the logs say

A machine fetches `InRelease` once a day, so the distinct addresses that
fetched it with the Kidux `User-Agent` on a day are the machines following
the archive that day, near enough; the distinct identifiers among them are
the machines whose adult shares statistics, counted one by one. A `.deb`
fetched is an install or an upgrade of that package.

`ci/usage.py fetch` downloads each day's access log from the hosting's logs
space, `https://logs.cluster131.hosting.ovh.net/kidux.org/osl/`, with the
logs user's line of the same netrc file, and keeps it gzipped on the
release machine; `report` prints machines per day, by identifier and by
address, the packages Kidux machines downloaded by version, and other
clients apart (packaging.md, "The public archive"). The same script runs on
the hosting behind `https://apt.kidux.org/usage/`, a page with a password
that `ci/publish-usage.sh` puts there, keeping the logs on the hosting
itself; a scheduled task of the hosting's runs `fetch` every day, set once
in its panel. The hosting's Logs Data Platform streams are not used, nor a
database: the daily files are what the counting needs, a year of them is
read in a moment, and they cost nothing.
