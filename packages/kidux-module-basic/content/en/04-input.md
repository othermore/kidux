# INPUT: talking with the computer

Until now the computer has talked and you have listened. `INPUT` turns it
round: the computer stops, asks, and waits for you to type an answer and
press Enter. The answer goes into a box.

```basic keys=Leo,Enter
10 INPUT "WHAT IS YOUR NAME? "; N$
20 PRINT "HELLO, "; N$
```

Press Run, type your name, press Enter. The computer answers.

> [point] The question goes between quotes, then a semicolon, then the box
> for the answer. Put a space before the last quote, so your answer does
> not stick to the question.

## Numbers as answers

If the box has no `$`, the answer is a number, and the computer can do
sums with it.

```basic keys=7,Enter
10 INPUT "HOW OLD ARE YOU? "; AGE
20 PRINT "NEXT YEAR YOU WILL BE "; AGE + 1
30 PRINT "IN TEN YEARS, "; AGE + 10
```

## A program that knows you

```basic keys=Ana,Enter,9,Enter,PIZZA,Enter
10 INPUT "YOUR NAME? "; N$
20 INPUT "YOUR AGE? "; A
30 INPUT "YOUR FAVOURITE FOOD? "; F$
40 PRINT
50 PRINT N$; " IS "; A; " AND LOVES "; F$
60 PRINT "IN "; 100 - A; " YEARS, "; N$; " WILL BE 100"
```

> [cheer] Now the same program says something different for each person
> who runs it. That is what makes programs useful.

## Keep trying

- Ask for two numbers and write their sum.
- Ask for an animal and a colour, and write a sentence with both.
- Type a word when the computer asks for a number. What does it do?

::: adult
`INPUT` with a box ending in `$` takes any text; without it, a number.
On this BASIC a word typed where a number is wanted gives `NaN`, "not a
number", rather than asking again. It is a good moment to talk about
checking what people type, which chapter 22 does properly.
:::
