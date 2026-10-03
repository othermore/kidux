---
source_sha256 = "5fa7845960a57815adbab7a5e47442e9a3a63dbb43bc087074810e6d51555c22"
---
# Poner las cosas en orden

El ordenador sabe comparar números con `<` y `>`, y también palabras:
para las palabras, *menor* quiere decir *antes en el abecedario*.

```basic
10 IF 3 < 7 THEN PRINT "EL 3 VA ANTES QUE EL 7"
20 IF "ANA" < "TOM" THEN PRINT "ANA VA ANTES QUE TOM"
30 IF "PIP" > "BEA" THEN PRINT "PIP VA DESPUES DE BEA"
```

## Cambiar dos cajas

Para cambiar lo que tienen dos cajas hace falta una tercera, de repuesto:
primero el pez va a la caja de repuesto, luego el copo de nieve a la caja
del pez, y luego el pez de la caja de repuesto a la del copo.

![Cambiar con una caja de repuesto](swap.svg)

```basic
10 LET A = 3: LET B = 8
20 PRINT "ANTES: "; A; " Y "; B
30 LET R = A
40 LET A = B
50 LET B = R
60 PRINT "DESPUES: "; A; " Y "; B
```

> [oops] Sin la caja de repuesto, `LET A = B` perdería lo que tenía A, y
> las dos cajas acabarían con un 8.

BASIC también tiene `SWAP A, B`, que hace los tres pasos de una vez.

## Ordenar números

El **método de la burbuja** recorre la estantería comparando cada caja con
la siguiente, y las cambia cuando están al revés. Tras una vuelta, el
número más grande ha subido como una burbuja hasta el final; tras
bastantes vueltas, todo está en orden.

```basic
10 DIM N(6)
20 FOR I = 1 TO 6: READ N(I): NEXT I
30 FOR V = 1 TO 5
40 FOR I = 1 TO 6 - V
50 IF N(I) > N(I + 1) THEN SWAP N(I), N(I + 1)
60 NEXT I
70 NEXT V
80 FOR I = 1 TO 6: PRINT N(I); " ";: NEXT I
90 PRINT
100 DATA 42, 7, 19, 3, 25, 11
```

## Ordenar nombres

El mismo programa ordena palabras, con cajas de palabras:

```basic
10 DIM N$(6)
20 FOR I = 1 TO 6: READ N$(I): NEXT I
30 FOR V = 1 TO 5
40 FOR I = 1 TO 6 - V
50 IF N$(I) > N$(I + 1) THEN SWAP N$(I), N$(I + 1)
60 NEXT I
70 NEXT V
80 FOR I = 1 TO 6: PRINT N$(I): NEXT I
90 DATA TOM, ANA, PIP, LULU, BEA, MAX
```

## Sigue probando

- Ordena los números de mayor a menor. ¿Qué signo cambias?
- Escribe la estantería después de cada vuelta, para ver subir las
  burbujas.

::: adult
Las palabras se comparan letra a letra por sus códigos (capítulo 28), así
que las mayúsculas van antes que las minúsculas, y una palabra con tilde
o con ñ puede no quedar donde la pone un diccionario. El método de la
burbuja es lento para listas largas pero fácil de seguir, y por eso se
enseña el primero.
:::
