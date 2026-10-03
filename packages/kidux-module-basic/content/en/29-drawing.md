# Drawing, colour and sound

`SCREEN 12` turns the screen into a grid of dots, 640 across and 480
down. A dot is named by two numbers in brackets: how far **across** it
is, then how far **down**. `(0, 0)` is the top left corner, and
`(320, 240)` the middle.

![The screen as a grid of dots](screen.svg)

## Colours

Every colour has a number from 0 to 15:

```basic
10 SCREEN 12
20 FOR C = 0 TO 15
30 LINE (C * 40, 200)-(C * 40 + 38, 280), C, BF
40 NEXT C
```

0 is black, 1 blue, 2 green, 3 turquoise, 4 red, 5 purple, 6 brown, 7
grey, 8 dark grey, then the light ones: 9 blue, 10 green, 11 turquoise,
12 red, 13 pink, 14 yellow and 15 white.

## Dots and lines

- `PSET (X, Y), C` paints one dot of colour C.
- `LINE (X1, Y1)-(X2, Y2), C` draws a line from one dot to another.
- With `, B` at the end, `LINE` draws a box with those two corners; with
  `, BF`, a box filled in.
- `CIRCLE (X, Y), R, C` draws a circle around (X, Y), R dots wide from
  the middle to the edge.
- `PAINT (X, Y), C` fills in with colour C from that dot until it meets
  a line of colour C, like paint poured into a shape.

A night sky with three hundred stars, each at a place chosen by `RND`:

```basic
10 SCREEN 12
20 RANDOMIZE
30 FOR N = 1 TO 300
40 PSET (INT(RND * 640), INT(RND * 480)), 15
50 NEXT N
60 CIRCLE (520, 90), 50, 14
70 PAINT (520, 90), 14
```

## A house

```basic
10 SCREEN 12
20 LINE (0, 400)-(639, 479), 2, BF
30 LINE (200, 220)-(440, 400), 4, BF
40 LINE (200, 220)-(320, 120), 6
50 LINE (320, 120)-(440, 220), 6
60 LINE (200, 220)-(440, 220), 6
70 PAINT (320, 180), 6
80 LINE (290, 310)-(350, 400), 6, BF
90 LINE (230, 260)-(270, 300), 11, BF
100 LINE (370, 260)-(410, 300), 11, BF
110 CIRCLE (560, 70), 40, 14
120 PAINT (560, 70), 14
```

The roof is three lines that close a triangle, and `PAINT` fills it.

> [point] Draw your picture on squared paper first, and write down the
> numbers of its corners. Then the program is easy.

## A snowman

```basic
10 SCREEN 12
20 LINE (0, 0)-(639, 479), 1, BF
30 LINE (0, 420)-(639, 479), 15, BF
40 CIRCLE (320, 340), 90, 15
50 PAINT (320, 340), 15
60 CIRCLE (320, 190), 65, 15
70 PAINT (320, 190), 15
80 CIRCLE (295, 170), 8, 0
90 PAINT (295, 170), 0
100 CIRCLE (345, 170), 8, 0
110 PAINT (345, 170), 0
120 LINE (320, 192)-(365, 200), 12, BF
130 LINE (250, 120)-(390, 132), 0, BF
140 LINE (275, 60)-(365, 120), 0, BF
150 FOR B = 1 TO 3
160 CIRCLE (320, 270 + B * 40), 7, 0
170 PAINT (320, 270 + B * 40), 0
180 NEXT B
```

## A flag

The flag of Penguin Island: a line from corner to corner cuts it in
two, and `PAINT` fills each half. Its second number says where to
stop: at the white lines.

```basic
10 SCREEN 12
20 LINE (100, 40)-(110, 460), 7, BF
30 LINE (110, 60)-(530, 300), 15, B
40 LINE (110, 300)-(530, 60), 15
50 PAINT (200, 120), 12, 15
60 PAINT (440, 240), 11, 15
70 CIRCLE (320, 180), 30, 14
80 PAINT (320, 170), 14
```

## Sound

`SOUND F, D` plays a note. F is how high it is: 262 is the note C, *do*,
and the bigger the number, the higher the note. D is how long it lasts,
in eighteenths of a second: 18 is one second.

```basic
10 FOR N = 1 TO 14
20 READ F, D
30 SOUND F, D
40 NEXT N
50 DATA 262, 6, 262, 6, 392, 6, 392, 6, 440, 6, 440, 6, 392, 12
60 DATA 349, 6, 349, 6, 330, 6, 330, 6, 294, 6, 294, 6, 262, 12
```

The notes from C up: 262, 294, 330, 349, 392, 440, 494, and 523 for the
next C.

## A bouncing ball

To move something, draw it, wait a moment, draw it again in black to rub
it out, and draw it a little further on. When the ball reaches an edge,
it turns round, with a sound.

```basic
10 SCREEN 12
20 LET X = 40: LET Y = 60: LET DX = 6: LET DY = 4
30 FOR T = 1 TO 600
40 CIRCLE (X, Y), 12, 0
50 LET X = X + DX: LET Y = Y + DY
60 IF X < 12 OR X > 627 THEN LET DX = -DX: SOUND 880, 1
70 IF Y < 12 OR Y > 467 THEN LET DY = -DY: SOUND 660, 1
80 CIRCLE (X, Y), 12, 14
90 SLEEP 20
100 NEXT T
```

> [cheer] The ball is only ever a circle drawn and rubbed out, fifty
> times a second. That is all a cartoon is too.

## Keep trying

- Give the house a chimney and a door handle.
- Give the snowman arms, two lines of colour 6.
- Draw the flag of your own island.
- Write a tune of your own with `SOUND`, or the start of one you know.

::: adult
The picture stays on the screen when the program ends, and *Stop* keeps
it too. `PAINT` fills up to lines of the colour it is given, or of the
second colour when there is one; a shape with a gap in its outline lets
the paint run out over the screen, which children discover quickly.
:::
