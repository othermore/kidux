---
source_sha256 = "cfa62060fc952829f8850cddcc156e75f5f66b7f64f3eaa191e545718a3fc13c"
---
# RND: el azar

`RND` da un número que nadie puede adivinar: un número al azar, desde 0
hasta casi 1. Cada vez es distinto.

```basic
10 RANDOMIZE
20 FOR N = 1 TO 5
30 PRINT RND
40 NEXT N
```

`RANDOMIZE` al principio mezcla los números, para que cada vez salgan
otros.

## Un dado

Un dado saca 1, 2, 3, 4, 5 o 6. Multiplica `RND` por 6, quédate con la
parte entera con `INT` y suma 1:

![Un dado](dice.svg)

```basic
10 RANDOMIZE
20 LET D = INT(RND * 6) + 1
30 PRINT "HAS SACADO UN "; D
```

Cada vez que pulsas Ejecutar, tiras el dado.

## Cien tiradas

¿Cuántos cincos salen en cien tiradas? Nadie lo sabe hasta probar, y el
ordenador prueba muy deprisa.

```basic
10 RANDOMIZE
20 LET CINCOS = 0
30 FOR T = 1 TO 100
40 LET D = INT(RND * 6) + 1
50 IF D = 5 THEN LET CINCOS = CINCOS + 1
60 NEXT T
70 PRINT "EN 100 TIRADAS, "; CINCOS; " CINCOS"
```

> [cheer] Ejecútalo varias veces. Muchas veces sale cerca de 16 o 17, la
> sexta parte de 100, pero casi nunca lo mismo.

## Sigue probando

- Tira mil veces en lugar de cien.
- Cuenta los seises además de los cincos.
- Tira dos dados y súmalos.

::: adult
`INT(RND * N) + 1` da un número entero del 1 al N, todos igual de
probables. Simular muchas tiradas es un primer vistazo, jugando, a la
probabilidad; vale la pena pedir al niño que adivine antes de ejecutar.
:::
