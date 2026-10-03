---
source_sha256 = "04b1740b592c330eb4a885bb84b254f8dfcbff205aff88eeba159271be8be7fc"
---
# INPUT: hablar con el ordenador

Hasta ahora el ordenador hablaba y tú escuchabas. `INPUT` le da la
vuelta: el ordenador se para, pregunta y espera a que escribas una
respuesta y pulses Intro. La respuesta va a una caja.

```basic keys=Leo,Enter
10 INPUT "¿COMO TE LLAMAS? "; N$
20 PRINT "HOLA, "; N$
```

Pulsa Ejecutar, escribe tu nombre y pulsa Intro. El ordenador contesta.

> [point] La pregunta va entre comillas, luego un punto y coma, y luego
> la caja para la respuesta. Deja un espacio antes de la última comilla,
> para que tu respuesta no se pegue a la pregunta.

## Respuestas que son números

Si la caja no lleva `$`, la respuesta es un número, y el ordenador puede
hacer cuentas con él.

```basic keys=7,Enter
10 INPUT "¿QUE EDAD TIENES? "; EDAD
20 PRINT "EL PROXIMO CUMPLE TENDRAS "; EDAD + 1
30 PRINT "DENTRO DE DIEZ, "; EDAD + 10
```

## Un programa que te conoce

```basic keys=Ana,Enter,9,Enter,PIZZA,Enter
10 INPUT "¿TU NOMBRE? "; N$
20 INPUT "¿TU EDAD? "; E
30 INPUT "¿TU COMIDA FAVORITA? "; C$
40 PRINT
50 PRINT N$; " TIENE "; E; " Y LE ENCANTA LA "; C$
60 PRINT "CUANDO PASEN "; 100 - E; " CUMPLES, "; N$; " TENDRA 100"
```

> [cheer] Ahora el mismo programa dice algo distinto para cada persona
> que lo ejecuta. Eso es lo que hace útiles a los programas.

## Sigue probando

- Pregunta dos números y escribe su suma.
- Pregunta un animal y un color, y escribe una frase con los dos.
- Escribe una palabra cuando el ordenador pide un número. ¿Qué hace?

::: adult
`INPUT` con una caja terminada en `$` acepta cualquier texto; sin
ella, un número. En este BASIC, una palabra escrita donde se espera un
número da `NaN`, «no es un número», en lugar de volver a preguntar. Es
un buen momento para hablar de comprobar lo que escribe la gente, que el
capítulo 22 hace como es debido.
:::
