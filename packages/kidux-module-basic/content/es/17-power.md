---
source_sha256 = "a32755d758c552101ffd222f0afc8a8039e24acb158d2b8011b382a9f6a9afcc"
---
# La quinta operación

Conoces cuatro operaciones: `+`, `-`, `*` y `/`. La quinta es la
**potencia**, que se escribe `^`. `2 ^ 3` quiere decir 2 multiplicado
por sí mismo tres veces: 2 × 2 × 2, que es 8.

```basic
10 PRINT 2 ^ 3
20 PRINT 10 ^ 2
30 PRINT 3 ^ 4
40 PRINT 5 ^ 1, 5 ^ 0
```

Cualquier número elevado a 0 es 1, y elevado a 1 es él mismo.

## Los peces del pingüino

El pingüino hace un trato con el pescador: un pez el primer día, dos el
segundo, cuatro el tercero, y cada día el doble que el día anterior,
tantos días como casillas tiene un tablero, sesenta y cuatro. Al
pescador le parece barato.

![Un pez, dos, cuatro, ocho](board.svg)

```basic
10 LET P = 1
20 FOR D = 1 TO 30
30 PRINT "DIA "; D; ": "; P; " PECES"
40 LET P = P * 2
50 NEXT D
```

El día 30 son más de quinientos millones de peces, y aún quedan 34 días.
El día D el pingüino recibe `2 ^ (D - 1)` peces:

```basic
10 PRINT "DIA 64: "; 2 ^ 63; " PECES"
20 PRINT "EN TOTAL: "; 2 ^ 64 - 1
```

> [cheer] Doblar crece más deprisa que nada que puedas contar. ¡Pobre
> pescador!

## Números enormes

Cuando un número tiene demasiadas cifras, el ordenador lo escribe corto:

```basic
10 PRINT 10 ^ 20
20 PRINT 10 ^ 21
30 PRINT 2 ^ 100
```

`1e+21` quiere decir un 1 seguido de 21 ceros. El número que va detrás
de `e+` dice cuántos sitios se mueve el punto hacia la derecha. Los
números muy grandes ya no son exactos: un número calculado en un
`PRINT` guarda unas dieciséis cifras, y uno guardado en una caja, unas
siete.

## Sigue probando

- ¿Cuántos días tienen que pasar hasta que el pingüino reciba más de mil
  peces en un día? ¿Y más de un millón?
- Escribe las potencias de 3, desde `3 ^ 0` hasta `3 ^ 10`.

::: adult
Es la vieja historia de los granos de trigo en el tablero de ajedrez,
contada con peces. Los últimos números no son exactos: un cálculo guarda
unas dieciséis cifras significativas, y una variable, de precisión
simple como en los BASIC de la época, unas siete.
:::
