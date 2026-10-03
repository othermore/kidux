# GOSUB and RETURN: a piece used many times

Sometimes the same lines are needed in several places. Instead of
writing them again, write them once, at the end, and go there with
`GOSUB`. `RETURN` comes back to just after the `GOSUB` that went there.

```basic
10 PRINT "FIRST QUESTION"
20 GOSUB 100
30 PRINT "SECOND QUESTION"
40 GOSUB 100
50 PRINT "THE END"
60 END
100 PRINT "*-*-*-*-*-*-*-*"
110 RETURN
```

Lines 100 and 110 are a **subroutine**: a little program inside the big
one.

> [oops] Look at line 60. Without `END`, the computer would carry on into
> the subroutine by itself, and its `RETURN` would have nowhere to go
> back to.

## A subroutine that does more

```basic
10 FOR N = 1 TO 3
20 GOSUB 100
30 NEXT N
40 END
100 PRINT "PENGUIN "; N; " WAVES:"
110 PRINT "  HELLO!"
120 PRINT
130 RETURN
```

## Keep trying

- Make a subroutine that draws a little fish with letters, and use it
  three times.
- Put a long line of stars in a subroutine and use it between the
  questions of your quiz.

::: adult
A subroutine is the first step towards organising a program in parts,
which matters more as programs grow. If a child's program ends with an
error naming a RETURN without its GOSUB, an `END` is usually missing
before the subroutines.
:::
