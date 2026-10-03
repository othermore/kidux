---
source_sha256 = "01c4373aecec49322b8ff1db2a73b8325218cc07300db0d71c15c7f853467e0b"
---
# Dibujo, color y sonido

`SCREEN 12` convierte la pantalla en una cuadrícula de puntos, 640 de
ancho y 480 de alto. Un punto se nombra con dos números entre paréntesis:
lo lejos que está **hacia la derecha**, y luego lo lejos que está **hacia
abajo**. `(0, 0)` es la esquina de arriba a la izquierda, y `(320, 240)`
el centro.

![La pantalla como una cuadrícula de puntos](screen.svg)

## Colores

Cada color tiene un número del 0 al 15:

```basic
10 SCREEN 12
20 FOR C = 0 TO 15
30 LINE (C * 40, 200)-(C * 40 + 38, 280), C, BF
40 NEXT C
```

El 0 es negro, el 1 azul, el 2 verde, el 3 turquesa, el 4 rojo, el 5
morado, el 6 marrón, el 7 gris, el 8 gris oscuro, y luego los claros: el
9 azul, el 10 verde, el 11 turquesa, el 12 rojo, el 13 rosa, el 14
amarillo y el 15 blanco.

## Puntos y líneas

- `PSET (X, Y), C` pinta un punto del color C.
- `LINE (X1, Y1)-(X2, Y2), C` traza una línea de un punto a otro.
- Con `, B` al final, `LINE` dibuja una caja con esas dos esquinas; con
  `, BF`, una caja rellena.
- `CIRCLE (X, Y), R, C` dibuja un círculo alrededor de (X, Y), de R
  puntos desde el centro hasta el borde.
- `PAINT (X, Y), C` rellena con el color C desde ese punto hasta que
  encuentra una línea del color C, como pintura vertida en una forma.

Un cielo de noche con trescientas estrellas, cada una en un sitio elegido
por `RND`:

```basic
10 SCREEN 12
20 RANDOMIZE
30 FOR N = 1 TO 300
40 PSET (INT(RND * 640), INT(RND * 480)), 15
50 NEXT N
60 CIRCLE (520, 90), 50, 14
70 PAINT (520, 90), 14
```

## Una casa

```basic
10 SCREEN 12
20 LINE (0, 400)-(639, 479), 2, BF
30 LINE (200, 220)-(440, 400), 4, BF
40 LINE (200, 220)-(320, 120), 6
50 LINE (320, 120)-(440, 220), 6
60 LINE (200, 220)-(440, 220), 6
70 PAINT (320, 180), 6
80 LINE (290, 310)-(350, 400), 6, BF
90 LINE (230, 260)-(270, 300), 11, BF
100 LINE (370, 260)-(410, 300), 11, BF
110 CIRCLE (560, 70), 40, 14
120 PAINT (560, 70), 14
```

El tejado son tres líneas que cierran un triángulo, y `PAINT` lo rellena.

> [point] Dibuja antes tu dibujo en papel cuadriculado, y apunta los
> números de sus esquinas. Así el programa es fácil.

## Un muñeco de nieve

```basic
10 SCREEN 12
20 LINE (0, 0)-(639, 479), 1, BF
30 LINE (0, 420)-(639, 479), 15, BF
40 CIRCLE (320, 340), 90, 15
50 PAINT (320, 340), 15
60 CIRCLE (320, 190), 65, 15
70 PAINT (320, 190), 15
80 CIRCLE (295, 170), 8, 0
90 PAINT (295, 170), 0
100 CIRCLE (345, 170), 8, 0
110 PAINT (345, 170), 0
120 LINE (320, 192)-(365, 200), 12, BF
130 LINE (250, 120)-(390, 132), 0, BF
140 LINE (275, 60)-(365, 120), 0, BF
150 FOR B = 1 TO 3
160 CIRCLE (320, 270 + B * 40), 7, 0
170 PAINT (320, 270 + B * 40), 0
180 NEXT B
```

## Una bandera

La bandera de la Isla de los Pingüinos: una línea de esquina a esquina la
parte en dos, y `PAINT` rellena cada mitad. Su segundo número dice dónde
pararse: en las líneas blancas.

```basic
10 SCREEN 12
20 LINE (100, 40)-(110, 460), 7, BF
30 LINE (110, 60)-(530, 300), 15, B
40 LINE (110, 300)-(530, 60), 15
50 PAINT (200, 120), 12, 15
60 PAINT (440, 240), 11, 15
70 CIRCLE (320, 180), 30, 14
80 PAINT (320, 170), 14
```

## Sonido

`SOUND F, D` toca una nota. F es lo aguda que es: 262 es el *do*, y
cuanto más grande el número, más aguda la nota. D es lo que dura, en
dieciochoavos de segundo: 18 es un segundo.

```basic
10 FOR N = 1 TO 14
20 READ F, D
30 SOUND F, D
40 NEXT N
50 DATA 262, 6, 262, 6, 392, 6, 392, 6, 440, 6, 440, 6, 392, 12
60 DATA 349, 6, 349, 6, 330, 6, 330, 6, 294, 6, 294, 6, 262, 12
```

Las notas desde el *do* hacia arriba: *do* 262, *re* 294, *mi* 330, *fa*
349, *sol* 392, *la* 440, *si* 494, y 523 para el *do* siguiente.

## Una pelota que rebota

Para mover algo, dibújalo, espera un momento, dibújalo otra vez en negro
para borrarlo, y dibújalo un poco más allá. Cuando la pelota llega a un
borde, da la vuelta, con un sonido.

```basic
10 SCREEN 12
20 LET X = 40: LET Y = 60: LET DX = 6: LET DY = 4
30 FOR T = 1 TO 600
40 CIRCLE (X, Y), 12, 0
50 LET X = X + DX: LET Y = Y + DY
60 IF X < 12 OR X > 627 THEN LET DX = -DX: SOUND 880, 1
70 IF Y < 12 OR Y > 467 THEN LET DY = -DY: SOUND 660, 1
80 CIRCLE (X, Y), 12, 14
90 SLEEP 20
100 NEXT T
```

> [cheer] La pelota no es más que un círculo dibujado y borrado, cincuenta
> veces por segundo. Eso es también todo lo que hay en unos dibujos
> animados.

## Sigue probando

- Ponle a la casa una chimenea y un pomo en la puerta.
- Ponle brazos al muñeco de nieve, dos líneas del color 6.
- Dibuja la bandera de tu propia isla.
- Escribe una melodía tuya con `SOUND`, o el principio de una que
  conozcas.

::: adult
El dibujo se queda en la pantalla cuando el programa termina, y *Parar*
también lo deja. `PAINT` rellena hasta las líneas del color que se le da,
o del segundo color cuando lo hay; una forma con un hueco en el borde deja
que la pintura se salga por toda la pantalla, algo que los niños
descubren enseguida.
:::
