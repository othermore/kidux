# Correo

*[English version](../../en/modules/mail.md)* · [Volver al manual](../user-guide.md#9-módulos-de-aprendizaje)

**Correo** es un cliente de correo electrónico adaptado para menores basado en Mozilla Thunderbird. Permite al niño leer y redactar mensajes en un entorno simplificado y seguro, sin necesidad de realizar configuraciones técnicas complejas: la cuenta es administrada directamente por un adulto desde el panel.

| | |
|---|---|
| **Edad recomendada** | A partir de 8 años |
| **Conexión a internet** | Requerida para enviar y sincronizar mensajes entrantes; admite cuentas estándar de Gmail, Outlook, iCloud o cualquier servidor IMAP |
| **Software utilizado** | [Thunderbird](https://www.thunderbird.net/), desarrollado por MZLA Technologies y la comunidad Mozilla bajo licencia MPL-2.0, empaquetado oficialmente en Debian |

## Qué es y cómo funciona

Kidux adapta Thunderbird para aislar la experiencia de mensajería: el menor tiene acceso directo a su bandeja de entrada y al editor de mensajes, mientras que las funciones no aptas para niños (como chats públicos, instalación de extensiones, navegación web integrada y menús de configuración avanzada) se encuentran completamente deshabilitadas.

![Correo](../../images/es/module-mail.png)

## Configuración para el adulto

El adulto configura los datos de la cuenta en la pestaña **Módulos** del panel de control:

| Parámetro | Descripción |
|---|---|
| **Dirección de correo** | Correo electrónico del menor. Correo autodetecta los servidores correspondientes para la gran mayoría de proveedores (Gmail, Outlook/Hotmail, iCloud, Yahoo, etc.). |
| **Nombre** | Nombre visible del remitente que aparecerá en los mensajes enviados por el niño. |
| **Servidor de entrada** | Necesario únicamente si el proveedor no se detecta de forma automática: dirección del servidor IMAP (por ejemplo, `imap.ejemplo.org`). Puede incluir puerto específico (`imap.ejemplo.org:993`). |
| **Servidor de salida** | Dirección del servidor SMTP del proveedor (por ejemplo, `smtp.ejemplo.org:465`). |

Tras guardar la configuración en el panel, el adulto debe acompañar al menor en la primera apertura de la aplicación:
- **Cuentas de Google o Microsoft**: se abrirá la ventana oficial de autenticación del proveedor para ingresar las credenciales y el segundo factor si procede.
- **Otros proveedores**: la aplicación solicitará la contraseña una única vez. El adulto introduce la clave y marca la casilla para recordarla de forma permanente.

Thunderbird guarda la contraseña del buzón dentro del propio perfil del menor. El panel de adultos de Kidux nunca almacena ni tiene acceso a la contraseña del buzón.

## Aspectos a tener en cuenta

- **Cuentas con Google Family Link**: Las cuentas de menores de trece años gestionadas por Family Link no admiten acceso mediante clientes de correo externos como Thunderbird. Para estas cuentas debe utilizarse el módulo [Gmail](gmail.md).
- **Inmutabilidad y seguridad**: Cualquier intento de modificar la cuenta o añadir cuentas secundarias se descarta automáticamente al reiniciar la aplicación; la configuración activa coincide siempre con la definida en el panel. Si no se introduce ninguna dirección de correo, la aplicación se abre únicamente con sus carpetas locales desconectadas.
- **Seguridad en enlaces y descargas**: Los hipervínculos externos contenidos en los mensajes están desactivados. Los archivos adjuntos recibidos se descargan en la carpeta personal de **Descargas** sin ejecutarse automáticamente.
- **Avisos de conexión**: Si el servidor de correo no está disponible o falla la conexión a internet, se muestra una notificación discreta sobre la barra inferior y en la barra de estado de la ventana.

![La burbuja de Correo cuando su servidor no contesta](../../images/es/mail-notice.png)
