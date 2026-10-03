# Games to make

Now you know enough to make games. Each of these uses only what the
chapters before taught. Type them, play them, and then change them.

## The multiplication trainer

```basic keys=8,Enter,24,Enter,32,Enter,40,Enter
10 INPUT "WHICH TABLE? "; T
20 FOR N = 3 TO 5
30 PRINT T; " TIMES "; N; "? ";
40 INPUT "", A
50 IF A = T * N THEN PRINT "RIGHT!" ELSE PRINT "NO, IT IS "; T * N
60 NEXT N
```

## Hide and seek

The penguin hides behind one of ten rocks. Find it!

![Ten rocks in the snow](garden.svg)

```basic keys=3,Enter,5,Enter,1,Enter,2,Enter,4,Enter,6,Enter,7,Enter,8,Enter,9,Enter,10,Enter
10 RANDOMIZE
20 LET R = INT(RND * 10) + 1
30 LET TRIES = 0
40 INPUT "WHICH ROCK, 1 TO 10? "; N
50 LET TRIES = TRIES + 1
60 IF N = R THEN 90
70 PRINT "NOT THERE..."
80 GOTO 40
90 PRINT "FOUND IT! IN "; TRIES; " TRIES"
```

## Guess my number

```basic keys=50,Enter,25,Enter,75,Enter,12,Enter,37,Enter,62,Enter,87,Enter,6,Enter,18,Enter,31,Enter,43,Enter,56,Enter,68,Enter,81,Enter,93,Enter,1,Enter,2,Enter,3,Enter,4,Enter,5,Enter
10 RANDOMIZE
20 LET R = INT(RND * 100) + 1
30 LET TRIES = 0
40 INPUT "MY NUMBER IS FROM 1 TO 100. GUESS: "; G
50 LET TRIES = TRIES + 1
60 IF G < R THEN PRINT "BIGGER!"
70 IF G > R THEN PRINT "SMALLER!"
80 IF G <> R AND TRIES < 20 THEN 40
90 IF G = R THEN PRINT "YES! IN "; TRIES; " TRIES" ELSE PRINT "IT WAS "; R
```

> [think] What is the cleverest first guess? Think about halves.

## The mind reader

The computer guesses the number you think of.

```basic keys=Enter,Enter,Enter,Enter,23,Enter
10 PRINT "THINK OF A NUMBER. DO NOT TELL ME!"
20 INPUT "PRESS ENTER WHEN READY", K$
30 PRINT "MULTIPLY IT BY 2"
40 INPUT "PRESS ENTER", K$
50 PRINT "ADD 10"
60 INPUT "PRESS ENTER", K$
70 PRINT "DIVIDE IT BY 2"
80 INPUT "PRESS ENTER", K$
90 INPUT "TELL ME WHAT YOU HAVE NOW: "; X
100 PRINT "YOU THOUGHT OF "; X - 5
```

> [cheer] How does it work? Write down what happens to the number, step
> by step, and you will see the trick.

## Keep trying

- Give the hide-and-seek penguin only five tries.
- In the trainer, ask all the table, from 1 to 10, and count the right
  answers.
- Make a game of your own: a quiz about your favourite animal.

::: adult
These games are the first chapters put together. The mind reader is a
good one to explain together: doubling, adding 10 and halving leaves the
number plus 5, whatever it was.
:::
