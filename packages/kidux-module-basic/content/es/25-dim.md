---
source_sha256 = "ff5767efc5809b0318c6e2f2fd02ec3852988a2906ba6bbc3e69b93d5a897245"
---
# DIM: una estantería de cajas

Cuando un programa necesita muchas cajas del mismo tipo, una para cada
amigo o para cada día, puede tener una **estantería** entera, con un solo
nombre y un número para cada caja. `DIM` hace la estantería:

```basic
10 DIM P(7)
20 FOR D = 1 TO 7
30 READ P(D)
40 NEXT D
50 PRINT "PECES EL DIA 3: "; P(3)
60 LET T = 0
70 FOR D = 1 TO 7
80 LET T = T + P(D)
90 NEXT D
100 PRINT "PECES EN TODA LA SEMANA: "; T
110 DATA 4, 6, 3, 8, 5, 9, 2
```

`P(3)` es la caja número 3 de la estantería `P`. El número entre
paréntesis también puede ser una caja, como `P(D)`, y esa es la magia: un
solo bucle recorre toda la estantería.

![Una estantería de cajas](boxes.svg)

## Una estantería de palabras

```basic
10 DIM N$(4)
20 FOR I = 1 TO 4: READ N$(I): NEXT I
30 FOR I = 4 TO 1 STEP -1
40 PRINT N$(I)
50 NEXT I
60 DATA PIP, TOM, LULU, BEA
```

Escribe a los amigos al revés. Un `FOR` con su `NEXT` en una sola línea,
con dos puntos, sigue siendo un bucle.

## Una tabla

Una estantería puede tener filas y columnas, como un armario. `DIM C(3, 4)`
hace tres filas de cuatro cajas; `C(2, 3)` es la fila 2, caja 3. Aquí tres
pingüinos apuntan los peces que pescan en cuatro días:

```basic
10 DIM C(3, 4)
20 FOR P = 1 TO 3
30 FOR D = 1 TO 4
40 READ C(P, D)
50 NEXT D
60 NEXT P
70 FOR P = 1 TO 3
80 LET T = 0
90 FOR D = 1 TO 4
100 LET T = T + C(P, D)
110 NEXT D
120 PRINT "EL PINGÜINO "; P; " PESCO "; T
130 NEXT P
140 DATA 3, 5, 2, 4
150 DATA 6, 1, 4, 4
160 DATA 2, 2, 7, 5
```

> [cheer] Con una estantería, un programa para cien amigos no es más
> largo que uno para cuatro.

## Sigue probando

- ¿Qué día fue el mejor para pescar en el primer programa? Busca el
  número más grande de la estantería.
- En la tabla, suma los peces de cada día de los tres pingüinos.

::: adult
`DIM` da nombre a un vector; las cajas se numeran desde 0, aunque la guía
las usa desde 1. Este BASIC dejaría usar una estantería sin `DIM`, pero la
guía siempre lo escribe: decir lo grande que es la estantería antes de
usarla es una costumbre que todos los lenguajes agradecen.
:::
