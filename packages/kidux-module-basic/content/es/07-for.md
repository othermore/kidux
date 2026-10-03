---
source_sha256 = "313f3612a5b56873dcca4c77acbbc9b177c1396fee089d55dc5ac7eee190928f"
---
# FOR y NEXT: el bucle que cuenta

Contar con `GOTO` necesita una caja, una suma y un salto. `FOR` hace las
tres cosas a la vez: cuenta de un número a otro, y hace las líneas entre
`FOR` y `NEXT` una vez por cada número.

```basic
10 FOR N = 1 TO 5
20 PRINT "PINGÜINO NUMERO "; N
30 NEXT N
40 PRINT "¡CINCO PINGÜINOS!"
```

![Un bucle da vueltas y vueltas](loop.svg)

`NEXT N` quiere decir *el siguiente N, por favor*. Cuando N ha valido 5,
el bucle termina y el ordenador sigue con la línea 40.

> [cheer] Cada `FOR` necesita su `NEXT`. Si se te olvida, el ordenador
> te dice que falta algo al final.

## STEP

`STEP` dice de cuánto en cuánto contar. Hasta puede contar hacia atrás.

```basic
10 FOR N = 0 TO 20 STEP 5
20 PRINT N
30 NEXT N
40 FOR N = 10 TO 1 STEP -1
50 PRINT N; " ";
60 NEXT N
70 PRINT "¡DESPEGUE!"
```

## Una tabla

```basic
10 FOR N = 1 TO 10
20 PRINT N; " POR 3 SON "; N * 3
30 NEXT N
```

## Sigue probando

- Escribe tu nombre diez veces.
- Escribe la tabla del 7, o pregunta con `INPUT` qué tabla escribir.
- Cuenta de 100 a 0 de diez en diez.

::: adult
La caja que va detrás de `FOR` es una variable normal: dentro del bucle
se puede escribir y usar en cuentas. Un bucle dentro de otro es cosa del
capítulo 21; de momento basta con uno.
:::
