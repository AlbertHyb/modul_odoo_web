import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]
COMPOSE = ROOT / "deploy/compose/compose.yaml"
ENV = ROOT / "deploy/compose/.env.example"


class StagingComposeContractTest(unittest.TestCase):
    def test_compose_has_only_private_database_and_loopback_odoo(self):
        compose = COMPOSE.read_text()
        self.assertIn("  db:\n", compose)
        self.assertIn("  odoo:\n", compose)
        self.assertEqual(compose.count("    image:"), 2)
        self.assertNotIn("      - \"5432", compose)
        self.assertIn('      - "127.0.0.1:${ODOO_PORT:-8069}:8069"', compose)
        self.assertIn("    internal: true", compose)
        self.assertIn("condition: service_healthy", compose)
        self.assertIn("postgres_password", compose)

    def test_images_are_pinned_and_environment_has_no_secret_value(self):
        environment = ENV.read_text()
        self.assertIn("ODOO_IMAGE=odoo@sha256:", environment)
        self.assertIn("POSTGRES_IMAGE=postgres@sha256:", environment)
        self.assertIn("POSTGRES_PASSWORD_FILE=/etc/financa-staging/secrets/postgres_password", environment)
        self.assertIn("ODOO_CONFIG_FILE=/etc/financa-staging/odoo.conf", environment)
        self.assertNotIn("POSTGRES_PASSWORD=", environment)

    def test_ci_actions_are_pinned_to_commits(self):
        workflow = (ROOT / ".github/workflows/validate.yml").read_text()
        self.assertIn("actions/checkout@11d5960a326750d5838078e36cf38b85af677262", workflow)
        self.assertIn("actions/setup-python@a26af69be951a213d495a4c3e4e4022e16d87065", workflow)
        self.assertNotIn("@v", workflow)

    def test_odoo_configuration_blocks_database_manager_and_real_smtp(self):
        config = (ROOT / "deploy/compose/odoo.conf").read_text()
        self.assertIn("/usr/lib/python3/dist-packages/odoo/addons,/mnt/extra-addons", config)
        self.assertIn("db_name = financa_staging", config)
        self.assertIn("dbfilter = ^financa_staging$", config)
        self.assertIn("list_db = False", config)
        self.assertIn("proxy_mode = True", config)
        self.assertIn("smtp_server = 127.0.0.1", config)
        self.assertIn("ODOO_CONFIG_FILE", COMPOSE.read_text())
        self.assertIn("smtp_port = 9", config)


if __name__ == "__main__":
    unittest.main()
