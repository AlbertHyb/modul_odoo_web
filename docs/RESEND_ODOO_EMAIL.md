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

## Confirmación de diagnóstico (lo que envía el módulo)

Desde esta versión, `financa_website` hace lo siguiente cuando alguien envía el formulario de `/contactus` en el sitio de Financa:

1. El formulario crea un **lead en CRM** (`crm.lead`) en lugar del correo interno `mail.mail` que Odoo usa por defecto.
2. Se genera un enlace personal y de un solo uso a la encuesta **Cuestionario de diagnóstico Financa** (`data/diagnostic_survey.xml`). La encuesta es solo por invitación: sin ese enlace, no se puede responder.
3. Se encola la plantilla **Financa: confirmación de solicitud de diagnóstico** (`data/mail_template_data.xml`), dirigida al correo del lead. El correo repite el plazo de 72 horas e incluye el botón al cuestionario, y queda registrado en el chatter del lead.

Las respuestas aparecen en **Encuestas → Cuestionario de diagnóstico Financa**, con el correo y el nombre del contacto.

Requisitos para que el correo salga por Resend:

- El correo de la compañía (**Ajustes → Compañías**) es el remitente. Tiene que pertenecer al dominio verificado en Resend y coincidir con el filtro FROM del servidor saliente. Si está vacío o es de otro dominio, Resend rechaza el envío.
- Preguntas, opciones y texto del correo se cambian **en este repositorio**. Si se editan en Odoo, la próxima actualización del módulo sobrescribe esos cambios.
- En staging el SMTP sigue bloqueado (`deploy/compose/odoo.conf`). Ahí el correo se genera y queda en *Ajustes → Técnico → Correos* con estado de excepción, sin llegar a nadie.
- Si algo falla al generar el correo, el lead se guarda igual y el error queda en el log del servidor (`Financa follow-up email failed`).
