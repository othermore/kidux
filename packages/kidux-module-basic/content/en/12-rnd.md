# RND: chance

`RND` gives a number nobody can guess: a number at random, from 0 up to,
but not including, 1. Every time it is different.

```basic
10 RANDOMIZE
20 FOR N = 1 TO 5
30 PRINT RND
40 NEXT N
```

`RANDOMIZE` at the start mixes the numbers, so each run is different.

## A die

A die gives 1, 2, 3, 4, 5 or 6. Multiply `RND` by 6, keep the whole part
with `INT`, and add 1:

![A die](dice.svg)

```basic
10 RANDOMIZE
20 LET D = INT(RND * 6) + 1
30 PRINT "YOU THREW A "; D
```

Each time you press Run, you throw the die.

## A hundred throws

How many fives come out of a hundred throws? Nobody knows until they
try, and the computer can try very fast.

```basic
10 RANDOMIZE
20 LET FIVES = 0
30 FOR T = 1 TO 100
40 LET D = INT(RND * 6) + 1
50 IF D = 5 THEN LET FIVES = FIVES + 1
60 NEXT T
70 PRINT "IN 100 THROWS, "; FIVES; " FIVES"
```

> [cheer] Run it several times. The answer is often near 16 or 17, a
> sixth of 100, but almost never exactly the same.

## Keep trying

- Throw a thousand times instead of a hundred.
- Count the sixes as well as the fives.
- Throw two dice and add them up.

::: adult
`INT(RND * N) + 1` gives a whole number from 1 to N, each as likely as
the others. Simulating many throws is a first, playful look at
probability; it is worth asking the child to guess before running.
:::
