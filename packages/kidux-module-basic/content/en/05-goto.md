# GOTO: jump!

`GOTO` sends the computer to another line, by its number, and it carries
on from there. A jump back makes the computer do the same lines again.

```basic forever
10 PRINT "THE PENGUIN SLIDES DOWN THE HILL"
20 GOTO 10
```

This program never ends: line 20 always sends the computer back to line
10. Press **Stop**, or the Escape key, to end it.

> [oops] A program that goes round and round for ever is called a loop.
> When yours will not stop, Escape always works.

## Counting

A loop with a box that grows can count.

```basic forever
10 LET N = 0
20 LET N = N + 2
30 PRINT N
40 GOTO 20
```

The computer counts by twos faster than you can read. Stop it, and
scroll your eyes up the screen.

## A jump forward

`GOTO` can jump forward too, over lines it should not do. `END` finishes
the program.

```basic
10 PRINT "ONE"
20 GOTO 40
30 PRINT "THIS LINE IS SKIPPED"
40 PRINT "TWO"
50 END
```

> [think] If you `GOTO` a line that is not in the program, the computer
> tells you before it starts. Try `GOTO 99`.

## Keep trying

- Make the counting program count by fives, or by tens.
- Count down from 100 by taking away instead of adding.
- Make a sum table: a number that grows by one each time, and the
  number with 3 added, written side by side.

::: adult
`GOTO` is how the first home computers made loops, and seeing a loop that
never ends is part of learning. The next chapters give loops an end: `IF`
decides when to stop, and `FOR` counts by itself. Escape, or the Stop
button, ends any program, and nothing is lost: the program stays in the
editor.
:::
