# FOR and NEXT, more

## Leaving a loop early

A `FOR` loop counts to the end, but a `GOTO` can leave it before. This
one squares numbers until you type 0, or until it has done ten:

```basic keys=3,Enter,12,Enter,0,Enter
10 FOR N = 1 TO 10
20 INPUT "A NUMBER, OR 0 TO STOP? "; X
30 IF X = 0 THEN 60
40 PRINT X; " TIMES "; X; " IS "; X * X
50 NEXT N
60 PRINT "BYE!"
```

## A loop that waits

`SLEEP` makes the computer wait. The number after it is in thousandths
of a second, so `SLEEP 1000` waits one second:

```basic
10 FOR N = 5 TO 1 STEP -1
20 PRINT N
30 SLEEP 1000
40 NEXT N
50 PRINT "LIFT OFF!"
```

> [point] `SLEEP 500` waits half a second, and `SLEEP 3000` three
> seconds.

## Loops inside loops

A loop can have another loop inside it. The inside one goes all the way
round each time the outside one goes round once, like the minutes inside
the hours of a clock.

```basic
10 FOR R = 1 TO 4
20 FOR S = 1 TO R
30 PRINT "*";
40 NEXT S
50 PRINT
60 NEXT R
```

The inside loop must end before the outside one: `NEXT S` comes before
`NEXT R`.

## The tables, one by one

```basic
10 FOR T = 2 TO 5
20 CLS
30 PRINT "THE TABLE OF "; T
40 FOR N = 1 TO 10
50 PRINT T; " X "; N; " = "; T * N
60 NEXT N
70 SLEEP 3000
80 NEXT T
```

Each table stays on the screen for three seconds, then the next one
takes its place.

## Keep trying

- Make the stars of the triangle into a tree, with a trunk at the bottom.
- Make the tables wait five seconds, or go from the table of 2 to the
  table of 10.

::: adult
Leaving a loop with `GOTO` is how the home computers did it, and it
works here. Nested loops are the first real difficulty for many
children: drawing the stars on squared paper, row by row, helps.
:::
