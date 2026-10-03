---
source_sha256 = "0dc3a785278d0a832edbaa6b674dc93690b141abd5f360347c7e91618b586011"
---
# Diagramas de flujo: dibújalo antes

Antes de escribir un programa, ayuda dibujarlo. Un **diagrama de flujo**
es un dibujo de un programa: cajas para lo que hay que hacer, y flechas
para el orden.

![Las formas de un diagrama de flujo](flowchart.svg)

- Una caja redondeada es el principio o el final.
- Una caja inclinada es algo que se pregunta o se enseña.
- Una caja normal es algo que se calcula, como una cuenta.
- Un rombo es una pregunta con dos salidas, sí y no: un `IF`.

> [point] Dibújalo antes en papel, con lápiz. Las flechas que vuelven
> hacia arriba son bucles.

## Del dibujo al programa

Un diagrama para *pide un número del 1 al 10, y vuelve a pedirlo hasta
que esté bien*: principio, pregunta, el rombo *¿está entre 1 y 10?*, el
no vuelve arriba, el sí sigue, lo enseña, final. En BASIC:

```basic keys=12,Enter,7,Enter
10 INPUT "¿UN NUMERO DEL 1 AL 10? "; N
20 IF N < 1 OR N > 10 THEN 10
30 PRINT "GRACIAS. EL DOBLE DE "; N; " ES "; N * 2
```

`OR` quiere decir *una cosa o la otra*: si el número es demasiado
pequeño o demasiado grande, vuelve a preguntar.

## Sigue probando

- Dibuja el diagrama del juego de adivinar del capítulo siguiente antes
  de leer su programa.
- Dibuja un diagrama de tu mañana, desde que te despiertas hasta que
  sales de casa.

::: adult
Los diagramas de flujo dejan ver la forma de un programa antes que sus
detalles. Son especialmente útiles cuando un niño se atasca: dibujar lo
que debería hacer el programa suele enseñar dónde se va por otro camino.
:::
