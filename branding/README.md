# Kidux visual identity

The logo, the mascot, the colours and the type, and how to use them. The
originals are the SVG files in `svg/`; `png/` holds them rendered at the sizes
anyone is likely to need, with transparent backgrounds, and
`ci/render-branding.sh` produces `png/` from `svg/`, and `sheet.png`, every
piece on one page with its name. Edit an SVG, run the script, commit all of it.

## 1. The pieces

| File | What it is | Use it for |
|---|---|---|
| `svg/logo.svg` | The mascot and the wordmark side by side | The first thing on a page, a slide, a boot screen, the installer |
| `svg/wordmark.svg` | The word *kidux* alone, ink on transparent | Wherever the logo is too tall or there is already a picture: headers, footers, small print |
| `svg/mascot.svg` | The penguin chick alone | Empty states, "nothing here yet", stickers, anywhere a friend helps |
| `svg/icon.svg` | The mascot on a rounded sky-blue square | App icons, favicons, a desktop file, anything that has to be square |
| `svg/logo-on-dark.svg`, `svg/wordmark-on-dark.svg`, `svg/mascot-on-dark.svg` | The same three for dark places: cream ink, and the mascot with a lighter body and a cream halo | On any dark background |
| `svg/wordmark-mono.svg` | The wordmark in one colour, dot included | One-colour printing, engraving, stamps |

Every PNG is `png/<name>-<size>.png`. Square things are named by width,
wide things by height: `icon-64.png` is 64 px wide, `wordmark-64.png` is 64
px tall.

## 2. The mascot

A penguin chick, after Tux: Linux's penguin, still small. Round body, one
white front from the eyes to the belly, a tuft of three feathers, orange beak
and feet, and pink cheeks. It is built from the same rules as the children's
avatars in `packages/kidux-common/data/avatars/`: flat shapes, no gradients,
nothing thinner than four units, so it reads at 32 px on a tab and at a metre
wide on a wall.

It has no name yet. The owner picks one.

Rules:

- It faces the viewer. No side views, no poses, until someone draws them
  in the same style; then they go in `svg/` too.
- It is never stretched, tilted, recoloured or given an outline, except in
  `mascot-on-dark.svg`, where the body is a lighter blue with a cream halo
  so that it stays a penguin on a dark background rather than an egg.
- It never wears text.
- Clear space around it: at least a quarter of its height on every side.

## 3. The wordmark

*kidux*, lower case, drawn as one continuous rounded stroke: it is not set in
a typeface, so it needs no font and looks the same on every machine and in
every program. The dot of the *i* is the beak's orange, which ties it to the
mascot; the one-colour version uses ink for the dot.

Rules:

- Always lower case, always this drawing. Never typed in a font, not even
  Andika.
- Smallest sizes: 24 px tall on a screen, 6 mm tall in print. Below that,
  use the icon.
- Clear space: the height of the *x* on every side.
- In the logo, the mascot's height is twice the wordmark's height, and the
  gap between them is half the wordmark's height; `logo.svg` has this built in.

## 4. Colours

| Name | Hex | Where it lives |
|---|---|---|
| Cream | `#fff6e9` | The background of every trusted screen, the paper of every document |
| Ink | `#3b2f2a` | Text and the wordmark: a warm dark brown, never pure black |
| Night | `#24313f` | The mascot's body |
| Deep | `#141c26` | Dark backgrounds, on which the on-dark versions go; never the mascot's own colour, or the body vanishes into it |
| Snow | `#fdf6f0` | The mascot's front; the white of eyes and pages on dark |
| Sun | `#f0a202` | The beak and feet, the dot of the *i*: the one accent, used sparingly |
| Sky | `#cfe3f3` | The icon's square; calm surfaces; the owl avatar's background |
| Peach | `#f6d7c4` | Cheeks; notices on the screens are a deeper `#ffe2c6` on `#7a3310` text |
| Tangerine | `#e2703a` | The fox; a second accent when Sun is already in use |

The children's avatars each have their own background colour, and on the
sign-in screen each child's tile is tinted with it. Those colours belong to
the avatars and are not brand colours; they are listed in the avatar files.

Contrast: Ink on Cream is 12:1 and Snow on Night is 12:1, both well over
the 7:1 that text for young readers should have. Sun is for shapes and dots,
never for text on Cream.

## 5. Type

- **On the screens**, Andika (`fonts-sil-andika`, SIL Open Font License):
  SIL's typeface for beginning readers, with a single-storey *a* and an *I*,
  *l* and *1* that cannot be mistaken for one another. Regular for text, Bold
  for names and titles. The sizes the sign-in screen uses are in
  `packages/kidux-greeter/kidux_greeter/view.py`: 24 px body, 26 px on
  buttons, 30 px names, 40 px titles, 56 px the clock, all at scale 1.
- **In documents and on the web**, Andika where it can be embedded, and
  Noto Sans otherwise. Never a typeface with a two-storey *a* in anything a
  child reads.
- **In code and terminals**, whatever the reader has.

## 6. Do and do not

- Do put the logo on Cream, Snow or white, and the on-dark versions on Deep or
  any other dark colour that is not the body's own.
- Do use the icon where the space is square and the mascot where it is not.
- Do not put the logo on a photograph or a busy pattern.
- Do not add drop shadows, gradients, bevels or a second colour to the
  wordmark.
- Do not draw the mascot doing things in a different style; ask for a new
  file in this one.
- Do not use Sun for text.
