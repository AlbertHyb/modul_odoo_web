"""Apply the website configuration that belongs to the Financa deployment."""

import json
import os
import sys


DOMAIN = os.environ["FINANCA_DOMAIN"]
REQUIRE_GA4 = os.environ.get("REQUIRE_GA4", "true").lower() == "true"

websites = env["website"].sudo().search([("domain", "=", DOMAIN)])
if len(websites) != 1:
    print(f"CONFIGURATION FAILED: expected one website for {DOMAIN!r}", file=sys.stderr)
    raise SystemExit(1)

website = websites.ensure_one()
website.write({"cookies_bar": True})
if REQUIRE_GA4 and not website.google_analytics_key:
    print("CONFIGURATION FAILED: GA4 is required but not configured on the target website", file=sys.stderr)
    raise SystemExit(1)

print(
    json.dumps(
        {
            "website_id": website.id,
            "cookies_bar": website.cookies_bar,
            "ga4_configured": bool(website.google_analytics_key),
        },
        sort_keys=True,
    )
)

