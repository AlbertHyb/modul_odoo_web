"""Apply the website configuration that belongs to the Financa deployment."""

import json
import os
import sys


DOMAIN = os.environ["FINANCA_DOMAIN"]
REQUIRE_GA4 = os.environ.get("REQUIRE_GA4", "true").lower() == "true"


def analytics_tag_kind(tag):
    """Classify the native website tag: Odoo loads GA4 and GTM from one field."""
    if not tag:
        return "none"
    if tag.upper().startswith("GTM-"):
        return "gtm"
    if tag.upper().startswith("G-"):
        return "ga4"
    return "other"


websites = env["website"].sudo().search([("domain", "=", DOMAIN)])
if len(websites) != 1:
    print(f"CONFIGURATION FAILED: expected one website for {DOMAIN!r}", file=sys.stderr)
    raise SystemExit(1)

website = websites.ensure_one()
website.write({"cookies_bar": True})

# ponytail: Odoo creates a stock "Contact us" menu per website; the module ships the single Contacto entry
module_menu = env.ref("financa_website.menu_financa_contact", raise_if_not_found=False)
contact_menus = env["website.menu"].sudo().search([("website_id", "=", website.id), ("url", "=", "/contactus")])
for menu in contact_menus:
    if module_menu and menu.id == module_menu.id:
        continue
    if menu.active:
        menu.active = False
if REQUIRE_GA4 and not website.google_analytics_key:
    print(
        "CONFIGURATION FAILED: the target website has no analytics tag; set the GA4 "
        "measurement ID or the Google Tag Manager container in Website > Settings",
        file=sys.stderr,
    )
    raise SystemExit(1)

print(
    json.dumps(
        {
            "website_id": website.id,
            "cookies_bar": website.cookies_bar,
            "analytics_tag_kind": analytics_tag_kind(website.google_analytics_key),
            "ga4_configured": bool(website.google_analytics_key),
        },
        sort_keys=True,
    )
)

