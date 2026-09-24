# Plan maestro, matriz y casos de prueba — `financa_website`

## 1. Control del documento

| Campo | Valor |
| --- | --- |
| Proyecto | Website corporativo Financa Consultores |
| Módulo | `financa_website` para Odoo 19 Community |
| Versión bajo prueba | `19.0.1.0.0` |
| Estado del documento | Línea base para ejecución |
| Fecha | 2026-08-16 |
| Fuente funcional | `SPEC_financa_website.md` |
| Enfoque | Pruebas basadas en riesgo y trazabilidad requisito–caso–evidencia |
| Objetivo de accesibilidad | WCAG 2.2 nivel AA |
| Responsable de aprobación | Product Owner Financa + responsable técnico + responsable legal cuando aplique |

## 2. Propósito

Definir cómo verificar que `financa_website` puede instalarse, actualizarse y operar en Odoo 19 sin afectar otros websites, que la experiencia pública convierte correctamente, que la edición nativa permanece funcional y que cookies, analítica, privacidad, seguridad, SEO, accesibilidad y despliegue cumplen el contrato del proyecto.

Este documento reúne en un solo lugar:

- plan y estrategia de pruebas;
- casos de uso y sus flujos principales y alternos;
- matriz de trazabilidad;
- matriz ejecutable de casos de prueba;
- criterios de entrada, suspensión, salida y liberación;
- evidencias y reporte de defectos.

## 3. Referencias y estándares

- [ISO/IEC/IEEE 29119](https://committee.iso.org/sites/jtc1sc7/home/projects/flagship-standards/isoiecieee-29119-series.html): procesos, documentación, diseño y ejecución de pruebas.
- [ISTQB CTFL 4.0.1](https://istqb.org/wp-content/uploads/2024/11/ISTQB_CTFL_Syllabus_v4.0.1.pdf): planificación continua, trazabilidad y pruebas basadas en riesgo.
- [Pruebas en Odoo 19](https://www.odoo.com/documentation/19.0/developer/reference/backend/testing.html): `TransactionCase`, `HttpCase`, pruebas JavaScript HOOT y tours de integración.
- [OWASP Web Security Testing Guide](https://owasp.org/www-project-web-security-testing-guide/latest/): configuración, autenticación, autorización, sesiones, validación y cliente web.
- [OWASP ASVS 5.0](https://owasp.org/www-project-application-security-verification-standard/): controles verificables de seguridad web.
- [WCAG 2.2](https://www.w3.org/TR/WCAG22/): accesibilidad; se adopta nivel AA.
- [Google Analytics 4: eventos](https://developers.google.com/analytics/devguides/collection/ga4/events): validación mediante Realtime y DebugView.
- [Core Web Vitals](https://web.dev/articles/vitals): LCP, INP y CLS como indicadores de experiencia.

## 4. Alcance

### 4.1 Incluido

- instalación limpia, actualización e idempotencia del módulo;
- preflight, configuración, postflight, publicación CI y recuperación;
- resolución del website por dominio y aislamiento multiwebsite;
- homepage, redirección 301, navegación, header y footer globales;
- siete snippets y edición con Website Builder;
- diseño responsive, compatibilidad y ausencia de desbordamiento;
- autenticación nativa y separación de usuarios público, portal e interno;
- formulario de contacto, redirección y confirmación deduplicada de lead;
- cookies, privacidad, GA4, protección de datos y A/B desactivado;
- SEO técnico, indexación por ambiente y página legal;
- accesibilidad WCAG 2.2 AA;
- seguridad web proporcional al alcance del módulo;
- rendimiento, carga de assets y errores de cliente/servidor;
- smoke test de producción y aceptación de negocio.

### 4.2 Fuera de alcance

- pruebas funcionales profundas de módulos Odoo no modificados;
- pentest de infraestructura completa o denegación de servicio;
- exactitud jurídica del aviso, que requiere aprobación legal;
- funcionamiento interno de GA4 como producto de Google;
- ejecución o evaluación estadística de experimentos A/B, porque permanecen desactivados;
- landing pages futuras, CRM personalizado e integraciones no incluidas en el módulo.

## 5. Estrategia de pruebas

### 5.1 Niveles y herramientas

| Nivel | Objetivo | Ejecución recomendada | Gate |
| --- | --- | --- | --- |
| Estático | Manifest, XML, convenciones, secretos, dependencias y contratos | `unittest`, parser XML, `bash -n`, revisión y escaneo de secretos | Cada commit |
| Componente | Lógica JavaScript de consentimiento, deduplicación, tracking y animación | HOOT con DOM y `gtag` simulados | Pull request |
| Integración Odoo | ORM, páginas, website específico, menús, rewrite y configuración | `TransactionCase` / `HttpCase` con `--test-tags` | Build de QA |
| Sistema web | Navegación, formulario, cookies, editor y roles en navegador | Tour Odoo o navegador automatizado | Staging |
| No funcional | Seguridad, WCAG, SEO, compatibilidad y rendimiento | Lighthouse/axe, DevTools, HTTP, revisión manual | Staging |
| UAT | Mensaje, contenido, identidad y flujo comercial | Product Owner y responsable legal | Preproducción |
| Producción | Disponibilidad y configuración mínima sin alterar datos | Smoke read-only + envío controlado autorizado | Postdespliegue |

### 5.2 Política de automatización

- Automatizar P1 y regresiones deterministas que no dependan de GA4 externo ni juicio visual.
- Mantener manuales las pruebas de DebugView, contenido comercial, validación jurídica y revisión visual final.
- Ejecutar casos Odoo dentro de `financa_website/tests/`; Odoo no descubre automáticamente las pruebas contractuales ubicadas solo en `/tests`.
- Usar `HttpCase` o tours para probar servidor y JavaScript juntos; una búsqueda textual no sustituye el renderizado real.
- No automatizar ataques destructivos contra producción. Seguridad activa se ejecuta en QA o staging.

### 5.3 Prioridades

| Prioridad | Regla | Ejemplos |
| --- | --- | --- |
| P1 crítica | Impacto legal, pérdida de leads, website equivocado, indisponibilidad o despliegue irrecuperable | multiwebsite, instalación, formulario, consentimiento, rollback |
| P2 alta | Afecta conversión, edición, acceso, SEO o experiencia mayoritaria | snippets, responsive, roles, indexación, analítica |
| P3 media | Degradación acotada con alternativa disponible | compatibilidad secundaria, detalles visuales, documentación |

## 6. Análisis de riesgos

Escala: probabilidad e impacto de 1 a 5. Exposición = probabilidad × impacto.

| Riesgo | P | I | Exposición | Mitigación mediante pruebas |
| --- | ---: | ---: | ---: | --- |
| El despliegue modifica el website homónimo incorrecto | 4 | 5 | 20 | MW-001 a MW-004, DEP-001 y DEP-002 |
| La instalación limpia no instala el módulo o deja el servicio inconsistente | 4 | 5 | 20 | DEP-003, DEP-004, DEP-006 y REC-001 |
| Se pierde o duplica una conversión | 4 | 5 | 20 | FORM-001 a FORM-004 y ANA-003 |
| Se envían datos o eventos sin consentimiento | 4 | 5 | 20 | CONS-001 a CONS-003 y ANA-001/002 |
| El rollback restaura código pero no el estado de base de datos | 3 | 5 | 15 | REC-001 |
| Staging queda indexado o se genera contenido duplicado | 3 | 4 | 12 | SEO-001 y SEO-002 |
| Website Builder rompe snippets o elimina atributos de medición | 3 | 4 | 12 | BLD-001, BLD-002 y ANA-001 |
| La experiencia móvil o accesible impide convertir | 3 | 4 | 12 | UI-003 y A11Y-001 a A11Y-003 |
| Un error JavaScript bloquea la página o contamina otros websites | 3 | 4 | 12 | UI-004, MW-004, ANA-002 y PERF-002 |
| Configuración GA4 pertenece a otro website | 3 | 4 | 12 | ANA-004 |

## 7. Ambientes, navegadores y datos

### 7.1 Ambientes

| Ambiente | Uso | Datos | Restricciones |
| --- | --- | --- | --- |
| CI efímero | Estático, componente e instalación limpia | Base Odoo mínima sin datos reales | Sin Analytics real; indexación desactivada |
| QA | Integración, roles, negativos y editor | Copia sintética con dos websites homónimos | Correo capturado; sin indexación |
| Staging | Sistema, GA4 DebugView, UAT, seguridad y rendimiento | Copia anonimizada o sintética | Mismo proxy/configuración de producción; noindex |
| Producción | Smoke y monitoreo | Datos reales | Cambios y formularios solo con autorización y limpieza posterior |

### 7.2 Datos mínimos

| Dato | Valor o condición |
| --- | --- |
| Website objetivo | Nombre `Financa Consultores`, dominio `https://financa-mx` o dominio confirmado del ambiente |
| Website control | Mismo nombre, dominio diferente, contenido y homepage distinguibles |
| Usuario público | Sesión anónima limpia |
| Usuario portal | Invitado con acceso portal y sin aplicaciones internas |
| Usuario interno | Acceso limitado y grupos conocidos |
| Editor | Grupo Website Designer |
| Formulario válido | Nombre QA, correo controlado, teléfono ficticio, asunto y mensaje sin datos reales |
| Formulario malicioso | Cadenas XSS inertes, longitudes límite y caracteres internacionales |
| Consentimiento | Sin decisión, solo esenciales, opcionales aceptadas y revocadas |
| GA4 | Propiedad de prueba/DebugView y `gtag` inspeccionable |
| Homepage previa | Página específica recuperable para probar preflight y rollback |

No usar nombres, correos, teléfonos ni mensajes de clientes reales en QA.

### 7.3 Matriz de compatibilidad

- Escritorio: Chrome, Edge y Firefox en versión actual y anterior; Safari actual y anterior.
- Móvil: Safari iOS actual y Chrome Android actual.
- Viewports mínimos: 360×800, 390×844, 768×1024 y 1440×900.
- Teclado solamente, zoom 200 % y preferencia `prefers-reduced-motion: reduce`.

## 8. Roles

| Rol | Responsabilidad |
| --- | --- |
| QA | Preparar datos, ejecutar, conservar evidencia y gestionar defectos |
| Desarrollo Odoo | Automatización, corrección y apoyo técnico |
| DevOps | CI, backup, despliegue, rollback, logs y observabilidad |
| Product Owner | UAT, copy, navegación y aceptación comercial |
| Legal/Privacidad | Aviso de privacidad, cookies y datos públicos |
| Analítica/Marketing | GA4, dimensiones, evento clave y validación del embudo |

## 9. Casos de uso y flujos

### UC-01 — Instalar o actualizar el website

**Actor:** DevOps.
**Precondición:** artifact identificado, backup válido, configuración del ambiente y website objetivo resoluble.

**Flujo principal:**

1. Publicar el artifact en staging remoto.
2. Ejecutar preflight y confirmar un único website por dominio.
3. Instalar si el módulo está `uninstalled`; actualizar si está `installed`.
4. Aplicar configuración posterior.
5. Ejecutar postflight y smoke.
6. Iniciar el servicio y registrar evidencia de versión.

**Alternos:** dominio inexistente/duplicado, homepage previa no archivada, GA4 requerido ausente, fallo de actualización o postflight; en todos esos casos se detiene la liberación y se recupera de forma coherente código y base.

### UC-02 — Visitar y navegar el sitio

**Actor:** visitante público.

**Flujo principal:**

1. Abrir `/` en el dominio Financa.
2. Comprender propuesta, servicios, Odoo, diagnóstico y proceso.
3. Navegar mediante header, anclas y footer.
4. Elegir `Solicitar diagnóstico` o `Ver soluciones Odoo`.
5. Llegar al destino sin errores, saltos ni pérdida de contexto.

**Alternos:** móvil, teclado, movimiento reducido, Analytics bloqueado, JavaScript parcialmente no disponible y entrada por URL histórica.

### UC-03 — Solicitar un diagnóstico

**Actor:** prospecto.

**Flujo principal:**

1. Hacer clic en un CTA instrumentado.
2. Abrir `/contactus` y comenzar el formulario.
3. Completar datos válidos y enviar.
4. Odoo confirma la creación/envío.
5. Redirigir a `/gracias-diagnostico?financa_submission=1`.
6. Registrar exactamente un `generate_lead` si existe consentimiento.

**Alternos:** campos inválidos, error de servidor, doble clic, recarga directa de gracias, consentimiento rechazado o Analytics bloqueado. Ningún alterno debe producir un falso lead.

### UC-04 — Acceder como cliente o usuario interno

**Actor:** visitante, portal o usuario interno.

**Flujo principal:**

1. Seleccionar `Acceso a clientes`.
2. Autenticarse mediante `/web/login` nativo.
3. Recibir únicamente menús y recursos autorizados por Odoo.
4. Cerrar sesión y regresar al estado público.

**Alternos:** credenciales inválidas, usuario portal intentando backend y registro público no invitado.

### UC-05 — Editar contenido con Website Builder

**Actor:** Website Designer.

**Flujo principal:**

1. Abrir la homepage en modo edición.
2. Editar texto, mover o insertar un snippet Financa.
3. Guardar y recargar.
4. Revisar escritorio y móvil.
5. Confirmar que persisten estructura, clases, atributos analíticos y responsive.

**Alternos:** cancelar cambios, duplicar/eliminar snippets y editar páginas legales. El modo editor no debe enviar eventos de negocio.

### UC-06 — Gestionar consentimiento y medir el embudo

**Actor:** visitante y responsable de analítica.

**Flujo principal:**

1. Entrar sin cookie previa: no emitir eventos opcionales.
2. Aceptar cookies opcionales.
3. Navegar por secciones, CTA, contacto y formulario.
4. Verificar eventos y parámetros en DebugView/Realtime.
5. Confirmar deduplicación y ausencia de PII.

**Alternos:** aceptar durante la sesión, rechazar, revocar, bloquear `gtag` o editar el website. El sitio debe seguir funcionando.

### UC-07 — Publicar contenido legal y SEO

**Actor:** editor, responsable SEO y Legal.

**Flujo principal:**

1. Mantener el aviso provisional sin publicar y sin indexar.
2. Completar datos, obtener aprobación jurídica y retirar marcadores.
3. Publicar el aviso.
4. Confirmar que aparece su enlace en el footer.
5. Validar metadatos, canónica, sitemap, robots e imagen social.

**Alterno:** si falta un dato o aprobación, el aviso permanece oculto y el despliegue público continúa sin inventar información.

### UC-08 — Recuperar un despliegue fallido

**Actor:** DevOps.

**Flujo principal:**

1. Detectar fallo en actualización, configuración o postflight.
2. Detener la liberación.
3. Restaurar addon y base al mismo punto de recuperación.
4. Iniciar servicio con la versión anterior.
5. Ejecutar smoke y documentar incidente.

**Alterno:** si no puede probarse consistencia, mantener el servicio detenido o en mantenimiento y escalar; no declarar rollback exitoso solo porque se restauró la carpeta.

## 10. Requisitos verificables

| ID | Requisito resumido |
| --- | --- |
| RQ-01 | Instalar, actualizar y validar el módulo sin errores |
| RQ-02 | Seleccionar exactamente el website objetivo y no alterar el homónimo |
| RQ-03 | Servir `/` y redirigir `/financa-consultores` con 301 aislado |
| RQ-04 | Renderizar contenido, navegación, header y footer definidos |
| RQ-05 | Proporcionar siete snippets editables y reutilizables |
| RQ-06 | Conservar sesión, permisos y cuenta por invitación nativos |
| RQ-07 | Funcionar de forma responsive, compatible y accesible |
| RQ-08 | Cumplir SEO, canónica e indexación por ambiente |
| RQ-09 | Usar cookies y privacidad nativas sin publicar marcadores |
| RQ-10 | Confirmar leads reales una sola vez y sin falsos positivos |
| RQ-11 | Medir el embudo con consentimiento, sin PII y sin duplicar el tag |
| RQ-12 | Mantener A/B desactivado en la primera publicación |
| RQ-13 | Mantener seguridad web y aislamiento de datos/sesiones |
| RQ-14 | Cumplir rendimiento y estabilidad operacional |
| RQ-15 | Recuperar un despliegue fallido de forma coherente |

## 11. Matriz de trazabilidad

| Requisito | Casos | Gate principal |
| --- | --- | --- |
| RQ-01 | DEP-001 a DEP-006 | CI + QA |
| RQ-02 | MW-001 a MW-004 | QA |
| RQ-03 | MW-003, WEB-001, SEO-002 | QA + staging |
| RQ-04 | WEB-002, WEB-003, UI-001 a UI-004, UAT-001 | Navegador/UAT |
| RQ-05 | BLD-001, BLD-002 | Tour/editor |
| RQ-06 | AUTH-001 a AUTH-004 | QA |
| RQ-07 | UI-003, UI-004, A11Y-001 a A11Y-003, COMP-001 | Staging |
| RQ-08 | SEO-001 a SEO-003 | Staging |
| RQ-09 | CONS-001 a CONS-003, LEGAL-001 a LEGAL-003 | Staging/UAT |
| RQ-10 | FORM-001 a FORM-004 | Tour + GA4 |
| RQ-11 | ANA-001 a ANA-004 | Staging/DebugView |
| RQ-12 | EXP-001 | CI + navegador |
| RQ-13 | SEC-001 a SEC-003, AUTH-002 a AUTH-004 | QA/staging |
| RQ-14 | PERF-001, PERF-002, PROD-001 | Staging/producción |
| RQ-15 | REC-001 | Ensayo de recuperación |

## 12. Matriz ejecutable de casos de prueba

Leyenda de automatización: **A** automatizada, **M** manual, **H** híbrida.

### 12.1 Despliegue e instalación

| ID | P | Auto | Flujo de prueba | Resultado esperado y evidencia |
| --- | --- | --- | --- | --- |
| DEP-001 | P1 | A | Preparar exactamente un website con dominio objetivo y cuenta `b2b`; ejecutar preflight. | Código 0; JSON identifica website, nombre, dominio, favicon, política de cuenta y homepage. Guardar stdout y log. |
| DEP-002 | P1 | A | Ejecutar preflight con cero websites, dos websites para el dominio, nombre incorrecto, cuenta distinta de `b2b` y homepage previa específica sin archivar. | Cada variante termina antes del swap con código distinto de 0 y mensaje accionable; no cambia addon, servicio ni base. |
| DEP-003 | P1 | A | Partir de módulo `uninstalled`; publicar artifact; ejecutar flujo completo; consultar `ir.module.module`. | Se usa instalación, no solo actualización; estado final `installed`, versión correcta, páginas y assets creados. Evidencia: logs y consulta ORM. |
| DEP-004 | P1 | A | Con módulo instalado, editar un contenido permitido, actualizar dos veces la misma versión y comparar conteos/IDs. | No duplica websites, páginas, menús ni rewrites; conserva edición permitida o documenta claramente qué datos XML se reponen. |
| DEP-005 | P1 | A | Ejecutar configuración con GA4 requerido presente y ausente; revisar cookie bar y website objetivo/control. | Con GA4 correcto activa cookies solo en objetivo; si falta, falla sin declarar despliegue exitoso; website control intacto. |
| DEP-006 | P1 | A | Tras instalación/actualización ejecutar postflight y provocar ausencia de homepage, privacidad publicada, rewrite duplicado y cookies apagadas. | Caso sano pasa; cada anomalía falla con mensaje específico y evidencia JSON suficiente. |

### 12.2 Aislamiento multiwebsite, rutas y layout

| ID | P | Auto | Flujo de prueba | Resultado esperado y evidencia |
| --- | --- | --- | --- | --- |
| MW-001 | P1 | A | Crear dos websites con el mismo nombre y dominios distintos; instalar; consultar `website.page`, `website.menu`, `website.rewrite` e `ir.ui.view`. | Todos los registros Financa dependientes del sitio apuntan al ID resuelto por dominio; no se crea un tercer website. |
| MW-002 | P1 | H | Abrir `/` en dominio objetivo y control antes/después del despliegue; comparar contenido, homepage y respuesta. | Solo objetivo muestra homepage Financa; control conserva página, menús y estilo originales. Capturas y respuestas HTTP. |
| MW-003 | P1 | H | Solicitar `/financa-consultores` en ambos dominios, con y sin slash/query; seguir redirecciones. | Objetivo responde 301 hacia `/` sin ciclo; control no hereda la regla; no existe contenido 200 duplicado en la ruta antigua. |
| MW-004 | P1 | H | Navegar homepage, contacto, gracias, cookies y privacidad en ambos sitios; observar header/footer, eventos y consola. | Footer/CTA/clases/eventos Financa aparecen solo en objetivo; el asset global no contamina Analytics del website control. |
| WEB-001 | P1 | A | Solicitar `/` como público y verificar página, `website.layout`, publicación y website. | HTTP 200; página publicada, marcada como homepage del objetivo y una sola estructura principal. |
| WEB-002 | P2 | H | Abrir cada enlace de header/footer y cada ancla desde `/` y desde `/contactus`. | Destinos correctos; las rutas `/#...` funcionan desde otras páginas; no hay 404 ni anclas ocultas por header. |
| WEB-003 | P2 | H | Contar header/footer visibles en homepage, contacto, gracias y legal. | Exactamente un header y un footer global por página cuando no se solicitan ocultos. |

### 12.3 Contenido, responsive y JavaScript

| ID | P | Auto | Flujo de prueba | Resultado esperado y evidencia |
| --- | --- | --- | --- | --- |
| UI-001 | P2 | H | Comparar hero, cuatro servicios, mapa Odoo, antes/después, diagnóstico, cinco pasos, CTA y footer contra el SPEC. | Copy esencial y orden correctos; cifras se identifican como ilustrativas; no faltan secciones. |
| UI-002 | P2 | A | Inspeccionar CTA hero, diagnóstico, final y header; activar `Ver soluciones Odoo`. | Diagnósticos llevan a `/contactus`; soluciones desplaza a `#odoo-erp`; cada CTA tiene atributos analíticos completos. |
| UI-003 | P2 | H | Probar viewports definidos, orientación horizontal, zoom 200 % y textos largos; revisar scroll horizontal. | Grid 2×2 pasa a una columna bajo 768 px; contenido refluye sin corte, superposición ni scroll horizontal. Capturas. |
| UI-004 | P2 | A | Cargar páginas sin secciones Financa, sin `IntersectionObserver`, sin `gtag`, con storage bloqueado y con movimiento reducido. | Sin excepciones; navegación funciona; elementos quedan visibles; no se anima cuando se solicita movimiento reducido. Consola limpia. |

### 12.4 Website Builder

| ID | P | Auto | Flujo de prueba | Resultado esperado y evidencia |
| --- | --- | --- | --- | --- |
| BLD-001 | P2 | H | Entrar como editor; localizar los siete snippets; insertar uno de cada tipo en página temporal; guardar y recargar. | Los siete aparecen, renderizan y persisten; no duplican `H1` sin advertencia en una misma página; no hay error de assets/QWeb. |
| BLD-002 | P1 | H | Editar texto, mover y duplicar sección; guardar; revisar DOM y móvil; volver a editar. | La página sigue editable y responsive; sobreviven `data-financa-section`/CTA; animaciones y navegación no se rompen. |

### 12.5 Autenticación y autorización

| ID | P | Auto | Flujo de prueba | Resultado esperado y evidencia |
| --- | --- | --- | --- | --- |
| AUTH-001 | P2 | H | Como público seleccionar `Acceso a clientes`; cancelar y autenticar con credenciales válidas. | Usa `/web/login` nativo, HTTPS y sesión Odoo; no existe formulario de autenticación propio. |
| AUTH-002 | P1 | H | Autenticar usuario portal; intentar URL de backend y aplicaciones no autorizadas. | Portal accede solo a recursos permitidos; no obtiene menús ni datos internos. Registrar respuestas sin guardar secretos. |
| AUTH-003 | P2 | H | Autenticar usuario interno con grupos limitados; abrir backend y volver al sitio. | Solo ve aplicaciones de sus grupos; menú de usuario y sesión estándar funcionan. |
| AUTH-004 | P1 | A | Consultar configuración de cuenta; intentar registro público no invitado. | `auth_signup_uninvited == "b2b"`; el módulo no habilita registro libre ni cambia la política del website control. |

### 12.6 Formulario y confirmación de lead

| ID | P | Auto | Flujo de prueba | Resultado esperado y evidencia |
| --- | --- | --- | --- | --- |
| FORM-001 | P1 | H | Abrir contacto desde CTA; enfocar/cambiar campos; enviar vacío, email inválido y límites definidos. | Errores accesibles; no hay redirección, registro exitoso ni `generate_lead`; `form_start` se emite máximo una vez con consentimiento. |
| FORM-002 | P1 | H | Con consentimiento, completar datos sintéticos válidos y enviar una vez. | Odoo confirma éxito y redirige a `/gracias-diagnostico?financa_submission=1`; se emite un `generate_lead` con `lead_source` y `form_name`. |
| FORM-003 | P1 | H | Simular error HTTP/servidor, timeout y doble clic durante envío. | Se informa fallo y se permite reintento seguro; no hay redirección ni conversión falsa; un éxito crea una sola solicitud. |
| FORM-004 | P1 | A | Abrir gracias directamente, con query fabricado, desde otro referrer, recargar tras éxito y volver con historial. | Ningún acceso inválido genera lead; recargar/revisitar no duplica; la página siempre permanece no indexada. |

### 12.7 Cookies, analítica y experimentación

| ID | P | Auto | Flujo de prueba | Resultado esperado y evidencia |
| --- | --- | --- | --- | --- |
| CONS-001 | P1 | H | Limpiar cookies/storage; abrir sitio y navegar sin elegir; repetir aceptando solo esenciales. | No se envían eventos Financa ni se crean marcadores de atribución opcionales; sitio y formulario funcionan. Network + storage. |
| CONS-002 | P1 | H | Aceptar opcionales sin recargar; observar sección visible, CTA, contacto y formulario. | Tracking se habilita durante la sesión sin romper navegación; cookie contiene `required`, `optional` y timestamp válidos. |
| CONS-003 | P1 | H | Tras aceptar, reabrir preferencias y negar; continuar navegando. | Eventos posteriores cesan y storage pendiente Financa se elimina; no se genera conversión residual. |
| ANA-001 | P1 | A | Simular `gtag`; provocar sección, CTA, contacto, inicio, login, exposición simulada y lead; repetir interacciones. | Cada evento permitido tiene nombre/parámetros estables y `page_path`; secciones, formulario, exposición y lead se deduplican según contrato. |
| ANA-002 | P1 | H | Introducir nombre, email, teléfono y mensaje centinela; inspeccionar dataLayer/network; repetir en modo editor. | Ningún valor ni identificador personal sale en eventos; editor no emite eventos de negocio; no se codifica ID GA4 en assets. |
| ANA-003 | P1 | M | Ejecutar embudo completo en GA4 DebugView/Realtime con consentimiento. | Orden y conteo coherentes: visita → sección → CTA → contacto → formulario → un lead; parámetros visibles y tag base cargado una vez. |
| ANA-004 | P2 | M | Comparar `google_analytics_key`, website ID y propiedad GA4; revisar dimensiones y evento clave. | ID corresponde al dominio objetivo; parámetros requeridos están registrados como dimensiones y `generate_lead` como evento clave. Evidencia administrativa. |
| EXP-001 | P1 | A | Cargar varias sesiones con y sin consentimiento; inspeccionar DOM, cookies, storage y eventos. | `EXPERIMENTS_ENABLED` sigue falso; no cambia contenido, no asigna/persiste variante y no emite exposición. |

### 12.8 SEO, cookies y privacidad legal

| ID | P | Auto | Flujo de prueba | Resultado esperado y evidencia |
| --- | --- | --- | --- | --- |
| SEO-001 | P2 | A | Inspeccionar HTML de `/`: title, description, canonical, robots, headings y alternativas textuales. | Metadatos coinciden con SPEC; canónica termina en `/`; un `H1`; jerarquía coherente; imágenes informativas tienen alternativa. |
| SEO-002 | P1 | H | Revisar ruta anterior, sitemap y robots en QA y producción; solicitar página gracias/legal. | QA no indexa; producción indexa solo lo aprobado; ruta antigua es 301; gracias y privacidad provisional llevan `noindex`. |
| SEO-003 | P2 | H | Compartir/depurar URL con herramienta social o inspeccionar Open Graph/Twitter. | Existe imagen social provisional o aprobada con URL accesible, título y descripción correctos; favicon existente no fue sustituido. |
| LEGAL-001 | P1 | A | Instalar con marcadores; solicitar privacidad como público y editor; revisar footer. | Página existe y es editable, pero no publicada/indexada; público no ve enlace; editor conserva advertencia y marcadores. |
| LEGAL-002 | P1 | H | Tras aprobación en staging, reemplazar marcadores, publicar y recargar páginas; volver a despublicar. | Enlace aparece solo publicada y en todo el website objetivo; desaparece al despublicar; nunca afecta website control. |
| LEGAL-003 | P2 | H | Activar cookies; abrir `/cookie-policy`, editar texto y recargar. | Página nativa accesible/editable y enlazada en footer; documenta servicios/cookies realmente usados. |

### 12.9 Accesibilidad

| ID | P | Auto | Flujo de prueba | Resultado esperado y evidencia |
| --- | --- | --- | --- | --- |
| A11Y-001 | P2 | H | Recorrer header, CTA, anclas, formulario, cookies y footer solo con teclado; usar lector de pantalla básico. | Orden lógico, foco visible/no oculto, controles activables y nombres/roles comprensibles; sin trampa de teclado. |
| A11Y-002 | P2 | H | Ejecutar auditor automático y revisión semántica: landmarks, headings, listas, labels, errores, alt y dashboard. | Cero violaciones críticas/serias sin excepción aprobada; estructura y errores son perceptibles; decorativos quedan ocultos correctamente. |
| A11Y-003 | P2 | H | Medir contraste, zoom 200 %, reflow 320 CSS px, objetivos táctiles y movimiento reducido. | Cumple WCAG 2.2 AA aplicable; contenido no depende de hover/color/movimiento y no pierde funcionalidad. Reporte y capturas. |

### 12.10 Seguridad y privacidad técnica

| ID | P | Auto | Flujo de prueba | Resultado esperado y evidencia |
| --- | --- | --- | --- | --- |
| SEC-001 | P1 | H | Revisar HTTPS, headers, cookies de sesión/consentimiento, métodos y páginas sensibles siguiendo OWASP WSTG. | Sin credenciales por HTTP; sesión conserva atributos seguros definidos por Odoo/proxy; no se exponen backups, listados o errores detallados. |
| SEC-002 | P1 | H | En QA enviar payloads XSS inertes y caracteres especiales por formulario/editor; visualizar resultados donde corresponda. | Entrada se valida/escapa; no ejecuta script ni altera DOM; CSRF nativo sigue activo; no hay SQL/error interno expuesto. |
| SEC-003 | P1 | A | Escanear repo, bundle, HTML, dataLayer y storage por secretos, ID GA4 codificado y PII centinela. | Sin claves, credenciales, datos reales ni PII analítica; storage contiene solo tokens/timestamps técnicos previstos. |

### 12.11 Rendimiento, estabilidad y compatibilidad

| ID | P | Auto | Flujo de prueba | Resultado esperado y evidencia |
| --- | --- | --- | --- | --- |
| PERF-001 | P2 | H | Ejecutar al menos tres mediciones móviles y escritorio en staging estable; tomar mediana y luego observar campo. | Objetivo: LCP ≤ 2.5 s, CLS ≤ 0.1 e INP de campo ≤ 200 ms al percentil 75; desviaciones justificadas y plan de corrección. |
| PERF-002 | P2 | A | Cargar homepage/contacto con caché fría/caliente, Analytics disponible/bloqueado; inspeccionar requests, consola y listeners. | Sin 4xx/5xx de assets, errores JS, tag duplicado ni bloqueo por animación; assets propios se cargan una vez y sin dependencias externas nuevas. |
| COMP-001 | P3 | H | Ejecutar smoke UC-02/03 en la matriz de navegadores y viewports. | Flujos P1 funcionan; diferencias cosméticas menores quedan documentadas y aceptadas, sin impedir navegación o conversión. |

### 12.12 Recuperación, UAT y producción

| ID | P | Auto | Flujo de prueba | Resultado esperado y evidencia |
| --- | --- | --- | --- | --- |
| REC-001 | P1 | H | En QA provocar fallo tras swap, durante upgrade, configuración y postflight; ejecutar recuperación; comparar versión de código y registros DB. | Código y base vuelven al mismo punto; servicio inicia; smoke anterior pasa; backups identificados y restaurables. RTO/RPO medidos. |
| UAT-001 | P2 | M | Product Owner recorre UC-02 y UC-03 en escritorio/móvil; valida copy, jerarquía, confianza y CTA. | Aprobación explícita o lista de cambios; ningún defecto comercial P1/P2 abierto. Evidencia firmada. |
| PROD-001 | P1 | H | Tras despliegue verificar versión, `/`, 301, contacto, cookies, login, consola, logs y GA4; envío controlado si está autorizado. | HTTP y configuración correctos, sin errores nuevos; lead controlado identificable y limpiado; monitoreo estable durante ventana acordada. |

## 13. Criterios de entrada, suspensión y salida

### 13.1 Entrada a QA

- artifact inmutable y versión identificada;
- revisión estática y pruebas contractuales aprobadas;
- ambiente Odoo 19 disponible con dos websites homónimos;
- backup probado y credenciales/roles de prueba;
- dominio, correo capturado, GA4 de prueba y política de indexación definidos;
- defectos conocidos documentados con responsable.

### 13.2 Suspensión

Suspender la ejecución afectada cuando ocurra cualquiera:

- no puede resolverse de forma única el website objetivo;
- instalación o servicio no completan arranque;
- datos de prueba pueden alcanzar clientes reales;
- staging puede ser indexado accidentalmente;
- no existe backup restaurable para pruebas destructivas;
- falla compartida impide más del 30 % de los casos del ciclo.

Reanudar cuando el bloqueo esté corregido, el ambiente vuelva a una línea base conocida y se ejecute smoke.

### 13.3 Salida y liberación

- 100 % de P1 ejecutados y aprobados;
- al menos 95 % del total aprobado; el resto con riesgo aceptado y fecha;
- cero defectos Severidad 1 o 2 abiertos;
- defectos Severidad 3 aceptados por Product Owner;
- pruebas de consentimiento, lead, aislamiento multiwebsite y rollback aprobadas;
- WCAG automático sin violaciones críticas/serias y revisión manual completada;
- Core Web Vitals dentro del objetivo o excepción aprobada con plan;
- GA4 DebugView, dimensiones y evento clave validados;
- UAT, legal y SEO aprobados en lo aplicable;
- evidencia y reporte final archivados.

## 14. Gestión de defectos

| Severidad | Definición | Ejemplo | SLA de decisión |
| --- | --- | --- | --- |
| S1 bloqueante | Indisponibilidad, pérdida/corrupción, cambio al website incorrecto o incumplimiento grave de privacidad | deploy rompe ambos sitios, PII enviada sin consentimiento | Inmediato; no liberar |
| S2 alta | Flujo principal imposible o resultado incorrecto sin alternativa razonable | formulario no crea lead, portal accede a backend | Antes de liberar |
| S3 media | Función degradada con alternativa | snippet no editable, error responsive localizado | Resolver o aceptar formalmente |
| S4 baja | Cosmético/documental sin impacto funcional | espaciado menor, errata | Backlog |

Cada defecto debe incluir: ID de caso, ambiente/build, precondiciones, pasos mínimos, esperado/observado, evidencia, frecuencia, severidad, website y usuario afectados.

## 15. Evidencia y reporte

Para cada ejecución registrar:

- build/commit y versión del módulo;
- fecha, ambiente, dominio, website ID, navegador y rol;
- estado `Passed`, `Failed`, `Blocked` o `Not run`;
- logs Odoo/CI relevantes sin secretos;
- respuesta/cadena de redirección HTTP cuando aplique;
- captura o video para visual/editor/accesibilidad;
- exportación o captura de DebugView para analítica;
- referencia de defecto y resultado de re-prueba.

El reporte final debe resumir alcance ejecutado, porcentaje por prioridad, defectos abiertos, riesgos residuales, excepciones y decisión `Go / Conditional Go / No-Go`.

## 16. Secuencia de ejecución recomendada

1. Ejecutar estáticos y componente en cada cambio.
2. Probar preflight negativo e instalación limpia en CI efímero.
3. Ejecutar actualización, idempotencia y postflight en QA.
4. Completar multiwebsite, rutas, contenido, roles y formulario.
5. Ejecutar cookies/analítica y pruebas negativas de conversión.
6. Validar editor, SEO, legal, accesibilidad, seguridad y rendimiento en staging.
7. Ensayar rollback completo.
8. Ejecutar UAT y cerrar criterios de salida.
9. Desplegar y ejecutar smoke de producción con ventana de observación.

## 17. Brechas conocidas que esta matriz debe revelar

- El script selecciona instalación o actualización según el estado del módulo; DEP-003 debe demostrar ambos caminos en Odoo real.
- Las pruebas actuales fuera del addon validan cadenas, no instalación ni navegador; faltan suites Odoo/HOOT/tours.
- La indexación de la homepage está fijada en XML; SEO-002 debe verificar el control por ambiente.
- No existe todavía una imagen social real/provisional configurada; SEO-003 no debe aprobarse hasta resolverla.
- El tracking de `/web/login` debe distinguir header/footer y no contaminar otros websites; MW-004 y ANA-001 lo cubren.
- El rollback de carpeta no demuestra rollback de base; REC-001 exige coherencia de ambos.
- La publicación CI está preparada como script, pero requiere un job real del proveedor elegido.
