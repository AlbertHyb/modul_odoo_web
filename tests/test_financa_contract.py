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
        self.assertIn("data/homepage_ensure.xml", manifest["data"])

        for xml_file in ADDON.rglob("*.xml"):
            ElementTree.parse(xml_file)

        snippets = (ADDON / "views/snippets.xml").read_text()
        self.assertEqual(snippets.count("t-snippet=\"financa_website.snippet_"), 9)
        self.assertEqual(snippets.count("<h1>"), 1)

        redirects = (ADDON / "data/redirects.xml").read_text()
        self.assertIn("<field name=\"redirect_type\">301</field>", redirects)
        self.assertIn("('domain', '=', '__FINANCA_DOMAIN__')", redirects)
        self.assertNotIn("https://financa-mx", redirects)

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

        homepage_ensure = (ADDON / "data/homepage_ensure.xml").read_text()
        self.assertIn('model="website.page"', homepage_ensure)
        self.assertIn("_financa_archive_competing_homepage", homepage_ensure)

        model_file = (ADDON / "models/website_page.py").read_text()
        self.assertIn("_inherit = \"website.page\"", model_file)
        self.assertIn("_financa_archive_competing_homepage", model_file)
        self.assertIn("view_id.key", model_file)

        model_init = (ADDON / "models/__init__.py").read_text()
        self.assertIn("website_page", model_init)

    def test_qweb_fallbacks_are_domain_scoped(self):
        homepage = (ADDON / "views/homepage.xml").read_text()
        self.assertNotIn("$0", homepage)
        self.assertEqual(homepage.count("add=\"website.domain != '__FINANCA_DOMAIN__'\""), 2)
        self.assertIn("t-if=\"website.domain == '__FINANCA_DOMAIN__'\"", homepage)
        self.assertIn("t-if=\"website.domain == '__FINANCA_DOMAIN__' and not no_footer\"", homepage)


    def test_scss_avoids_libsass_min_with_calc(self):
        scss = (ADDON / "static/src/scss/financa.scss").read_text()
        self.assertNotIn("min(calc(", scss)
        self.assertIn("width: calc(100% - 40px);", scss)
        self.assertIn("width: calc(100% - 28px);", scss)
        self.assertIn("max-width: 1180px;", scss)

    def test_deployment_contract(self):
        deploy_root = ROOT / "deploy"
        required_files = (
            "ci/publish_financa.sh",
            "ci/render_financa_artifact.py",
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
        self.assertIn("DEPLOY_DOMAIN", ci_script)
        self.assertIn("render_financa_artifact.py", ci_script)
        self.assertIn("--environment production", ci_script)
        self.assertIn("artifact-manifest.json", ci_script)

        renderer = (deploy_root / "ci/render_financa_artifact.py").read_text()
        self.assertIn("__FINANCA_DOMAIN__", renderer)
        self.assertIn("STAGING_DOMAIN", renderer)
        self.assertIn("deploy/odoo/preflight_financa.py", renderer)
        self.assertIn('parser.add_argument("--domain", required=True)', renderer)
        self.assertIn('parser.add_argument("--environment", choices=ENVIRONMENTS, required=True)', renderer)

        env_example = (deploy_root / "server/financa-deploy.env.example").read_text()
        self.assertIn("DEPLOY_DOMAIN", env_example)

if __name__ == "__main__":
    unittest.main()

