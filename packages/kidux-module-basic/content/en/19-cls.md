# CLS: a clean screen

`CLS` wipes the screen clean and starts writing again at the top. It
does not touch your program or its boxes: it only clears what is shown.

```basic
10 PRINT "THIS WILL VANISH"
20 PRINT "AND THIS TOO"
30 CLS
40 PRINT "A CLEAN SCREEN"
```

A quiz looks better when each question has the screen to itself:

```basic keys=2,Enter,FISH,Enter
10 CLS
20 PRINT "QUESTION 1"
30 INPUT "HOW MANY LEGS HAS A PENGUIN? "; A
40 IF A = 2 THEN PRINT "RIGHT!" ELSE PRINT "IT HAS TWO"
50 CLS
60 PRINT "QUESTION 2"
70 INPUT "WHAT DOES A PENGUIN EAT? "; F$
80 IF F$ = "FISH" THEN PRINT "RIGHT!" ELSE PRINT "MOSTLY FISH"
```

> [think] The answer to question 1 vanishes before you can read it. Can
> you make the program wait? Chapter 21 shows how, and chapter 27 shows
> how to wait for a key.

## Three ways to start clean

- `CLS` clears the **screen**. The program goes on.
- Every **Run** starts with empty boxes, as chapter 16 showed.
- **New** clears the **editor**, and the program in it is gone. It asks
  first, so that nothing is lost by mistake.

## Keep trying

- Add a third question to the quiz, on its own clean screen.
- Count the right answers in a box, and show the score on a clean screen
  at the end.

::: adult
`CLS` is the first instruction of most programs that use the screen as
a page rather than a scroll of text. Every run here starts with its
variables empty, so a program never needs to clear them itself.
:::
