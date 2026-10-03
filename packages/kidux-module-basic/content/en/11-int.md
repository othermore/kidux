# INT: whole numbers

Divide 7 fish between 2 penguins and the computer says 3.5. But a fish
cut in half is no good to anyone. `INT` keeps the whole part of a number
and throws the rest away.

```basic
10 PRINT 7 / 2
20 PRINT INT(7 / 2)
30 PRINT INT(9.99)
```

`INT` does not round: 9.99 becomes 9, not 10.

## How many each, and how many left

```basic keys=17,Enter,5,Enter
10 INPUT "HOW MANY FISH? "; F
20 INPUT "HOW MANY PENGUINS? "; P
30 LET EACH = INT(F / P)
40 LET LEFT = F - EACH * P
50 PRINT "EACH ONE GETS "; EACH
60 PRINT "AND "; LEFT; " ARE LEFT OVER"
```

> [think] To round to the nearest whole number, add a half first:
> `INT(X + 0.5)`. Try it with 9.99 and with 9.2.

## Keep trying

- Is a number even? It is when `INT(N / 2) * 2 = N`. Write a program that
  says whether a number is even or odd.
- Share sweets between friends, and say how many each gets and how many
  are left.

::: adult
`INT` gives the whole number at or below: `INT(-2.5)` is -3. Chapter 12
needs it to turn chance into whole numbers.
:::
