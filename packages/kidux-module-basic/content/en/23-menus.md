# IF, more: menus

A program that does several things can offer them in a **menu**: a list
with a number for each, and a question.

`ON … GOTO` jumps to the first line of its list when the box holds 1, to
the second when it holds 2, and so on. When the number is not in the
list, it goes on to the next line.

```basic keys=2,Enter
10 PRINT "THE PENGUIN CAFE"
20 PRINT "1  FISH SOUP"
30 PRINT "2  ICE CREAM"
40 PRINT "3  HOT CHOCOLATE"
50 INPUT "WHAT WOULD YOU LIKE? "; C
60 ON C GOTO 100, 200, 300
70 PRINT "THAT IS NOT ON THE MENU."
80 END
100 PRINT "ONE FISH SOUP, NICE AND HOT."
110 END
200 PRINT "ONE ICE CREAM, NICE AND COLD."
210 END
300 PRINT "ONE HOT CHOCOLATE, WITH A MARSHMALLOW."
```

`END` stops the program there, so that each order does not run on into
the next.

## ELSE

`ELSE` says what to do when the `IF` is not true. You met it in the games
of chapter 14:

```basic keys=7,Enter
10 INPUT "HOW OLD ARE YOU? "; A
20 IF A < 8 THEN PRINT "THE SMALL SLIDE" ELSE PRINT "THE BIG SLIDE"
```

## A menu that comes back

```basic keys=1,Enter,2,Enter,3,Enter
10 PRINT
20 PRINT "1 SAY HELLO   2 TELL A JOKE   3 LEAVE"
30 INPUT "CHOOSE: "; C
40 ON C GOSUB 100, 200
50 IF C <> 3 THEN 10
60 PRINT "BYE!"
70 END
100 PRINT "HELLO THERE!"
110 RETURN
200 PRINT "WHAT DO PENGUINS WEAR ON THEIR HEADS? ICE CAPS!"
210 RETURN
```

`ON … GOSUB` is the same with `GOSUB`: each choice is a subroutine that
returns to the menu.

> [cheer] Most programs you use have a menu. Now yours can too.

## Keep trying

- Add a fourth thing to the café.
- Give the menu that comes back a fourth choice: a riddle.

::: adult
A menu is the first program structure a child can design on paper before
typing: the list of choices, and a piece of program for each.
:::
