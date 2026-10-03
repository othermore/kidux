---
source_sha256 = "c68f879ec8f5d88ecebf132604e23fe4d2965ec9ac3e048b60a51b3ac3f3f31c"
---
# Qué hace primero el ordenador

¿Cuánto es 2 + 3 × 4? Si sumas primero, 20; si multiplicas primero, 14.
El ordenador hace las cosas siempre en el mismo orden:

1. lo que está entre paréntesis, `(` y `)`;
2. las potencias, `^`;
3. `*` y `/`, de izquierda a derecha;
4. `+` y `-`, de izquierda a derecha.

```basic
10 PRINT 2 + 3 * 4
20 PRINT (2 + 3) * 4
30 PRINT 10 - 4 - 3
40 PRINT 2 * 3 ^ 2
```

## La vuelta equivocada

Pip compra 2 peces a 4 monedas cada uno y 3 conchas a 1 moneda cada una,
y paga con 20 monedas. ¿Cuánto le devuelven?

```basic
10 LET VUELTA = 20 - 2 * 4 + 3 * 1
20 PRINT "VUELTA MAL: "; VUELTA
30 LET VUELTA = 20 - (2 * 4 + 3 * 1)
40 PRINT "VUELTA BIEN: "; VUELTA
```

La línea 10 quita los peces y luego *suma* las conchas: a Pip le
devolverían 15 monedas por una compra de 11. Los paréntesis de la línea
30 hacen que el ordenador sume primero la compra.

> [oops] Cuando no estés seguro de qué hará primero el ordenador, pon
> paréntesis. Nunca hacen daño.

## La media

La media de tres notas es su suma dividida entre tres:

```basic
10 LET A = 7: LET B = 8: LET C = 9
20 PRINT "SIN PARENTESIS: "; A + B + C / 3
30 PRINT "CON PARENTESIS: "; (A + B + C) / 3
```

Dos puntos, `:`, ponen dos órdenes en la misma línea.

## Sigue probando

- Calcula en papel 100 - 10 * 5 + 2, y luego pregúntaselo al ordenador.
- Escribe un programa que pida cuatro notas y escriba su media.

::: adult
Son las reglas de siempre de la aritmética. Un error muy común, aquí y en
cualquier lenguaje, es la media sin paréntesis; una buena costumbre es
poner entre paréntesis toda suma que se divide.
:::
