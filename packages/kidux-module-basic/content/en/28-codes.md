# CHR$ and ASC: the letters' numbers

Inside the computer every letter is a number. `ASC` tells you a letter's
number, and `CHR$` turns a number back into its letter:

```basic
10 PRINT ASC("A"), ASC("B"), ASC("Z")
20 PRINT CHR$(72); CHR$(73); CHR$(33)
```

`A` is 65, `B` is 66, and so on up to `Z`, 90. A space is 32.

## The alphabet

```basic
10 FOR C = 65 TO 90
20 PRINT CHR$(C); " ";
30 NEXT C
40 PRINT
```

## A secret code

To write in code, change every letter for the one after it: A becomes
B, B becomes C, and Z goes back round to A. Your friend changes each
letter for the one before it to read the message.

![Each letter becomes the next](code.svg)

```basic keys=MEET,Space,AT,Space,THE,Space,IGLOO,Enter
10 INPUT "YOUR MESSAGE? "; M$
20 LET S$ = ""
30 FOR I = 1 TO LEN(M$)
40 LET C = ASC(MID$(M$, I, 1))
50 IF C >= 65 AND C <= 90 THEN LET C = C + 1
60 IF C = 91 THEN LET C = 65
70 LET S$ = S$ + CHR$(C)
80 NEXT I
90 PRINT "IN CODE: "; S$
```

Line 50 only moves capital letters, so spaces stay spaces. Line 60
sends the letter after Z back to A.

> [think] How would you read a message in code? Change line 50 to take
> 1 away, and line 60 to turn 64 into 90.

## Keep trying

- Move every letter three places instead of one.
- Write the program that reads the code back, and test it on a friend.

::: adult
The numbers are ASCII codes, the same on almost every computer. A code
that moves each letter a fixed number of places is a Caesar cipher,
after Julius Caesar, who is said to have used one.
:::
