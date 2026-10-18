# Step

*[English version](../../en/modules/step.md)* · [Volver al manual](../user-guide.md#9-módulos-de-aprendizaje)

**Step** es un simulador físico interactivo en dos dimensiones desarrollado por el proyecto KDE. Permite a los estudiantes diseñar mundos mecánicos virtuales colocando cuerpos, resortes, cuerdas y fuerzas sobre un plano para simular en tiempo real leyes del movimiento, colisiones y transformaciones de energía.

| | |
|---|---|
| **Edad recomendada** | Estudiantes de 10 a 16 años |
| **Módulos recomendados antes** | Simulaciones |
| **Conexión a internet** | No requerida (opera de manera totalmente autónoma sin conexión) |
| **Software utilizado** | [Step](https://apps.kde.org/step/), desarrollado por la comunidad KDE bajo licencia GPL-2, empaquetado en Debian |

## Qué es y cómo funciona

La interfaz de Step ofrece una completa paleta de componentes mecánicos: partículas puntuales, discos, cajas rígidas, resortes lineales, motores, generadores de fuerza, campos gravitatorios, anclajes fijos y sensores de medición.

El estudiante arrastra los cuerpos al escenario, define parámetros físicos reales (como masa, velocidad inicial, fricción o rigidez elástica) en el panel de propiedades y pulsa **Simular**. El motor numérico resuelve las ecuaciones diferenciales del movimiento en tiempo real, trazando trayectorias vectoriales y generando gráficas interactivas. El menú **Archivo > Ejemplos** incluye además multitud de experimentos clásicos listos para observar.

![Step](../../images/es/module-step.png)

## Guía didáctica interactiva

Kidux incorpora un panel lateral derecho con seis lecciones didácticas guiadas. Cinco de ellas contienen una **misión de laboratorio**: un archivo de proyecto con experimentos preconfigurados y preguntas para reflexionar, que se copia automáticamente en `Documentos/Misiones de Step` en la carpeta del estudiante:

1. **Una bola cae**: aceleración de la gravedad y representación gráfica de la caída libre. Misión: `caida.step`.
2. **El muelle**: osciladores armónicos con dos masas y efecto de la constante de rigidez. Misión: `muelle.step`.
3. **El péndulo**: conservación del periodo en pequeñas oscilaciones. Misión: `pendulo.step`.
4. **Lanzamiento parabólico**: trayectoria en dos dimensiones de proyectiles lanzados con velocidad horizontal. Misión: `lanzamiento.step`.
5. **Instrumentación y medidas**: uso de medidores, vectores de velocidad y gráficas en tiempo real.
6. **Choques y rebotes**: colisiones elásticas e inelásticas y conservación del momento lineal. Misión: `rebote.step`.

Para aprovechar al máximo el espacio de simulación, el botón **Plegar** en la cabecera del panel lateral colapsa la guía; el botón **Guía** en la barra inferior la restaura inmediatamente.

## Guardado de archivos y misiones

Los experimentos personalizados pueden guardarse en formato `.step` mediante **Archivo > Guardar** en la carpeta de documentos del estudiante. Las misiones didácticas se abren desde **Archivo > Abrir > Documentos > Misiones de Step**.

## Aspectos a tener en cuenta

- **Aislamiento de seguridad**: Las funciones de descarga en línea de experimentos de la comunidad y los accesos a ayuda externa en la web están desactivados para garantizar la concentración en el entorno local.
- **Hipervínculos**: Cualquier intento de abrir enlaces en el navegador web muestra un aviso informativo recordando que la navegación externa permanece bloqueada.
