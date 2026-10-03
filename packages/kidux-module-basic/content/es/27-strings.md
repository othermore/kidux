---
source_sha256 = "937a86dbadf882448559f2ef4c7879ba2cdbdc937da4fdd9f09604e429d643d3"
---
# Cadenas

Una caja de palabras guarda una **cadena**: letras una detrás de otra,
como las cuentas de un collar. BASIC tiene herramientas para desmontar
cadenas.

- `LEN(P$)` es cuántas letras tiene P$.
- `LEFT$(P$, 3)` son sus 3 primeras letras, y `RIGHT$(P$, 3)` sus 3
  últimas.
- `MID$(P$, 2, 4)` son 4 letras a partir de la segunda.

```basic
10 LET P$ = "PINGÜINO"
20 PRINT LEN(P$)
30 PRINT LEFT$(P$, 4)
40 PRINT RIGHT$(P$, 4)
50 PRINT MID$(P$, 3, 3)
```

## Letra a letra

```basic keys=PINGUINO,Enter
10 INPUT "¿UNA PALABRA? "; P$
20 FOR I = 1 TO LEN(P$)
30 PRINT MID$(P$, I, 1)
40 NEXT I
```

Y al revés, para ver tu palabra en un espejo:

```basic keys=ROMA,Enter
10 INPUT "¿UNA PALABRA? "; P$
20 LET R$ = ""
30 FOR I = LEN(P$) TO 1 STEP -1
40 LET R$ = R$ + MID$(P$, I, 1)
50 NEXT I
60 PRINT R$
```

## Números y cadenas

`VAL` convierte una cadena de cifras en un número, y `STR$` convierte
un número en una cadena:

```basic
10 LET A$ = "12"
20 PRINT A$ + A$
30 PRINT VAL(A$) + VAL(A$)
40 PRINT "LA RESPUESTA ES" + STR$(6 * 7)
```

`"12" + "12"` junta dos cadenas; `VAL` las convierte en números para
sumarlos.

## Esperar una tecla

`INKEY$` es la tecla que se está pulsando, o una cadena vacía cuando no
hay ninguna. No espera: un programa que quiere una tecla pregunta una y
otra vez hasta que llega una.

```basic keys=x
10 PRINT "PULSA UNA TECLA PARA DESPERTAR AL PINGÜINO"
20 LET T$ = INKEY$
30 IF T$ = "" THEN 20
40 PRINT "UAAAH... HAS PULSADO "; T$
```

> [point] La línea 30 vuelve a la 20 mientras no se ha pulsado ninguna
> tecla. Ese pequeño bucle es la manera de esperar de un programa.

## Sigue probando

- Pide un nombre, y escribe su primera letra y cuántas letras tiene.
- ¿Se lee igual una palabra al revés? Escribe si es un *palíndromo*, como
  `RADAR`.
- Haz que el concurso del capítulo 19 espere una tecla después de cada
  respuesta.

::: adult
`INKEY$` vuelve enseguida, así que un juego puede seguir moviéndose
mientras vigila el teclado; el juego de dibujar del capítulo 30 lo hace.
`STR$` pone un espacio delante de un número positivo, donde iría su
signo.
:::
