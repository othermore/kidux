---
source_sha256 = "c2525c8e5dda011c7a7121086674a1619791e65d142fc7fd979237d7b60cc725"
---
# GOTO: ¡salta!

`GOTO` manda al ordenador a otra línea, por su número, y sigue desde
allí. Un salto hacia atrás hace que el ordenador repita las mismas
líneas.

```basic forever
10 PRINT "EL PINGÜINO SE TIRA POR LA CUESTA"
20 GOTO 10
```

Este programa no termina nunca: la línea 20 siempre manda al ordenador a
la 10. Pulsa **Parar**, o la tecla Escape, para acabarlo.

> [oops] Un programa que da vueltas y vueltas para siempre se llama
> bucle. Cuando el tuyo no se pare, Escape siempre funciona.

## Contar

Un bucle con una caja que crece sabe contar.

```basic forever
10 LET N = 0
20 LET N = N + 2
30 PRINT N
40 GOTO 20
```

El ordenador cuenta de dos en dos más deprisa de lo que puedes leer.
Páralo y repasa la pantalla con los ojos.

## Un salto hacia delante

`GOTO` también puede saltar hacia delante, por encima de líneas que no
debe hacer. `END` termina el programa.

```basic
10 PRINT "UNO"
20 GOTO 40
30 PRINT "ESTA LINEA SE LA SALTA"
40 PRINT "DOS"
50 END
```

> [think] Si haces `GOTO` a una línea que no está en el programa, el
> ordenador te lo dice antes de empezar. Prueba `GOTO 99`.

## Sigue probando

- Haz que el programa de contar cuente de cinco en cinco, o de diez en
  diez.
- Cuenta hacia atrás desde 100, restando en lugar de sumar.
- Haz una tabla de sumar: un número que crece de uno en uno, y ese número
  más 3, escritos uno al lado del otro.

::: adult
`GOTO` es como los primeros ordenadores de casa hacían los bucles, y ver
un bucle que no termina es parte de aprender. Los capítulos siguientes
les ponen fin: `IF` decide cuándo parar, y `FOR` cuenta solo. Escape, o
el botón Parar, acaba cualquier programa, y no se pierde nada: el
programa sigue en el editor.
:::
