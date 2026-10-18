# BASIC

*[Versión en español](../../es/modules/basic.md)* · [Back to the user guide](../user-guide.md#9-learning-modules)

**BASIC** was the programming language that introduced millions of children to computing during the home computer revolution of the 1980s, and it remains one of the most accessible and rewarding ways to learn real programming. This module recreates that foundational experience in a modern, split-screen format: on the left, an interactive environment with a code editor and display screen; on the right, a comprehensive step-by-step interactive tutorial.

| | |
|---|---|
| **Recommended age** | Children ages 8 to 14 with good reading skills |
| **Recommended prior modules** | Scratch |
| **Internet connection** | Not required (works completely offline) |
| **Underlying software** | [wwwBASIC](https://github.com/google/wwwbasic), developed by Google under the Apache-2.0 licence, integrated into an exclusive Kidux educational environment |

## Overview and how it works

The left half of the screen is organized into three main sections:
- **The code editor (top)**: where the child writes and edits lines of BASIC code.
- **The control toolbar (center)**: contains buttons to control execution. The **Run** button (or the Ctrl+Enter keyboard shortcut) starts the program immediately. If a program runs indefinitely or needs interruption, the **Stop** button (or Escape key) terminates it safely.
- **The output display (bottom)**: presents the program output, including text, graphics, colors, and retro audio tones. When a syntax or runtime error occurs, the display identifies the exact line number, and the editor visually highlights it to make debugging simple.

The right half of the screen houses the interactive guide, organized chapter by chapter. Using the **Back**, **Next**, or **Chapters** navigation buttons, the child reads explanations, types example code into the editor, and experiments with variations. Each chapter concludes with creative exercises for further exploration and an **For adults** section summarizing the educational concepts introduced.

![BASIC](../../images/en/module-basic.png)

## The thirty course chapters

1. Hello, computer
2. PRINT: the computer writes
3. LET: named containers (variables)
4. INPUT: talking with the computer
5. GOTO: jumping through code
6. IF: making decisions
7. FOR and NEXT: counting loops and repetition
8. GOSUB and RETURN: reusable subroutines
9. READ and DATA: storing data tables
10. REM: notes and comments for yourself
11. INT: integer arithmetic and rounding
12. RND: generating random numbers
13. Flowcharts: planning before programming
14. Building interactive games
15. Saving and organizing your programs
16. Inside the computer: how it works
17. Advanced mathematical operations
18. Order of operations and precedence
19. CLS: clearing and resetting the screen
20. Advanced user input with INPUT
21. Nested loops with FOR and NEXT
22. Boolean logic: AND and OR
23. Building interactive menus with IF
24. Advanced data management with READ, DATA, and RESTORE
25. DIM: structured arrays and lists
26. Sorting algorithms
27. Working with strings and text
28. ASCII codes: CHR$ and ASC
29. Coordinate drawing, color palettes, and sound
30. Complete projects to keep and expand

## Adult configuration options

| Setting | Function and purpose |
|---|---|
| **Type for me** | Displays a convenience button under each code block in the guide that automatically copies the program into the editor. When turned off, the child must type each program manually character by character to practice typing and syntax. Enabled by default. |

This setting can be configured independently for each child from the BASIC **Settings** button in the Modules tab of the adult panel.

## Saving and managing files

Code written in the editor is automatically preserved when leaving BASIC and will be waiting when the module reopens, until the child clicks **New**.

To store programs permanently, the **Save** button opens a standard file dialog in the child's folders (inside **Downloads**) to save files with a `.bas` extension. The **Open** button allows loading any previously saved program.
