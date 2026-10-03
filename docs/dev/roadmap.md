# Roadmap

Phases in order of priority, no fixed dates. Phase 3 is built before phase 2
(D31): the first family machine, the development MacBook, gets Kidux from the
package archive, and the VMs stand in for the ISO until it exists, so the
module framework and GCompris come first and the ISO waits for as long as it
can. Each phase assumes what it builds on is reasonably stable.

## Phase 0 — Infrastructure (complete)
- [x] Requirements and roadmap.
- [x] GitHub repository.
- [x] Project conventions (`CLAUDE.md`): English code and dev docs, bilingual public
      docs, i18n as a launch requirement.
- [x] Architecture and decision log (`docs/dev/architecture.md`).
- [x] Debian 13 installed on the MacBook Pro 15" (2015) development server.
- [x] Stable SSH access from the Mac; VS Code Remote-SSH working.
- [x] Claude Code on the server, authenticated with the existing subscription.
- [x] Public product name: **Kidux**, from *kid* + *tux* (see D19).

## Phase 1 — Base system, access control and i18n foundation
- [x] Packaging skeleton and signed apt repository: local on the LAN first, GitHub
      Pages from phase 2.
- [x] `kidux-common`: shared Python library, state format, i18n bootstrap, avatars.
- [x] `kidux-daemon`: privileged D-Bus service with polkit; adult password, child
      accounts, audit log.
- [x] Access control in the daemon: unlimited, daily-limit and adult-authorised modes;
      time accounting that survives a reboot; warnings, then a lock that freezes a
      session instead of ending it.
- [x] `kidux-session`: `greetd` + `cage`, session wrapper, locker unit, and kiosk
      hardening (VTs, SysRq, Ctrl+Alt+Del, GRUB password, polkit rules, ptrace).
- [x] Sign-in screen and lock screen, both running outside any child's session; the
      power button always reaches the lock screen.
- [x] Adult panel and first-run wizard: children, access modes, module switches,
      "Update" action.
- [x] `kidux-launcher`: the child's screen, remaining time, Lock and Log out.
- [x] i18n CI checks: no untranslated `es.po` strings, content trees in parity.

## Phase 2 — First installable image
- [ ] `live-build` configuration in `image/`, hybrid ISO (UEFI + BIOS), live session
      is the kiosk itself.
- [ ] Calamares with our branding, translated, guided layout with separate `/home`,
      and a "Reinstall, keep my data" path; the non-free firmware ticked by
      default and untickable (D74).
- [ ] GitHub Actions: build ISO on tag, QEMU smoke test, publish to Releases.
- [ ] Install on the development MacBook and on at least one old BIOS-only PC.
- [x] The package archive's stable suite published at `https://kidux.org/apt`,
      signed with a key of its own, which the user guide's installation on
      Debian fetches from (D2, D81, D82).

## Phase 3 — Module framework
- [x] Module manifest format and `kidux-module-*` packaging template.
- [x] Enable and disable per module and per child through the daemon; launch
      under `systemd-run` scopes, the child's home shared by every module.
- [x] Several modules at once, and the launcher's bar.
- [x] Install and remove modules from the panel through the daemon.
- [x] `kidux-webapps`: local static server + Chromium application window per module.
- [x] Reference module `kidux-module-hello` end to end.
- [x] First real module with zero own content: GCompris.
- [ ] **Children start using the MacBook daily** with the kiosk and GCompris; from
      here on every phase is dogfooded at home.
- [x] Every module closes from the launcher's bar: asked first, forced only after
      a question (D45).
- [x] Modules on offer named and described in the machine's language before they
      are installed, from their packages' control fields (D47).
- [x] GCompris's description says it needs the internet (D48).
- [x] One display scale for every screen, automatic until an adult chooses one,
      in finer steps; a larger screen is more space (D49, D53).
- [x] The adult sets a child's time left for today, zero included (D50).
- [x] *Advanced* settings on the panel's System page, Chromium's flags for a
      machine's graphics first (D51, D52).
- [x] Windows as a setting of the child: modules that can be moved, resized, put
      fullscreen and opened several at once; a module may require it (D46).
- [x] The quick loop: a change tried in minutes on a machine that already runs
      Kidux, the whole battery for the end of a step (test-battery-plan.md, B7).
- [x] A child's time on the days of the week an adult ticks (D54).
- [x] Modules say who they are for: an age range, and the modules best done first
      (D55).
- [x] `labwc` as the child's compositor, XWayland on, an X11
      stand-in module in the tests, the whole sizes marked as preferred (D58, D59).
- [x] With windows on, every window on one desk, in `labwc`'s frame with its
      buttons, and the bar as the taskbar (D57).
- [x] A laptop's keys for its screen, keyboard light and sound, the corner of
      the child's screen showing them and the battery, the lid powering the
      panel off, and the bar saying the keys (D61, D64).
- [x] The network page of the panel, the versions shown, Chromium in the
      child's language, and the trusted screens' keys and lid (D61, D62).
- [x] The second hand test's findings: the keyboard light writable, the
      corner on every screen and answering at once, the network page in a
      second, the scale on every start, Alt+Tab written on Home (3.24).
- [x] What does not fit scrolls, and shows it, on every screen (D63).
- [x] The third hand test's findings: a laptop's keys on the trusted screens,
      the scale when the panel closes, the bar's room for the modules, and
      Alt+Tab going round with the bar (3.27, D64).
- [x] Every screen tested and photographed in Spanish and in English, each
      document showing its own language's pictures (3.28, D65).
- [x] Alt+Tab round the modules in the bar's order, Home out of it (3.29, D66).
- [x] A session left alone locks itself, the screen turns off, the lid locks;
      the minutes are the adult's to set (3.30, D67).

## Phase 4 — Content modules
- [x] A program that is not in trixie built at development time in a machine of
      its own, published as a tarball, and packaged from it (4.1, D68).
- [x] The test modules named `[Test]`, and out of the user guide (4.2, D70).
- [x] Typing: tuxtype (4.3); own course later.
- [x] Scratch: the official editor served locally, and TurboWarp beside it for a
      slower computer; the child's projects saved and opened as files (4.4, 4.5, D69).
- [x] ScratchJr, from the community desktop port, and Blockly Games (4.6, 4.7, D69).
- [ ] micro:bit: MakeCode and micro:bit Python Editor static builds served locally,
      guided projects, WebUSB/USB access for the child user.
- [x] BASIC: wwwBASIC in an editor of Kidux's own, with its guide beside
      it (phase-4b-plan.md 4.10, 4.11, D84).
- [ ] Weigh offering wwwBASIC the fixes in kidux-module-basic's `patches/`
      as a pull request, documented and explained, once phase 4 is done
      (D88); the owner reviews and edits it before it is sent.
- [x] A web module that is a door to one website on the internet, held to
      that site's hosts (4.12, D85).
- [x] CodeCombat, a door to codecombat.com, nothing of it shipped, not
      connected with CodeCombat (4.13, D86).
- [x] Wikipedia, a door to the encyclopedia (4.14, D87).

## Phase 5 — AI learning module
- [ ] `kidux-ai-gateway`: adult-held credentials, guardrails, logging visible to
      adults.
- [ ] Guided projects in which the child builds and uses simple agents safely.

## Phase 6 — Python module
- [ ] Course design: turtle graphics, Pygame Zero games, micro:bit.
- [ ] Progressive projects with automatic checking and feedback in Thonny.

## Phase 7 — Public release 1.0
- [ ] Upgrade tooling: unattended security updates, panel-driven feature updates,
      tested reinstall-keeping-data.
- [ ] Tests on 3+ machines with different hardware (UEFI, BIOS, low RAM).
- [ ] The user guide complete in both languages, with final screenshots.
- [x] Public name and visual identity (`branding/`).
- [x] The website (`site/`, website.md).
- [x] The website counts its visits, once the visitor says yes (D83).
- [ ] Its download page: `download` in `site/site.toml`, once there is an image.
- [x] A Plymouth splash screen with Kidux's logo for the installed system.
- [ ] A themed GRUB menu for the ISO, in the project's visual identity.

## Phase 8 — Future (not planned in detail)
- [ ] Graded web browsing module (Firefox ESR policies).
- [ ] Linux system administration module.
- [ ] Debian 14 "forky" upgrade path.
- [ ] Third language, driven by a volunteer translator.
