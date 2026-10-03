# Strings

A word box holds a **string**: letters one after another, like beads on
a string. BASIC has tools for taking strings apart.

- `LEN(W$)` is how many letters W$ has.
- `LEFT$(W$, 3)` is its first 3 letters, and `RIGHT$(W$, 3)` its last 3.
- `MID$(W$, 2, 4)` is 4 letters starting from the second.

```basic
10 LET W$ = "SNOWBALL"
20 PRINT LEN(W$)
30 PRINT LEFT$(W$, 4)
40 PRINT RIGHT$(W$, 4)
50 PRINT MID$(W$, 3, 3)
```

## Letter by letter

```basic keys=PENGUIN,Enter
10 INPUT "A WORD? "; W$
20 FOR I = 1 TO LEN(W$)
30 PRINT MID$(W$, I, 1)
40 NEXT I
```

And backwards, to see your word in a mirror:

```basic keys=STRESSED,Enter
10 INPUT "A WORD? "; W$
20 LET B$ = ""
30 FOR I = LEN(W$) TO 1 STEP -1
40 LET B$ = B$ + MID$(W$, I, 1)
50 NEXT I
60 PRINT B$
```

## Numbers and strings

`VAL` turns a string of figures into a number, and `STR$` turns a number
into a string:

```basic
10 LET A$ = "12"
20 PRINT A$ + A$
30 PRINT VAL(A$) + VAL(A$)
40 PRINT "THE ANSWER IS" + STR$(6 * 7)
```

`"12" + "12"` joins two strings; `VAL` makes them numbers to add.

## Waiting for a key

`INKEY$` is the key being pressed, or an empty string when there is none.
It does not wait: a program that wants a key asks again and again until
one comes.

```basic keys=x
10 PRINT "PRESS ANY KEY TO WAKE THE PENGUIN"
20 LET K$ = INKEY$
30 IF K$ = "" THEN 20
40 PRINT "YAWN... YOU PRESSED "; K$
```

> [point] Line 30 jumps back to line 20 while no key has been pressed.
> That little loop is how a program waits.

## Keep trying

- Ask for a name, and print its first letter and how long it is.
- Is a word the same backwards? Print whether it is a *palindrome*, like
  `LEVEL`.
- Make the quiz of chapter 19 wait for a key after each answer.

::: adult
`INKEY$` returns at once, so a game can keep moving while it watches the
keyboard; chapter 30's drawing game does. `STR$` puts a space before a
positive number, where its sign would go.
:::
