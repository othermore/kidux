---
source_sha256 = "4523565c511ab744df0dddb45e8e375208b55f48d9087c6c8764e5703a8a3fdd"
---
# INT: números enteros

Reparte 7 peces entre 2 pingüinos y el ordenador dice 3.5. Pero medio pez
no le sirve a nadie. `INT` se queda con la parte entera de un número y
tira el resto.

```basic
10 PRINT 7 / 2
20 PRINT INT(7 / 2)
30 PRINT INT(9.99)
```

`INT` no redondea: 9.99 se queda en 9, no en 10. Fíjate también en que
los ordenadores escriben los decimales con un punto, no con una coma.

## Cuántos a cada uno, y cuántos sobran

```basic keys=17,Enter,5,Enter
10 INPUT "¿CUANTOS PECES? "; P
20 INPUT "¿CUANTOS PINGÜINOS? "; G
30 LET CADA = INT(P / G)
40 LET SOBRAN = P - CADA * G
50 PRINT "A CADA UNO LE TOCAN "; CADA
60 PRINT "Y SOBRAN "; SOBRAN
```

> [think] Para redondear al entero más cercano, suma antes un medio:
> `INT(X + 0.5)`. Pruébalo con 9.99 y con 9.2.

## Sigue probando

- ¿Es par un número? Lo es cuando `INT(N / 2) * 2 = N`. Escribe un
  programa que diga si un número es par o impar.
- Reparte caramelos entre amigos, y di cuántos le tocan a cada uno y
  cuántos sobran.

::: adult
`INT` da el entero igual o menor: `INT(-2.5)` es -3. El capítulo 12 lo
necesita para convertir el azar en números enteros.
:::
