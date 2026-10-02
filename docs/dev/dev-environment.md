# Development environment: VS Code + Remote-SSH + Claude Code

Development happens **on the Debian server** (the MacBook Pro 2015, see
[install-debian-macbookpro-2015.md](install-debian-macbookpro-2015.md)), driven from
the main Mac through SSH. Claude Code runs on the server with the existing claude.ai
subscription; no API key, no Anthropic Console credit.

Antigravity was dropped as the primary editor because using Claude inside it requires
paid API credit, and because its extension registry (Open VSX) does not carry
Microsoft's genuine "Remote - SSH" extension.

## 1. SSH from the Mac

`~/.ssh/config` on the Mac:

```
Host kidux
    HostName kidux.local
    User <user>
    IdentityFile ~/.ssh/id_ed25519
```

`kidux.local` resolves through mDNS (`avahi-daemon` on the server), so no fixed
IP is needed. Copy the key once:

```bash
ssh-copy-id -i ~/.ssh/id_ed25519.pub <user>@kidux.local
```

## 2. VS Code + Remote-SSH

1. Install VS Code (code.visualstudio.com) on the Mac.
2. Install the **"Remote - SSH"** extension (publisher Microsoft).
3. `Cmd+Shift+P` → **Remote-SSH: Connect to Host** → `kidux`. The new window
   works directly on the server's file system.

## 3. Claude Code extension (inside the remote window)

Install **"Claude Code for VS Code"**, publisher **Anthropic** (extension id
`Anthropic.claude-code`, verified publisher). Searching "claude" returns many
third-party extensions with similar names (Claude Code Chat, Claude Code Usage, Claude
Code YOLO, …); they are not the official one, and "YOLO" specifically skips permission
prompts. Always check the publisher.

Log in with the usual claude.ai account. Open the repository folder
(`~/kidux` on the server). File changes appear as standard VS Code diffs and
in Source Control; the integrated terminal runs on the server.

## 4. Workflow

- The repository is cloned on the server and synced with GitHub with `git pull` /
  `git push` from the remote window.
- The copy on the Mac (`~/Projects/kidux`) is for documentation and planning;
  code, packages and images are built and tested on the server.
- Headless alternative: `ssh kidux` and run `claude` in the terminal. Same
  login, same cost (none extra).
- Read `CLAUDE.md` at the repository root before starting a session; it holds the
  language and documentation rules.

## 5. Build toolchain and signing key

Set up in step 9.0 of the phase 1 plan; everything here lives on `kidux`.

Packages: `build-essential devscripts debhelper dh-python python3-all lintian sbuild
mmdebstrap reprepro gnupg nginx qemu-system-x86 ovmf python3-pytest python3-dbusmock
pamtester`.

The build chroot is a tarball, not a `schroot` installation:

```
mmdebstrap --mode=unshare --variant=buildd trixie ~/.cache/sbuild/trixie-amd64.tar
sbuild --chroot-mode=unshare --dist=trixie <package>.dsc
```

`--chroot-mode=unshare` needs no root and no `schroot`, so CI runs the same command.
Rebuild the tarball with the same `mmdebstrap` line whenever it drifts from trixie.

**Development archive signing key**, created 2026-09-22:

- ed25519, fingerprint `C5635C3123C0A599645929CF813EF459076E9055`, expires 2028-09-21.
- UID: `Kidux development archive signing key (development only, do not trust for
  releases) <dev-archive@kidux.local>`.
- No passphrase, because `reprepro` signs unattended in CI.
- The private key and the revocation certificate in `~/.gnupg/openpgp-revocs.d/` stay
  on `kidux` and need an off-machine backup.
- The public part is in the repository at
  `packages/kidux-archive-keyring/keyrings/kidux-archive-keyring.pgp`.

This key signs the testing suite only, which never leaves the LAN, and no package
ships it.

**Archive signing key**, created 2026-10-02:

- ed25519, fingerprint `27E3FC17DBA9E4578268F8EEB3768AF190169C5E`, expires 2031-10-01.
- UID: `Kidux archive signing key <info@kidux.org>`.
- It signs the stable suite, the one published at `https://kidux.org/apt`, and its
  public part is the keyring every Kidux machine has: a package signed with it is
  installed by every family's computer without a word.
- No passphrase, so that `ci/promote.sh` signs without anyone typing. It can be given
  one at any time, `gpg --edit-key 27E3FC17DBA9E4578268F8EEB3768AF190169C5E passwd`,
  without changing the key the machines know; `ci/promote.sh` then asks for it.
- The private key and its revocation certificate in `~/.gnupg/openpgp-revocs.d/` stay
  on `kidux`, and need an encrypted off-machine backup, as the development key's.
- It has to be renewed, `gpg --quick-set-expire`, and the keyring package released
  with the renewed key, well before October 2031: a machine that only knows the
  expired key stops taking updates.

## 6. Optional: Antigravity with Gemini

If Antigravity (antigravity.google) is ever preferred, use its bundled Gemini model and
its own third-party Remote-SSH implementation against the same `kidux` host.
Claude inside Antigravity needs paid credit on `console.anthropic.com`, independent of
the claude.ai subscription, which is why it is not the default.
