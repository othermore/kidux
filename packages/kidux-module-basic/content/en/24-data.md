# READ, DATA and RESTORE

`DATA` lines are a store of things the program reads in order with
`READ`. They can hold words and numbers together.

```basic
10 FOR N = 1 TO 4
20 READ F$, G$
30 PRINT F$; " PLAYS "; G$
40 NEXT N
50 DATA PIP, FOOTBALL, TOM, CHESS
60 DATA LULU, THE PIANO, BEA, HIDE AND SEEK
```

## Searching

To find what someone plays, read the friends one by one until the name
is the one you want. The last `DATA` is a marker that says *no more*, as
in chapter 9:

```basic keys=LULU,Enter
10 INPUT "WHICH FRIEND? "; W$
20 READ F$, G$
30 IF F$ = "END" THEN PRINT "I DO NOT KNOW "; W$: END
40 IF F$ = W$ THEN PRINT W$; " PLAYS "; G$: END
50 GOTO 20
60 DATA PIP, FOOTBALL, TOM, CHESS
70 DATA LULU, THE PIANO, BEA, HIDE AND SEEK
80 DATA END, END
```

## Reading again

`READ` remembers where it got to. `RESTORE` sends it back to the first
`DATA`, to read everything again:

```basic keys=TOM,Enter,YES,Enter,BEA,Enter,NO,Enter
10 INPUT "WHICH FRIEND? "; W$
20 RESTORE
30 READ F$, G$
40 IF F$ = "END" THEN PRINT "I DO NOT KNOW "; W$: GOTO 70
50 IF F$ = W$ THEN PRINT W$; " PLAYS "; G$: GOTO 70
60 GOTO 30
70 INPUT "ANOTHER? "; A$
80 IF A$ = "YES" THEN 10
90 DATA PIP, FOOTBALL, TOM, CHESS
100 DATA LULU, THE PIANO, BEA, HIDE AND SEEK
110 DATA END, END
```

> [point] Without line 20 the second search would start where the first
> one stopped, and miss the friends before it.

## Keep trying

- Add your own friends and what they play.
- Make a quiz from `DATA`: a question and its answer on each line.

::: adult
`RESTORE` can also name a line, `RESTORE 100`, to read from that `DATA`
line on. Searching a list one item at a time is how a computer finds
things when they are not in order; chapter 26 puts them in order.
:::
