# LET: boxes with names

A computer remembers things in boxes in its memory, and each box has a
name. A box like this is called a **variable**. `LET` puts something in
a box.

![Boxes with names](boxes.svg)

```basic
10 LET FISH = 12
20 PRINT FISH
```

The box is called `FISH`, and it holds the number 12. `PRINT FISH`,
without quotes, writes what is inside the box, not its name.

> [think] With quotes, `PRINT "FISH"` writes the word FISH. Without
> them, `PRINT FISH` writes 12. Try both!

## Sums

The computer is very good at sums. It uses `+` and `-`, `*` for times
and `/` for divided by.

```basic
10 LET FISH = 12
20 LET FRIENDS = 4
30 LET EACH = FISH / FRIENDS
40 PRINT "EACH FRIEND GETS "; EACH; " FISH"
50 LET FISH = FISH + 10
60 PRINT "NOW THERE ARE "; FISH
```

Line 50 looks strange: it means *take what is in FISH, add 10, and put
the result back in FISH*. A box can change what it holds as often as you
like, which is why it is called a variable.

## Boxes for words

A box whose name ends in `$` holds words instead of numbers. Words go
between quotes, and `+` joins them together.

```basic
10 LET A$ = "SNOW"
20 LET B$ = "BALL"
30 PRINT A$ + B$
```

You can even leave out the word `LET`: `FISH = 12` means the same.

## Keep trying

- Work out how many legs four penguins have, with a variable for each.
- Make a sentence by joining three word boxes.
- What happens if you `PRINT` a box you never filled?

::: adult
Variables with `$` are string variables. Numbers and strings do not mix:
`A = "SNOW"` gives no error on this BASIC, but leaves A as 0, so it is
worth showing the child which kind of box each one is. A box never
filled holds 0, or an empty string.
:::
