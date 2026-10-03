---
source_sha256 = "2340034df0e1f3f1a21d45ff99de8675fcded02d6a79c9ce532ef98c06032b80"
---
# INPUT, más

`INPUT` puede hacer una pregunta y esperar la respuesta en una sola
línea, como haces desde el capítulo 4. También puede recoger varias
respuestas a la vez: pon sus cajas detrás de la pregunta, separadas por
comas, y escribe las respuestas separadas también por comas.

```basic keys=6,Comma,4,Enter
10 INPUT "¿ANCHO Y LARGO DEL JARDIN? "; A, L
20 PRINT "TIENE "; A * L; " METROS CUADRADOS"
30 PRINT "Y UNA VALLA DE "; 2 * A + 2 * L; " METROS"
```

Para contestar, escribe `6,4` y pulsa Intro.

## Palabras y números juntos

```basic keys=PIP,Comma,7,Comma,PESCADO,Enter
10 INPUT "¿NOMBRE, EDAD Y COMIDA FAVORITA? "; N$, E, C$
20 PRINT N$; " TIENE "; E; " Y LE ENCANTA EL "; C$
```

> [point] Di en la pregunta cuántas respuestas quieres, y en qué orden.
> Quien escribe no puede ver tu programa.

## Una máquina de cuentos

```basic keys=PIP,Comma,BAILABA,Comma,HIELO,Enter
10 PRINT "DAME ALGUIEN, UNA ACCION Y UN SITIO."
20 INPUT "SEPARALOS CON COMAS: "; Q$, A$, S$
30 PRINT "HABIA UNA VEZ "; Q$; " QUE "; A$; " EN EL "; S$; "."
40 PRINT "Y TODOS APLAUDIERON."
```

## Sigue probando

- Pide los tres lados de un triángulo y escribe cuánto mide todo
  alrededor.
- Haz que la máquina de cuentos pida cinco palabras y cuente un cuento
  más largo.

::: adult
Una coma dentro de una respuesta la separa de la siguiente, así que una
respuesta con una coma no se puede escribir así en una caja de palabras.
Si se escriben menos respuestas de las que se piden, un número que falta
sale como `NaN`, *no es un número*; por eso la pregunta debe decir
cuántas quiere.
:::
