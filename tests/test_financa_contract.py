import ast
import re
import unittest
from pathlib import Path
from xml.etree import ElementTree


ROOT = Path(__file__).parents[1]
ADDON = ROOT / "financa_website"


class FinancaContractTest(unittest.TestCase):
    def test_module_contract(self):
        manifest = ast.literal_eval((ADDON / "__manifest__.py").read_text())
        self.assertEqual(manifest["version"], "19.0.1.0.0")
        self.assertEqual(manifest["depends"], ["website"])
        self.assertEqual(len(manifest["assets"]["web.assets_frontend"]), 4)

        for xml_file in ADDON.rglob("*.xml"):
            ElementTree.parse(xml_file)

        snippets = (ADDON / "views/snippets.xml").read_text()
        self.assertEqual(snippets.count("t-snippet=\"financa_website.snippet_"), 7)
        self.assertEqual(snippets.count("<h1>"), 1)

        redirects = (ADDON / "data/redirects.xml").read_text()
        self.assertIn("<field name=\"redirect_type\">301</field>", redirects)
        self.assertIn("('domain', '=', 'https://financa-mx')", redirects)

        tracking = (ADDON / "static/src/js/financa_tracking.js").read_text()
        for event in (
            "financa_section_view",
            "financa_cta_click",
            "financa_contact_view",
            "financa_form_start",
            "generate_lead",
            "financa_login_click",
            "financa_experiment_exposure",
        ):
            self.assertIn(event, tracking)
        self.assertIsNone(re.search(r"G-[A-Z0-9]{10}", tracking))

        experiments = (ADDON / "static/src/js/financa_experiments.js").read_text()
        self.assertIn("EXPERIMENTS_ENABLED = false", experiments)


    def test_deployment_contract(self):
        deploy_root = ROOT / "deploy"
        required_files = (
            "ci/publish_financa.sh",
            "server/deploy_financa.sh",
            "server/financa-deploy.env.example",
            "odoo/preflight_financa.py",
            "odoo/module_state_financa.py",
            "odoo/configure_financa.py",
            "odoo/postflight_financa.py",
        )
        for relative_path in required_files:
            self.assertTrue((deploy_root / relative_path).is_file(), relative_path)

        server_script = (deploy_root / "server/deploy_financa.sh").read_text()
        self.assertIn("run_odoo_shell", server_script)
        self.assertIn('module_action == "install"', server_script)
        self.assertIn("-i financa_website", server_script)
        self.assertIn("-u financa_website", server_script)
        self.assertIn("FINANCA_BACKUP_BIN", server_script)
        self.assertIn("FINANCA_RESTORE_BIN", server_script)
        self.assertIn("flock -n", server_script)
        self.assertIn("systemctl stop", server_script)

        ci_script = (deploy_root / "ci/publish_financa.sh").read_text()
        self.assertIn("StrictHostKeyChecking=yes", ci_script)
        self.assertIn("/usr/local/sbin/financa-deploy", ci_script)

if __name__ == "__main__":
    unittest.main()

