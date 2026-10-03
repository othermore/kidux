---
source_sha256 = "0a17822b5a1d2ea129c1e3498e66c358a3b72ae33131ec8587ae107452a1221e"
---
# Dentro del ordenador

Todo ordenador tiene tres partes que le importan a un programa. El
**teclado** es por donde entran las cosas. La **memoria** es donde el
ordenador guarda aquello con lo que está trabajando: allí viven las cajas
del capítulo 3. La **pantalla** es por donde salen.

![El teclado, la memoria y la pantalla](inside.svg)

Cuando pulsas **Ejecutar**, tu programa entra en la memoria y el
ordenador hace sus líneas una a una. Todas las cajas empiezan vacías: una
caja de números tiene 0, y una caja de palabras no tiene nada. Ejecuta
esto dos veces:

```basic
10 PRINT "PECES ANTES: "; PECES
20 LET PECES = PECES + 5
30 PRINT "PECES DESPUES: "; PECES
```

Dice 0 y luego 5 todas las veces. Cuando el programa termina, sus cajas
se vacían, y la siguiente vez empieza desde nada.

> [think] Entonces, ¿qué guarda el ordenador? Tu programa se queda en el
> editor, aunque cierres BASIC. Un programa que guardas se queda en un
> archivo todo el tiempo que quieras. Pero las cajas solo existen
> mientras el programa funciona.

## Bits

Dentro de la memoria todo está hecho de interruptores diminutos llamados
**bits**. Un bit está apagado o encendido: 0 o 1. Ocho bits juntos son un
**byte**, y un byte puede guardar cualquier número entero del 0 al 255.
Cada bit vale el doble que el anterior:

```basic
10 LET V = 1
20 FOR B = 1 TO 8
30 PRINT "EL BIT "; B; " VALE "; V
40 LET V = V * 2
50 NEXT B
```

Súmalos todos, 1 + 2 + 4 + … + 128, y sale 255, el número más grande que
cabe en un byte. Una letra también cabe en un byte: el capítulo 28
enseña qué número es cada letra.

## Sigue probando

- Cambia la línea 20 del primer programa para sumar 10 en vez de 5. ¿Qué
  dice la segunda vez que lo ejecutas?
- Haz que el programa de los bits llegue hasta 16 bits.

::: adult
La idea de este capítulo es que una variable solo vive mientras el
programa funciona, y que el programa es otra cosa, que se guarda en el
editor y en archivos. La memoria de un ordenador se mide en bytes:
millones de ellos, llamados megabytes, y miles de millones, gigabytes.
:::
