# Programs to keep

These programs use everything in this guide. Type them, play with them,
change them, and save the ones you like with **Save**.

## The reflex game

How fast are you? Press a key as soon as the star appears.

```basic keys=x
10 RANDOMIZE
20 CLS
30 PRINT "WHEN THE STAR APPEARS, PRESS A KEY!"
40 SLEEP 1000 + INT(RND * 3000)
50 PRINT "*"
60 LET T# = TIMER
70 IF INKEY$ = "" THEN 70
80 PRINT "YOU TOOK "; INT((TIMER - T#) * 100) / 100; " SECONDS"
```

`TIMER` is the computer's clock: the seconds it has counted since the
start of 1970, with decimals, a number of ten figures. That is more than
an ordinary box keeps, so the time goes in a `#` box, as chapter 17
showed. Line 60 notes the time the star appeared, and line 80 takes it
away from the time the key came.

## The Ice League

Five penguin teams play basketball. A win is worth 2 points and a loss
1. The program works out the points and puts the teams in order, the
best first.

```basic
10 DIM N$(5), P(5)
20 FOR I = 1 TO 5
30 READ N$(I), W, L
40 LET P(I) = W * 2 + L
50 NEXT I
60 FOR R = 1 TO 4
70 FOR I = 1 TO 5 - R
80 IF P(I) < P(I + 1) THEN SWAP P(I), P(I + 1): SWAP N$(I), N$(I + 1)
90 NEXT I
100 NEXT R
110 PRINT "THE ICE LEAGUE"
120 FOR I = 1 TO 5
130 PRINT I; ". "; N$(I); SPACE$(10 - LEN(N$(I))); P(I); " POINTS"
140 NEXT I
150 DATA PIP, 6, 2, TOM, 3, 5, LULU, 7, 1, BEA, 4, 4, MAX, 2, 6
```

When two shelves go together, a name and its points, they must be
swapped together, as line 80 does. `SPACE$(10 - LEN(N$(I)))` writes
spaces after each name so that the points line up.

## The address book

```basic keys=LULU,Enter,SAM,Enter,Enter
10 DIM N$(4), T$(4)
20 FOR I = 1 TO 4: READ N$(I), T$(I): NEXT I
30 INPUT "WHOSE NUMBER? (ENTER TO STOP) "; W$
40 IF W$ = "" THEN END
50 FOR I = 1 TO 4
60 IF N$(I) = W$ THEN PRINT W$; ": "; T$(I): GOTO 30
70 NEXT I
80 PRINT "NOT IN THE BOOK"
90 GOTO 30
100 DATA PIP, 555 0101, TOM, 555 0102
110 DATA LULU, 555 0103, BEA, 555 0104
```

Pressing Enter without typing anything gives an empty answer, and line 40
ends the program.

## An alphabetical list

Type names in any order, and the computer puts them in the order of the
alphabet. An empty answer means there are no more.

```basic keys=TOM,Enter,ANA,Enter,PIP,Enter,BEA,Enter,Enter
10 DIM N$(20)
20 LET C = 0
30 INPUT "A NAME (ENTER TO FINISH)? "; A$
40 IF A$ = "" OR C = 20 THEN 70
50 LET C = C + 1: LET N$(C) = A$
60 GOTO 30
70 FOR R = 1 TO C - 1
80 FOR I = 1 TO C - R
90 IF N$(I) > N$(I + 1) THEN SWAP N$(I), N$(I + 1)
100 NEXT I
110 NEXT R
120 FOR I = 1 TO C: PRINT N$(I): NEXT I
```

## Your library

Write down your own books in the `DATA` lines: the title, then who wrote
it. The program finds every book by an author.

```basic keys=ROSA,Enter
10 INPUT "WHICH AUTHOR? "; A$
20 LET F = 0
30 READ T$, W$
40 IF T$ = "END" THEN 70
50 IF W$ = A$ THEN PRINT T$: LET F = F + 1
60 GOTO 30
70 PRINT F; " BOOKS BY "; A$
80 DATA THE SNOW CASTLE, ROSA
90 DATA FISH FOR TEA, MAX
100 DATA THE NIGHT PENGUIN, ROSA
110 DATA END, END
```

## The drawing game

Draw with the arrow keys; the space bar changes the colour. Escape stops
the program, and the drawing stays on the screen.

```basic keys=Right,Right,Space,Down,Down forever
10 SCREEN 12
20 LET X = 320: LET Y = 240: LET C = 14
30 LET K$ = INKEY$
40 IF K$ = "" THEN 30
50 IF K$ = " " THEN LET C = C + 1: IF C > 15 THEN LET C = 1
60 IF LEN(K$) < 2 THEN 30
70 LET OX = X: LET OY = Y
80 LET A$ = RIGHT$(K$, 1)
90 IF A$ = "H" THEN LET Y = Y - 8
100 IF A$ = "P" THEN LET Y = Y + 8
110 IF A$ = "K" THEN LET X = X - 8
120 IF A$ = "M" THEN LET X = X + 8
130 LINE (OX, OY)-(X, Y), C
140 GOTO 30
```

An arrow key is two characters: `CHR$(0)` and a letter, `H` up, `P`
down, `K` left and `M` right. Line 60 lets only such keys through, and
line 80 looks at the letter.

## Programming well

You can write programs now. These are the habits that make them good:

- **Think first.** What should the program do? What does it ask, and what
  does it show?
- **Draw the chart** before writing, as in chapter 13.
- **Name the boxes well:** `SCORE` says more than `S`.
- **Put `REM`s** where a part of the program begins, saying what it is
  for.
- **Catch wrong answers**, so that a mistake while typing does not stop
  the program, as in chapter 22.
- **Make a menu** when the program does several things, as in chapter
  23.
- **Try it with somebody else.** They will do things you never thought of.

> [cheer] That is the whole guide. From here on, the programs are yours.

::: adult
The guide ends where a child can go on alone: changing these programs is
the best next step, and the habits in the last section are the same in
every language they will meet afterwards, Scratch, Python or any other.
:::
