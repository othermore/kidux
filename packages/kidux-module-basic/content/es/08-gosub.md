---
source_sha256 = "280f2450044e5e15c0c5994d5d8300b77f221822f6263e0440015349e00fc34c"
---
# GOSUB y RETURN: un trozo que se usa muchas veces

A veces hacen falta las mismas líneas en varios sitios. En lugar de
escribirlas otra vez, se escriben una vez, al final, y se va a ellas con
`GOSUB`. `RETURN` vuelve justo detrás del `GOSUB` que fue allí.

```basic
10 PRINT "PRIMERA PREGUNTA"
20 GOSUB 100
30 PRINT "SEGUNDA PREGUNTA"
40 GOSUB 100
50 PRINT "FIN"
60 END
100 PRINT "*-*-*-*-*-*-*-*"
110 RETURN
```

Las líneas 100 y 110 son una **subrutina**: un programa pequeño dentro
del grande.

> [oops] Mira la línea 60. Sin `END`, el ordenador seguiría solo hasta
> la subrutina, y su `RETURN` no tendría adónde volver.

## Una subrutina que hace más

```basic
10 FOR N = 1 TO 3
20 GOSUB 100
30 NEXT N
40 END
100 PRINT "EL PINGÜINO "; N; " SALUDA:"
110 PRINT "  ¡HOLA!"
120 PRINT
130 RETURN
```

## Sigue probando

- Haz una subrutina que dibuje un pez pequeño con letras, y úsala tres
  veces.
- Pon una línea larga de estrellas en una subrutina y úsala entre las
  preguntas de tu concurso.

::: adult
Una subrutina es el primer paso para organizar un programa por partes,
lo que importa más cuanto más crecen los programas. Si el programa de un
niño termina con un error que habla de un RETURN sin su GOSUB, casi
siempre falta un `END` antes de las subrutinas.
:::
