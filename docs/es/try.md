# Probar Kidux en un emulador

*[English version](../en/try.md)*

**Kidux se puede probar en el ordenador de todos los días, antes de
dedicarle un ordenador propio.** Un emulador, un programa que hace
funcionar un ordenador entero dentro de una ventana, arranca Kidux desde
una imagen preparada para él, con una familia ya creada: un niño y los
módulos de aprendizaje activados para él. No se instala nada en tu
ordenador aparte del emulador, y al cerrar la ventana todo queda como
estaba.

Es Kidux entero, no una demostración: el mismo sistema que el instalador
pone en un ordenador, con su pantalla de entrada, la pantalla del niño,
los límites de tiempo, la pantalla de bloqueo y el panel de adulto. Se
actualiza solo desde el archivo de Kidux como cualquier ordenador con
Kidux.

| | |
|---|---|
| **El niño** | **Leo**, contraseña `leo`. |
| **La contraseña de adulto**, que abre el panel de adulto | `kidux` |
| **El administrador**, para la consola de texto, que una prueba no necesita | `ana`, contraseña `kidux` |
| **Módulos de aprendizaje instalados y activados para Leo** | BASIC, Tux Typing, Scratch, GCompris, Simulaciones y Kig. El panel de adulto instala más. |
| **Tiempo** | Leo no tiene límite de tiempo, para que puedas probar con calma. El panel de adulto pone uno. |
| **Idiomas** | Una imagen en español y otra en inglés. |
| **Lo que necesita** | 4 GB de memoria libres para el emulador, y unos 10 GB de disco. |

Una vez arrancado, Kidux muestra su pantalla de entrada con Leo y, tras
la contraseña de Leo, la pantalla de Leo con sus módulos:

![La pantalla de entrada de la imagen de prueba, con Leo](../images/es/trial-sign-in.png)

![La pantalla de Leo, con seis módulos de aprendizaje](../images/es/trial-leo.png)

## Qué imagen, para qué emulador

| Tu ordenador | El emulador | La imagen |
|---|---|---|
| **Windows** | [VirtualBox](https://www.virtualbox.org/), gratuito | [kidux-trial-es.ova](https://iso.kidux.org/kidux-trial-es.ova) |
| **Mac con procesador Intel** | VirtualBox, o [UTM](https://mac.getutm.app/) | el `.ova` para VirtualBox, el `.qcow2` para UTM |
| **Mac con procesador de Apple** (M1 y posteriores) | [UTM](https://mac.getutm.app/), gratuito | [kidux-trial-es.qcow2](https://iso.kidux.org/kidux-trial-es.qcow2) |
| **Linux** | QEMU, o VirtualBox | el `.qcow2` para QEMU, el `.ova` para VirtualBox |

Las imágenes en inglés son `kidux-trial-en.ova` y `kidux-trial-en.qcow2`,
en la misma dirección. Cada archivo ocupa unos 1,5 GB. Sus sumas
SHA-256 están en [SHA256SUMS](https://iso.kidux.org/SHA256SUMS), cada una
junto al nombre del archivo con su versión, que es el nombre con que lo
guarda el navegador; un archivo guardado con el nombre del enlace se
compara a mano con la línea de su idioma y su tipo.

## Windows, o un Mac o Linux, con VirtualBox

1. Instala VirtualBox y descarga la imagen `.ova`.
2. En VirtualBox, elige **Archivo > Importar servicio virtualizado**,
   elige la imagen y pulsa **Terminar**. VirtualBox crea una máquina con
   dos procesadores, 4 GB de memoria y arranque UEFI, como un ordenador
   comprado en los últimos diez años.
3. Elige la máquina y pulsa **Iniciar**. Aparece el logo de Kidux, y
   después su pantalla de entrada con Leo.

Para ver enteras las pantallas de Kidux, haz la ventana de al menos 1280
por 800, o usa **Ver > Modo pantalla completa**.

## Un Mac con UTM

1. Instala UTM y descarga la imagen `.qcow2`.
2. En UTM, pulsa **Crear una nueva Máquina Virtual (VM)**, después
   **Emular** y después **Otro**.
3. En **Hardware**, deja elegida la máquina **Intel ICH9 based PC (2009,
   x86_64)** y la memoria en **4096 MiB**, y en **Núcleos de CPU** escribe
   **4**, o la mitad de los núcleos de tu Mac si tiene más de 8. Pulsa
   **Continuar**.
4. En la pantalla siguiente, en **Boot Device**, marca **Ninguno**, deja
   marcado **Arranque UEFI** y pulsa **Continuar**.
5. En **Almacenamiento**, pulsa **Continuar** tal cual: ese disco se
   sustituye enseguida. En **Directorio compartido**, pulsa **Continuar**
   sin elegir nada. En **Resumen**, ponle de nombre *Kidux*, marca **Abrir
   configuración de la VM** y pulsa **Guardar**.
6. En la configuración que se abre, baja por la columna de la izquierda
   hasta **Unidades de disco**. Elige **Unidad IDE**, pulsa **Eliminar** y
   confírmalo. Después pulsa **Nuevo...**, cambia **Interfaz** a
   **VirtIO**, pulsa **Importar...** y elige la imagen `.qcow2`. Pulsa
   **Guardar**.
7. Arranca la máquina con el triángulo que hay junto a su nombre. Aparece
   el logo de UTM, después el de Kidux y, en menos de un minuto, su
   pantalla de entrada con Leo. Si entre medias la pantalla se queda negra
   unos segundos, espera: es normal.

UTM copia la imagen al importarla y la deja en unos 3,5 GB, así que el
archivo descargado se puede borrar después.

En un Mac con procesador de Apple, UTM emula un procesador de PC entero,
porque Kidux está hecho para PC: todo funciona, pero más despacio que en
un ordenador real. Cuantos más núcleos le des, mejor: con 2 va muy lento,
con 4 se puede usar y con 8 va bastante bien. En un Mac con procesador
Intel, UTM o VirtualBox lo hacen funcionar a velocidad normal.

## Linux con QEMU

Instala QEMU y su firmware UEFI (en Debian o Ubuntu, los paquetes
`qemu-system-x86` y `ovmf`), descarga la imagen `.qcow2` y, en la carpeta
en que esté, arráncala con:

```
qemu-system-x86_64 -enable-kvm -cpu host -m 4096 -smp 2 -machine q35 \
    -bios /usr/share/ovmf/OVMF.fd \
    -drive file=kidux-trial-es.qcow2,if=virtio \
    -vga none -device VGA,xres=1280,yres=800 \
    -device qemu-xhci -device usb-tablet -nic user,model=virtio-net-pci
```

Aparece el logo de Kidux, y después su pantalla de entrada con Leo. Todo
lo que se cambia al probar se guarda en el propio archivo de la imagen;
una descarga nueva empieza otra vez desde el principio.

## Lo que una prueba no puede enseñar

- **Las piezas propias del ordenador real**: su wifi, su tapa, su batería,
  sus teclas de brillo y volumen. Dentro de un emulador, Kidux ve la red
  del emulador como un cable, y ni batería ni tapa.
- **La velocidad de un ordenador real.** Un emulador es más lento que el
  mismo ordenador con Kidux, y mucho más lento cuando emula un procesador
  distinto.
- **Las teclas que el ordenador se guarda para sí.** Algunas
  combinaciones, como Ctrl+Alt+Supr, las recibe el ordenador que rodea al
  emulador, no Kidux.

Cuando hayas visto suficiente, [la guía de uso](user-guide.md#2-instalar-kidux)
explica cómo instalar Kidux en un ordenador propio.
