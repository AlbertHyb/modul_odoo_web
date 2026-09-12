"""Run with `odoo-bin shell -d <database>` after updating financa_website.

Odoo 19 resolves "/" with `website.page` ordered by `website_id asc`
(website_page._get_page_info, _order = 'website_id'), so a generic page with
website_id False wins over the Financa-specific homepage. Archive every other
page at "/" so the Financa homepage is the one served.
"""

import json
import os
import sys


DOMAIN = os.environ["FINANCA_DOMAIN"]
MODULE_HOMEPAGE_KEY = "financa_website.financa_homepage"
ARCHIVE_SUFFIX = "-odoo-homepage-archivo"


def fail(message):
    print(f"HOMEPAGE ENSURANCE FAILED: {message}", file=sys.stderr)
    raise SystemExit(1)


websites = env["website"].sudo().search([("domain", "=", DOMAIN)])
if len(websites) != 1:
    fail(f"expected exactly one website for {DOMAIN!r}, found {len(websites)}")
website = websites.ensure_one()

Page = env["website.page"].sudo()
homepages = Page.search([("website_id", "=", website.id), ("url", "=", "/")])
module_homepage = homepages.filtered(lambda page: page.view_id.key == MODULE_HOMEPAGE_KEY)

if not module_homepage:
    fail(f"the {MODULE_HOMEPAGE_KEY} page is not installed on {DOMAIN!r}")

others = homepages - module_homepage
for page in others:
    archive_url = page.url + ARCHIVE_SUFFIX
    while Page.search([("website_id", "=", website.id), ("url", "=", archive_url)]):
        archive_url += "2"
    page.write({"url": archive_url, "is_published": False})
    if page.menu_ids:
        page.menu_ids.write({"url": archive_url})

remaining = Page.search([("website_id", "=", website.id), ("url", "=", "/")])
if len(remaining) != 1 or remaining.id != module_homepage.id:
    fail(f"expected the {MODULE_HOMEPAGE_KEY} page alone at '/', found {remaining.ids}")

print(
    json.dumps(
        {
            "website_id": website.id,
            "module_homepage_id": module_homepage.id,
            "archived_pages": [
                {"page_id": page.id, "url": page.url, "view_key": page.view_id.key}
                for page in others
            ],
        },
        sort_keys=True,
    )
)
