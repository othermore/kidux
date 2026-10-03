# READ and DATA: a store of things

When a program needs many values, `DATA` keeps them in a list, and
`READ` takes them out one by one, in order.

```basic
10 READ A, B, C
20 PRINT A + B + C
30 DATA 5, 7, 4
```

`READ A, B, C` puts the first value in A, the next in B, the next in C.

## Words in DATA

`DATA` can hold words too, read into boxes with `$`.

```basic
10 FOR N = 1 TO 3
20 READ NAME$, FOOD$
30 PRINT NAME$; " LIKES "; FOOD$
40 NEXT N
50 DATA PIP, FISH, TOM, CAKE, LULU, APPLES
```

> [think] What happens if `READ` wants more values than `DATA` has? Try
> changing `3` to `4` on line 10.

The computer says there are no more `DATA` to read.

## A marker that says stop

To read a list without counting it, put an extra value at the end that
means *the end*, and let `IF` watch for it.

```basic
10 LET TOTAL = 0
20 READ N
30 IF N = -1 THEN 60
40 LET TOTAL = TOTAL + N
50 GOTO 20
60 PRINT "THE TOTAL IS "; TOTAL
70 DATA 3, 8, 12, 5, -1
```

## Keep trying

- Keep the names and ages of five friends in `DATA` and write them.
- Add a sixth friend, without changing anything but the `DATA`, in the
  marker program.

::: adult
`DATA` lines can be anywhere in the program; at the end is clearest.
`RESTORE` starts reading from the first value again, which chapter 24
uses.
:::
