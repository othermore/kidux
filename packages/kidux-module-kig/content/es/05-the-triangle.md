---
source_sha256 = "f53568357ae2debded090a9254c46174519711f9936def10db3b6c4db9b56b79"
---
# Un triángulo con tres lados iguales

Esta es la construcción más antigua de la geometría, de hace dos mil
años. Con dos circunferencias haces un triángulo cuyos tres lados miden
exactamente lo mismo, y siguen midiendo lo mismo cuando lo arrastras.

![Dos circunferencias y el triángulo equilátero](images/kig-triangle.svg)

@mission missions/triangulo.kig

1. Abre la misión. Los puntos A y B, y la circunferencia con centro A
   que pasa por B.
2. ![Circunferencia a partir de un centro y un punto](images/tools/circlebcp.svg)
   Pulsa **Circunferencia a partir de un centro y un punto**, haz clic
   en B y luego en A: la circunferencia con centro B que pasa por A.
3. ![Intersección](images/tools/curvelineintersection.svg) Pulsa
   **Intersección**, haz clic en una circunferencia y luego en la otra.
   Kig marca los dos cruces. Llama C al de arriba: clic derecho sobre
   él, **Establecer el nombre**.
4. ![Segmento](images/tools/segment.svg) Pulsa **Segmento** y haz clic
   en A y luego en B. Otra vez de B a C, y de C a A.
5. Arrastra A o B. El triángulo crece y se encoge, pero sus tres lados
   siguen siendo iguales.

> [think] ¿Por qué? AC es un radio de la primera circunferencia, así que
> mide lo mismo que AB. BC es un radio de la segunda, así que también
> mide lo mismo que AB. Tres lados iguales.

::: try
Oculta las dos circunferencias: clic derecho en cada una, **Ocultar**.
Luego busca el punto medio de cada lado y une los puntos medios: cuatro
triángulos pequeños, todos iguales. Arrastra A.
:::
