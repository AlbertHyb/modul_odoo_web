"""Run with `odoo-bin shell -d <database>` after updating financa_website."""

import json
import os
import sys
import unicodedata

# The helpers below are mirrored verbatim in cleanup_financa_legacy.py so the
# cleanup step and the deployment gate share one definition of legacy content.
# --- Financa legacy inventory helpers ---
MODULE_RECORD_PREFIX = "financa_website."


def load_legacy_inventory(path):
    """Read the reviewed inventory of the content the previous site left behind."""
    try:
        with open(path, encoding="utf-8") as handle:
            document = json.load(handle)
    except OSError as error:
        raise ValueError(f"legacy inventory is unreadable: {path}: {error}") from error
    except json.JSONDecodeError as error:
        raise ValueError(f"legacy inventory is not valid JSON: {path}: {error}") from error
    if not isinstance(document, dict):
        raise ValueError("legacy inventory must be a JSON object")
    menus = document.get("menus", [])
    pages = document.get("pages", [])
    if not isinstance(menus, list) or not isinstance(pages, list):
        raise ValueError("legacy inventory 'menus' and 'pages' must be arrays")
    if not menus and not pages:
        raise ValueError("legacy inventory is empty; the deployment gate would never fire")
    for entry in menus:
        if not isinstance(entry, dict):
            raise ValueError(f"menu entry must be an object: {entry!r}")
        if not any(isinstance(entry.get(key), str) and entry[key] for key in ("name", "url")):
            raise ValueError(f"menu entry needs a non-empty name or url: {entry!r}")
    for entry in pages:
        if not isinstance(entry, str) or not entry.startswith("/"):
            raise ValueError(f"page entry must be an absolute path: {entry!r}")
    return {"menus": menus, "pages": pages}


def normalize_label(value):
    """Compare menu labels across accents and case, e.g. 'Histórias' == 'Historias'."""
    decomposed = unicodedata.normalize("NFKD", value or "")
    stripped = "".join(char for char in decomposed if not unicodedata.combining(char))
    return " ".join(stripped.casefold().split())


def is_module_record(record):
    return bool((record.get_external_id().get(record.id) or "").startswith(MODULE_RECORD_PREFIX))


def legacy_menu_matches(menu, entry):
    name = entry.get("name")
    if isinstance(name, str) and normalize_label(menu.name) == normalize_label(name):
        return True
    url = entry.get("url")
    if not isinstance(url, str):
        return False
    linked = menu.page_id.url if menu.page_id else False
    return url in {candidate for candidate in (menu.url, linked) if candidate}


def legacy_menus(menus, inventory):
    return [
        menu
        for menu in menus
        if not is_module_record(menu)
        and any(legacy_menu_matches(menu, entry) for entry in inventory["menus"])
    ]


def legacy_pages(pages, inventory, website_id):
    urls = set(inventory["pages"])
    return [
        page
        for page in pages
        if page.url in urls and page.website_id.id == website_id and not is_module_record(page)
    ]


# --- end Financa legacy inventory helpers ---


DOMAIN = os.environ["FINANCA_DOMAIN"]
LEGACY_INVENTORY = os.environ["FINANCA_LEGACY_INVENTORY"]

FINANCA_MENU_KEYS = (
    "financa_website.menu_financa_services",
    "financa_website.menu_financa_odoo",
    "financa_website.menu_financa_diagnosis",
    "financa_website.menu_financa_process",
    "financa_website.menu_financa_contact",
    "financa_website.menu_financa_login",
)


def fail(message):
    print(f"POST-FLIGHT FAILED: {message}", file=sys.stderr)
    raise SystemExit(1)


websites = env["website"].sudo().search([("domain", "=", DOMAIN)])
if len(websites) != 1:
    fail(f"expected exactly one website for {DOMAIN!r}")
website = websites.ensure_one()

Page = env["website.page"].sudo()
homepage = Page.search(
    [
        ("website_id", "=", website.id),
        ("url", "=", "/"),
        ("key", "=", "financa_website.financa_homepage"),
    ]
)
if len(homepage) != 1 or not homepage.is_published:
    fail("the published Financa homepage was not installed on the target website")

privacy_page = Page.search(
    [
        ("website_id", "=", website.id),
        ("url", "=", "/aviso-de-privacidad"),
        ("key", "=", "financa_website.financa_privacy_page"),
    ]
)
if len(privacy_page) != 1 or privacy_page.is_published:
    fail("the provisional privacy page must exist and remain unpublished")

rewrite = env["website.rewrite"].sudo().search(
    [
        ("website_id", "=", website.id),
        ("url_from", "=", "/financa-consultores"),
        ("url_to", "=", "/"),
        ("redirect_type", "=", "301"),
        ("active", "=", True),
    ]
)
if len(rewrite) != 1:
    fail("the target website does not have exactly one active 301 redirect")
if not website.cookies_bar:
    fail("the native cookies bar is not enabled")

Menu = env["website.menu"].sudo()
top_level = Menu.search([("website_id", "=", website.id), ("parent_id", "=", False)])
if website.menu_id in top_level:
    root_menu = website.menu_id
elif len(top_level) == 1:
    root_menu = top_level.ensure_one()
else:
    fail(f"could not identify one top-level menu for {DOMAIN!r}: {len(top_level)} candidates")

website_menus = Menu.search([("website_id", "=", website.id)])
foreign_menus = website_menus - root_menu
website_pages = Page.search([("website_id", "=", website.id)])

try:
    inventory = load_legacy_inventory(LEGACY_INVENTORY)
except ValueError as error:
    fail(error)

absent = []
detached = []
module_menus = []
for key in FINANCA_MENU_KEYS:
    menu = env.ref(key, raise_if_not_found=False)
    if not menu or menu.website_id != website or not menu.active:
        absent.append(key)
        continue
    module_menus.append(menu)
    if menu.parent_id != root_menu:
        detached.append(f"{menu.id}:{menu.name}")
if absent:
    fail("these Financa menus are missing, inactive or belong to another website: " + ", ".join(absent))
if detached:
    fail("these Financa menus are no longer top-level navigation items: " + ", ".join(detached))

surviving_menus = [menu for menu in legacy_menus(list(foreign_menus), inventory) if menu.active]
surviving_pages = [
    page for page in legacy_pages(list(website_pages), inventory, website.id) if page.is_published
]
if surviving_menus or surviving_pages:
    offenders = [f"menu {menu.id}:{menu.name}" for menu in surviving_menus] + [
        f"page {page.id}:{page.url}" for page in surviving_pages
    ]
    fail(
        "catalogued legacy content is still live on this website: "
        + ", ".join(offenders)
        + f". Add the reviewed entries to {LEGACY_INVENTORY} and redeploy."
    )

labels = {normalize_label(menu.name) for menu in module_menus}
duplicates = [
    menu
    for menu in foreign_menus
    if menu.active and not is_module_record(menu) and normalize_label(menu.name) in labels
]
if duplicates:
    fail(
        "non-Financa menus duplicate a Financa navigation label: "
        + ", ".join(f"{menu.id}:{menu.name}" for menu in duplicates)
        + f". Add them to {LEGACY_INVENTORY} or deactivate them in the website UI."
    )

shared_pages = Page.search([("website_id", "=", False), ("url", "in", inventory["pages"])])

print(
    json.dumps(
        {
            "website_id": website.id,
            "homepage_id": homepage.id,
            "privacy_page_id": privacy_page.id,
            "redirect_id": rewrite.id,
            "cookies_bar": website.cookies_bar,
            "ga4_configured": bool(website.google_analytics_key),
            "financa_menus": sorted(FINANCA_MENU_KEYS),
            "legacy_gate": {
                "inventory_menus": len(inventory["menus"]),
                "inventory_pages": len(inventory["pages"]),
                "active_legacy_menus": len(surviving_menus),
                "published_legacy_pages": len(surviving_pages),
                "duplicate_menu_labels": len(duplicates),
            },
            "shared_legacy_pages": [
                {"id": page.id, "url": page.url} for page in shared_pages if page.is_published
            ],
        },
        sort_keys=True,
    )
)

