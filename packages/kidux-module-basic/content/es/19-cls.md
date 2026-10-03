---
source_sha256 = "d52cd8c8ad5c2955e45a5762a2d5aa2f093d4753ad2557e7844f7ea79dc95555"
---
# CLS: una pantalla limpia

`CLS` borra la pantalla y vuelve a escribir desde arriba. No toca tu
programa ni sus cajas: solo borra lo que se ve.

```basic
10 PRINT "ESTO VA A DESAPARECER"
20 PRINT "Y ESTO TAMBIEN"
30 CLS
40 PRINT "UNA PANTALLA LIMPIA"
```

Un concurso queda mejor cuando cada pregunta tiene la pantalla para ella
sola:

```basic keys=2,Enter,PECES,Enter
10 CLS
20 PRINT "PREGUNTA 1"
30 INPUT "¿CUANTAS PATAS TIENE UN PINGÜINO? "; A
40 IF A = 2 THEN PRINT "¡BIEN!" ELSE PRINT "TIENE DOS"
50 CLS
60 PRINT "PREGUNTA 2"
70 INPUT "¿QUE COME UN PINGÜINO? "; C$
80 IF C$ = "PECES" THEN PRINT "¡BIEN!" ELSE PRINT "SOBRE TODO PECES"
```

> [think] La respuesta a la pregunta 1 desaparece antes de que puedas
> leerla. ¿Puedes hacer que el programa espere? El capítulo 21 enseña
> cómo, y el 27 enseña a esperar una tecla.

## Tres maneras de empezar limpio

- `CLS` borra la **pantalla**. El programa sigue.
- Cada vez que pulsas **Ejecutar**, las cajas empiezan vacías, como
  enseñó el capítulo 16.
- **Nuevo** borra el **editor**, y el programa que había se pierde. Antes
  pregunta, para que no se pierda nada sin querer.

## Sigue probando

- Añade una tercera pregunta al concurso, en su propia pantalla limpia.
- Cuenta los aciertos en una caja, y enseña la puntuación al final en una
  pantalla limpia.

::: adult
`CLS` es la primera orden de la mayoría de los programas que usan la
pantalla como una página y no como un rollo de texto. Cada ejecución
empieza aquí con las variables vacías, así que un programa nunca necesita
vaciarlas él mismo.
:::
