"""Run with `odoo-bin shell -d <database>` before updating financa_website."""

import json
import os
import sys


DOMAIN = os.environ["FINANCA_DOMAIN"]
MODULE_HOMEPAGE_KEY = "financa_website.financa_homepage"
EXPECTED_MODULE_DOMAIN = "https://financa-mx"


def fail(message):
    print(f"PRE-FLIGHT FAILED: {message}", file=sys.stderr)
    raise SystemExit(1)


if DOMAIN != EXPECTED_MODULE_DOMAIN:
    fail("FINANCA_DOMAIN differs from the module XML target; update the module only after confirming the new domain")

websites = env["website"].sudo().search([("domain", "=", DOMAIN)])
if len(websites) != 1:
    fail(f"expected exactly one website for {DOMAIN!r}, found {len(websites)}")

website = websites.ensure_one()
if website.name != "Financa Consultores":
    fail(f"expected website name 'Financa Consultores', found {website.name!r}")
if website.auth_signup_uninvited != "b2b":
    fail("Customer Account must remain 'On invitation' (b2b)")
if website.homepage_url not in (False, "", "/"):
    fail(
        f"homepage_url is {website.homepage_url!r}; preserve and archive that homepage "
        "before changing the target site's root page"
    )

Page = env["website.page"].sudo()
specific_root_pages = Page.search([("website_id", "=", website.id), ("url", "=", "/")])
foreign_root_pages = specific_root_pages.filtered(
    lambda page: page.view_id.key != MODULE_HOMEPAGE_KEY
)
if foreign_root_pages:
    fail(
        "a website-specific homepage already exists at '/': "
        + ", ".join(f"{page.id}:{page.view_id.key}" for page in foreign_root_pages)
        + ". Archive it recoverably before deployment."
    )

generic_root_pages = Page.search([("website_id", "=", False), ("url", "=", "/")])
evidence = {
    "website_id": website.id,
    "website_name": website.name,
    "domain": website.domain,
    "favicon_present": bool(website.favicon),
    "customer_account": website.auth_signup_uninvited,
    "homepage_url": website.homepage_url or "/",
    "generic_homepages": [
        {"page_id": page.id, "view_key": page.view_id.key, "published": page.is_published}
        for page in generic_root_pages
    ],
    "module_homepages": [
        {"page_id": page.id, "view_key": page.view_id.key, "published": page.is_published}
        for page in specific_root_pages
    ],
}
print(json.dumps(evidence, sort_keys=True))

