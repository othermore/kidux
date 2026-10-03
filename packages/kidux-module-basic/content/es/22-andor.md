---
source_sha256 = "6c4a3c91ef0979c35c3fe157c6db47c5a2b694849866ddfbbb294dc4d2ba5390"
---
# AND y OR

A veces una pregunta no basta. ¿Hace frío **y** nieva? Entonces es un día
para hacer un muñeco de nieve. ¿Llueve **o** nieva? Entonces necesitas el
abrigo.

- `AND`, *y*, es sí solo cuando **los dos** lados son sí.
- `OR`, *o*, es sí cuando **un lado o el otro**, o los dos, son sí.

```basic keys=SI,Enter,NO,Enter
10 INPUT "¿HACE FRIO? "; F$
20 INPUT "¿ESTA NEVANDO? "; N$
30 IF F$ = "SI" AND N$ = "SI" THEN PRINT "¡VAMOS A HACER UN MUÑECO DE NIEVE!"
40 IF F$ = "SI" OR N$ = "SI" THEN PRINT "PONTE EL ABRIGO."
50 IF F$ = "NO" AND N$ = "NO" THEN PRINT "UN DIA PARA EL PARQUE."
```

## Atrapar una respuesta equivocada

Cuando un programa pide un número del 1 al 9, un programa cuidadoso dice
que no a cualquier otro y vuelve a preguntar:

```basic keys=0,Enter,15,Enter,4,Enter
10 INPUT "¿UN NUMERO DEL 1 AL 9? "; N
20 IF N < 1 OR N > 9 THEN PRINT "DEL 1 AL 9, POR FAVOR": GOTO 10
30 PRINT "GRACIAS. EL "; N; " ENTONCES."
```

## La contraseña del iglú

```basic keys=PEZ,Enter,HIELO,Enter,BOLADENIEVE,Enter
10 LET T = 0
20 INPUT "¿CONTRASEÑA? "; C$
30 LET T = T + 1
40 IF C$ <> "BOLADENIEVE" AND T < 3 THEN PRINT "NO. PRUEBA OTRA VEZ.": GOTO 20
50 IF C$ = "BOLADENIEVE" THEN PRINT "¡BIENVENIDO AL IGLU!" ELSE PRINT "LA PUERTA SIGUE CERRADA."
```

Tienes tres intentos. La línea 40 vuelve a preguntar solo mientras la
contraseña está mal **y** quedan intentos.

> [think] `NOT` convierte el sí en no y el no en sí: `IF NOT (N = 5)`
> es lo mismo que `IF N <> 5`.

## Sigue probando

- Dale al iglú dos contraseñas que lo abran.
- Pregunta un día de la semana y una hora, y di si la tienda está
  abierta.

::: adult
Las condiciones unidas con `AND` y `OR` son donde la lógica entra en la
programación. Decir la condición en voz alta, *está mal y quedan
intentos*, es la forma más segura de acertar. En este BASIC una condición
verdadera vale -1 y una falsa 0, algo que la guía nunca necesita enseñar.
:::
