# Throw it

Throw a ball and it flies in a curve: up, over and down. Step can draw
that curve for you.

![A ball and the arc it flies](images/step-throw.svg)

@mission missions/throw.step

1. Open the mission. A ball on the left, with a velocity already set,
   and a **Tracer** on it that draws where it goes.
2. Press **Simulate**. The ball flies in an arc and the tracer leaves
   its path behind.
3. Stop and press **Undo** until the ball is back. Click it and set the
   velocity to (6, 4). Simulate. Then (4, 6). Which throw goes further?
   Which goes higher?

> [think] The first number is the sideways speed, the second the upward
> speed. Up decides how high; sideways, with the time it is in the air,
> decides how far.

## Do it yourself

1. New world, **WeightForce** on, a **Particle**.
2. In **Properties**, set its velocity to (5, 5).
3. **Tracer** in the palette, then click the ball.
4. Simulate.

::: try
Find the velocity that lands the ball exactly at x = 10. Then try to do
it with a smaller total speed.
:::
