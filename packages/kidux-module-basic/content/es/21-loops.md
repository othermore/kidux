---
source_sha256 = "f73c91e9649d41b8fbdc18a4bd68d9ba0c76dae6725059c3363670cc82b17347"
---
# FOR y NEXT, más

## Salir antes de un bucle

Un bucle `FOR` cuenta hasta el final, pero un `GOTO` puede sacarte
antes. Este eleva números al cuadrado hasta que escribes 0, o hasta que
ha hecho diez:

```basic keys=3,Enter,12,Enter,0,Enter
10 FOR N = 1 TO 10
20 INPUT "¿UN NUMERO, O 0 PARA ACABAR? "; X
30 IF X = 0 THEN 60
40 PRINT X; " POR "; X; " SON "; X * X
50 NEXT N
60 PRINT "¡ADIOS!"
```

## Un bucle que espera

`SLEEP` hace que el ordenador espere. El número que va detrás está en
milésimas de segundo, así que `SLEEP 1000` espera un segundo:

```basic
10 FOR N = 5 TO 1 STEP -1
20 PRINT N
30 SLEEP 1000
40 NEXT N
50 PRINT "¡DESPEGUE!"
```

> [point] `SLEEP 500` espera medio segundo, y `SLEEP 3000` tres
> segundos.

## Bucles dentro de bucles

Un bucle puede tener otro bucle dentro. El de dentro da la vuelta entera
cada vez que el de fuera da una vuelta, como los minutos dentro de las
horas de un reloj.

```basic
10 FOR F = 1 TO 4
20 FOR E = 1 TO F
30 PRINT "*";
40 NEXT E
50 PRINT
60 NEXT F
```

El bucle de dentro tiene que acabar antes que el de fuera: `NEXT E` va
antes que `NEXT F`.

## Las tablas, una a una

```basic
10 FOR T = 2 TO 5
20 CLS
30 PRINT "LA TABLA DEL "; T
40 FOR N = 1 TO 10
50 PRINT T; " X "; N; " = "; T * N
60 NEXT N
70 SLEEP 3000
80 NEXT T
```

Cada tabla se queda tres segundos en la pantalla, y luego la siguiente
ocupa su sitio.

## Sigue probando

- Convierte el triángulo de estrellas en un árbol, con su tronco abajo.
- Haz que las tablas esperen cinco segundos, o que vayan de la tabla del
  2 a la del 10.

::: adult
Salir de un bucle con `GOTO` es como lo hacían los ordenadores de casa,
y aquí funciona. Los bucles anidados son la primera dificultad de verdad
para muchos niños: dibujar las estrellas en papel cuadriculado, fila a
fila, ayuda.
:::
