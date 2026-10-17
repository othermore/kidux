<p align="center"><img src="branding/png/logo-128.png" alt="Kidux" height="128"></p>

<p align="center">
  <a href="https://kidux.org/"><b>kidux.org</b></a> ·
  <a href="README.es.md">Versión en español</a>
</p>
<p align="center"><a href="https://github.com/sponsors/othermore"><img src="https://img.shields.io/badge/Donate-GitHub%20Sponsors-EA4AAA?style=for-the-badge&logo=githubsponsors&logoColor=white" alt="Donate with GitHub Sponsors"></a></p>

**Kidux is a Linux for a child's first computer.** You install it on any
64-bit computer, old or new, and hand the computer over. The child gets a
machine that is theirs. It has their own name and picture on the sign-in
screen, their own password and their own language. It has only what an
adult has decided they may use, and only for as long as the adult has
decided.

Kidux is free for families, and its code is published. It is built on
Debian, in English and Spanish.

## What a child sees

The computer starts on a sign-in screen that shows each child's picture.
A child taps their picture, types their password, and is inside. There is
no desktop, no settings and no way out. The screen belongs to the child,
and everything on it is something an adult chose.

![The sign-in screen, with each child's picture](docs/images/en/sign-in.png)

Inside, the child's screen shows the learning modules an adult has
switched on for them, one tile each. A module can work in one of two
ways, and an adult chooses which for each child:

- **Full screen.** This is how every child starts. Each module fills the
  screen, above a bar that runs along the bottom. From the bar the child
  can go home, go to any other module they have open, or close the module
  on screen. Several modules can be open at once, as on any computer, and
  the child moves between them from the bar or with the keyboard.
- **Windows.** For an older child, an adult can switch windows on. The
  modules then open in windows with a frame and the usual buttons. Several
  can be in view at once, and the child can move them, resize them,
  minimise them and maximise them, as on any computer. The bar along the
  bottom becomes the list of open windows.

![A child's screen, with a tile for each learning module](docs/images/en/launcher-modules.png)

When the child's time for the day is over, the screen locks. Nothing is
lost: what the child was doing waits underneath. An adult can give more
time, let the child save their work, or end the session. The child can
lock the screen themselves whenever they step away. A session left alone
for a few minutes locks by itself, and so does a laptop whose lid is
closed. The child can always turn the computer off.

Brothers and sisters take turns. One signs out and the next signs in, each
with their own password, language and settings.

## What an adult decides

Everything is decided from one place: the adult panel. It opens with the
adult password from the sign-in screen or from the lock screen, and from
nowhere else.

From the panel, an adult:

- adds children, and chooses each child's picture, language, keyboard and
  password;
- decides how each child may use the computer. There are three choices:
  - **whenever they like**;
  - **a set time each day**. The time counts while the session is
    unlocked, and starts again early every morning;
  - **only when an adult says so**. The adult gives time each time;
- chooses, for the first two, which days of the week the child may use
  the computer. Only at the weekend, for instance;
- gives more time at any moment, or sets what is left of today to any
  number of minutes, including none;
- switches windows on or off for each child;
- chooses after how many minutes a session left alone locks itself, and
  after how many the screen turns off;
- adds and removes learning modules, and switches each one on for each
  child.

![A child, in the adult panel](docs/images/en/panel-children.png)

The adult password is never typed inside a child's session, so nothing a
child does on the computer can ever capture it.

## Learning modules

Everything a child does on Kidux is a learning module. An adult adds
modules from the adult panel and switches each one on for each child. For
each module, the panel says which ages it is meant for and which modules
are best done before it.

These are the modules Kidux offers:

- [GCompris](docs/en/modules/gcompris.md): over a hundred activities for
  children from two to ten, about reading, counting, colours, the keyboard
  and the mouse.
- [Tux Typing](docs/en/modules/tuxtype.md): a typing course for
  children from six to twelve. Letters and words fall from the sky, and
  the child catches them by typing them.
- [ScratchJr](docs/en/modules/scratchjr.md): Scratch for the youngest, from
  five to seven, with picture blocks and no words to read.
- [Blockly Games](docs/en/modules/blockly-games.md): puzzles that teach programming
  with blocks, one step harder each time, for children who read a little.
  They work without the internet.
- [Scratch](docs/en/modules/scratch.md): the editor children use at school
  to make games and stories with blocks, for children from eight up. It
  runs on the computer itself, without the Scratch website's community.
- [TurboWarp](docs/en/modules/turbowarp.md): Scratch made faster, with the same
  blocks and the same projects, for a slower computer.
- [BASIC](docs/en/modules/basic.md): the language of the first home computers, through
  [wwwBASIC](https://github.com/google/wwwbasic), with a guide beside it.
  It is for children from eight who read well, and it works without the
  internet.
- [CodeCombat](docs/en/modules/codecombat.md): a door to the [CodeCombat](https://codecombat.com/) website,
  where children learn Python and JavaScript by playing. It needs the
  internet and an account, and most of the site is paid for. Kidux has no
  connection with CodeCombat.
- [Wikipedia](docs/en/modules/wikipedia.md): a door to the whole of
  [Wikipedia](https://www.wikipedia.org/) in the child's language, and to
  its sister projects, with the rest of the internet closed. Wikipedia is
  written for everyone, not only for children.
- [Mail](docs/en/modules/mail.md): a mailbox of the child's own, in
  [Thunderbird](https://www.thunderbird.net/), with the account an adult
  gives. It works with Gmail, Outlook, iCloud or any other provider, and
  the child has nothing to set up.
- [Gmail](docs/en/modules/gmail.md): a door to the [Gmail](https://mail.google.com/) website, for a
  Google account. It is the one way for a child whose account is managed
  with Family Link. It needs the internet, and Kidux has no connection
  with Google.
- [Kig](docs/en/modules/kig.md): geometry a child can move. Points,
  lines, circles and shapes keep their rules when they are dragged. It is
  for children from ten to fourteen, works without the internet, and comes
  with a guide.
- [Kalzium](docs/en/modules/kalzium.md): the periodic table, with what
  each element is like and a drawing of its atom. It is for children from
  ten up, works without the internet, and comes with a guide.
- [Step](docs/en/modules/step.md): a physics playground. Bodies,
  springs and forces go on a plane, and the child runs the experiment and
  measures it. It is for children from ten up, works without the internet,
  and comes with a guide.
- [Simulations](docs/en/modules/simulations.md): experiments to play with on the screen, from
  [PhET Interactive Simulations](https://phet.colorado.edu/) of the
  University of Colorado Boulder, chosen for children from six to
  fourteen. They are kept on the computer itself, in the versions PhET
  published under the CC BY 4.0 licence. Kidux is not connected with PhET.
- [Photography](docs/en/modules/photography.md): a guide to taking photographs with a real camera, for
  children from eight who read well. It has thirty chapters, each with
  something to try with the camera, and it works without the internet.

![GCompris](docs/images/en/module-gcompris.png)

## Getting Kidux

There are two ways to install Kidux:

- **From the Kidux image. Coming soon.** Download the image, write it to a
  USB stick, an SD card or any other external drive, start the computer
  from it and follow the steps on the screen.
- **On Debian.** Install a Debian 13 with nothing else on it, add Kidux's
  package archive and install Kidux from it. The user guide has
  [every step](docs/en/user-guide.md#2-installing-kidux).

## Documentation

- [User guide](docs/en/user-guide.md), also [in Spanish](docs/es/user-guide.md):
  installing Kidux, the first start, and every screen an adult or a child
  will meet.
- [Developer documentation](docs/dev/README.md): how Kidux is built, how
  it works inside, and how to make a learning module.

## Supporting Kidux

Kidux is an independent project, made over weekends and in spare time.
Donations boost our motivation to keep maintaining and improving it, and
help cover some of the costs.

<p align="center"><a href="https://github.com/sponsors/othermore"><img src="https://img.shields.io/badge/Donate-GitHub%20Sponsors-EA4AAA?style=for-the-badge&logo=githubsponsors&logoColor=white" alt="Donate with GitHub Sponsors"></a></p>

## Name and licence

*Kidux* is *kid* and *Tux*, the Linux penguin. The visual identity is in
[branding/](branding/README.md).

Kidux is developed by [Antonio Morales García](https://antonio.mg). Its
own code, images and documents are published under the **Business Source
License 1.1**. The full text, with its terms for Kidux, is in
[LICENSE](LICENSE). Copyright (C) 2026 Antonio Morales García.

In short: anyone may read the code, change it and pass it on. A family
may use Kidux at home, on the computers of the children in their care,
for free. An organisation, such as a school or an academy, needs a
licence, which [info@kidux.org](mailto:info@kidux.org) grants. Four years
after each version is published, that version becomes free software under
the GNU General Public License, version 3 or later. The name Kidux and the
penguin are not covered by the licence.

Kidux is a Debian derivative, and it installs software written by other
people under their own licences, which each component keeps. That is true
of Debian's packages and of the learning modules' programs: Scratch
(AGPL-3), TurboWarp (GPL-3), ScratchJr (BSD-3), Blockly Games
(Apache-2.0), wwwBASIC (Apache-2.0), GCompris (GPL-3), Tux Typing (GPL-2)
and PhET's simulations (CC BY 4.0). The source of each program Kidux
builds is published beside the build, with the changes it is built with.

The Photography guide shows photographs by other people, under Creative
Commons licences or in the public domain, each credited where it is shown.
Some of its pictures were made by a computer, and they say so.
