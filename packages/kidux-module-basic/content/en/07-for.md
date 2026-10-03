# FOR and NEXT: the loop that counts

Counting with `GOTO` takes a box, a sum and a jump. `FOR` does all three
at once: it counts from one number to another, and does the lines
between `FOR` and `NEXT` once for each number.

```basic
10 FOR N = 1 TO 5
20 PRINT "PENGUIN NUMBER "; N
30 NEXT N
40 PRINT "FIVE PENGUINS!"
```

![A loop goes round and round](loop.svg)

`NEXT N` means *the next N, please*. When N has been 5, the loop is over
and the computer goes on to line 40.

> [cheer] Every `FOR` needs its `NEXT`. If you forget it, the computer
> tells you something is missing at the end.

## STEP

`STEP` says how much to count by. It can even count backwards.

```basic
10 FOR N = 0 TO 20 STEP 5
20 PRINT N
30 NEXT N
40 FOR N = 10 TO 1 STEP -1
50 PRINT N; " ";
60 NEXT N
70 PRINT "LIFT OFF!"
```

## A table

```basic
10 FOR N = 1 TO 10
20 PRINT N; " TIMES 3 IS "; N * 3
30 NEXT N
```

## Keep trying

- Write your name ten times.
- Write the table of 7, or ask which table to write with `INPUT`.
- Count from 100 down to 0 by tens.

::: adult
The box after `FOR` is an ordinary variable: inside the loop it can be
printed and used in sums. A loop inside another loop is chapter 21's;
for now one is enough.
:::
