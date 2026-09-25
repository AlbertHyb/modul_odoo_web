"""Neutralize the content the previous Financa site left on the target website.

Run with `odoo-bin shell -d <database>` after updating the module and before the
postflight gate. The addon only creates its own records, so a database that
already hosted the previous site keeps serving its pages and menus next to the
new navigation; a staging database created from scratch has nothing to inherit,
which is why the mix only shows up in production. Legacy pages are unpublished
in place and their menus are deactivated, never deleted, so the previous site
stays recoverable from the website UI. Idempotent: a second run reports no
changes. The reviewed inventory comes from FINANCA_LEGACY_INVENTORY.
"""

import json
import os
import sys
import unicodedata

# The helpers below are mirrored verbatim in postflight_financa.py so the
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
INVENTORY = os.environ["FINANCA_LEGACY_INVENTORY"]


def abort(message):
    print(f"LEGACY CLEANUP FAILED: {message}", file=sys.stderr)
    raise SystemExit(1)


def describe(menu):
    return {
        "id": menu.id,
        "name": menu.name,
        "url": menu.url or "",
        "xmlid": menu.get_external_id().get(menu.id) or "",
    }


def describe_page(page):
    return {"id": page.id, "url": page.url, "key": page.view_id.key}


def website_root_menu(menu_model, website):
    """Return the single top-level menu the website navigation hangs from."""
    top_level = menu_model.search([("website_id", "=", website.id), ("parent_id", "=", False)])
    if website.menu_id in top_level:
        return website.menu_id
    if len(top_level) == 1:
        return top_level.ensure_one()
    abort(f"could not identify one top-level menu for {DOMAIN!r}: {len(top_level)} candidates")


def branch(menu_model, menu):
    """Return every descendant of menu, so a legacy subtree leaves together."""
    found = menu_model.browse()
    pending = list(menu.child_id)
    while pending:
        current = pending.pop()
        found |= current
        pending.extend(current.child_id)
    return found


try:
    inventory = load_legacy_inventory(INVENTORY)
except ValueError as error:
    abort(error)

websites = env["website"].sudo().search([("domain", "=", DOMAIN)])
if len(websites) != 1:
    abort(f"expected exactly one website for {DOMAIN!r}, found {len(websites)}")
website = websites.ensure_one()

Menu = env["website.menu"].sudo()
Page = env["website.page"].sudo()

root_menu = website_root_menu(Menu, website)
foreign_menus = Menu.search([("website_id", "=", website.id)]) - root_menu
website_pages = Page.search([("website_id", "=", website.id)])

targets = Menu.browse([menu.id for menu in legacy_menus(list(foreign_menus), inventory)])

subtree = Menu.browse()
for menu in targets:
    subtree |= branch(Menu, menu)

rescue_scope = subtree - targets
doomed = targets | Menu.browse(
    [menu.id for menu in rescue_scope if not is_module_record(menu)]
)
rescued = [menu for menu in rescue_scope if is_module_record(menu)]

before = {
    "active_menus": [describe(menu) for menu in foreign_menus if menu.active],
    "published_pages": [describe_page(page) for page in website_pages if page.is_published],
}

deactivated = []
for menu in doomed:
    if menu.active:
        deactivated.append(describe(menu))
        menu.write({"active": False})

reparented = []
for menu in rescued:
    if menu.parent_id != root_menu:
        reparented.append(describe(menu))
        menu.write({"parent_id": root_menu.id})

unpublished = []
for page in legacy_pages(list(website_pages), inventory, website.id):
    if page.is_published:
        unpublished.append(describe_page(page))
        page.write({"is_published": False})

remaining_menus = Menu.search(
    [("website_id", "=", website.id), ("active", "=", True), ("id", "!=", root_menu.id)]
)

shared_pages = Page.search([("website_id", "=", False), ("url", "in", inventory["pages"])])

print(
    json.dumps(
        {
            "website_id": website.id,
            "domain": website.domain,
            "inventory": {"menus": len(inventory["menus"]), "pages": len(inventory["pages"])},
            "before": before,
            "deactivated_menus": deactivated,
            "reparented_menus": reparented,
            "unpublished_pages": unpublished,
            "changed": bool(deactivated or reparented or unpublished),
            "audit": {
                "remaining_foreign_active_menus": [
                    describe(menu) for menu in remaining_menus if not is_module_record(menu)
                ],
                "remaining_published_pages": [
                    describe_page(page) for page in website_pages if page.is_published
                ],
                "shared_legacy_pages": [
                    describe_page(page) for page in shared_pages if page.is_published
                ],
            },
        },
        sort_keys=True,
    )
)

