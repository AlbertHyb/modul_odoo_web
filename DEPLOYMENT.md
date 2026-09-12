# Despliegue de `financa_website`

El módulo selecciona el website por `domain = https://financa-mx`. El preflight
es obligatorio porque una búsqueda XML no valida unicidad ni puede documentar
el estado anterior de la base.

## 1. Preflight en Odoo shell

Ejecutar antes de instalar o actualizar:

```python
DOMAIN = "https://financa-mx"
websites = env["website"].search([("domain", "=", DOMAIN)])
assert len(websites) == 1, f"Preflight detenido: {len(websites)} websites para {DOMAIN}"

website = websites.ensure_one()
assert website.name == "Financa Consultores", website.name
assert website.auth_signup_uninvited == "b2b", website.auth_signup_uninvited

homepage_url = website.homepage_url or "/"
homepages = env["website.page"].sudo().search([
    ("website_id", "in", [False, website.id]),
    ("url", "=", homepage_url),
])

evidence = {
    "website_id": website.id,
    "name": website.name,
    "domain": website.domain,
    "favicon_presente": bool(website.favicon),
    "cuenta_cliente": website.auth_signup_uninvited,
    "homepage_url": homepage_url,
    "homepage_actual": [
        {
            "page_id": page.id,
            "website_id": page.website_id.id or None,
            "view_id": page.view_id.id,
            "view_key": page.view_id.key,
            "url": page.url,
            "publicada": page.is_published,
        }
        for page in homepages
    ],
}
evidence
```

Guardar la salida en la evidencia del despliegue. Si existe una página
específica del website objetivo en `/`, respaldarla o asignarle una URL de
archivo desde **Sitio web > Sitio > Páginas** antes de instalar. No eliminarla.
La homepage genérica de Odoo permanece en la base y la nueva página específica
del módulo la sustituye únicamente para el website objetivo. El despliegue
ejecuta `ensure_financa_homepage.py` tras instalar o actualizar el módulo:
archiva (renombra y despublica) cualquier otra página en `/` del website
objetivo para que la homepage de Financa sea la que se sirve. En Odoo 19 la
resolución de `/` ordena por `website_id asc`, por lo que despublicar sola no
basta; renombrar la URL es obligatorio para que la página específica gane.

## 2. Instalación

El despliegue automatizado consulta `ir.module.module`: usa
`-i financa_website` cuando el módulo es nuevo o está desinstalado y
`-u financa_website` únicamente cuando está instalado. Cualquier estado
transitorio detiene la liberación. Antes de modificar el addon se exige un
punto de recuperación consistente de PostgreSQL y filestore.

## 3. Configuración posterior

En el website cuyo dominio es `https://financa-mx`:

1. Activar la barra nativa de cookies en **Seguimiento y SEO**.
2. Confirmar que GA4 conserva el ID esperado del ambiente y que el tag base se
   carga una sola vez. El módulo no contiene el ID ni carga `gtag.js`.
3. Mantener **Cuenta de cliente** en **Por invitación**.
4. Mantener la indexación desactivada en ambientes de prueba.
5. No publicar `/aviso-de-privacidad` hasta reemplazar todos los marcadores y
   obtener validación jurídica.

## 4. QA externo pendiente

Validar en la base Odoo 19 real: instalación/actualización, respuesta 301,
edición de los siete snippets, envío exitoso del formulario, DebugView de GA4,
rechazo/aceptación de cookies, ausencia de eventos en modo editor y responsive
en navegador. Estos puntos no pueden comprobarse sin una base y un dominio en
ejecución.

