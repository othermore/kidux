# DIM: a shelf of boxes

When a program needs many boxes of the same kind, one for each friend or
each day, it can have a whole **shelf** of them, with one name and a
number for each box. `DIM` makes the shelf:

```basic
10 DIM F(7)
20 FOR D = 1 TO 7
30 READ F(D)
40 NEXT D
50 PRINT "FISH ON DAY 3: "; F(3)
60 LET T = 0
70 FOR D = 1 TO 7
80 LET T = T + F(D)
90 NEXT D
100 PRINT "FISH ALL WEEK: "; T
110 DATA 4, 6, 3, 8, 5, 9, 2
```

`F(3)` is box number 3 of the shelf `F`. The number in brackets can be a
box too, like `F(D)`, and that is the magic: one loop goes along the
whole shelf.

![A shelf of boxes](boxes.svg)

## A shelf of words

```basic
10 DIM N$(4)
20 FOR I = 1 TO 4: READ N$(I): NEXT I
30 FOR I = 4 TO 1 STEP -1
40 PRINT N$(I)
50 NEXT I
60 DATA PIP, TOM, LULU, BEA
```

It prints the friends backwards. A `FOR` with its `NEXT` on one line,
with colons, is still a loop.

## A table

A shelf can have rows and columns, like a cupboard. `DIM C(3, 4)` makes
three rows of four boxes; `C(2, 3)` is row 2, box 3. Here three penguins
write down the fish they catch on four days:

```basic
10 DIM C(3, 4)
20 FOR P = 1 TO 3
30 FOR D = 1 TO 4
40 READ C(P, D)
50 NEXT D
60 NEXT P
70 FOR P = 1 TO 3
80 LET T = 0
90 FOR D = 1 TO 4
100 LET T = T + C(P, D)
110 NEXT D
120 PRINT "PENGUIN "; P; " CAUGHT "; T
130 NEXT P
140 DATA 3, 5, 2, 4
150 DATA 6, 1, 4, 4
160 DATA 2, 2, 7, 5
```

> [cheer] With a shelf, a program for a hundred friends is no longer than
> a program for four.

## Keep trying

- Which day was the best for fishing in the first program? Find the
  biggest number on the shelf.
- In the table, add up each day's fish for all three penguins.

::: adult
`DIM` names an array; the boxes are numbered from 0, though the guide
uses them from 1. This BASIC would let a shelf be used without `DIM`,
but the guide always writes it: saying how big the shelf is, before
using it, is a habit every language rewards.
:::
