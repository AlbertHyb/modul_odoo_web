# Plan maestro de auditoría de seguridad

## Proyecto: `financa_website`

| Campo | Valor |
|---|---|
| Sistema | Sitio web Financa sobre Odoo 19 Community |
| Alcance técnico | Código, SCM, CI/CD, servidor, Odoo, PostgreSQL, filestore, respaldos, registros y terceros |
| Clasificación | Uso interno — Seguridad |
| Versión del plan | 1.0 |
| Estado | Propuesto para aprobación |
| Propietario sugerido | Responsable de Seguridad / CTO |
| Aprobadores sugeridos | Propietario del servicio, DevOps, DBA y responsable de cumplimiento |
| Frecuencia | Auditoría completa anual y después de cambios mayores o incidentes |

> Este documento define cómo auditar; no declara vulnerabilidades confirmadas. Toda observación inicial es una hipótesis que debe comprobarse con evidencia trazable.

## 1. Objetivo

Determinar si el sitio y su cadena de entrega protegen adecuadamente la confidencialidad, integridad, disponibilidad, autenticidad y trazabilidad de:

- código fuente y artefactos;
- credenciales y secretos de despliegue;
- servidor, Odoo y reverse proxy;
- base de datos PostgreSQL y filestore;
- datos personales, telemetría y registros;
- respaldos, recuperación y continuidad operativa.

El resultado debe permitir decidir si el sistema puede operar o liberarse, qué riesgos deben contenerse de inmediato y qué remediaciones deben incorporarse al backlog.

## 2. Alcance

### 2.1 Incluido

- Addon `financa_website`: Python, XML/QWeb, JavaScript, SCSS, manifiesto, recursos estáticos y pruebas.
- Repositorio, ramas, revisiones, etiquetas, dependencias y permisos del sistema de control de versiones.
- Pipeline o mecanismo CI/CD, runners, secretos, artefactos, aprobaciones y bitácoras.
- Scripts `deploy/ci`, `deploy/server` y `deploy/odoo`.
- SSH, `sudo`, cuentas técnicas, systemd, firewall, reverse proxy, TLS, archivos y permisos del host.
- Configuración y nivel de parche de Odoo; usuarios, grupos, sesiones, páginas y administración de bases.
- PostgreSQL: red, autenticación, roles, privilegios, cifrado, auditoría, disponibilidad y respaldos.
- Filestore y consistencia transaccional con PostgreSQL.
- Google Analytics 4 y cualquier otro tercero que reciba datos.
- Monitoreo, gestión de incidentes, continuidad, restauración y eliminación de datos.

### 2.2 Fuera de alcance salvo autorización adicional

- Ingeniería social, phishing o pruebas físicas.
- Denegación de servicio, estrés sobre producción o explotación destructiva.
- Acceso a cuentas personales de colaboradores.
- Pentest de infraestructura compartida de proveedores externos.
- Modificación de datos reales o extracción masiva de información.

### 2.3 Supuestos que deben confirmarse en la apertura

- Distribución y versión exactas del servidor.
- Topología: reverse proxy, Odoo, PostgreSQL y runner local o remoto.
- Si PostgreSQL es local, administrado o remoto.
- Proveedor real de SCM/CI y controles disponibles.
- Ambientes existentes y separación entre desarrollo, pruebas y producción.
- Clasificación de datos, RPO, RTO y obligaciones legales aplicables.
- Inventario de dominios, certificados, integraciones y propietarios.

## 3. Marco de referencia

La auditoría usará una selección proporcional de los siguientes marcos:

| Referencia | Uso en esta auditoría |
|---|---|
| NIST SP 800-218 SSDF 1.1 | Prácticas de desarrollo seguro y protección del ciclo de vida |
| OWASP ASVS 5.0 | Requisitos verificables de seguridad de aplicación |
| OWASP WSTG | Técnicas de validación web controlada |
| OWASP CI/CD Security Cheat Sheet | Identidades, secretos, runners, dependencias y artefactos |
| OWASP Database Security Cheat Sheet | Red, autenticación, mínimos privilegios, parches y respaldos |
| OWASP Logging Cheat Sheet | Eventos, protección, retención y exclusión de secretos/PII |
| CIS Benchmark de la distribución instalada | Línea base de hardening del sistema operativo |
| Documentación de despliegue seguro de Odoo 19 | Reverse proxy, `proxy_mode`, `dbfilter`, `list_db`, cuentas y PostgreSQL |
| Documentación vigente de PostgreSQL | `pg_hba.conf`, TLS, roles, registros y recuperación |
| CVSS 4.0 + contexto de negocio | Apoyo para severidad técnica; no sustituye el análisis de impacto |

Referencias oficiales:

- https://csrc.nist.gov/pubs/sp/800/218/final
- https://owasp.org/www-project-application-security-verification-standard/
- https://owasp.org/www-project-web-security-testing-guide/latest/
- https://cheatsheetseries.owasp.org/cheatsheets/CI_CD_Security_Cheat_Sheet.html
- https://cheatsheetseries.owasp.org/cheatsheets/Database_Security_Cheat_Sheet.html
- https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html
- https://www.cisecurity.org/benchmark/ubuntu_linux
- https://www.odoo.com/documentation/19.0/administration/on_premise/deploy.html
- https://www.odoo.com/documentation/19.0/developer/reference/backend/security.html
- https://www.postgresql.org/docs/current/auth-pg-hba-conf.html
- https://www.postgresql.org/docs/current/ssl-tcp.html

## 4. Arquitectura y fronteras de confianza a confirmar

```text
Desarrollador
    │ commit / revisión
    ▼
Repositorio SCM ──► Runner CI ──► Artefacto ──► SSH/SCP
                                                │
                                                ▼
                                   sudo: financa-deploy
                                                │
                         ┌──────────────────────┼──────────────────────┐
                         ▼                      ▼                      ▼
                    Odoo 19               PostgreSQL              Filestore
                         │                      │                      │
                         └──────── Reverse proxy / TLS ───────────────┘
                                                │
                                                ▼
                                         Navegador / GA4
```

Activos críticos:

| Activo | Riesgo principal | Propietario a designar |
|---|---|---|
| Código y ramas protegidas | Alteración no autorizada | Desarrollo |
| Llave SSH y secretos CI | Toma del servidor/pipeline | DevOps |
| Script root de despliegue | Escalada de privilegios | Operaciones |
| Configuración y sesiones Odoo | Toma de administración | Dueño de aplicación |
| Base PostgreSQL | Exposición o alteración de datos | DBA |
| Filestore | Fuga o pérdida de adjuntos | DBA/Operaciones |
| Backups y snapshots | Exposición o recuperación fallida | Operaciones |
| Logs y analítica | Secretos/PII o falta de evidencia | Seguridad/Privacidad |

## 5. Reglas de ejecución segura

1. Obtener autorización escrita, alcance, horario, IP de origen, contactos y criterios de aborto.
2. Usar primero un ambiente de pruebas representativo y datos sintéticos.
3. En producción, comenzar con inspección de solo lectura. Cualquier prueba activa requiere una ventana y aprobación separadas.
4. No ejecutar fuerza bruta, DoS, borrado, cifrado, modificación masiva ni explotación persistente.
5. Confirmar respaldo recuperable de base y filestore antes de una prueba que pueda cambiar estado.
6. No copiar contraseñas, cookies, tokens, llaves privadas, cadenas de conexión ni PII a tickets o reportes.
7. Redactar secretos en capturas y salidas; conservar sólo los campos necesarios para probar el control.
8. Cifrar evidencia en tránsito y reposo, limitar accesos y fijar una fecha de eliminación.
9. Detener la prueba ante indisponibilidad, corrupción, exposición inesperada o impacto a terceros.
10. Comunicar de inmediato un hallazgo crítico explotable; no esperar al informe final.

## 6. Gobierno de la auditoría

### 6.1 Roles

| Rol | Responsabilidad |
|---|---|
| Patrocinador | Autoriza alcance, riesgo residual y excepciones |
| Líder de auditoría | Planifica, preserva independencia y emite el dictamen |
| Desarrollo | Explica código, corrige y aporta pruebas |
| DevOps/Operaciones | Facilita CI/CD, host, proxy, Odoo y evidencias |
| DBA | Facilita PostgreSQL, respaldos y restauración |
| Privacidad/Legal | Valida datos personales, consentimiento y retención |
| Dueño del servicio | Acepta criterios y confirma impacto de negocio |

Nadie debe aprobar como auditor independiente la remediación que implementó sin una segunda revisión.

### 6.2 Evidencia

Cada evidencia tendrá identificador `EVD-AAAA-NNN`, fecha/hora UTC, fuente, responsable de obtención, control relacionado, clasificación y hash SHA-256 cuando sea un archivo. Los secretos se sustituyen por `[REDACTADO]` antes de almacenarla.

Tipos aceptables:

- configuración exportada y redactada;
- salida de comando de sólo lectura;
- captura con fecha y contexto;
- consulta SQL de metadatos;
- registro de pipeline o de auditoría;
- prueba automatizada reproducible;
- entrevista corroborada por evidencia técnica.

Una declaración verbal por sí sola no cierra un control.

## 7. Método y fases

| Fase | Actividad | Resultado | Criterio de salida |
|---|---|---|---|
| 0. Autorización | Alcance, contactos, reglas y accesos temporales | Acta de inicio | Firmada por responsables |
| 1. Descubrimiento | Inventario, datos, topología y flujo de despliegue | Diagrama e inventario | Activos y dueños identificados |
| 2. Modelado de amenazas | Actores, abusos, fronteras y controles | Registro de amenazas | Riesgos priorizados |
| 3. Código | Revisión manual, SAST, secretos, dependencias y pruebas | Hallazgos CODE | Cobertura acordada completada |
| 4. CI/CD | IAM, runner, secretos, artefactos, SSH/sudo y rollback | Hallazgos CICD | Pipeline trazado extremo a extremo |
| 5. Servidor/Odoo | Host, red, TLS, proxy, systemd, archivos y aplicación | Hallazgos SRV/APP | Baseline documentada |
| 6. Base y recuperación | PostgreSQL, filestore, backup y restore | Hallazgos DB/BCP | Restauración demostrada |
| 7. Validación controlada | Pruebas web y escenarios de abuso autorizados | Evidencia reproducible | Sin impacto pendiente |
| 8. Informe | Riesgo, causa, recomendación, propietario y fecha | Informe ejecutivo/técnico | Aceptado por patrocinador |
| 9. Remediación/retest | Corrección y repetición de pruebas | Dictamen de cierre | Riesgo eliminado o aceptado |

## 8. Matriz maestra de auditoría

Prioridades: `P0` bloquea liberación u exige contención inmediata; `P1` debe resolverse antes de la siguiente liberación; `P2` entra al ciclo próximo; `P3` es mejora programable.

### 8.1 Código y aplicación

| ID | Pri. | Qué revisar | Procedimiento y evidencia | Resultado esperado |
|---|---:|---|---|---|
| CODE-001 | P1 | Inventario y superficie del addon | Enumerar Python, XML/QWeb, JS, recursos, dependencias y endpoints; comparar con manifiesto | Sólo componentes necesarios y trazables |
| CODE-002 | P0 | Secretos en historial y árbol | Escáner de secretos más revisión de llaves, tokens, dominios internos y cadenas de conexión; revisar historial sin imprimir valores | Ningún secreto válido en código, commits o artefactos |
| CODE-003 | P0 | XSS y salidas QWeb | Buscar `t-raw`, `Markup`, atributos/URL dinámicos y contenido HTML; probar entradas no confiables | Salidas escapadas, URLs validadas y sin ejecución de script |
| CODE-004 | P0 | JavaScript peligroso | Revisar `innerHTML`, `eval`, `Function`, DOM sinks, listeners globales, `postMessage`, URL y storage | Sin sinks explotables; origen y esquema validados |
| CODE-005 | P1 | Ámbito multiwebsite | Verificar que selectores, páginas, redirects, datos y activos se limiten al website correcto | Ninguna lectura/escritura o indexación cruzada |
| CODE-006 | P0 | `sudo()` y elevación ORM | Justificar cada `sudo`, reducir búsqueda/campos y probar usuarios public/portal/internal | No se eluden ACL o record rules para datos sensibles |
| CODE-007 | P0 | Controladores presentes o futuros | Revisar `auth`, método, CSRF, CORS, validación, errores, rate limit y autorización por objeto | Denegación por defecto y CSRF activo en rutas HTTP con estado |
| CODE-008 | P1 | Redirects y navegación | Probar redirecciones abiertas, esquemas peligrosos, host header y rutas obsoletas | Sólo destinos locales o allowlist explícita |
| CODE-009 | P1 | Consentimiento y analítica | Verificar que GA4 sólo cargue/emita tras consentimiento; inspeccionar payloads y revocación | Sin PII, IDs sensibles ni eventos previos al consentimiento |
| CODE-010 | P2 | Almacenamiento del navegador | Revisar claves de `sessionStorage`/cookies, expiración y ausencia de tokens sensibles | Datos mínimos, no sensibles y con ciclo de vida definido |
| CODE-011 | P1 | Manejo de errores y logs | Provocar fallas controladas y buscar stack traces, rutas, secretos o PII | Mensaje público genérico y detalle sólo en log protegido |
| CODE-012 | P1 | Dependencias y licencias | Generar inventario/SBOM del addon y runtime; revisar versiones, origen, CVE y necesidad | Componentes soportados, íntegros y sin CVE fuera del SLA |
| CODE-013 | P1 | Pruebas de seguridad | Ejecutar tests estáticos, de unidad/Odoo e integración para autorización, consentimiento y aislamiento | Casos críticos automatizados y bloqueantes |
| CODE-014 | P2 | Código muerto y opciones de depuración | Buscar flags, comentarios temporales, datos demo, consola y recursos no usados | Producción sin debug ni superficie innecesaria |
| CODE-015 | P1 | Privacidad de formularios | Confirmar minimización, propósito, aviso, retención, destinatarios y protección antiabuso | Recogida legítima, mínima y protegida |

### 8.2 Repositorio y CI/CD

| ID | Pri. | Qué revisar | Procedimiento y evidencia | Resultado esperado |
|---|---:|---|---|---|
| CICD-001 | P0 | Identidades del SCM | Exportar usuarios, bots, admins, MFA, llaves y tokens; confirmar bajas | MFA y mínimo privilegio; sin cuentas huérfanas |
| CICD-002 | P1 | Protección de ramas y releases | Revisar PR obligatoria, dos ojos para áreas críticas, checks, firmas y restricción de force-push | Ningún cambio a producción sin revisión y controles exitosos |
| CICD-003 | P0 | Secretos del pipeline | Revisar ubicación, scopes, masking, acceso por ambiente, rotación y exposición en forks/logs | Secretos en bóveda, temporales cuando sea posible y no exportables |
| CICD-004 | P0 | Runner | Confirmar aislamiento, efimeridad, parches, red, cachés y ausencia de montajes/credenciales compartidas | Job no confiable no puede alcanzar secretos o producción |
| CICD-005 | P1 | Integridad de acciones/herramientas | Fijar acciones por digest/commit, verificar imágenes y restringir plugins | Dependencias de pipeline inmutables y aprobadas |
| CICD-006 | P0 | Composición del artefacto | Inspeccionar tar, rutas, enlaces simbólicos, permisos y archivos inesperados | Artefacto mínimo; sin traversal, secretos, `.git` ni symlinks peligrosos |
| CICD-007 | P1 | Proveniencia e integridad | Generar hash, SBOM y metadatos de commit/build; verificar antes de desplegar | Producción puede vincularse a un commit y artefacto exactos |
| CICD-008 | P0 | SSH del despliegue | Verificar host key fija, algoritmo, rotación y llave restringida por host/comando/IP | Sin TOFU; llave exclusiva y de alcance mínimo |
| CICD-009 | P0 | Regla `sudo` | Revisar ruta absoluta, argumentos permitidos, variables, wildcards y posibilidad de sustituir script | El usuario de deploy sólo ejecuta el comando exacto necesario |
| CICD-010 | P0 | Script privilegiado | Confirmar root ownership, no escritura grupal, rutas canónicas, archivos regulares, no symlink y `umask` seguro | Entradas no controlan ejecución root ni sobrescriben rutas arbitrarias |
| CICD-011 | P1 | Concurrencia y estado | Simular dos despliegues, cancelación y pérdida de conexión; revisar lock y transacciones | Un despliegue a la vez y estado determinista |
| CICD-012 | P0 | Instalación/actualización de Odoo | Probar base limpia y existente; diferenciar `-i` de `-u`; validar códigos de salida | Primera instalación y upgrade fallan de forma segura y observable |
| CICD-013 | P0 | Rollback consistente | Ensayar fallo después de migración; restaurar código, DB y filestore del mismo punto | Sin versión de código incompatible con esquema/datos |
| CICD-014 | P1 | Aprobación de producción | Revisar ambientes protegidos, separación de funciones y ventana | Despliegue prod requiere autorización trazable |
| CICD-015 | P1 | Logs y retención | Revisar que el job registre quién/qué/cuándo sin mostrar secretos | Trazabilidad íntegra, centralizada y con retención definida |
| CICD-016 | P1 | Escaneo continuo | Confirmar SAST, secretos, SCA, IaC/shell lint y umbrales de bloqueo | Controles automáticos en PR y release, con excepciones caducables |

### 8.3 Servidor, red y Odoo

| ID | Pri. | Qué revisar | Procedimiento y evidencia | Resultado esperado |
|---|---:|---|---|---|
| SRV-001 | P1 | Inventario, soporte y parches | Registrar OS, kernel, paquetes, Odoo, proxy y fecha de parche; comparar avisos vigentes | Versiones soportadas y CVE dentro del SLA |
| SRV-002 | P0 | Cuentas y SSH | Revisar usuarios, grupos, UID 0, llaves, root login, password auth, allowlist/VPN y caducidad | Llaves individuales, root remoto deshabilitado y acceso limitado |
| SRV-003 | P0 | Exposición de red | Enumerar listeners y reglas; contrastar con diagrama | Sólo 80/443 públicos; administración y DB restringidas |
| SRV-004 | P0 | TLS | Probar protocolos, cifrados, cadena, hostname, renovación, HSTS y redirección HTTP | TLS vigente, renovación alertada y sin protocolos débiles |
| SRV-005 | P1 | Reverse proxy | Revisar headers, tamaño/timeouts, IP real confiable, websocket/longpolling y rate limit | Proxy impide spoofing y limita abuso sin romper Odoo |
| SRV-006 | P0 | Configuración base Odoo | Verificar `proxy_mode`, `dbfilter`, `list_db=False`, `admin_passwd`, `db_name` y debug | DB manager no expuesto; selección de DB no controlable por atacante |
| SRV-007 | P0 | Administradores Odoo | Revisar admin por defecto, MFA si disponible, grupos, cuentas inactivas y superusuario | Mínimos administradores, cuentas nominativas y revisión periódica |
| SRV-008 | P1 | Usuarios public/portal/internal | Probar navegación y objetos con cada rol; revisar signup B2B | Cada rol ve únicamente lo requerido |
| SRV-009 | P1 | Sesiones y cookies | Inspeccionar Secure, HttpOnly, SameSite, logout, expiración y revocación | Sesiones protegidas y revocables |
| SRV-010 | P0 | Gestor de bases Odoo | Probar `/web/database/*` desde Internet sin realizar cambios | Inaccesible externamente y protegido por master password robusta |
| SRV-011 | P1 | Servicio systemd | Revisar usuario/grupo, `NoNewPrivileges`, capacidades, `ProtectSystem`, `PrivateTmp`, límites y restart | Odoo no corre como root y el sandbox no impide persistencia necesaria |
| SRV-012 | P0 | Permisos de archivos | Revisar config, deploy env, scripts, addons, logs, filestore, backups y directorios padres | Secretos 0600/propietario correcto; código privilegiado inmutable |
| SRV-013 | P1 | Temporal y enlaces | Auditar creación/extracción/movimiento de archivos y resistencia a symlink/TOCTOU | Temporales exclusivos y destinos canónicos validados |
| SRV-014 | P1 | Headers y contenido web | Verificar CSP viable, frame-ancestors/X-Frame-Options, nosniff, Referrer-Policy y caché | Navegador recibe una política coherente y probada |
| SRV-015 | P1 | Antiabuso | Probar rate limit de login/formularios, bloqueo progresivo y alertas con límites seguros | Automatización abusiva contenida sin DoS accidental |
| SRV-016 | P1 | Logs del host y Odoo | Revisar auth, sudo, deploy, Odoo y proxy; permisos, rotación, reloj y envío central | Eventos correlacionables, protegidos y sin secretos/PII innecesarios |
| SRV-017 | P1 | Monitoreo | Confirmar alertas de disponibilidad, TLS, disco, CPU, errores, auth y cambios críticos | Alertas accionables con propietario y escalamiento probado |
| SRV-018 | P1 | Persistencia y malware | Revisar cron, timers, services, authorized_keys, paquetes y cambios de integridad | No hay persistencia no autorizada ni binarios sin origen |
| SRV-019 | P2 | Hardening CIS aplicable | Ejecutar evaluación contra la versión exacta de OS y justificar excepciones | Cumplimiento medido; excepciones documentadas y compensadas |
| SRV-020 | P0 | Separación de ambientes | Comparar hosts, DB, secretos, dominios y datos de no producción | Prod aislado; no producción no usa secretos ni PII reales sin anonimizar |

### 8.4 PostgreSQL, datos, filestore y recuperación

| ID | Pri. | Qué revisar | Procedimiento y evidencia | Resultado esperado |
|---|---:|---|---|---|
| DB-001 | P1 | Versión, soporte y extensiones | Consultar versión, extensiones, paquetes y calendario de soporte | Versión soportada; extensiones necesarias y actualizadas |
| DB-002 | P0 | Exposición y `listen_addresses` | Revisar listener, firewall y topología; probar sólo desde redes autorizadas | DB no pública; socket/local o red privada estricta |
| DB-003 | P0 | Reglas `pg_hba.conf` | Consultar `pg_hba_file_rules` y orden; buscar `trust`, rangos amplios y métodos obsoletos | Reglas mínimas, específicas y con SCRAM/certificado según riesgo |
| DB-004 | P0 | TLS cliente-DB | Si la conexión es remota, revisar `hostssl`, certificados y `db_sslmode` | TLS verificado (`verify-full` cuando sea viable), sin downgrade |
| DB-005 | P0 | Rol de aplicación | Consultar atributos y membresías de rol Odoo | `NOSUPERUSER`, `NOCREATEDB`, `NOCREATEROLE`, `NOREPLICATION`, sin `BYPASSRLS` |
| DB-006 | P0 | Propiedad de la base | Comparar propietario con rol de aplicación y proceso de migración | Rol Odoo no es superusuario; propietario separado cuando el diseño lo permita |
| DB-007 | P1 | Privilegios de esquema | Revisar `public`, CREATE, funciones, secuencias, default privileges y membresías | Sin CREATE público ni privilegios heredados innecesarios |
| DB-008 | P1 | `search_path` y funciones | Inspeccionar roles/DB/funciones SECURITY DEFINER y rutas mutables | Objetos privilegiados no resuelven nombres desde esquemas escribibles |
| DB-009 | P1 | Credenciales | Revisar origen, permisos, rotación, cuentas separadas y ausencia en logs | Secretos en gestor seguro, rotables y exclusivos por ambiente |
| DB-010 | P1 | Cifrado en reposo | Confirmar cifrado de disco/volumen, snapshots, backups y custodia de claves | Datos y copias cifrados; claves separadas y recuperables |
| DB-011 | P1 | Auditoría y logging | Revisar conexiones, fallas auth, DDL, lentas, retención, acceso y PII | Eventos útiles sin contraseñas, sentencias sensibles ni exceso de datos |
| DB-012 | P1 | Disponibilidad y límites | Revisar conexiones, timeouts, almacenamiento, autovacuum, alertas y réplica si aplica | Agotamiento y crecimiento detectados antes de indisponibilidad |
| DB-013 | P0 | Respaldo de PostgreSQL | Verificar frecuencia, cifrado, retención, inmutabilidad, separación y éxito real | Copias válidas conforme a RPO, fuera del host y protegidas contra borrado |
| DB-014 | P0 | Respaldo de filestore | Confirmar que DB y filestore se capturan en un punto consistente | Adjuntos y metadatos restauran juntos, sin huérfanos |
| DB-015 | P0 | Restauración | Restaurar en ambiente aislado, validar integridad, login, páginas y adjuntos; medir | RPO/RTO demostrados, no sólo declarados |
| DB-016 | P1 | Datos de no producción | Muestrear dumps/clones, anonimización, acceso y expiración | No se reutiliza PII real sin base y controles equivalentes |
| DB-017 | P1 | Retención y eliminación | Mapear tablas/adjuntos/logs a propósito y plazo; probar borrado o anonimización | Retención mínima, legal y técnicamente ejecutable |
| DB-018 | P1 | Cuentas de backup/replicación | Revisar atributos, red y almacenamiento de credenciales | Sólo privilegios técnicos requeridos, sin login interactivo innecesario |
| DB-019 | P1 | Integridad de filestore | Comparar muestra de `ir_attachment`, rutas, hashes/permisos y archivos huérfanos | Adjuntos íntegros, no navegables directamente y sin path traversal |
| DB-020 | P0 | Respuesta a compromiso | Ensayar rotación del rol DB, aislamiento y recuperación de claves | Playbook ejecutable sin pérdida de trazabilidad |

### 8.5 Gobierno, privacidad y respuesta

| ID | Pri. | Qué revisar | Procedimiento y evidencia | Resultado esperado |
|---|---:|---|---|---|
| GOV-001 | P1 | Inventario y responsables | Conciliar DNS, certificados, hosts, repos, runners, DB, backups y terceros | 100% de activos críticos con dueño |
| GOV-002 | P1 | Clasificación y flujo de datos | Diagramar cada dato desde captura hasta eliminación/terceros | Categoría, propósito, acceso, retención y base definidos |
| GOV-003 | P1 | Gestión de accesos | Revisar altas, cambios, bajas y recertificación | Baja inmediata y revisión trimestral de privilegios críticos |
| GOV-004 | P1 | Vulnerabilidades | Revisar fuentes, triage, SLA, excepciones y retest | Hallazgos con propietario, fecha y aceptación formal si aplica |
| GOV-005 | P0 | Incidentes | Ejercicio de compromiso de deploy key/DB/admin y fuga de datos | Contactos, contención, evidencia y comunicación probados |
| GOV-006 | P1 | Terceros | Revisar GA4, hosting y proveedores: datos, acceso, región, retención e incidentes | Riesgo y contrato acordes al dato compartido |
| GOV-007 | P1 | Continuidad | Alinear dependencias, RPO/RTO, capacidad y retorno a operación | Objetivos aprobados y demostrados mediante ejercicio |
| GOV-008 | P2 | Capacitación | Revisar entrenamiento por rol y simulaciones | Personal crítico conoce secretos, phishing, incidentes y cambios seguros |

## 9. Flujos de prueba prioritarios

### FLUJO-SEC-01 — Cambio a producción

1. Un desarrollador crea una rama sin acceso directo a producción.
2. El PR ejecuta pruebas, secretos, SAST, SCA y validación del artefacto.
3. Un revisor distinto aprueba; la rama protegida impide bypass.
4. El build genera hash, SBOM y referencia al commit.
5. El ambiente protegido solicita aprobación de producción.
6. El runner usa credenciales temporales o mínimas y valida host SSH.
7. El servidor valida artefacto, ruta, propietario y hash antes de usar privilegio.
8. Preflight, instalación/upgrade y postflight producen evidencia.
9. El despliegue registra actor, versión, hora y resultado sin secretos.
10. Ante falla, se restaura un conjunto consistente de código, DB y filestore.

Aceptación: ningún actor individual puede introducir y desplegar silenciosamente un cambio no revisado; la versión productiva es reproducible y recuperable.

### FLUJO-SEC-02 — Primera instalación y actualización

1. Crear una base limpia sintética y otra con la versión anterior.
2. Instalar el addon en la limpia mediante la operación de instalación de Odoo.
3. Actualizar el addon en la existente mediante la operación de upgrade.
4. Interrumpir de forma controlada antes y después de la migración.
5. Verificar que códigos de salida, servicio y logs indiquen el estado real.
6. Ejecutar rollback y comprobar consistencia funcional y de datos.

Aceptación: instalación, actualización y rollback son rutas distintas, probadas y observables.

### FLUJO-SEC-03 — Usuario anónimo y aislamiento multiwebsite

1. Acceder con sesión nueva por cada dominio/website autorizado.
2. Probar homepage, privacidad, agradecimiento, redirects, login y formularios.
3. Manipular host, parámetros, cookies y referencias de website con límites autorizados.
4. Confirmar que contenido, analítica, páginas y datos pertenecen al website correcto.
5. Verificar que usuario public no lee modelos ni campos no destinados al sitio.

Aceptación: no existe cruce de contenido/datos ni ampliación de privilegio por cambiar el contexto web.

### FLUJO-SEC-04 — Consentimiento y telemetría

1. Abrir navegador limpio con consentimiento ausente.
2. Confirmar que no se carga ni emite GA4.
3. Rechazar y repetir navegación, CTA, formulario y login.
4. Aceptar y confirmar únicamente eventos y parámetros aprobados.
5. Revocar consentimiento y verificar detención/borrado conforme a política.
6. Inspeccionar payloads para email, teléfono, nombre, IDs internos, URL sensible o texto libre.

Aceptación: no hay emisión previa/rechazada ni PII en analítica.

### FLUJO-SEC-05 — Compromiso de credencial de despliegue

1. Simular pérdida de deploy key sin usar una llave real comprometida.
2. Confirmar que la llave no permite shell general, otros hosts ni otros comandos `sudo`.
3. Revocar y rotar la credencial.
4. Buscar uso histórico y correlacionar SCM, CI, SSH y sudo.
5. Reemitir credencial mínima y probar recuperación.

Aceptación: contención dentro del RTO de seguridad, alcance limitado y trazabilidad completa.

### FLUJO-SEC-06 — Restauración y desastre

1. Seleccionar un punto de recuperación aprobado.
2. Restaurar PostgreSQL y filestore en red aislada.
3. Aplicar la versión exacta de código/configuración correspondiente.
4. Validar integridad, permisos, login, páginas, redirects, adjuntos y jobs.
5. Medir pérdida de datos y duración contra RPO/RTO.
6. Destruir de forma segura la copia temporal al cerrar la prueba.

Aceptación: restauración funcional demostrada, consistente y dentro de objetivos.

## 10. Catálogo de evidencia técnica de sólo lectura

Los siguientes ejemplos deben adaptarse a la distribución y ejecutarse únicamente por personal autorizado. La salida se redactará antes de adjuntarla.

### 10.1 Repositorio y archivos

```bash
git status --short
git log --show-signature --oneline -n 20
git ls-files
find financa_website deploy -xdev -type l -ls
find financa_website deploy -xdev -type f -printf '%m %u %g %p\n'
```

Escáneres sugeridos, sujetos a aprobación y disponibilidad: detector de secretos, Semgrep u otro SAST, análisis de dependencias/SBOM, ShellCheck y pruebas propias del repositorio. Guardar versión, reglas, exclusiones y resultado; no limitarse a “sin hallazgos”.

### 10.2 Host y red

```bash
cat /etc/os-release
uname -a
ss -lntup
systemctl cat odoo
systemctl show odoo
systemd-analyze security odoo
sshd -T
sudo -l -U <usuario_deploy>
stat /etc/odoo/odoo.conf /etc/financa/deploy.env /usr/local/sbin/financa-deploy
```

También obtener reglas de `nftables`/firewall, configuración efectiva del proxy y estado de parches. No anexar configuraciones completas si contienen secretos.

### 10.3 Configuración Odoo

Registrar sólo valores no secretos o redactados:

- `proxy_mode`, `dbfilter`, `list_db`, `db_name` y `db_sslmode`;
- interfaz/puerto de escucha;
- workers y límites;
- rutas de addons, data dir y logs;
- presencia y custodia de `admin_passwd`, nunca su valor;
- versión/commit y módulos instalados;
- administradores, grupos y cuentas inactivas mediante exportación protegida.

### 10.4 PostgreSQL

Consultas de metadatos de sólo lectura:

```sql
SELECT version();
SELECT current_database(), current_user;
SELECT rolname, rolsuper, rolcreatedb, rolcreaterole,
       rolreplication, rolbypassrls, rolcanlogin
FROM pg_roles ORDER BY rolname;
SELECT datname, pg_get_userbyid(datdba) AS owner
FROM pg_database WHERE datallowconn;
SELECT name, setting, source
FROM pg_settings
WHERE name IN ('listen_addresses','ssl','password_encryption',
               'log_connections','log_disconnections','log_min_duration_statement');
SELECT line_number, type, database, user_name, address, auth_method, error
FROM pg_hba_file_rules ORDER BY line_number;
SELECT extname, extversion FROM pg_extension ORDER BY extname;
```

Ejecutar con una cuenta de auditoría temporal y permisos mínimos. No consultar hashes de contraseñas, contenido de tablas ni valores de secretos salvo aprobación específica.

### 10.5 TLS y superficie web

Comprobar desde un origen autorizado:

- certificado, SAN, cadena, expiración, protocolos y redirección HTTP;
- headers de respuesta y caché;
- exposición de `/web/database`, páginas de debug y archivos de respaldo;
- cookies y comportamiento de consentimiento;
- límites de login y formularios sin generar carga significativa.

## 11. Hipótesis específicas del estado actual

Estas condiciones observadas en el repositorio deben abrirse como verificaciones, no como hallazgos definitivos:

| Ref. | Hipótesis a validar | Riesgo si se confirma | Control relacionado |
|---|---|---|---|
| H-01 | No existe todavía una definición versionada del job del proveedor CI; sólo el script de publicación | Checks y aprobaciones podrían no ejecutarse | CICD-002, 014, 016 |
| H-02 | La primera instalación podría intentar `-u` en lugar de `-i` | Instalación limpia fallida o estado incompleto | CICD-012 |
| H-03 | El rollback restaura código, pero no se observa restauración coordinada de DB/filestore | Incompatibilidad después de una migración parcial | CICD-013, DB-014/015 |
| H-04 | El ejemplo de sudoers acepta argumentos con wildcard | El usuario de deploy podría ampliar los parámetros autorizados | CICD-009/010 |
| H-05 | El JavaScript de tracking se incluye como activo frontend global | Captura de eventos fuera del website previsto | CODE-005/009 |
| H-06 | Todo acceso a `/web/login` puede clasificarse como CTA de header | Telemetría inexacta y decisiones erróneas | CODE-009 |
| H-07 | El postflight comprueba que GA4 esté configurado, no el ID aprobado ni ausencia de PII | Envío al destino equivocado o datos no autorizados | CODE-009, GOV-006 |
| H-08 | La indexación de homepage aparece habilitada de forma fija | Indexación prematura de staging/ambiente equivocado | CODE-005, SRV-020 |
| H-09 | Las pruebas actuales son principalmente contratos estáticos | Regresiones de seguridad de Odoo no detectadas | CODE-013 |
| H-10 | El footer usa una consulta con `sudo()` para estado de la página legal | Elevación innecesaria o fuga de estado entre websites | CODE-005/006 |

## 12. Severidad, tratamiento y SLA propuesto

Calcular probabilidad e impacto de 1 a 5. Riesgo inherente = probabilidad × impacto:

| Puntaje | Nivel | Tratamiento propuesto |
|---:|---|---|
| 20–25 | Crítico | Contener en 24 h; bloquear despliegue; corregir objetivo ≤ 7 días |
| 12–19 | Alto | Plan en 5 días hábiles; corregir objetivo ≤ 30 días |
| 6–11 | Medio | Corregir objetivo ≤ 60 días |
| 1–5 | Bajo | Corregir objetivo ≤ 90 días o aceptar formalmente |

Cada hallazgo debe contener: activo, escenario, evidencia redactada, condición, causa raíz, impacto, probabilidad, severidad, recomendación verificable, propietario, fecha objetivo y prueba de cierre. CVSS puede agregarse para vulnerabilidades técnicas, pero la decisión final incorpora exposición, datos y continuidad del negocio.

La aceptación de riesgo requiere propietario ejecutivo, justificación, controles compensatorios y fecha de caducidad. No se permite aceptación indefinida.

## 13. Criterios de liberación y cierre

Una liberación de producción se bloquea cuando:

- existe un hallazgo crítico abierto;
- existe un alto explotable desde Internet sin control compensatorio probado;
- aparecen secretos válidos en código, logs o artefactos;
- no puede vincularse el artefacto a un commit aprobado;
- el rol de aplicación tiene privilegios administrativos innecesarios;
- la base o el gestor de bases Odoo está expuesto públicamente;
- no existe un respaldo consistente de DB/filestore o la restauración no ha sido demostrada para un cambio con migración;
- el despliegue privilegiado admite comandos/rutas no previstos.

La auditoría cierra cuando:

1. se ejecutó el 100% de controles P0 y P1 aplicables;
2. los no aplicables tienen justificación aprobada;
3. críticos y altos están corregidos, contenidos o aceptados formalmente;
4. cada corrección tiene retest independiente;
5. inventario, evidencias, reporte y backlog están entregados;
6. el riesgo residual fue aceptado por el dueño del servicio.

## 14. Entregables

- Acta de alcance y reglas de ejecución.
- Inventario de activos, identidades, datos y terceros.
- Diagrama de arquitectura y flujo de datos.
- Matriz de controles con estado: Conforme / Parcial / No conforme / No aplica.
- Índice de evidencia redactada y hashes.
- Registro de hallazgos y riesgo.
- Informe ejecutivo con exposición y decisión de liberación.
- Informe técnico con reproducción y causa raíz.
- Plan de remediación con propietario y fecha.
- Resultado de restauración y medición RPO/RTO.
- Informe de retest y dictamen de cierre.

## 15. Calendario base

Estimación para un auditor con apoyo puntual de Desarrollo, DevOps y DBA; ajustar tras inventario:

| Día | Trabajo |
|---:|---|
| 1 | Autorización, inventario, datos, arquitectura y amenazas |
| 2 | Código, dependencias, secretos y pruebas de aplicación |
| 3 | SCM, CI/CD, runner, artefacto, SSH, sudo y rollback |
| 4 | Host, red, TLS, proxy, systemd y configuración Odoo |
| 5 | PostgreSQL, filestore, respaldos y ejercicio de restauración |
| 6 | Validación web controlada, correlación y análisis de riesgo |
| 7 | Informe, mesa de hallazgos y plan de remediación |

El retest se programa cuando estén disponibles las correcciones; no se considera incluido automáticamente en los siete días.

## 16. Cadencia operativa después de la auditoría

| Frecuencia | Control mínimo |
|---|---|
| Cada commit/PR | Tests, secretos, SAST, SCA, lint y revisión |
| Cada release | SBOM/hash, aprobación, pre/postflight, vulnerabilidades y rollback preparado |
| Diario | Disponibilidad, errores, disco, backups y alertas de autenticación |
| Semanal | Parches críticos, fallas CI, eventos privilegiados y anomalías |
| Mensual | Vulnerabilidades, certificados, dependencias y exposición externa |
| Trimestral | Recertificación de accesos, rotación basada en riesgo y restore parcial/completo alternado |
| Anual | Auditoría integral y simulacro de incidente/continuidad |
| Por evento | Auditoría tras incidente, cambio arquitectónico, migración o nuevo tercero |

## 17. Primer ciclo recomendado

Orden de ejecución por reducción de riesgo:

1. Confirmar exposición de PostgreSQL y del gestor de bases Odoo.
2. Auditar usuarios administrativos, SSH, deploy key y `sudoers`.
3. Validar que el rol PostgreSQL de Odoo no sea superusuario ni creador de bases.
4. Probar restauración consistente de DB y filestore.
5. Corregir/probar instalación limpia y rollback posterior a migración.
6. Incorporar el pipeline versionado con ramas/ambientes protegidos.
7. Añadir escaneo de secretos, SAST, SCA/SBOM y checks bloqueantes.
8. Validar aislamiento multiwebsite, `sudo()` y tracking/consentimiento.
9. Aplicar baseline de host, TLS, proxy, systemd, logging y alertas.
10. Retestar P0/P1 y emitir la decisión de liberación.

## 18. Aprobación

| Rol | Nombre | Decisión | Fecha | Firma/referencia |
|---|---|---|---|---|
| Patrocinador |  | Aprobar / Rechazar |  |  |
| Dueño del servicio |  | Aprobar / Rechazar |  |  |
| Desarrollo |  | Enterado |  |  |
| DevOps |  | Enterado |  |  |
| DBA |  | Enterado |  |  |
| Seguridad/Privacidad |  | Aprobar / Rechazar |  |  |
