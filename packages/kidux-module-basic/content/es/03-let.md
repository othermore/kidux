---
source_sha256 = "28f373b2b1fb157e98ff02d9864b50331fcbeb44726b982dba340fd72d3fbcbc"
---
# LET: cajas con nombre

Un ordenador recuerda las cosas en cajas de su memoria, y cada caja tiene
un nombre. Una caja así se llama **variable**. `LET` mete algo en una
caja.

![Cajas con nombre](boxes.svg)

```basic
10 LET PECES = 12
20 PRINT PECES
```

La caja se llama `PECES` y guarda el número 12. `PRINT PECES`, sin
comillas, escribe lo que hay dentro de la caja, no su nombre.

> [think] Con comillas, `PRINT "PECES"` escribe la palabra PECES. Sin
> ellas, `PRINT PECES` escribe 12. ¡Prueba las dos!

## Cuentas

El ordenador es muy bueno haciendo cuentas. Usa `+` y `-`, `*` para
multiplicar y `/` para dividir.

```basic
10 LET PECES = 12
20 LET AMIGOS = 4
30 LET CADA = PECES / AMIGOS
40 PRINT "A CADA AMIGO LE TOCAN "; CADA; " PECES"
50 LET PECES = PECES + 10
60 PRINT "AHORA HAY "; PECES
```

La línea 50 parece rara: quiere decir *coge lo que hay en PECES, súmale
10 y vuelve a guardarlo en PECES*. Una caja puede cambiar lo que guarda
tantas veces como quieras, y por eso se llama variable.

## Cajas para palabras

Una caja cuyo nombre termina en `$` guarda palabras en lugar de números.
Las palabras van entre comillas, y `+` las junta.

```basic
10 LET A$ = "BOLA"
20 LET B$ = " DE NIEVE"
30 PRINT A$ + B$
```

Hasta puedes quitar la palabra `LET`: `PECES = 12` quiere decir lo
mismo.

## Sigue probando

- Calcula cuántas patas tienen cuatro pingüinos, con una variable para
  cada cosa.
- Haz una frase juntando tres cajas de palabras.
- ¿Qué pasa si haces `PRINT` de una caja que nunca llenaste?

::: adult
Las variables con `$` son variables de texto. Números y textos no se
mezclan: `A = "NIEVE"` no da error en este BASIC, pero deja A en 0, así
que conviene enseñar al niño de qué clase es cada caja. Una caja que
nunca se llenó guarda 0, o un texto vacío.
:::
