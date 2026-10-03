---
source_sha256 = "715820360a073cd69cf4bc9202809b1f2806fdc3eb930436aba50dc9da027b8f"
---
# READ, DATA y RESTORE

Las líneas `DATA` son un almacén de cosas que el programa lee en orden
con `READ`. Pueden tener palabras y números juntos.

```basic
10 FOR N = 1 TO 4
20 READ A$, J$
30 PRINT A$; " JUEGA "; J$
40 NEXT N
50 DATA PIP, AL FUTBOL, TOM, AL AJEDREZ
60 DATA LULU, CON EL PIANO, BEA, AL ESCONDITE
```

## Buscar

Para encontrar a qué juega alguien, lee a los amigos uno a uno hasta que
el nombre sea el que buscas. El último `DATA` es una marca que dice *no
hay más*, como en el capítulo 9:

```basic keys=LULU,Enter
10 INPUT "¿QUE AMIGO? "; Q$
20 READ A$, J$
30 IF A$ = "FIN" THEN PRINT "NO CONOZCO A "; Q$: END
40 IF A$ = Q$ THEN PRINT Q$; " JUEGA "; J$: END
50 GOTO 20
60 DATA PIP, AL FUTBOL, TOM, AL AJEDREZ
70 DATA LULU, CON EL PIANO, BEA, AL ESCONDITE
80 DATA FIN, FIN
```

## Volver a leer

`READ` se acuerda de por dónde iba. `RESTORE` lo devuelve al primer
`DATA`, para leerlo todo otra vez:

```basic keys=TOM,Enter,SI,Enter,BEA,Enter,NO,Enter
10 INPUT "¿QUE AMIGO? "; Q$
20 RESTORE
30 READ A$, J$
40 IF A$ = "FIN" THEN PRINT "NO CONOZCO A "; Q$: GOTO 70
50 IF A$ = Q$ THEN PRINT Q$; " JUEGA "; J$: GOTO 70
60 GOTO 30
70 INPUT "¿OTRO? "; O$
80 IF O$ = "SI" THEN 10
90 DATA PIP, AL FUTBOL, TOM, AL AJEDREZ
100 DATA LULU, CON EL PIANO, BEA, AL ESCONDITE
110 DATA FIN, FIN
```

> [point] Sin la línea 20, la segunda búsqueda empezaría donde paró la
> primera, y se saltaría los amigos de antes.

## Sigue probando

- Añade a tus amigos y a qué juegan.
- Haz un concurso con `DATA`: una pregunta y su respuesta en cada línea.

::: adult
`RESTORE` también puede nombrar una línea, `RESTORE 100`, para leer desde
esa línea `DATA` en adelante. Buscar en una lista elemento a elemento es
como encuentra las cosas un ordenador cuando no están ordenadas; el
capítulo 26 las ordena.
:::
