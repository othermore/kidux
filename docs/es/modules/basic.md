# BASIC

*[English version](../../en/modules/basic.md)* · [Volver al manual](../user-guide.md#9-módulos-de-aprendizaje)

**BASIC** fue el lenguaje con el que aprendieron a programar millones de personas en los primeros ordenadores domésticos de los años 80, y sigue siendo una de las formas más didácticas, directas y divertidas de comprender cómo funciona un programa. Este módulo recrea esa experiencia clásica mediante un entorno dividido en dos partes: a la izquierda, un ordenador interactivo con su editor de código y pantalla de salida; a la derecha, un completo manual interactivo paso a paso.

| | |
|---|---|
| **Edad recomendada** | Niños de 8 a 14 años con buen nivel de lectura |
| **Módulos recomendados antes** | Scratch |
| **Conexión a internet** | No requerida (funciona de forma 100 % local y fuera de línea) |
| **Software utilizado** | [wwwBASIC](https://github.com/google/wwwbasic), desarrollado por Google bajo licencia Apache-2.0, integrado en un entorno didáctico desarrollado para Kidux |

## Qué es y cómo funciona

La mitad izquierda de la pantalla se compone de tres zonas principales:
- **El editor (arriba)**: el espacio donde el niño escribe y modifica las líneas de código de su programa BASIC.
- **La barra de control (centro)**: botones para ejecutar y detener el código. El botón **Ejecutar** (o el atajo de teclado Ctrl+Intro) pone el programa en marcha de inmediato. Si un programa entra en un bucle infinito o se desea interrumpir, se utiliza el botón **Parar** (o la tecla Escape).
- **La pantalla de salida (abajo)**: muestra el resultado del programa, incluyendo texto, gráficos, colores y efectos de sonido. Si el código contiene algún error de sintaxis, la pantalla indica con precisión en qué línea se ha producido y el editor la resalta visualmente para facilitar su corrección.

La mitad derecha contiene la guía interactiva, diseñada para leerse capítulo a capítulo. Mediante los botones **Atrás**, **Siguiente** o el índice general de **Capítulos**, el menor puede seguir las explicaciones, teclear el código de ejemplo en el editor y experimentar con él. Cada capítulo concluye con retos prácticos para profundizar y una sección especial titulada **Para el adulto**, que resume brevemente los conceptos pedagógicos que se trabajan en esa lección.

![BASIC](../../images/es/module-basic.png)

## Los treinta capítulos del curso

1. Hola, ordenador
2. PRINT: el ordenador escribe
3. LET: cajas con nombre (variables)
4. INPUT: hablar con el ordenador
5. GOTO: saltos de control en el programa
6. IF: el ordenador toma decisiones
7. FOR y NEXT: bucles para contar y repetir
8. GOSUB y RETURN: subrutinas reutilizables
9. READ y DATA: almacenar series de datos
10. REM: comentarios y notas explicativas
11. INT: redondeo y números enteros
12. RND: números aleatorios y azar
13. Diagramas de flujo: planificar antes de programar
14. Juegos interactivos paso a paso
15. Cómo guardar y organizar tus programas
16. ¿Qué ocurre dentro del ordenador?
17. Operaciones matemáticas avanzadas
18. Orden de evaluación y precedencia de operadores
19. CLS: limpiar y preparar la pantalla
20. Entrada de datos avanzada con INPUT
21. Bucles anidados con FOR y NEXT
22. Operadores lógicos: AND y OR
23. Menús interactivos con IF
24. Gestión avanzada de datos con READ, DATA y RESTORE
25. DIM: matrices y listas estructuradas
26. Algoritmos de ordenación
27. Manipulación de cadenas de texto
28. Códigos ASCII: CHR$ y ASC
29. Dibujo por coordenadas, paletas de color y sonido
30. Proyectos completos para guardar y compartir

## Ajustes disponibles para el adulto

| Ajuste | Descripción y finalidad |
|---|---|
| **Escríbemelo** | Muestra un botón bajo cada bloque de código de la guía interactiva que copia automáticamente el programa en el editor. Si se desactiva, el menor debe teclear el código manualmente carácter a carácter para afianzar la práctica. Por defecto viene activado. |

Este ajuste puede modificarse individualmente para cada hijo desde la sección **Ajustes** del módulo BASIC en la pestaña Módulos del panel de adulto.

## Guardar y recuperar los trabajos

El código presente en el editor se conserva automáticamente al salir del módulo y se recupera la próxima vez que se inicie, hasta que el niño pulse **Nuevo**.

Para archivar sus programas de manera permanente, el botón **Guardar** abre el selector de archivos del sistema en la carpeta del niño (dentro de **Descargas**) para guardarlo con extensión `.bas`. El botón **Abrir** permite volver a cargar cualquier programa guardado con anterioridad.
