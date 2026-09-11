"""Choose installation or update from the module state stored in Odoo."""

import sys


modules = env["ir.module.module"].sudo().search([("name", "=", "financa_website")])
if len(modules) > 1:
    print("MODULE STATE FAILED: duplicate module records", file=sys.stderr)
    raise SystemExit(1)

state = modules.ensure_one().state if modules else None
if state in (None, "uninstalled"):
    action = "install"
elif state == "installed":
    action = "update"
else:
    print(f"MODULE STATE FAILED: unsupported state {state!r}", file=sys.stderr)
    raise SystemExit(1)

print(f"FINANCA_MODULE_ACTION={action}")
