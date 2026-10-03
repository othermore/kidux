# The fifth operation

You know four operations: `+`, `-`, `*` and `/`. The fifth is the
**power**, written `^`. `2 ^ 3` means 2 times itself three times:
2 × 2 × 2, which is 8.

```basic
10 PRINT 2 ^ 3
20 PRINT 10 ^ 2
30 PRINT 3 ^ 4
40 PRINT 5 ^ 1, 5 ^ 0
```

Any number to the power 0 is 1, and to the power 1 is itself.

## The penguin's fish

The penguin makes a deal with the fisherman: one fish on the first day,
two on the second, four on the third, and every day twice as many as
the day before, for as many days as a board has squares, sixty-four.
The fisherman thinks that is cheap.

![One fish, two, four, eight](board.svg)

```basic
10 LET F = 1
20 FOR D = 1 TO 30
30 PRINT "DAY "; D; ": "; F; " FISH"
40 LET F = F * 2
50 NEXT D
```

On day 30 it is more than five hundred million fish, and there are still
34 days to go. On day D the penguin gets `2 ^ (D - 1)` fish:

```basic
10 PRINT "DAY 64: "; 2 ^ 63; " FISH"
20 PRINT "ALL OF THEM: "; 2 ^ 64 - 1
```

> [cheer] Doubling grows faster than anything else you can count. Poor
> fisherman!

## Very big numbers

When a number has too many figures, the computer writes it short:

```basic
10 PRINT 10 ^ 20
20 PRINT 10 ^ 21
30 PRINT 2 ^ 100
```

`1e+21` means 1 followed by 21 zeros. The number after `e+` says how many
places the point moves to the right. Very big numbers are not exact any
more: a number worked out in a `PRINT` keeps about sixteen figures, and
one kept in a box about seven.

## Keep trying

- How many days does it take until the penguin has more than a thousand
  fish in one day? And more than a million?
- Print the powers of 3, from `3 ^ 0` to `3 ^ 10`.

::: adult
The story is the old one of the grains of rice on a chessboard, told
with fish. The last numbers are not exact: a calculation keeps about
sixteen significant figures, and a variable, single precision as in the
BASICs of the time, about seven.
:::
