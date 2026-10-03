# Flowcharts: draw it first

Before writing a program, it helps to draw it. A **flowchart** is a
drawing of a program: boxes for what to do, and arrows for the order.

![The shapes of a flowchart](flowchart.svg)

- A rounded box is the start or the end.
- A slanted box is something asked or shown.
- A plain box is something worked out, like a sum.
- A diamond is a question with two ways out, yes and no: an `IF`.

> [point] Draw it on paper first, with a pencil. Arrows that go back up
> are loops.

## From the drawing to the program

A flowchart for *ask a number from 1 to 10, and ask again until it is
right*: start, ask, the diamond *is it from 1 to 10?*, no goes back up,
yes goes on, show it, end. Here it is in BASIC:

```basic keys=12,Enter,7,Enter
10 INPUT "A NUMBER FROM 1 TO 10? "; N
20 IF N < 1 OR N > 10 THEN 10
30 PRINT "THANK YOU. TWICE "; N; " IS "; N * 2
```

`OR` means *one or the other*: if the number is too small or too big,
ask again.

## Keep trying

- Draw the flowchart of the guessing game in the next chapter before you
  read its program.
- Draw a flowchart of your morning, from waking up to leaving home.

::: adult
Flowcharts make the shape of a program visible before its details. They
are especially useful when a child is stuck: drawing what the program
should do usually shows where it goes another way.
:::
