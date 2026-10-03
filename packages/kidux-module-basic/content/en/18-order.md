# What the computer does first

What is 2 + 3 × 4? If you add first it is 20; if you multiply first it
is 14. The computer always does things in the same order:

1. what is inside brackets, `(` and `)`;
2. powers, `^`;
3. `*` and `/`, from left to right;
4. `+` and `-`, from left to right.

```basic
10 PRINT 2 + 3 * 4
20 PRINT (2 + 3) * 4
30 PRINT 10 - 4 - 3
40 PRINT 2 * 3 ^ 2
```

## The wrong change

Pip buys 2 fish at 4 coins each and 3 shells at 1 coin each, and pays
with 20 coins. How much change?

```basic
10 LET CHANGE = 20 - 2 * 4 + 3 * 1
20 PRINT "WRONG CHANGE: "; CHANGE
30 LET CHANGE = 20 - (2 * 4 + 3 * 1)
40 PRINT "RIGHT CHANGE: "; CHANGE
```

Line 10 takes away the fish and then *adds* the shells: Pip would get 15
coins back for 11 coins of shopping. The brackets in line 30 make the
computer add up the shopping first.

> [oops] When you are not sure what the computer will do first, put
> brackets. They never hurt.

## The average

The average of three marks is their sum divided by three:

```basic
10 LET A = 7: LET B = 8: LET C = 9
20 PRINT "WITHOUT BRACKETS: "; A + B + C / 3
30 PRINT "WITH BRACKETS: "; (A + B + C) / 3
```

A colon, `:`, puts two instructions on one line.

## Keep trying

- Work out 100 - 10 * 5 + 2 on paper, then ask the computer.
- Write a program that asks for four marks and prints their average.

::: adult
These are the usual rules of arithmetic. A common mistake, here and in
every language, is the average without brackets; a good habit is to
bracket every sum that is divided.
:::
