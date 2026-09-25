# Producción Docker Compose

Producción se despliega únicamente de forma manual desde
`.github/workflows/deploy-production.yml`. El job usa el Environment protegido
`production`, valida el repositorio y envía al servidor solamente
`deploy <GITHUB_SHA>`. El servidor acepta exclusivamente el tip actual de
`origin/master`, exige un checkout limpio, verifica el manifiesto y sus hashes,
crea un respaldo conjunto de PostgreSQL y filestore, instala o actualiza el
módulo y comprueba las URLs local y pública. Un fallo restaura release, base y
filestore; si esa recuperación falla, Odoo queda detenido.

## Environment `production` en GitHub

El Environment exige aprobación manual de `AlbertHyb`. Mientras exista un solo
administrador se permite la autoaprobación; al incorporar otro operador se debe
activar `prevent_self_review` y usarlo como aprobador. Configurar exclusivamente
en ese Environment:

| Nombre | Tipo |
| --- | --- |
| `PRODUCTION_SSH_HOST` | Variable |
| `PRODUCTION_SSH_PORT` | Variable |
| `PRODUCTION_SSH_USER` | Variable |
| `PRODUCTION_DOMAIN` | Variable, un hostname `https://` sin ruta |
| `PRODUCTION_SSH_PRIVATE_KEY` | Secreto, clave exclusiva de producción |
| `PRODUCTION_SSH_KNOWN_HOSTS` | Secreto, huella verificada de producción |

No copiar valores `STAGING_*`. Proteger `master` con pull request y el workflow
de validación requerido antes de habilitar el despliegue.

## Preparación única del host

1. Clonar `master` en `/srv/financa-production/repo`, propiedad de `REPO_USER`.
   El checkout debe permanecer limpio; cualquier cambio o archivo no rastreado
   bloquea el despliegue.
2. Crear `/srv/financa-production/releases/bootstrap/financa_website` vacío y
   el enlace `/srv/financa-production/releases/current` apuntando a `bootstrap`.
   Mantener todo `/srv/financa-production/releases` propiedad de root.
3. Crear `/srv/financa-production/render`, propiedad de `REPO_USER`. El
   artefacto solo pasa a releases después de verificarlo y convertirlo en
   root-owned.
4. Copiar `deploy/compose/.env.production.example` a
   `/etc/financa-production/compose.env`, sustituir los digests y mantener
   staging y producción con proyectos, rutas, DB y secretos distintos.
5. Instalar `deploy/compose/compose.yaml` como
   `/etc/financa-production/compose.yaml`, propiedad `root:root`, modo `0644`.
   El despliegue no ejecuta Compose desde el checkout modificable.
6. Crear `/etc/financa-production/odoo.conf` para Odoo 19 con `db_name` y
   `dbfilter` exclusivos, `list_db = False`, `proxy_mode = True` y
   `admin_passwd` fuera del repositorio.
7. Copiar `deploy/server/financa-production-deploy.env.example` a
   `/etc/financa-production/deploy.env`, completar sus valores y aplicar
   propietario `root:root`, modo `0600`.
8. Instalar el comando forzado y el verificador como archivos inmutables para
   `REPO_USER`:

   ```bash
   sudo install -o root -g root -m 0750 deploy/server/financa-production-deploy.sh /usr/local/sbin/financa-production-deploy
   sudo install -o root -g root -m 0750 deploy/ci/verify_financa_artifact.py /usr/local/sbin/verify-financa-artifact
   ```

   El script instalado es una copia congelada, no un enlace: cuando
   `deploy/server/financa-production-deploy.sh` cambie en el repositorio hay que
   reinstalarlo. El despliegue compara su propia copia instalada con la del SHA
   aprobado y se detiene imprimiendo el comando de reinstalación si no coinciden,
   para no ejecutar lógica privilegiada que no es la revisada.

9. Instalar los hooks `FINANCA_BACKUP_BIN` y `FINANCA_RESTORE_BIN`. Deben ser
   archivos regulares, canónicos, ejecutables, propiedad de root y no
   escribibles por grupo u otros. El backup devuelve un token para el mismo
   punto consistente de PostgreSQL y filestore; restore recibe la base y ese
   token. Retener cada punto al menos siete días.
10. Mantener el usuario SSH fuera del grupo `docker`. Autorizar solo el script
    y conservar `SSH_ORIGINAL_COMMAND`:

    ```text
    Defaults:financa-deploy env_keep += "SSH_ORIGINAL_COMMAND"
    financa-deploy ALL=(root) NOPASSWD: /usr/local/sbin/financa-production-deploy
    ```

    La clave pública usa el comando forzado:

    ```text
    restrict,command="sudo -n /usr/local/sbin/financa-production-deploy" ssh-ed25519 <clave-publica-produccion>
    ```

Antes del primer despliegue ejecutar:

```bash
docker compose --env-file /etc/financa-production/compose.env -f /etc/financa-production/compose.yaml config
```

Después, ejecutar **Deploy Financa production** manualmente desde GitHub
Actions sobre `master`, aprobar el gate y conservar como evidencia: SHA,
preflight, token de recuperación, acción `install` o `update`, reporte de
saneamiento, gate de navegación, ambos health checks y smoke posterior.

## Contenido heredado del sitio anterior

El addon solo crea sus propios registros: nunca borra las páginas ni los menús
que dejó el sitio anterior en la base. Por eso producción servía la navegación
antigua junto a la nueva, mientras que un staging con base nueva no hereda nada
y no reproduce el defecto. El despliegue de producción lo neutraliza en tres
pasos, después de actualizar el módulo:

1. `deploy/odoo/cleanup_financa_legacy.py` despublica en su lugar las páginas
   catalogadas (nunca las borra) y desactiva sus menús. Si un menú a desactivar
   contiene menús del módulo, los vuelve a colgar de la raíz para no ocultarlos.
   Es idempotente: la segunda ejecución no reporta cambios.
2. `deploy/odoo/configure_financa.py` aplica el resto de la configuración.
3. `deploy/odoo/postflight_financa.py` falla si el contenido catalogado sigue
   activo o publicado, si los seis menús del módulo no están activos y colgados
   de la raíz, o si un menú ajeno duplica una etiqueta de la navegación de
   Financa. Un fallo restaura release, base y filestore.

`deploy/odoo/financa_legacy.json` es la lista revisada de ese contenido y el
pipeline la pasa como `FINANCA_LEGACY_INVENTORY`. Cada entrada se empareja por
`name` o por `url`, y basta con que coincida una de las dos. El `name` se compara
con la etiqueta del menú en todos los idiomas activos, sin distinguir acentos ni
mayúsculas: el mismo registro se ve como «Noticias» en español y «Blog» en
inglés, y una entrada escrita con la etiqueta del sitio no debe depender del
idioma con el que corre el shell. Los registros con `xml_id` de `financa_website`
nunca se tocan.

Ambos pasos imprimen en JSON el estado previo, las acciones aplicadas y los
menús y páginas ajenos que permanecen en el website. Esa evidencia es la que
amplía la lista con datos y no por suposición: cuando el gate falla, nombra los
registros exactos que faltan catalogar. Una página compartida (`website_id`
vacío) que coincida con el inventario se reporta pero no se toca, porque
despublicarla afectaría a otros websites.

## Deuda técnica de salida a producción

Mientras una fila permanezca abierta, la automatización está implementada pero
el despliegue productivo continúa bloqueado.

| Estado | Deuda | Responsable | Evidencia requerida | Condición de cierre |
| --- | --- | --- | --- | --- |
| Mitigada | Separar a quien dispara y aprueba el despliegue | Administrador GitHub | Environment `production` creado con aprobación manual de `AlbertHyb` y ramas protegidas | Incorporar otro operador y activar `prevent_self_review` |
| Cerrada | Proteger `master` y exigir validación | Administrador GitHub | Regla activa: PR obligatorio, `validate` estricto y aplicada a administradores | Push directo, force-push y borrado rechazados |
| Abierta | Instalar comando forzado y permisos SSH/sudo | Administrador servidor | `authorized_keys`, sudoers y prueba negativa | Solo `deploy <sha>` válido llega al script |
| Abierta | Definir dominio, rutas, DB, secretos y digests reales | Administrador servidor | Compose renderizado y valores no secretos | `docker compose config` y Odoo 19 pasan |
| Abierta | Implementar hooks DB + filestore | Administrador servidor | Token y listado de ambos componentes | Backup completa antes de activar release |
| Abierta | Aplicar retención mínima de siete días | Administrador servidor | Política y muestra de puntos vigentes | Token sigue resolviendo antes del día 7 |
| Abierta | Ensayar restore y fallo posterior al backup | DevOps/QA | Log, RTO/RPO y health checks | Código, DB y filestore vuelven al mismo punto |
| Abierta | Ejecutar QA de instalación, actualización y multiwebsite | QA/Product Owner | Reporte firmado de staging | Cero defectos S1/S2 y P1 aprobados |
| Abierta | Completar contenido y aviso de privacidad | Product Owner/Legal | Aprobación comercial y jurídica | No quedan datos ficticios ni marcadores |
