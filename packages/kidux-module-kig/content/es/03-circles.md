---
source_sha256 = "245efd3524d2cf8f92b0e566344768f0e931f9191f0ae3734d16088d003bc0db"
---
# Circunferencias

Una circunferencia son todos los puntos que están a la misma distancia
de su centro. En Kig dibujas una con su centro y un punto por el que
pasa.

![Dos circunferencias que se cruzan](images/kig-circles.svg)

@mission missions/dos-circunferencias.kig

1. Abre la misión. Hay una circunferencia con centro A que pasa por B.
2. ![Circunferencia a partir de un centro y un punto](images/tools/circlebcp.svg)
   Pulsa **Circunferencia a partir de un centro y un punto**, haz clic
   en B y luego en A. Una segunda circunferencia, con centro B, que pasa
   por A.
3. ![Intersección](images/tools/curvelineintersection.svg) Las
   circunferencias se cruzan en dos sitios. Pulsa **Intersección** y haz
   clic en una circunferencia y luego en la otra. Kig marca los dos
   puntos de cruce.
4. Arrastra B lejos de A. Las circunferencias crecen a la vez y los
   puntos de cruce se mueven con ellas.

> [cheer] Las dos circunferencias son siempre del mismo tamaño: el radio
> de cada una es la distancia de A a B. Al arrastrar cambias esa
> distancia para las dos.

## Un punto que vive en una circunferencia

1. ![Circunferencia a partir de un centro y un punto](images/tools/circlebcp.svg)
   Pulsa **Circunferencia a partir de un centro y un punto** y haz clic
   en dos sitios vacíos: una circunferencia, con su centro y un punto
   en ella.
2. ![Punto](images/tools/point.svg) Pulsa **Punto** y haz clic justo
   sobre la línea de la circunferencia.
3. Arrastra ese punto. Se desliza por la circunferencia y nunca se sale.

::: try
Pulsa **Segmento**, haz clic en el centro de la circunferencia y luego
en el punto que vive en ella. Arrastra el punto alrededor. El segmento
es siempre un *radio*: su longitud nunca cambia.
:::
