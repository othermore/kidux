# INPUT, more

`INPUT` can ask a question and wait for an answer in one line, as you
have done since chapter 4. It can also take several answers at once:
put their boxes after the question, separated by commas, and type the
answers separated by commas too.

```basic keys=6,Comma,4,Enter
10 INPUT "WIDTH AND LENGTH OF THE GARDEN? "; W, L
20 PRINT "IT HAS "; W * L; " SQUARE METRES"
30 PRINT "AND A FENCE OF "; 2 * W + 2 * L; " METRES"
```

To answer, type `6,4` and press Enter.

## Words and numbers together

```basic keys=PIP,Comma,7,Comma,FISH,Enter
10 INPUT "NAME, AGE AND FAVOURITE FOOD? "; N$, A, F$
20 PRINT N$; " IS "; A; " AND LOVES "; F$
```

> [point] Say in the question how many answers you want, and in what
> order. The person typing cannot see your program.

## A story machine

```basic keys=PIP,Comma,DANCED,Comma,ICE,Enter
10 PRINT "GIVE ME SOMEONE, AN ACTION AND A PLACE."
20 INPUT "SEPARATE THEM WITH COMMAS: "; W$, A$, P$
30 PRINT "ONCE UPON A TIME, "; W$; " "; A$; " ON "; P$; "."
40 PRINT "AND EVERYBODY CLAPPED."
```

## Keep trying

- Ask for the three sides of a triangle and print the length all round.
- Make the story machine ask for five words and tell a longer story.

::: adult
A comma inside an answer separates it from the next, so an answer with
a comma in it cannot be typed into a word box this way. When fewer
answers are typed than asked for, a missing number shows as `NaN`, *not
a number*; that is why the question should say how many it wants.
:::
