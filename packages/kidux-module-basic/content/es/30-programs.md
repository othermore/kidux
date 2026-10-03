---
source_sha256 = "a449b4331e65975b8a38a0105f3b8b4d6bb2fee92e302ae73d0b59d0c815baa0"
---
# Programas para guardar

Estos programas usan todo lo de esta guía. Escríbelos, juega con ellos,
cámbialos, y guarda los que te gusten con **Guardar**.

## El juego de los reflejos

¿Qué rápido eres? Pulsa una tecla en cuanto aparezca la estrella.

```basic keys=x
10 RANDOMIZE
20 CLS
30 PRINT "¡CUANDO SALGA LA ESTRELLA, PULSA UNA TECLA!"
40 SLEEP 1000 + INT(RND * 3000)
50 PRINT "*"
60 LET T = TIMER
70 IF INKEY$ = "" THEN 70
80 PRINT "HAS TARDADO "; INT((TIMER - T) * 100) / 100; " SEGUNDOS"
```

`TIMER` es el reloj del ordenador: los segundos desde medianoche, con
decimales. La línea 60 apunta la hora a la que salió la estrella, y la
línea 80 la resta de la hora a la que llegó la tecla.

## La Liga del Hielo

Cinco equipos de pingüinos juegan al baloncesto. Una victoria vale 2
puntos y una derrota 1. El programa calcula los puntos y ordena a los
equipos, el mejor primero.

```basic
10 DIM N$(5), P(5)
20 FOR I = 1 TO 5
30 READ N$(I), G, D
40 LET P(I) = G * 2 + D
50 NEXT I
60 FOR V = 1 TO 4
70 FOR I = 1 TO 5 - V
80 IF P(I) < P(I + 1) THEN SWAP P(I), P(I + 1): SWAP N$(I), N$(I + 1)
90 NEXT I
100 NEXT V
110 PRINT "LA LIGA DEL HIELO"
120 FOR I = 1 TO 5
130 PRINT I; ". "; N$(I); SPACE$(10 - LEN(N$(I))); P(I); " PUNTOS"
140 NEXT I
150 DATA PIP, 6, 2, TOM, 3, 5, LULU, 7, 1, BEA, 4, 4, MAX, 2, 6
```

Cuando dos estanterías van juntas, un nombre y sus puntos, hay que
cambiarlas juntas, como hace la línea 80. `SPACE$(10 - LEN(N$(I)))`
escribe espacios detrás de cada nombre para que los puntos queden en
columna.

## La agenda

```basic keys=LULU,Enter,SAM,Enter,Enter
10 DIM N$(4), T$(4)
20 FOR I = 1 TO 4: READ N$(I), T$(I): NEXT I
30 INPUT "¿EL TELEFONO DE QUIEN? (INTRO PARA ACABAR) "; Q$
40 IF Q$ = "" THEN END
50 FOR I = 1 TO 4
60 IF N$(I) = Q$ THEN PRINT Q$; ": "; T$(I): GOTO 30
70 NEXT I
80 PRINT "NO ESTA EN LA AGENDA"
90 GOTO 30
100 DATA PIP, 555 0101, TOM, 555 0102
110 DATA LULU, 555 0103, BEA, 555 0104
```

Pulsar Intro sin escribir nada da una respuesta vacía, y la línea 40
termina el programa.

## Una lista por orden alfabético

Escribe nombres en cualquier orden, y el ordenador los pone en el orden
del abecedario. Una respuesta vacía quiere decir que no hay más.

```basic keys=TOM,Enter,ANA,Enter,PIP,Enter,BEA,Enter,Enter
10 DIM N$(20)
20 LET C = 0
30 INPUT "¿UN NOMBRE? (INTRO PARA ACABAR) "; A$
40 IF A$ = "" OR C = 20 THEN 70
50 LET C = C + 1: LET N$(C) = A$
60 GOTO 30
70 FOR V = 1 TO C - 1
80 FOR I = 1 TO C - V
90 IF N$(I) > N$(I + 1) THEN SWAP N$(I), N$(I + 1)
100 NEXT I
110 NEXT V
120 FOR I = 1 TO C: PRINT N$(I): NEXT I
```

## Tu biblioteca

Apunta tus propios libros en las líneas `DATA`: el título, y luego quién
lo escribió. El programa encuentra todos los libros de un autor.

```basic keys=ROSA,Enter
10 INPUT "¿QUE AUTOR? "; A$
20 LET F = 0
30 READ T$, E$
40 IF T$ = "FIN" THEN 70
50 IF E$ = A$ THEN PRINT T$: LET F = F + 1
60 GOTO 30
70 PRINT F; " LIBROS DE "; A$
80 DATA EL CASTILLO DE NIEVE, ROSA
90 DATA PESCADO PARA MERENDAR, MAX
100 DATA EL PINGÜINO DE LA NOCHE, ROSA
110 DATA FIN, FIN
```

## El juego de dibujar

Dibuja con las flechas; la barra espaciadora cambia el color. Escape para
el programa, y el dibujo se queda en la pantalla.

```basic keys=Right,Right,Space,Down,Down forever
10 SCREEN 12
20 LET X = 320: LET Y = 240: LET C = 14
30 LET K$ = INKEY$
40 IF K$ = "" THEN 30
50 IF K$ = " " THEN LET C = C + 1: IF C > 15 THEN LET C = 1
60 IF LEN(K$) < 2 THEN 30
70 LET VX = X: LET VY = Y
80 LET A$ = RIGHT$(K$, 1)
90 IF A$ = "H" THEN LET Y = Y - 8
100 IF A$ = "P" THEN LET Y = Y + 8
110 IF A$ = "K" THEN LET X = X - 8
120 IF A$ = "M" THEN LET X = X + 8
130 LINE (VX, VY)-(X, Y), C
140 GOTO 30
```

Una flecha son dos caracteres: `CHR$(0)` y una letra, `H` arriba, `P`
abajo, `K` izquierda y `M` derecha. La línea 60 solo deja pasar esas
teclas, y la línea 80 mira la letra.

## Programar bien

Ya sabes escribir programas. Estas son las costumbres que los hacen
buenos:

- **Piensa primero.** ¿Qué debe hacer el programa? ¿Qué pregunta, y qué
  enseña?
- **Dibuja el diagrama** antes de escribir, como en el capítulo 13.
- **Pon buenos nombres a las cajas:** `PUNTOS` dice más que `P`.
- **Pon `REM`** donde empieza cada parte del programa, diciendo para qué
  sirve.
- **Atrapa las respuestas equivocadas**, para que un error al escribir no
  pare el programa, como en el capítulo 22.
- **Haz un menú** cuando el programa haga varias cosas, como en el
  capítulo 23.
- **Pruébalo con otra persona.** Hará cosas que a ti nunca se te
  ocurrieron.

> [cheer] Esa es toda la guía. A partir de aquí, los programas son tuyos.

::: adult
La guía termina donde un niño puede seguir solo: cambiar estos programas
es el mejor paso siguiente, y las costumbres de la última sección son las
mismas en todos los lenguajes que conocerá después, Scratch, Python o
cualquier otro.
:::
