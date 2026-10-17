# Bounce and crash

Balls bounce off walls and crash into each other. Step knows how.

![A ball bouncing off a box](images/step-bounce.svg)

@mission missions/bounce.step

1. Open the mission. A disk above a box held still by an anchor,
   gravity on, and a collision solver in the world list, which is what
   makes things bounce instead of passing through.
2. Press **Simulate**. The disk falls, hits the box and bounces.
3. Add a second **Disk** from the palette, give it a velocity towards
   the first, and simulate. They crash and fly apart.

> [cheer] Every bounce obeys one rule: what one ball loses in speed, the
> other gains. Nothing is lost, only passed on.

## Do it yourself

1. New world. **Box** from the palette, drawn wide and flat.
2. **Anchor** from the palette, then click the box: it stays where it
   is, whatever pulls it.
3. A **Disk** above it. **WeightForce**, and click on the canvas.
4. Simulate. A new world already has its collision solver.

::: try
Make a slope: a box turned by setting its *angle* to 0.3. Let a disk roll
down it. Then try **Gas** from the palette: a hundred particles bouncing
in a box, which is what air is.
:::
