---
source_sha256 = "00ed99536ac4a14140af9d7f1a9a9fd7f424efcf92e5e4886a324e50b4fdde75"
---
# Juegos para hacer

Ya sabes lo bastante para hacer juegos. Cada uno usa solo lo que
enseñaron los capítulos anteriores. Escríbelos, juega, y luego cámbialos.

## El entrenador de tablas

```basic keys=8,Enter,24,Enter,32,Enter,40,Enter
10 INPUT "¿QUE TABLA? "; T
20 FOR N = 3 TO 5
30 PRINT "¿"; T; " POR "; N; "? ";
40 INPUT "", A
50 IF A = T * N THEN PRINT "¡BIEN!" ELSE PRINT "NO, SON "; T * N
60 NEXT N
```

## El escondite

El pingüino se esconde detrás de una de diez rocas. ¡Encuéntralo!

![Diez rocas en la nieve](garden.svg)

```basic keys=3,Enter,5,Enter,1,Enter,2,Enter,4,Enter,6,Enter,7,Enter,8,Enter,9,Enter,10,Enter
10 RANDOMIZE
20 LET R = INT(RND * 10) + 1
30 LET INTENTOS = 0
40 INPUT "¿QUE ROCA, DEL 1 AL 10? "; N
50 LET INTENTOS = INTENTOS + 1
60 IF N = R THEN 90
70 PRINT "AQUI NO ESTA..."
80 GOTO 40
90 PRINT "¡ENCONTRADO! EN "; INTENTOS; " INTENTOS"
```

## Adivina mi número

```basic keys=50,Enter,25,Enter,75,Enter,12,Enter,37,Enter,62,Enter,87,Enter,6,Enter,18,Enter,31,Enter,43,Enter,56,Enter,68,Enter,81,Enter,93,Enter,1,Enter,2,Enter,3,Enter,4,Enter,5,Enter
10 RANDOMIZE
20 LET R = INT(RND * 100) + 1
30 LET INTENTOS = 0
40 INPUT "MI NUMERO ES DEL 1 AL 100. ADIVINA: "; G
50 LET INTENTOS = INTENTOS + 1
60 IF G < R THEN PRINT "¡MAS GRANDE!"
70 IF G > R THEN PRINT "¡MAS PEQUEÑO!"
80 IF G <> R AND INTENTOS < 20 THEN 40
90 IF G = R THEN PRINT "¡SI! EN "; INTENTOS; " INTENTOS" ELSE PRINT "ERA EL "; R
```

> [think] ¿Cuál es el primer intento más listo? Piensa en mitades.

## El adivino

El ordenador adivina el número que piensas.

```basic keys=Enter,Enter,Enter,Enter,23,Enter
10 PRINT "PIENSA UN NUMERO. ¡NO ME LO DIGAS!"
20 INPUT "PULSA INTRO CUANDO ESTES LISTO", K$
30 PRINT "MULTIPLICALO POR 2"
40 INPUT "PULSA INTRO", K$
50 PRINT "SUMALE 10"
60 INPUT "PULSA INTRO", K$
70 PRINT "DIVIDELO ENTRE 2"
80 INPUT "PULSA INTRO", K$
90 INPUT "DIME LO QUE TIENES AHORA: "; X
100 PRINT "HABIAS PENSADO EL "; X - 5
```

> [cheer] ¿Cómo funciona? Apunta lo que le pasa al número, paso a paso,
> y verás el truco.

## Sigue probando

- Dale al pingüino del escondite solo cinco intentos.
- En el entrenador, pregunta la tabla entera, del 1 al 10, y cuenta los
  aciertos.
- Inventa un juego tuyo: un concurso sobre tu animal favorito.

::: adult
Estos juegos son los primeros capítulos puestos juntos. El adivino es
bueno para explicarlo juntos: multiplicar por dos, sumar 10 y dividir
entre dos deja el número más 5, fuera el que fuera.
:::
