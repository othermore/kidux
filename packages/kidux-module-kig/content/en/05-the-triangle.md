# A triangle with three equal sides

This is the oldest construction in geometry, two thousand years old.
With two circles you make a triangle whose three sides are exactly the
same length, and it stays that way when you drag it.

![Two circles and the equilateral triangle](images/kig-triangle.svg)

@mission missions/triangle.kig

1. Open the mission. Points A and B, and the circle with centre A
   through B.
2. ![Circle by centre and point](images/tools/circlebcp.svg) Press
   **Circle by centre and point**, click B, then A: the circle with
   centre B through A.
3. ![Intersect](images/tools/curvelineintersection.svg) Press
   **Intersect**, click one circle, then the other. Kig marks the two
   crossings. Call the upper one C: right-click it, **Set name**.
4. ![Segment](images/tools/segment.svg) Press **Segment** and click A,
   then B. Again from B to C, and from C to A.
5. Drag A or B. The triangle grows and shrinks, but its three sides
   stay equal.

> [think] Why? AC is a radius of the first circle, so it is as long as
> AB. BC is a radius of the second, so it is as long as AB too. Three
> equal sides.

::: try
Hide the two circles: right-click each, **Hide**. Then find the midpoint
of each side and join the midpoints: four small triangles, all equal.
Drag A.
:::
