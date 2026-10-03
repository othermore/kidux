# AND and OR

Sometimes one question is not enough. Is it cold **and** snowing? Then
it is a day for building a snowman. Is it raining **or** snowing? Then
you need a coat.

- `AND` is yes only when **both** sides are yes.
- `OR` is yes when **one side or the other**, or both, is yes.

```basic keys=YES,Enter,NO,Enter
10 INPUT "IS IT COLD? "; C$
20 INPUT "IS IT SNOWING? "; S$
30 IF C$ = "YES" AND S$ = "YES" THEN PRINT "LET'S BUILD A SNOWMAN!"
40 IF C$ = "YES" OR S$ = "YES" THEN PRINT "PUT YOUR COAT ON."
50 IF C$ = "NO" AND S$ = "NO" THEN PRINT "A DAY FOR THE PARK."
```

## Catching a wrong answer

When a program asks for a number from 1 to 9, a careful program says no
to anything else and asks again:

```basic keys=0,Enter,15,Enter,4,Enter
10 INPUT "A NUMBER FROM 1 TO 9? "; N
20 IF N < 1 OR N > 9 THEN PRINT "FROM 1 TO 9, PLEASE": GOTO 10
30 PRINT "THANK YOU. "; N; " IT IS."
```

## The igloo's password

```basic keys=FISH,Enter,ICE,Enter,SNOWBALL,Enter
10 LET T = 0
20 INPUT "PASSWORD? "; P$
30 LET T = T + 1
40 IF P$ <> "SNOWBALL" AND T < 3 THEN PRINT "NO. TRY AGAIN.": GOTO 20
50 IF P$ = "SNOWBALL" THEN PRINT "WELCOME TO THE IGLOO!" ELSE PRINT "THE DOOR STAYS SHUT."
```

You have three tries. Line 40 asks again only while the password is
wrong **and** there are tries left.

> [think] `NOT` turns yes into no and no into yes: `IF NOT (N = 5)` is
> the same as `IF N <> 5`.

## Keep trying

- Give the igloo two passwords that both open it.
- Ask for a day of the week and a time, and say whether the shop is open.

::: adult
Conditions joined by `AND` and `OR` are where logic enters programming.
Saying the condition aloud, *wrong and tries left*, is the surest way
to get it right. In this BASIC a condition that is true is worth -1 and
one that is false 0, which the guide never needs to show.
:::
