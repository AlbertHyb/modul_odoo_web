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

## Comando forzado del despliegue

El despliegue llega por SSH con un comando forzado: la clave autorizada ejecuta
`sudo -n /usr/local/sbin/financa-staging-deploy` y el script acepta únicamente
`deploy <sha de 40 caracteres>` que sea el tip actual de `origin/staging`.
Instalarlo una vez desde una sesión administrativa confiable, copiándolo tal cual
desde el repositorio:

```bash
sudo install -o root -g root -m 0750 deploy/server/financa-staging-deploy.sh /usr/local/sbin/financa-staging-deploy
```

El archivo instalado es una copia, no un enlace: **cada vez que
`deploy/server/financa-staging-deploy.sh` cambie en el repositorio hay que
reinstalarlo antes de desplegar**. Para que ese olvido no vuelva a fallar en
silencio, el script compara su propia copia instalada con la del SHA solicitado y
se detiene imprimiendo el comando de reinstalación cuando difieren. Ajustar sus
constantes `repo` o `releases` obliga a mantener la copia instalada sincronizada,
porque la comparación es literal.

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
