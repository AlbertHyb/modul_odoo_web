# Resend para correo saliente de Odoo

## Decisión

Sí. Para este Odoo autohospedado, usar **SMTP de Resend** como servidor de correo saliente. Odoo ya admite un servidor SMTP externo, por lo que no hace falta crear ni mantener un addon ni integrar la API HTTP.

| Campo Odoo | Valor |
| --- | --- |
| Servidor SMTP | `smtp.resend.com` |
| Puerto | `465` |
| Seguridad | SSL/TLS implícito |
| Usuario | `resend` |
| Contraseña | API key de Resend |
| Filtro FROM | el dominio o subdominio verificado, por ejemplo `mail.example.com` |

Resend también soporta STARTTLS en el puerto `587`; `465` es la opción directa recomendada por su documentación. [SMTP de Resend](https://resend.com/docs/send-with-smtp)

## Configuración mínima

1. En Resend, crear una API key y verificar un dominio propio. Añadir los registros DNS que Resend indique. Resend recomienda usar un subdominio para separar la reputación de envío, por ejemplo `mail.example.com`. [Dominios verificados de Resend](https://resend.com/docs/dashboard/domains/introduction)
2. En Odoo: **Ajustes → Email → Usar servidores de correo personalizados → Servidores de correo saliente → Nuevo**. Configurar la tabla anterior, limitar el filtro FROM al dominio verificado y ejecutar **Probar conexión**. [Correo saliente en Odoo 19](https://www.odoo.com/documentation/19.0/applications/general/email_communication/email_servers_outbound.html)
3. Guardar la API key únicamente como secreto del host/entorno de producción, no en el módulo ni en XML o datos de Odoo.

## Límites relevantes

- SMTP de Resend es solo la ruta de salida. Para que respuestas, rebotes y aliases lleguen al chatter de Odoo, conservar/configurar una ruta entrante de Odoo (redirección, IMAP o DNS); Odoo documenta esos tres mecanismos. [Correo entrante en Odoo 19](https://www.odoo.com/documentation/19.0/applications/general/email_communication/email_servers_inbound.html)
- Un test SMTP correcto no garantiza la entrega: Odoo recomienda comprobar también las restricciones del proveedor. Resend aplica el mismo rate limit a SMTP que a su API y no proporciona logs del servidor SMTP para depuración. [Odoo](https://www.odoo.com/documentation/19.0/applications/general/email_communication/email_servers_outbound.html), [Resend](https://resend.com/docs/send-with-smtp)
- La API HTTP de Resend es posible, pero para Odoo requeriría código propio que sustituya o intercepte el envío estándar. Usarla solo si se necesitan capacidades específicas de la API, como programación o webhooks. [API de correo de Resend](https://resend.com/features/email-api)
