# PRINT: the computer writes

`PRINT` writes on the screen whatever is between the quotes, exactly as
it is.

```basic
10 PRINT "THE PENGUIN LIVES ON THE ICE"
20 PRINT "IT EATS FISH"
30 PRINT
40 PRINT "AND IT LOVES SNOW"
```

A `PRINT` with nothing after it writes an empty line, like line 30.

## When BASIC does not understand

This program has a mistake on purpose, in line 20: `PIRNT` instead of
`PRINT`. Type it in as it is, and press **Run**.

```basic mistake
10 PRINT "THE PENGUIN LIVES ON THE ICE"
20 PIRNT "IT EATS FISH"
30 PRINT "AND IT LOVES SNOW"
```

Nothing is written, not even line 10. BASIC reads the whole program
before it runs any of it, and it stops at a line it does not understand.
The words under the screen say which line, and the editor marks it.
Write `PRINT` properly in line 20 and press **Run** again.

> [oops] A forgotten quote at the start of the words does the same. When
> BASIC does not understand a line, look at its spelling and its quotes
> first.

## Commas and semicolons

After a `PRINT` you can put several things, separated by `;` or by `,`.
A semicolon writes the next thing straight after; a comma jumps a little
further along the line first.

```basic
10 PRINT "ICE"; "CREAM"
20 PRINT "ICE", "CREAM"
30 PRINT "ONE "; "TWO "; "THREE"
```

The space inside `"ONE "` is what keeps the words apart.

## Drawing with letters

The screen is made of rows of letters, so letters can draw pictures.

```basic
10 PRINT "  *****"
20 PRINT " *     *"
30 PRINT "*  O O  *"
40 PRINT "*   ^   *"
50 PRINT " * --- *"
60 PRINT "  *****"
```

> [cheer] When you start a new program, press **New** first, so that the
> old lines do not get mixed with the new ones.

## Keep trying

- Draw a house, a fish or a rocket with letters.
- Write your name in big letters made of `#`.
- Put a `,` and then a `;` between two words, and see the difference.

::: adult
The comma moves to the next print zone, a column fourteen characters
wide; the semicolon adds nothing. Numbers printed with `;` are not given
spaces around them on this BASIC, so the guide puts a `" "` between them
where they must stay apart.
:::
