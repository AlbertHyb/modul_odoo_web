# Despliegue CI/CD de Financa

Los scripts no dependen de un proveedor de CI. El runner solo debe ejecutar:

```bash
./deploy/ci/publish_financa.sh
```

## Configuración única del servidor

1. Instalar el script root una vez desde una sesión administrativa confiable:

   ```bash
   sudo install -o root -g root -m 0750 deploy/server/deploy_financa.sh /usr/local/sbin/financa-deploy
   ```

2. Crear `/etc/financa/deploy.env` a partir de
   [`server/financa-deploy.env.example`](server/financa-deploy.env.example).
3. Ajustar los binarios, base de datos, servicio systemd y dominio de ese ambiente.
4. Instalar los hooks `FINANCA_BACKUP_BIN` y `FINANCA_RESTORE_BIN`. El
   primero recibe la base, crea un respaldo consistente de PostgreSQL y
   filestore y devuelve un token en una sola línea; el segundo recibe la base
   y ese token y restaura ambos al mismo punto. Su implementación depende del
   proveedor de PostgreSQL, almacenamiento y snapshots del ambiente.
5. Mantener ambos hooks como archivos regulares, propiedad de `root`,
   ejecutables, con ruta canónica y sin escritura para grupo u otros.
6. Proteger el archivo: `sudo chown root:root /etc/financa/deploy.env` y
   `sudo chmod 600 /etc/financa/deploy.env`.
7. Autorizar al usuario SSH del runner a ejecutar, sin contraseña, únicamente:

   ```text
   /usr/local/sbin/financa-deploy *
   ```

   El script debe permanecer propiedad de `root`; el CI no lo carga ni lo
   reemplaza. Los checks incluidos en el artifact se ejecutan como el usuario
   de Odoo, nunca como root.

El script serializa despliegues con `flock`, consulta el estado del módulo y
elige instalación o actualización. Antes de cambiar el addon crea un punto de
recuperación obligatorio. Ante un fallo restaura el código anterior y llama al
hook de recuperación para PostgreSQL y filestore. El servicio sólo vuelve a
arrancar si ambas restauraciones terminan correctamente; en caso contrario
permanece detenido para intervención manual.

## Variables del runner CI

| Variable | Tipo | Descripción |
| --- | --- | --- |
| `DEPLOY_HOST` | variable | Host del servidor Odoo. |
| `DEPLOY_USER` | variable | Usuario SSH de despliegue. |
| `DEPLOY_PORT` | variable opcional | Puerto SSH; por defecto `22`. |
| `DEPLOY_REMOTE_ROOT` | variable opcional | Staging remoto; por defecto `/var/tmp/financa-deploy`. |
| `DEPLOY_SSH_KEY` | secreto como archivo | Ruta al archivo temporal con la clave privada. |
| `DEPLOY_KNOWN_HOSTS` | secreto como archivo | Ruta al `known_hosts` verificado del servidor. |

El runner debe crear los dos archivos secretos con permisos `0600` antes de
invocar el script. No desactivar `StrictHostKeyChecking` ni usar `ssh-keyscan`
durante cada despliegue: registrar la huella del servidor una vez y guardarla
como secreto del CI.

## Gates incluidos

1. Preflight: unicidad por dominio, nombre del website, acceso por invitación,
   favicon, URL de inicio y preservación de una homepage previa.
2. Selección explícita entre instalación limpia y actualización.
3. Punto de recuperación consistente de base y filestore con Odoo detenido.
4. Activación de la barra nativa de cookies y verificación opcional de GA4 sin
   registrar ningún ID en el repositorio.
5. Postflight: homepage, redirección 301, página privada sin publicar y cookies.

La validación visual, la respuesta HTTP real y GA4 DebugView requieren un job
de navegador posterior al despliegue, porque dependen del dominio en ejecución.
