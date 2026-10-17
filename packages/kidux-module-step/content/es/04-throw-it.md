---
source_sha256 = "57d6dfe911944053d96a6aa42ffdc33a31ef49c0bf8a7f779601e9a4053d7e15"
---
# Lánzala

Lanza una bola y vuela en una curva: sube, pasa y baja. Step puede
dibujarte esa curva.

![Una bola y el arco que recorre](images/step-throw.svg)

@mission missions/lanzamiento.step

1. Abre la misión. Una bola a la izquierda, con una velocidad ya puesta,
   y un **Trazador** en ella que dibuja por dónde va.
2. Pulsa **Simular**. La bola vuela en un arco y el trazador deja su
   camino detrás.
3. Para y pulsa **Deshacer** hasta que la bola vuelva. Haz clic en ella y
   pon la velocidad en (6, 4). Simula. Luego (4, 6). ¿Qué lanzamiento
   llega más lejos? ¿Cuál sube más?

> [think] El primer número es la velocidad de lado, el segundo la de
> subida. La de subida decide la altura; la de lado, con el tiempo que
> está en el aire, decide la distancia.

## Hazlo tú

1. Mundo nuevo, **FuerzaPeso** encendida, una **Partícula**.
2. En **Propiedades**, pon su velocidad en (5, 5).
3. **Trazador** en la paleta, y luego clic en la bola.
4. Simula.

::: try
Busca la velocidad que haga caer la bola justo en x = 10. Luego intenta
hacerlo con una velocidad total más pequeña.
:::
