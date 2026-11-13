# Desarrollo en el VPS

Odoo 19 + PostgreSQL en Docker, con `financa_website` montado desde el repositorio. Mismas imágenes fijadas que staging y producción.

## Requisitos

- Docker con el plugin Compose, git y `python3` (para las pruebas).
- Unos 3 GB de RAM libres mientras está encendido (Odoo limitado a 2 GB y PostgreSQL a 1 GB).

## Uso

```bash
./deploy/dev/financa-dev.sh up       # la primera vez crea la base (~2 min); después arranca en segundos
./deploy/dev/financa-dev.sh update   # tras cambiar el manifest o los datos XML (data/, records nuevos)
./deploy/dev/financa-dev.sh test     # pruebas del repositorio
./deploy/dev/financa-dev.sh logs     # log de Odoo
./deploy/dev/financa-dev.sh stop     # libera la RAM; la base se conserva
./deploy/dev/financa-dev.sh reset    # borra la base de desarrollo (pide confirmación)
```

Odoo corre con `--dev=xml,reload`. Las vistas QWeb y el SCSS se ven al recargar la página, y un cambio en Python reinicia Odoo solo. Los registros de `data/` (encuesta, plantilla de correo, redirecciones) se aplican con `update`.

## Abrirlo desde la laptop

Odoo solo escucha en `127.0.0.1` del VPS. Desde la laptop:

```bash
ssh -N -L 8079:localhost:8079 dev@vmi3700969
```

Después abre `http://localhost:8079`. El usuario es `admin` y la contraseña `admin`; la base solo existe en el VPS. Para usar otro puerto: `FINANCA_DEV_PORT=8089 ./deploy/dev/financa-dev.sh up`.

## Diferencias con staging y producción

- El sitio conserva el marcador `__FINANCA_DOMAIN__` como dominio, porque el addon se monta tal cual, sin pasar por el render. Odoo lo usa como sitio por defecto con cualquier host.
- El correo está bloqueado. Los correos (por ejemplo, la confirmación con el cuestionario) quedan en **Ajustes → Técnico → Correos**, y el enlace al cuestionario se puede abrir desde ahí.
- No cargues aquí una copia de la base de producción: contiene datos de clientes.
