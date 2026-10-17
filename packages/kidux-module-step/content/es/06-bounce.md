---
source_sha256 = "a8566e4999275d45c7a9c46bc889859783ef4e58990057c807853b1b28ad918a"
---
# Rebota y choca

Las bolas rebotan en las paredes y chocan unas con otras. Step sabe
cómo.

![Una bola que rebota en una caja](images/step-bounce.svg)

@mission missions/rebote.step

1. Abre la misión. Un disco sobre una caja sujeta por un ancla,
   gravedad encendida, y en la lista del mundo un resolutor de
   colisiones, que es lo que hace que las cosas reboten en vez de
   atravesarse.
2. Pulsa **Simular**. El disco cae, golpea la caja y rebota.
3. Añade un segundo **Disco** de la paleta, dale una velocidad hacia el
   primero y simula. Chocan y salen despedidos.

> [cheer] Cada rebote obedece una regla: lo que una bola pierde de
> velocidad, la otra lo gana. Nada se pierde, solo se pasa.

## Hazlo tú

1. Mundo nuevo. **Caja** de la paleta, dibujada ancha y plana.
2. **Ancla** de la paleta, y luego clic en la caja: se queda donde está,
   tire lo que tire de ella.
3. Un **Disco** encima. **FuerzaPeso**, y clic en el lienzo.
4. Simula. Un mundo nuevo ya trae su resolutor de colisiones.

::: try
Haz una rampa: una caja girada poniendo su *ángulo* en 0,3. Deja que un
disco ruede por ella. Luego prueba **Gas** de la paleta: cien partículas
rebotando en una caja, que es lo que es el aire.
:::
