---
source_sha256 = "d89cc6366742446f78edbca7c8be0c79ab3b2edb8bb31e716b0f3277307ed123"
---
# REM: notas para ti

Un programa que escribiste la semana pasada puede ser difícil de entender
hoy. Las líneas `REM` son notas para las personas: el ordenador se las
salta.

```basic keys=4,Enter
10 REM LA TIENDA DE PECES
20 REM HECHA POR MI
30 LET PRECIO = 3
40 INPUT "¿CUANTOS PECES? "; N
50 REM CALCULA LO QUE CUESTA
60 PRINT "SON "; N * PRECIO; " MONEDAS"
```

Un apóstrofo, `'`, es un `REM` más corto, y también puede ir al final
de una línea:

```basic
10 LET PRECIO = 3 ' LO QUE CUESTA UN PEZ
20 ' UNA LINEA ENTERA DE NOTA
30 PRINT PRECIO
```

> [point] Las buenas notas dicen *por qué*, no solo *qué*. Tú, más
> adelante, lo agradecerás.

## Sigue probando

- Añade notas a tu concurso del capítulo 6.
- Escribe arriba de cada programa su nombre y lo que hace.

::: adult
Las notas son una costumbre que conviene coger pronto. Leer un programa
en voz alta, con sus notas, es también una buena manera de que el niño
explique lo que ha hecho.
:::
