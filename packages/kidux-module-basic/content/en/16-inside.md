# Inside the computer

Every computer has three parts that matter to a program. The
**keyboard** is how things go in. The **memory** is where the computer
keeps what it is working on: the boxes of chapter 3 live there. The
**screen** is how things come out.

![The keyboard, the memory and the screen](inside.svg)

When you press **Run**, your program goes into the memory, and the
computer does its lines one by one. Every box starts empty: a number box
holds 0 and a word box holds nothing at all. Run this twice:

```basic
10 PRINT "FISH BEFORE: "; FISH
20 LET FISH = FISH + 5
30 PRINT "FISH AFTER: "; FISH
```

It says 0 and then 5 every time. When the program ends, its boxes are
emptied, and the next run starts from nothing.

> [think] So what does the computer keep? Your program stays in the
> editor, even when you close BASIC. A program you save is kept in a file
> for as long as you like. But the boxes are only there while the program
> runs.

## Bits

Inside the memory everything is made of tiny switches called **bits**.
A bit is either off or on: 0 or 1. Eight bits together are a **byte**,
and a byte can hold any whole number from 0 to 255. Each bit is worth
twice the one before it:

```basic
10 LET V = 1
20 FOR B = 1 TO 8
30 PRINT "BIT "; B; " IS WORTH "; V
40 LET V = V * 2
50 NEXT B
```

Add them all up, 1 + 2 + 4 + … + 128, and you get 255, the biggest
number one byte can hold. A letter fits in one byte too: chapter 28
shows which number each letter is.

## Keep trying

- Change line 20 of the first program to add 10 instead of 5. What does
  it say the second time you run it?
- Make the bit program go up to 16 bits.

::: adult
The point of this chapter is that a variable lives only while the
program runs, and that the program itself is something else, kept in
the editor and in files. A computer's memory is measured in bytes:
millions of them, called megabytes, and thousands of millions,
gigabytes.
:::
