---
source_sha256 = "24c9c5cc9d61d85801d4ac1375e89da62e397522c1f920f0a490c73b370ac2d4"
---
# CHR$ y ASC: los números de las letras

Dentro del ordenador cada letra es un número. `ASC` te dice el número de
una letra, y `CHR$` convierte un número otra vez en su letra:

```basic
10 PRINT ASC("A"), ASC("B"), ASC("Z")
20 PRINT CHR$(72); CHR$(79); CHR$(76); CHR$(65)
```

La `A` es el 65, la `B` el 66, y así hasta la `Z`, el 90. Un espacio es
el 32.

## El abecedario

```basic
10 FOR C = 65 TO 90
20 PRINT CHR$(C); " ";
30 NEXT C
40 PRINT
```

Es el abecedario de los ordenadores, que viene del inglés: no tiene la Ñ.

## Un código secreto

Para escribir en clave, cambia cada letra por la siguiente: la A se
convierte en B, la B en C, y la Z vuelve a la A. Tu amigo cambia cada
letra por la anterior para leer el mensaje.

![Cada letra se convierte en la siguiente](code.svg)

```basic keys=NOS,Space,VEMOS,Space,EN,Space,EL,Space,IGLU,Enter
10 INPUT "¿TU MENSAJE? "; M$
20 LET S$ = ""
30 FOR I = 1 TO LEN(M$)
40 LET C = ASC(MID$(M$, I, 1))
50 IF C >= 65 AND C <= 90 THEN LET C = C + 1
60 IF C = 91 THEN LET C = 65
70 LET S$ = S$ + CHR$(C)
80 NEXT I
90 PRINT "EN CLAVE: "; S$
```

La línea 50 solo mueve las mayúsculas, así que los espacios siguen
siendo espacios. La línea 60 manda la letra de después de la Z otra vez a
la A.

> [think] ¿Cómo leerías un mensaje en clave? Cambia la línea 50 para
> restar 1, y la línea 60 para convertir el 64 en un 90.

## Sigue probando

- Mueve cada letra tres sitios en vez de uno.
- Escribe el programa que lee la clave, y pruébalo con un amigo.

::: adult
Los números son los códigos ASCII, los mismos en casi todos los
ordenadores. Una clave que mueve cada letra un número fijo de sitios es
la cifra de César, por Julio César, que según se cuenta la usaba.
:::
