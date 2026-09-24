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
preflight, token de recuperación, acción `install` o `update`, ambos health
checks y smoke posterior.

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
