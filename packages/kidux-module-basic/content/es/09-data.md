---
source_sha256 = "228809a494d1115fafd88d913dc9ff43a55874e83b330154aa3c52ecc9d2869e"
---
# READ y DATA: un almacén de cosas

Cuando un programa necesita muchos valores, `DATA` los guarda en una
lista, y `READ` los va sacando uno a uno, en orden.

```basic
10 READ A, B, C
20 PRINT A + B + C
30 DATA 5, 7, 4
```

`READ A, B, C` pone el primer valor en A, el siguiente en B y el
siguiente en C.

## Palabras en DATA

`DATA` también puede guardar palabras, que se leen en cajas con `$`.

```basic
10 FOR N = 1 TO 3
20 READ NOMBRE$, COMIDA$
30 PRINT "A "; NOMBRE$; " LE GUSTA "; COMIDA$
40 NEXT N
50 DATA PIP, EL PESCADO, TOM, LA TARTA, LULU, EL HELADO
```

> [think] ¿Qué pasa si `READ` quiere más valores de los que tiene
> `DATA`? Prueba a cambiar el `3` por un `4` en la línea 10.

El ordenador dice que no quedan más `DATA` que leer.

## Una señal que dice basta

Para leer una lista sin contarla, se pone al final un valor de más que
quiere decir *se acabó*, y `IF` lo vigila.

```basic
10 LET TOTAL = 0
20 READ N
30 IF N = -1 THEN 60
40 LET TOTAL = TOTAL + N
50 GOTO 20
60 PRINT "EL TOTAL ES "; TOTAL
70 DATA 3, 8, 12, 5, -1
```

## Sigue probando

- Guarda en `DATA` los nombres y las edades de cinco amigos, y
  escríbelos.
- Añade un sexto amigo en el programa de la señal, sin cambiar nada más
  que los `DATA`.

::: adult
Las líneas `DATA` pueden ir en cualquier sitio del programa; al final es
lo más claro. `RESTORE` vuelve a leer desde el primer valor, cosa que
usa el capítulo 24.
:::
