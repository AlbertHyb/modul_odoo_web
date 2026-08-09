# Prompts de construcción — Sitio web corporativo de Financa Consultores

Usar en orden. `SPEC_financa_website.md` es la fuente de verdad: leer la sección relacionada antes de ejecutar cada prompt y aplicar el SPEC cuando exista cualquier diferencia.

Objetivo común: construir en **Odoo 19 Community** el módulo `financa_website` para la **homepage corporativa de Financa Consultores**, publicada en `/` dentro del website existente identificado por el dominio `https://financa-mx`. Usar QWeb, SCSS y JavaScript nativo, sin modificar core, añadir librerías externas ni crear modelos, controladores o autenticación propia.

## 1. Preflight del website

```text
Antes de crear archivos, valida que el dominio https://financa-mx resuelva exactamente un registro website. Confirma que su nombre visible sea “Financa Consultores”, conserva su favicon y la opción Cuenta de cliente = Por invitación, e identifica la homepage actual para preservarla de forma recuperable. Si el dominio no resuelve exactamente un website, detén la instalación y reporta el hallazgo. No selecciones por nombre ni uses un ID numérico fijo.
```

**Terminado cuando:** existe evidencia del único `website_id` objetivo y del estado recuperable de la homepage anterior.

## 2. Estructura base

```text
Crea el módulo Odoo 19 Community financa_website con nombre visible “Financa Consultores Website”, según la estructura definida en el SPEC. Incluye __init__.py, __manifest__.py, data/redirects.xml, views/homepage.xml, views/snippets.xml, views/legal.xml, views/thank_you.xml, static/src/scss/financa.scss, static/src/js/financa_animations.js, static/src/js/financa_tracking.js, static/src/js/financa_experiments.js y static/src/img/README.md. Depende de website; carga SCSS y los tres archivos JavaScript en web.assets_frontend. No agregues modelos Python, hooks, controladores ni dependencias externas.
```

**Terminado cuando:** el árbol y el manifest coinciden con el SPEC y todos los archivos declarados existen.

## 3. Homepage y redirección

```text
Crea views/homepage.xml. Define financa_homepage con t-call="website.layout" y <div id="wrap" class="financa-homepage">. Registra website.page en /, publícala y configúrala como homepage únicamente del website resuelto por https://financa-mx. Conserva la homepage anterior sin eliminarla. Crea una redirección 301, específica del mismo website, desde /financa-consultores hacia /. Evita contenido duplicado, ciclos y cambios en el website homónimo.
```

**Terminado cuando:** `/` es la homepage del website objetivo, la página anterior sigue recuperable y `/financa-consultores` responde 301 hacia `/`.

## 4. Header, navegación y footer

```text
Conserva el header nativo de website.layout y configúralo para el website objetivo con: Servicios /#servicios, Odoo ERP /#odoo-erp, Diagnóstico /#diagnostico, Proceso /#proceso, Contacto /contactus, Acceso a clientes /web/login y Solicitar diagnóstico /contactus. Mantén el acceso visualmente secundario y deja que la sesión, grupos y permisos nativos determinen las opciones de cada usuario.

Personaliza un único footer global para el website Financa Consultores con marca, Servicios, Empresa, Contacto, /cookie-policy y el enlace a /aviso-de-privacidad únicamente cuando esa página esté publicada. Usa la frase “Más que números. Más que contabilidad. Más que fiscal.” y © 2026 Financa Consultores. No renderices otro footer dentro de la homepage.
```

**Terminado cuando:** header y footer se heredan en las páginas del website objetivo, no aparecen duplicados y el website homónimo permanece intacto.

## 5. Hero

```text
Construye financa-hero. Usa un único H1: “Consultoría financiera y Odoo ERP para empresas que quieren crecer con estructura”. Añade el texto comercial definido en el SPEC. Incluye Solicitar diagnóstico hacia /contactus y Ver soluciones Odoo hacia #odoo-erp. A la derecha, muestra el dashboard ilustrativo con Ventas +18%, Contabilidad Reportes listos, Inventario 6 alertas y CRM 24 oportunidades; identifícalo como información ilustrativa. Usa las clases y atributos analíticos definidos en el SPEC.
```

**Terminado cuando:** el hero es responsive, tiene un solo H1, ambos CTAs funcionan y conserva el contrato de tracking.

## 6. Servicios

```text
Construye la sección financa-services con id="servicios" y data-financa-section="servicios". Añade el título “Servicios Principales”, la introducción del SPEC y cuatro cards: Consultoría financiera y de negocio; Atención fiscal y contable; Tecnología ERP Odoo; Desarrollo, automatización e IA. Usa iconos placeholder accesibles y copy comercial. Mantén grid 2×2 en escritorio y una columna en móvil.
```

**Terminado cuando:** las cuatro líneas de servicio son legibles, editables en Website Builder y no generan desbordamiento horizontal.

## 7. Odoo como centro de control

```text
Construye financa-odoo-center con id="odoo-erp" y data-financa-section="odoo_erp". Usa el título “Odoo ERP como centro de control empresarial” y presenta un mapa responsivo con núcleo Odoo ERP y seis módulos: Ventas, Contabilidad, Inventarios, CRM, Compras y Automatización. Incluye una descripción breve por módulo y evita posiciones absolutas en móvil.
```

**Terminado cuando:** el mapa se entiende en escritorio y como flujo o lista en móvil, sin scroll horizontal.

## 8. Antes y después

```text
Construye financa-before-after con data-financa-section="antes_despues". Título: “Cuando Odoo está bien implementado, la empresa deja de operar a ciegas”. Usa las listas Antes y Después del SPEC, destaca Después con el sistema dorado y conserva contraste accesible.
```

**Terminado cuando:** ambas situaciones se comparan con claridad en escritorio y se apilan correctamente en móvil.

## 9. Diagnóstico Odoo

```text
Construye financa-diagnosis con id="diagnostico" y data-financa-section="diagnostico". Usa el título “¿Tu implementación de Odoo no quedó como esperabas?”, el texto y los checks definidos en el SPEC. El CTA Solicitar diagnóstico Odoo apunta a /contactus y declara data-financa-cta, data-financa-cta-name y data-financa-cta-location.
```

**Terminado cuando:** el diagnóstico explica problema, alcance y siguiente acción, y el CTA queda medible sin enviar datos personales.

## 10. Proceso y CTA final

```text
Construye financa-process con id="proceso" y data-financa-section="proceso". Incluye los cinco pasos del SPEC en timeline horizontal para escritorio y lista vertical para móvil. Después crea financa-final-cta con el mensaje “¿Listo para ver más allá de los números?” y Solicitar diagnóstico hacia /contactus. Instrumenta el CTA con los atributos data-financa-* definidos en el SPEC.
```

**Terminado cuando:** los cinco pasos mantienen su orden en todos los tamaños y el CTA final funciona y queda instrumentado.

## 11. Edición y snippets

```text
Haz editable la homepage completa mediante zonas oe_structure sin romper el template, el header ni el footer global. Crea siete snippets reutilizables: Hero Financa, Servicios Financa, Odoo Centro de Control, Antes vs Después, Diagnóstico Odoo, Proceso Financa y CTA Financa. Regístralos en Website Builder usando parciales QWeb y conserva en cada snippet los IDs, clases y atributos data-financa-* necesarios. No dupliques la homepage completa.
```

**Terminado cuando:** los siete snippets pueden insertarse, moverse, editarse y eliminarse desde Website Builder manteniendo responsive, estilos y tracking.

## 12. Sistema visual y responsive

```text
Crea static/src/scss/financa.scss con las variables del SPEC: dark #111111, gold #C6A15B, light #F6F4EF, white #FFFFFF, muted #666666 y border #E5E5E5. Usa contenedor máximo de 1180px, secciones de 90px en escritorio, cards de radio 20px, sombra discreta y hover translateY(-6px). Cubre homepage, header, footer global, dashboard, servicios, mapa Odoo, comparación, diagnóstico, timeline, CTA, legales y agradecimiento. Bajo 768px apila columnas y elimina cualquier scroll horizontal. Respeta focus visible y prefers-reduced-motion.
```

**Terminado cuando:** escritorio, tableta y móvil mantienen jerarquía, contraste, foco visible y ausencia de desbordamientos.

## 13. Animaciones

```text
Implementa financa_animations.js como módulo frontend compatible con Odoo 19. Usa IntersectionObserver para añadir is-visible a .financa-reveal y anima [data-count] solo cuando exista. Tolera elementos ausentes, contenido insertado desde Website Builder y navegación con anclas. Reduce o desactiva movimiento con prefers-reduced-motion.
```

**Terminado cuando:** las animaciones son progresivas, no bloquean carga y no producen errores en páginas que no contienen componentes Financa.

## 14. Analítica y confirmación de lead

```text
Implementa financa_tracking.js sin insertar gtag.js, Google Tag Manager ni el ID de medición en el código. Reutiliza Google Analytics 4 configurado por Odoo y emite eventos solo cuando Analytics esté disponible y exista consentimiento opcional. Implementa mediante delegación de eventos: financa_section_view, financa_cta_click, financa_contact_view, financa_form_start, generate_lead, financa_login_click y financa_experiment_exposure con los parámetros del SPEC. Excluye el modo editor y cualquier dato personal.

Crea /gracias-diagnostico como página pública no indexada. Configura el formulario nativo de /contactus para redirigir allí únicamente tras un envío exitoso. Emite generate_lead una sola vez por envío confirmado; una visita directa, recarga o clic en enviar no cuenta como lead.
```

**Terminado cuando:** DebugView muestra un único evento por acción, el rechazo de cookies bloquea tracking, el tag base no se duplica y generate_lead solo representa un envío confirmado.

## 15. Preparación A/B

```text
Implementa financa_experiments.js con una feature flag desactivada por defecto. Mientras esté desactivada no debe cambiar contenido, asignar variantes, persistir datos ni emitir exposiciones. Deja preparado el contrato data-financa-experiment y data-financa-variant para futuras landing pages o experimentos aprobados de la homepage. No actives una prueba en la primera publicación.
```

**Terminado cuando:** el archivo carga sin efectos observables con la flag desactivada y el tráfico permanece sin división.

## 16. SEO, cookies y legales

```text
Configura la homepage con el meta title y meta description del SPEC, canonical /, un solo H1, jerarquía semántica y alt text. Mantén /financa-consultores como 301 y no como contenido indexable. Conserva sitemap.xml y robots.txt nativos.

Después de instalar, activa la barra nativa de cookies para el website https://financa-mx y conserva /cookie-policy. Crea /aviso-de-privacidad editable, sin publicar mientras tenga marcadores o carezca de validación jurídica. Conserva el favicon actual y usa placeholders para logo e imagen social hasta recibir activos aprobados.
```

**Terminado cuando:** SEO apunta a `/`, cookies respetan consentimiento y ninguna página legal provisional se publica accidentalmente.

## 17. QA final

```text
Ejecuta el QA completo del SPEC. Verifica instalación y actualización en Odoo 19 Community; aislamiento del website https://financa-mx; homepage en /; 301 desde /financa-consultores; preservación del website homónimo, favicon y acceso Por invitación; header y footer globales sin duplicados; edición y siete snippets; assets; CTAs; /contactus y /gracias-diagnostico; SEO; cookies; eventos GA4; ausencia de datos personales; motor A/B desactivado; consola limpia; y responsive sin scroll horizontal. Corrige únicamente problemas del módulo y reporta bloqueadores de configuración externa por separado.
```

**Terminado cuando:** todos los criterios de aceptación del SPEC tienen evidencia de aprobación o un bloqueo externo explícitamente documentado.
