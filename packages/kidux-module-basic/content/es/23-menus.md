---
source_sha256 = "3a0c33f29d68aedad13397e1944c57ca2ce61b0f0518adc1404cec217ebabe4d"
---
# IF, más: menús

Un programa que hace varias cosas puede ofrecerlas en un **menú**: una
lista con un número para cada una, y una pregunta.

`ON … GOTO` salta a la primera línea de su lista cuando la caja tiene un
1, a la segunda cuando tiene un 2, y así. Cuando el número no está en la
lista, sigue en la línea siguiente.

```basic keys=2,Enter
10 PRINT "LA CAFETERIA DEL PINGÜINO"
20 PRINT "1  SOPA DE PESCADO"
30 PRINT "2  HELADO"
40 PRINT "3  CHOCOLATE CALIENTE"
50 INPUT "¿QUE TE APETECE? "; C
60 ON C GOTO 100, 200, 300
70 PRINT "ESO NO ESTA EN EL MENU."
80 END
100 PRINT "UNA SOPA DE PESCADO, BIEN CALIENTE."
110 END
200 PRINT "UN HELADO, BIEN FRIO."
210 END
300 PRINT "UN CHOCOLATE CALIENTE, CON UNA NUBE."
```

`END` para el programa ahí, para que cada pedido no siga con el
siguiente.

## ELSE

`ELSE`, *si no*, dice qué hacer cuando el `IF` no se cumple. Ya lo viste
en los juegos del capítulo 14:

```basic keys=7,Enter
10 INPUT "¿QUE EDAD TIENES? "; E
20 IF E < 8 THEN PRINT "EL TOBOGAN PEQUEÑO" ELSE PRINT "EL TOBOGAN GRANDE"
```

## Un menú que vuelve

```basic keys=1,Enter,2,Enter,3,Enter
10 PRINT
20 PRINT "1 SALUDAR   2 CONTAR UN CHISTE   3 SALIR"
30 INPUT "ELIGE: "; C
40 ON C GOSUB 100, 200
50 IF C <> 3 THEN 10
60 PRINT "¡ADIOS!"
70 END
100 PRINT "¡HOLA, HOLA!"
110 RETURN
200 PRINT "¿QUE LE DICE UN PINGÜINO A OTRO? ¡QUE FRIO HACE!"
210 RETURN
```

`ON … GOSUB` es lo mismo con `GOSUB`: cada opción es una subrutina que
vuelve al menú.

> [cheer] Casi todos los programas que usas tienen un menú. Ahora los
> tuyos también.

## Sigue probando

- Añade una cuarta cosa a la cafetería.
- Dale al menú que vuelve una cuarta opción: una adivinanza.

::: adult
Un menú es la primera estructura de programa que un niño puede diseñar en
papel antes de escribirla: la lista de opciones, y un trozo de programa
para cada una.
:::
