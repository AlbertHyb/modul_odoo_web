# SPEC — Financa Consultores Website

## 1. Propósito

Crear el sitio web corporativo principal de **Financa Consultores** en **Odoo 19 Community**. Esta primera implementación funciona como homepage institucional y debe posicionar a Financa como aliado estratégico que integra consultoría financiera y de negocio, atención fiscal y contable, tecnología Odoo ERP, desarrollo, automatización e IA.

**Mensaje principal:**

> Consultoría financiera y Odoo ERP para empresas que quieren crecer con estructura.

La página debe convertir la información financiera en una propuesta de valor clara: control, rentabilidad, cumplimiento, operación conectada y crecimiento.

Las landing pages orientadas a campañas, audiencias o servicios específicos se implementarán posteriormente dentro del mismo website y reutilizarán el sistema visual, los snippets y la instrumentación definidos por este módulo.

## 2. Alcance

- Homepage corporativa publicada en `/` y configurada como página de inicio del website objetivo.
- Redirección permanente 301, específica del website, desde `/financa-consultores` hacia `/`.
- Página asignada al website existente **Financa Consultores** cuyo dominio actual es `https://financa-mx`.
- La base contiene al menos dos websites con el mismo nombre; el sitio objetivo no debe identificarse únicamente por `name`.
- Módulo web propio; no modificar archivos core de Odoo.
- QWeb, SCSS y JavaScript nativo, sin librerías externas.
- Siete snippets reutilizables incluidos desde la primera versión para Website Builder.
- Contenido completo de la homepage editable desde Website Builder mediante zonas `oe_structure` y snippets reutilizables.
- El CTA comercial `Solicitar diagnóstico` apunta temporalmente a `/contactus`; el CTA `Ver soluciones Odoo` navega a `#odoo-erp`.
- SEO inicial configurado con las herramientas nativas de Odoo.
- Barra y política de cookies administradas por Odoo.
- Aviso de privacidad provisional, editable y pendiente de validación jurídica y datos definitivos de Financa.
- Medición del embudo mediante la integración existente de Google Analytics 4, sin duplicar ni codificar el tag dentro del módulo.
- Instrumentación preparada para pruebas A/B, inicialmente desactivadas mientras se construye una línea base con el tráfico real.

No incluye modelos, lógica de negocio, CRM, formularios a medida, integraciones externas ni la construcción de landing pages adicionales en esta primera versión.

## 3. Arquitectura técnica

| Área | Decisión |
| --- | --- |
| Plataforma | Odoo 19 Community + `website` |
| Vistas | Templates QWeb XML |
| Estilos | SCSS en `web.assets_frontend` |
| Interacción | JavaScript nativo con `IntersectionObserver` |
| Página | Registro `website.page`, publicado en `/`, marcado como homepage y asignado al website existente con dominio `https://financa-mx` |
| Redirección | 301 específica del website desde `/financa-consultores` hacia `/` |
| Edición | Contenido editable desde Website Builder mediante `oe_structure` y snippets |
| Reutilización | Partiales QWeb y siete snippets obligatorios que servirán también como base para futuras landing pages |
| Sesión | Header, autenticación, menú de usuario, grupos y permisos nativos de Odoo |
| Cookies | Barra nativa de Odoo y página `/cookie-policy` |
| Privacidad | Página provisional `/aviso-de-privacidad`, editable y pendiente de validación jurídica |
| Analítica | Google Analytics 4 configurado en Odoo; eventos propios enviados únicamente después del consentimiento |
| Experimentación | Instrumentación A/B disponible mediante feature flag, desactivada en la primera publicación |

### Identificación del website objetivo

- En la base de Odoo Community existen al menos dos registros llamados **Financa Consultores**.
- El nombre visible configurado en **Identificación del sitio web** es exactamente **Financa Consultores**.
- El website objetivo es el registro existente que combina ese nombre visible con el campo `domain` configurado actualmente como `https://financa-mx`.
- El campo de nombre visible no es un identificador técnico único, porque ambos websites muestran el mismo nombre; el dominio sigue siendo el criterio de selección.
- La instalación no debe crear un nuevo registro `website` ni seleccionar el sitio solamente por nombre.
- La página, los menús, el SEO y cualquier configuración dependiente del sitio deben usar el mismo `website_id` resuelto por dominio.
- No se debe codificar un identificador numérico de base de datos. Si el dominio cambia entre ambientes, el despliegue debe proporcionar o confirmar el dominio correspondiente antes de instalar o actualizar el módulo.
- Antes de instalar o actualizar, un preflight de despliegue debe confirmar que la búsqueda por dominio devuelve exactamente un website.
- La asignación XML puede utilizar una búsqueda por dominio después del preflight, pero no se considera un mecanismo de validación de unicidad. El módulo no añade hooks ni lógica Python solamente para esta comprobación.
- Si el preflight no obtiene exactamente un resultado, no debe iniciarse la instalación para evitar crear contenido global o modificar el sitio equivocado.

### Homepage y ruta anterior

- La página creada por el módulo debe quedar marcada como homepage del website resuelto por `https://financa-mx`.
- La asignación como homepage debe limitarse a ese `website_id` y no alterar la página de inicio del website homónimo.
- Si ya existe otra homepage en el website objetivo, debe conservarse de forma recuperable; la instalación no debe eliminarla.
- `/financa-consultores` debe responder con una redirección HTTP 301 hacia `/`, sin duplicar contenido ni generar ciclos.
- La redirección debe estar asociada al mismo `website_id` y no afectar rutas equivalentes en otros websites.

## 4. Estructura del módulo

```text
financa_website/
├── __init__.py
├── __manifest__.py
├── data/
│   └── redirects.xml
├── views/
│   ├── homepage.xml
│   ├── snippets.xml
│   ├── legal.xml
│   └── thank_you.xml
└── static/
    └── src/
        ├── scss/
        │   └── financa.scss
        ├── js/
        │   ├── financa_animations.js
        │   ├── financa_tracking.js
        │   └── financa_experiments.js
        └── img/
            └── README.md
```

### Manifest mínimo

```python
{
    "name": "Financa Consultores Website",
    "version": "19.0.1.0.0",
    "depends": ["website"],
    "data": [
        "data/redirects.xml",
        "views/homepage.xml",
        "views/snippets.xml",
        "views/legal.xml",
        "views/thank_you.xml",
    ],
    "assets": {
        "web.assets_frontend": [
            "financa_website/static/src/scss/financa.scss",
            "financa_website/static/src/js/financa_animations.js",
            "financa_website/static/src/js/financa_tracking.js",
            "financa_website/static/src/js/financa_experiments.js",
        ],
    },
    "installable": True,
}
```

## 5. Secciones y copy base

| # | Sección | Objetivo |
| --- | --- | --- |
| 1 | Header nativo | Conservar el header de `website.layout`; configurar navegación hacia servicios, Odoo, diagnóstico, proceso y contacto sin duplicarlo dentro de la homepage. |
| 2 | Hero | Presentar la propuesta y un dashboard Odoo visual. |
| 3 | Servicios | Comunicar las cuatro líneas de servicio en cards 2×2. |
| 4 | Odoo como centro | Mostrar cómo ventas, contabilidad, inventarios, CRM, compras y automatización se conectan. |
| 5 | Antes / Después | Hacer visible el valor de una implementación ordenada. |
| 6 | Diagnóstico Odoo | Convertir el dolor de una implementación incompleta en una solicitud de diagnóstico. |
| 7 | Cómo trabajamos | Explicar el método de cinco pasos. |
| 8 | CTA final | Solicitar diagnóstico. |
| 9 | Footer global personalizado | Personalizar el footer nativo del website Financa con servicios, navegación, contacto, enlaces legales y frase de marca; debe heredarse en las páginas del sitio sin duplicarse dentro de la homepage. |

### Identificadores y navegación

Cada sección navegable debe contar con un identificador estable. Como el header es global para el website, debe utilizar rutas completas que también funcionen desde otras páginas:

| Elemento | Destino |
| --- | --- |
| Servicios | `/#servicios` |
| Odoo ERP | `/#odoo-erp` |
| Diagnóstico | `/#diagnostico` |
| Proceso | `/#proceso` |
| Contacto | `/contactus` |
| Acceso a clientes | `/web/login` |
| Solicitar diagnóstico | `/contactus` |

### Hero

- **Título:** Consultoría financiera y Odoo ERP para empresas que quieren crecer con estructura.
- **Texto:** Transformamos la información financiera en decisiones claras, conectando contabilidad, estrategia de negocio y tecnología ERP para impulsar control, rentabilidad y crecimiento.
- **CTAs:** `Solicitar diagnóstico` hacia `/contactus` y `Ver soluciones Odoo` hacia `#odoo-erp`.
- **Dashboard ilustrativo:** Ventas `+18%`, Contabilidad `Reportes listos`, Inventario `6 alertas`, CRM `24 oportunidades`.

### Servicios

1. **Consultoría financiera y de negocio:** estrategias para costos, rentabilidad, capital de trabajo y crecimiento.
2. **Atención fiscal y contable:** cumplimiento y mejor toma de decisiones basada en información financiera.
3. **Tecnología ERP Odoo:** conexión de ventas, contabilidad, inventarios, compras, CRM y operación.
4. **Desarrollo, automatización e IA:** extensiones, integraciones y automatizaciones cuando la operación lo requiere.

### Diagnóstico Odoo

**Título:** ¿Tu implementación de Odoo no quedó como esperabas?

Financa revisa configuración, procesos contables y operación para detectar errores, desconexiones y oportunidades de mejora. La salida esperada es una ruta útil, ordenada y alineada al crecimiento.

## 6. Acceso al sistema Odoo

El sitio público debe conservar el manejo de sesión nativo de Odoo; el módulo no debe crear formularios, controladores ni menús propios de autenticación.

### Comportamiento

- Se conserva el header global proporcionado por `website.layout`; no se crea un segundo header dentro de la homepage.
- El header incluye un enlace secundario **Acceso a clientes** hacia `/web/login`, mediante la autenticación nativa de Odoo.
- El CTA comercial principal sigue siendo **Solicitar diagnóstico** y apunta temporalmente a `/contactus`.
- Cuando exista una sesión válida, Odoo muestra únicamente las opciones permitidas por los grupos y reglas de acceso del usuario.
- Los usuarios portal conservan sus limitaciones y acceso a las funciones de portal autorizadas; no reciben acceso a aplicaciones internas.
- Los usuarios internos pueden acceder al backend y a las aplicaciones autorizadas por sus permisos.
- La opción **Cuenta de cliente** del website se conserva en **Por invitación**; el módulo no debe habilitar **Registro gratis** ni modificar esta política.
- **Aplicaciones** no se publica como enlace estático ni se replica en el header: debe seguir protegido por la sesión y las reglas de acceso de Odoo.
- Si Financa habilita portal para clientes, el mismo acceso debe conducir a la autenticación estándar de Odoo; la autorización posterior queda a cargo de los grupos y permisos configurados en Odoo.

### Ubicación visual

```text
[Logo Financa]  Servicios · Odoo ERP · Diagnóstico · Contacto
                                           Acceso a clientes  [Solicitar diagnóstico]
```

El acceso es visualmente secundario: enlace de texto o botón de contorno. No debe competir con el CTA dorado de conversión. La configuración debe realizarse sobre el header nativo del website identificado por el dominio `https://financa-mx`, sin alterar el otro website que comparte el nombre **Financa Consultores**.

## 7. Sistema visual

```css
--financa-dark: #111111;
--financa-gold: #C6A15B;
--financa-light: #F6F4EF;
--financa-white: #FFFFFF;
--financa-muted: #666666;
--financa-border: #E5E5E5;
```

- Contenedor: máximo `1180px`.
- Secciones: `90px` verticales en escritorio; reducir en móvil.
- Cards: radio `20px`, borde suave y sombra discreta.
- Servicios: grid 2×2; una columna bajo `768px`.
- Interacción: `hover` con `translateY(-6px)`; transiciones breves y sin exceso de movimiento.
- Estilo: sobrio, editorial y empresarial; negro/grafito, blanco y dorado. Evitar estética genérica de despacho o dashboard real saturado.

## 8. Restricciones técnicas

- Usar `t-call="website.layout"` y `<div id="wrap" class="financa-homepage">`.
- Mantener clases con prefijo `financa-` para evitar colisiones.
- Conservar el header global de `website.layout` y evitar cualquier header duplicado dentro de la homepage.
- Personalizar el footer global nativo únicamente para el website resuelto por `https://financa-mx`.
- No renderizar un segundo footer dentro de la homepage. La homepage, `/contactus`, las páginas legales y las futuras páginas del website deben heredar el mismo footer Financa, salvo que una futura landing defina explícitamente ocultarlo.
- Incluir zonas `oe_structure` apropiadas para que toda la homepage pueda editarse desde Website Builder.
- Reutilizar la sesión, menú de usuario, grupos y permisos nativos de Odoo; no implementar autenticación propia.
- No usar jQuery ni dependencias externas.
- El JavaScript debe tolerar que las secciones no existan.
- Las animaciones deben respetar `prefers-reduced-motion` y no bloquear la carga.
- Las cifras del dashboard son ilustrativas; no presentarlas como datos reales.
- Usar placeholders para iconos e imágenes hasta que se entreguen activos aprobados.
- Conservar el favicon actualmente configurado en el website; el módulo no debe reemplazarlo automáticamente.
- Conservar la configuración nativa de Google Analytics del website y no insertar manualmente otro `gtag.js`, código de Google Tag Manager o ID de medición.
- No enviar a Analytics nombres, correos, teléfonos, contenido de formularios, identificadores de usuario ni otros datos personales.

## 9. SEO

La homepage debe aprovechar las herramientas nativas de SEO de Odoo y quedar preparada para ajustes posteriores desde **Sitio web > Sitio > Optimizar SEO**.

### Configuración inicial

- **Meta title:** `Consultoría financiera y Odoo ERP | Financa Consultores`
- **Meta description:** `Consultoría financiera, fiscal y tecnológica para conectar procesos, mejorar la rentabilidad e implementar Odoo ERP con estructura.`
- **URL canónica de contenido:** `/`.
- `/financa-consultores` no debe declarar contenido canónico propio; debe redirigir mediante 301 a `/`.
- Mantener un único encabezado `H1` en la página.
- Usar una jerarquía semántica ordenada de `H2` y `H3`.
- Añadir texto alternativo descriptivo a todas las imágenes informativas.
- Usar una imagen social provisional hasta recibir el activo aprobado de Financa.
- Permitir que Odoo administre `sitemap.xml`, `robots.txt` y la configuración de indexación.
- Mantener la indexación desactivada en ambientes de prueba y habilitarla solamente en producción.

Quedan pendientes la imagen social definitiva y cualquier dato estructurado que requiera información legal o comercial todavía no confirmada. El favicon actual debe conservarse.

## 10. Cookies y privacidad

### Cookies

- Usar la barra de cookies nativa de Odoo; no desarrollar un banner alternativo.
- Activarla después de instalar el módulo para el website identificado por `https://financa-mx`, desde la configuración de Seguimiento y SEO.
- Conservar la página nativa `/cookie-policy` generada por Odoo y permitir su edición desde Website Builder.
- Añadir un enlace a `/cookie-policy` en el footer personalizado.
- Documentar en esa página cualquier cookie o servicio de terceros que se incorpore posteriormente.
- No enviar eventos de Analytics ni asignar variantes persistentes antes de que el visitante acepte las cookies opcionales.

### Aviso de privacidad provisional

- Crear una página editable en `/aviso-de-privacidad`.
- Mantenerla sin publicar mientras conserve marcadores o no haya recibido validación jurídica.
- Preparar su enlace en el footer personalizado, pero mostrarlo públicamente únicamente cuando la página esté completa y publicada.
- Identificar claramente su contenido como provisional mientras no haya sido validado jurídicamente.
- Contemplar, como mínimo: identidad y domicilio del responsable; datos personales tratados; finalidades; transferencias; mecanismos para limitar el uso; conservación; medios para ejercer derechos ARCO; contacto; y procedimiento para comunicar cambios.
- No inventar razón social, domicilio, teléfono, correo ni otros datos legales. Mantener marcadores editables hasta que Financa proporcione la información definitiva.

Antes de publicar el sitio en producción, el aviso deberá sustituir todos los marcadores y recibir validación jurídica conforme a la legislación aplicable en México.

## 11. Analítica y experimentación

### Configuración existente

- El website objetivo ya tiene Google Analytics 4 habilitado desde la configuración nativa de Odoo.
- El ID de medición observado es `G-R0ER57VZ90` y se usa solamente como valor de verificación del ambiente; no debe codificarse en los archivos del módulo.
- Antes del QA se debe confirmar que el ID pertenece al website resuelto por `https://financa-mx` y no al website homónimo.
- Odoo conserva la responsabilidad de cargar el tag y aplicar el consentimiento. El módulo solamente emite eventos cuando la función de medición está disponible después del consentimiento.

### Embudo de medición

El embudo principal es:

`Visita → sección vista → CTA → formulario visto → formulario iniciado → lead generado`

Se deben instrumentar los siguientes eventos:

| Evento | Momento | Parámetros mínimos |
| --- | --- | --- |
| `financa_section_view` | Primera visualización significativa de una sección | `section_name`, `page_path` |
| `financa_cta_click` | Clic en un CTA instrumentado | `cta_name`, `cta_location`, `destination`, `page_path` |
| `financa_contact_view` | Carga de la página de contacto desde el flujo comercial | `source_cta`, `page_path` |
| `financa_form_start` | Primera interacción con el formulario de contacto | `form_name`, `page_path` |
| `generate_lead` | Envío del formulario confirmado correctamente | `lead_source`, `form_name` |
| `financa_login_click` | Clic en **Acceso a clientes** | `cta_location`, `page_path` |
| `financa_experiment_exposure` | Primera exposición real a una variante activa | `experiment_id`, `variant_id`, `page_path` |

- Los nombres de parámetros deben mantenerse estables y documentados.
- `generate_lead` es la conversión principal y debe marcarse como evento clave en GA4.
- Los parámetros `experiment_id`, `variant_id`, `cta_name`, `cta_location`, `section_name`, `source_cta` y `form_name` deben registrarse en GA4 como dimensiones personalizadas cuando empiecen a recibirse.
- Los eventos de exposición y sección deben deduplicarse para no emitirse repetidamente durante la misma carga o sesión.
- Los eventos deben tolerar que Analytics esté bloqueado, no haya consentimiento o `gtag` no esté disponible.
- La actividad realizada dentro del modo de edición de Website Builder no debe emitir eventos de negocio ni contaminar las métricas públicas.

### Contrato de marcado

- Las secciones medibles deben usar `data-financa-section="<section_name>"`.
- Los CTAs deben declarar `data-financa-cta`, `data-financa-cta-name` y `data-financa-cta-location`.
- Los formularios medibles deben declarar un nombre estable mediante `data-financa-form-name` cuando el markup nativo permita añadirlo sin modificar core.
- Las variantes futuras deben declarar `data-financa-experiment` y `data-financa-variant`.
- El tracking de clics e inicio de formulario debe usar delegación de eventos para continuar funcionando después de ediciones realizadas con Website Builder.
- Los atributos analíticos son parte del contrato del snippet: mover o editar visualmente una sección no debe eliminarlos.

### Confirmación de lead

- Crear una página pública y no indexada en `/gracias-diagnostico`.
- Configurar el formulario nativo de contacto para redirigir a esa página solamente después de un envío exitoso.
- Emitir `generate_lead` al confirmar que la navegación procede de un envío válido.
- Recargar directamente la página de agradecimiento no debe generar conversiones duplicadas.
- Un clic en `/contactus` o en el botón de envío no cuenta por sí mismo como lead.

### Estrategia inicial de pruebas A/B

- El volumen registrado durante **julio de 2026** fue de aproximadamente **234 visitas**.
- Ese volumen corresponde a un periodo en el que el sitio todavía estaba en implementación, por lo que se considera solamente una referencia histórica y no la línea base de la homepage terminada.
- La línea base de producción comienza cuando esta implementación esté publicada, Analytics y cookies hayan superado el QA y se haya descartado el tráfico de edición o pruebas.
- Antes de diseñar el primer experimento se debe observar al menos un ciclo mensual completo posterior al lanzamiento y calcular las tasas reales del embudo.
- La primera publicación instrumenta el embudo completo, pero mantiene desactivada la asignación A/B.
- `financa_experiments.js` debe incluir una feature flag desactivada por defecto y no debe cambiar contenido ni persistir variantes mientras permanezca desactivada.
- Antes de activar un experimento se debe definir por escrito: hipótesis, variante de control, variante propuesta, conversión principal, métricas de diagnóstico y tamaño objetivo.
- Activar un solo experimento a la vez y priorizar cambios sustanciales de propuesta, jerarquía o CTA sobre diferencias cosméticas.
- Como referencia operativa inicial, no dividir tráfico hasta poder reunir aproximadamente entre **1,000 y 1,500 visitas elegibles por experimento**, o hasta calcular un tamaño de muestra basado en la conversión real observada.
- Cuando se active, la asignación debe ser aleatoria, 50/50, persistente para el visitante que haya consentido y acompañada de un único evento de exposición.
- No declarar una variante ganadora por observaciones tempranas; el experimento debe alcanzar el tamaño o duración definidos antes de comenzar.
- La activación de experimentos constituye una configuración explícita de una versión posterior, no parte del lanzamiento inicial.
- La instrumentación podrá reutilizarse en futuras landing pages; cada página o campaña deberá definir su propio embudo, hipótesis y población elegible.

### QA de medición

- Verificar en GA4 DebugView o Tiempo real que cada evento se emite una sola vez y con los parámetros esperados.
- Confirmar que rechazar cookies opcionales impide el envío de eventos y la asignación persistente de variantes.
- Confirmar que aceptar cookies habilita la medición sin recargar ni romper la navegación.
- Validar que no se envían datos personales ni valores introducidos en el formulario.
- Confirmar que editar la página desde Website Builder no genera conversiones ni eventos públicos.
- Comprobar que el tag base de Google se carga una sola vez.

## 12. Criterios de aceptación

- El módulo instala y actualiza sin errores en Odoo 19 Community.
- `/` carga la homepage corporativa publicada con `website.layout` y asignada al website existente cuyo dominio es `https://financa-mx`.
- La página queda marcada como homepage únicamente para el website objetivo.
- `/financa-consultores` responde con 301 hacia `/` en el website objetivo y no genera un segundo contenido indexable.
- El preflight confirma exactamente un website por dominio antes de instalar; el módulo no crea otro registro ni modifica el website homónimo.
- SCSS y JavaScript se cargan desde `web.assets_frontend`.
- Las nueve secciones están presentes, legibles y ordenadas.
- `Solicitar diagnóstico` apunta a `/contactus` y `Ver soluciones Odoo` navega a `#odoo-erp`.
- Se conserva un único header: el nativo de Odoo, configurado con **Acceso a clientes** y separado del CTA comercial.
- Un usuario autenticado conserva el menú estándar y las limitaciones correspondientes a sus grupos; no existe un enlace público estático a Aplicaciones.
- El acceso de clientes permanece configurado **Por invitación** y el registro público gratuito continúa deshabilitado.
- Existe un único footer global personalizado para el website Financa; se hereda en la homepage y las demás páginas sin duplicarse.
- El footer incluye `/cookie-policy` y muestra el enlace a `/aviso-de-privacidad` solo cuando este último esté publicado.
- El diseño se adapta a escritorio, tableta y móvil; grids y mapa Odoo no generan desbordamiento horizontal.
- No hay errores en consola ni cambios a core.
- Los siete snippets reutilizan templates parciales y no duplican el HTML de la homepage.
- La homepage completa puede editarse desde Website Builder sin romper la estructura responsive ni las animaciones.
- La barra de cookies nativa queda activada en la configuración posterior a la instalación para el website `https://financa-mx`, y `/cookie-policy` permanece accesible.
- `/aviso-de-privacidad` existe, es editable y permanece sin publicar mientras conserve marcadores pendientes.
- El meta title, meta description, jerarquía de encabezados y textos alternativos cumplen la configuración SEO inicial.
- El tag de Analytics no está duplicado ni codificado en el módulo.
- Los eventos del embudo se validan en GA4 y no contienen datos personales.
- `/gracias-diagnostico` registra un único `generate_lead` por envío confirmado y permanece fuera del índice.
- Rechazar cookies opcionales impide el tracking y aceptar cookies habilita los eventos.
- El motor A/B se entrega desactivado y no divide el tráfico de la primera publicación.
- Las 234 visitas de julio de 2026 se conservan como referencia histórica, pero no se utilizan como línea base para declarar mejoras o ganadores.

## 13. Información pendiente de Financa

- Confirmar si `https://financa-mx` es el hostname definitivo de producción o únicamente el dominio interno del ambiente actual.
- Razón social o identidad legal del responsable.
- Domicilio del responsable.
- Correo para privacidad y ejercicio de derechos ARCO.
- Teléfono y correo comercial.
- Logo definitivo e imagen para compartir en redes; el favicon existente se conserva salvo que Financa entregue un reemplazo aprobado.
- URLs verificadas de redes sociales.
- Validación jurídica del aviso de privacidad.

Estos pendientes no bloquean el desarrollo: deben representarse mediante marcadores editables y activos provisionales, pero sí bloquean la publicación definitiva del aviso de privacidad y de los datos de contacto.

## 14. Orden de construcción

1. Estructura y manifest.
2. Template base, registro como homepage y redirección 301.
3. Hero y servicios.
4. Mapa de Odoo y Antes/Después.
5. Diagnóstico, proceso, CTA y footer.
6. SCSS responsive.
7. Animaciones JavaScript e instrumentación del embudo.
8. Página de agradecimiento y confirmación deduplicada de `generate_lead`.
9. Siete snippets reutilizables y edición completa desde Website Builder.
10. SEO, footer legal, barra nativa de cookies y aviso de privacidad provisional.
11. Motor de experimentos preparado con feature flag desactivada.
12. Preflight del website, instalación, configuración de Analytics/cookies y QA responsive y de medición.
