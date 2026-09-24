# Staging con Docker Compose

Este proyecto ejecuta exactamente dos servicios persistentes: Odoo y
PostgreSQL. Caddy queda fuera de Compose y será el único proceso que llegue a
Odoo por `127.0.0.1:8069`.

## Preparación del host

1. Copiar `.env.example` como `.env` y ajustar exclusivamente las rutas del
   host. No cambiar los digests de imagen sin una revisión explícita.
2. Crear `POSTGRES_PASSWORD_FILE` como archivo `root:root`, modo `0600`, con
   una contraseña de PostgreSQL en una sola línea.
3. Crear los directorios persistentes bajo `/srv/financa-staging/data` y el
   release activo bajo `/srv/financa-staging/releases/current`.
4. Copiar `odoo.conf` a `ODOO_CONFIG_FILE`, añadirle `admin_passwd` y mantenerlo fuera del repositorio antes
   de iniciar el entorno. Esta plantilla no incluye secretos.

## Validación

Desde este directorio, con el archivo `.env` y el secreto del host presentes:

```bash
docker compose --env-file .env config
```

No ejecutar `up` hasta que el artifact haya sido renderizado y validado:

```bash
python3 ../ci/render_financa_artifact.py \
  --source ../.. --output /tmp/financa-artifact --commit <commit> \
  --environment staging --domain https://staging.financa.mx
```

La primera ejecución real, migración, backup y configuración de Caddy se
realizan en la fase operativa posterior.
