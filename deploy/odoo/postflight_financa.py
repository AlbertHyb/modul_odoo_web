"""Run with `odoo-bin shell -d <database>` after updating financa_website."""

import json
import os
import sys


DOMAIN = os.environ["FINANCA_DOMAIN"]


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

print(
    json.dumps(
        {
            "website_id": website.id,
            "homepage_id": homepage.id,
            "privacy_page_id": privacy_page.id,
            "redirect_id": rewrite.id,
            "cookies_bar": website.cookies_bar,
            "ga4_configured": bool(website.google_analytics_key),
        },
        sort_keys=True,
    )
)

