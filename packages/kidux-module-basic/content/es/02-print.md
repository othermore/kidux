---
source_sha256 = "568286770c0011c230c589b3bed437af7d7f92e84fac2bd2fb98bb0f3db1769e"
---
# PRINT: el ordenador escribe

`PRINT` escribe en la pantalla lo que haya entre las comillas, tal cual.

```basic
10 PRINT "EL PINGÜINO VIVE EN EL HIELO"
20 PRINT "COME PECES"
30 PRINT
40 PRINT "Y LE ENCANTA LA NIEVE"
```

Un `PRINT` sin nada detrás escribe una línea vacía, como la 30.

## Cuando BASIC no entiende

Este programa tiene un error a propósito, en la línea 20: `PIRNT` en lugar
de `PRINT`. Escríbelo tal cual y pulsa **Ejecutar**.

```basic mistake
10 PRINT "EL PINGÜINO VIVE EN EL HIELO"
20 PIRNT "COME PECES"
30 PRINT "Y LE ENCANTA LA NIEVE"
```

No se escribe nada, ni siquiera la línea 10. BASIC lee el programa entero
antes de ejecutar nada, y se para en la línea que no entiende. Las
palabras de debajo de la pantalla dicen qué línea es, y el editor la
marca. Escribe bien `PRINT` en la línea 20 y pulsa **Ejecutar** otra vez.

> [oops] Si se te olvida la comilla del principio de las palabras, pasa
> lo mismo. Cuando BASIC no entienda una línea, mira primero cómo está
> escrita y sus comillas.

## Comas y puntos y comas

Detrás de un `PRINT` puedes poner varias cosas, separadas por `;` o
por `,`. El punto y coma escribe lo siguiente justo detrás; la coma
salta antes un poco más allá en la línea.

```basic
10 PRINT "BOLA"; "NIEVE"
20 PRINT "BOLA", "NIEVE"
30 PRINT "UNO "; "DOS "; "TRES"
```

El espacio de dentro de `"UNO "` es lo que separa las palabras.

## Dibujar con letras

La pantalla está hecha de filas de letras, así que las letras pueden
hacer dibujos.

```basic
10 PRINT "  *****"
20 PRINT " *     *"
30 PRINT "*  O O  *"
40 PRINT "*   ^   *"
50 PRINT " * --- *"
60 PRINT "  *****"
```

> [cheer] Cuando empieces un programa nuevo, pulsa antes **Nuevo**, para
> que las líneas viejas no se mezclen con las nuevas.

## Sigue probando

- Dibuja con letras una casa, un pez o un cohete.
- Escribe tu nombre en letras grandes hechas de `#`.
- Pon una `,` y luego un `;` entre dos palabras, y mira la diferencia.

::: adult
La coma salta a la siguiente zona de escritura, una columna de catorce
caracteres; el punto y coma no añade nada. Los números escritos con `;`
no llevan espacios alrededor en este BASIC, así que la guía pone un
`" "` entre ellos cuando tienen que quedar separados.
:::
