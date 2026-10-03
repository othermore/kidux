# Putting things in order

The computer can compare numbers with `<` and `>`, and words too: for
words, *smaller* means *earlier in the alphabet*.

```basic
10 IF 3 < 7 THEN PRINT "3 COMES BEFORE 7"
20 IF "ANA" < "TOM" THEN PRINT "ANA COMES BEFORE TOM"
30 IF "PIP" > "BEA" THEN PRINT "PIP COMES AFTER BEA"
```

## Swapping two boxes

To swap what two boxes hold, you need a third, spare box: first the
fish goes into the spare box, then the snowflake into the fish's box,
then the fish from the spare box into the snowflake's.

![Swapping with a spare box](swap.svg)

```basic
10 LET A = 3: LET B = 8
20 PRINT "BEFORE: "; A; " AND "; B
30 LET S = A
40 LET A = B
50 LET B = S
60 PRINT "AFTER: "; A; " AND "; B
```

> [oops] Without the spare box, `LET A = B` would lose what A held, and
> both boxes would end up with 8.

BASIC also has `SWAP A, B`, which does all three steps at once.

## Sorting numbers

The **bubble sort** walks along the shelf comparing each box with the
next, and swaps them when they are the wrong way round. After one walk,
the biggest number has bubbled up to the end; after enough walks,
everything is in order.

```basic
10 DIM N(6)
20 FOR I = 1 TO 6: READ N(I): NEXT I
30 FOR W = 1 TO 5
40 FOR I = 1 TO 6 - W
50 IF N(I) > N(I + 1) THEN SWAP N(I), N(I + 1)
60 NEXT I
70 NEXT W
80 FOR I = 1 TO 6: PRINT N(I); " ";: NEXT I
90 PRINT
100 DATA 42, 7, 19, 3, 25, 11
```

## Sorting names

The same program sorts words, with word boxes:

```basic
10 DIM N$(6)
20 FOR I = 1 TO 6: READ N$(I): NEXT I
30 FOR W = 1 TO 5
40 FOR I = 1 TO 6 - W
50 IF N$(I) > N$(I + 1) THEN SWAP N$(I), N$(I + 1)
60 NEXT I
70 NEXT W
80 FOR I = 1 TO 6: PRINT N$(I): NEXT I
90 DATA TOM, ANA, PIP, LULU, BEA, MAX
```

## Keep trying

- Sort the numbers from biggest to smallest. Which sign do you change?
- Print the shelf after every walk, to watch the numbers bubble.

::: adult
Words are compared letter by letter by their codes (chapter 28), so
capital letters come before small ones, and a word with an accent may
not land where a dictionary puts it. The bubble sort is slow for long
lists but easy to follow, which is why it is taught first.
:::
