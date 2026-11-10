import contextlib
import io
import json
import os
import runpy
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).parents[1]
SCRIPT = ROOT / "deploy/odoo/configure_financa.py"
DOMAIN = "https://financa.mx"


class Recordset(list):
    def ensure_one(self):
        if len(self) != 1:
            raise AssertionError(f"expected one record, found {len(self)}")
        return self[0]


class Website:
    def __init__(self, tag=None):
        self.id = 7
        self.cookies_bar = False
        self.google_analytics_key = tag

    def write(self, values):
        if "group_ids" in values:
            self.group_ids.extend(command[1] for command in values["group_ids"] if command[0] == 4)
        self.__dict__.update({key: value for key, value in values.items() if key != "group_ids"})


class Menu:
    def __init__(self, identifier, group_ids=()):
        self.id = identifier
        self.group_ids = list(group_ids)

    def write(self, values):
        self.group_ids.extend(command[1] for command in values.get("group_ids", []) if command[0] == 4)


class Model:
    def __init__(self, records):
        self.records = records

    def sudo(self):
        return self

    def search(self, domain):
        return Recordset(self.records)


class Cursor:
    """`odoo shell` rolls back on exit, so a step only persists what it commits."""

    def __init__(self):
        self.commits = 0

    def commit(self):
        self.commits += 1


class FakeEnv:
    def __init__(self, website, menus, module_menu=None):
        self.website = website
        self.models = {"website": Model([website]), "website.menu": Model(menus)}
        self.module_menu = module_menu
        self.hidden_group = type("Group", (), {"id": 99})()
        self.cr = Cursor()

    def __getitem__(self, name):
        return self.models[name]

    def ref(self, xmlid, raise_if_not_found=True):
        if xmlid == "base.group_no_one":
            return self.hidden_group
        if self.module_menu is None and raise_if_not_found:
            raise KeyError(xmlid)
        return self.module_menu


class ConfigureTest(unittest.TestCase):
    def configure(self, website, menus=(), module_menu=None, require_ga4="true"):
        output, errors = io.StringIO(), io.StringIO()
        environment = FakeEnv(website, list(menus), module_menu)
        self.environment = environment
        variables = {"FINANCA_DOMAIN": DOMAIN, "REQUIRE_GA4": require_ga4}
        status = 0
        with mock.patch.dict(os.environ, variables):
            with contextlib.redirect_stdout(output), contextlib.redirect_stderr(errors):
                try:
                    runpy.run_path(SCRIPT, init_globals={"env": environment})
                except SystemExit as exit_error:
                    status = exit_error.code
        return output.getvalue(), errors.getvalue(), status

    def test_evidence_reports_a_google_tag_manager_container(self):
        website = Website("GTM-KC4KR95Z")
        stdout, _, status = self.configure(website)
        self.assertEqual(status, 0)
        evidence = json.loads(stdout)
        self.assertEqual(evidence["analytics_tag_kind"], "gtm")
        self.assertTrue(evidence["ga4_configured"])
        self.assertTrue(website.cookies_bar)

    def test_the_configuration_is_committed(self):
        _, _, status = self.configure(Website("G-ABCDEF1234"))
        self.assertEqual(status, 0)
        self.assertEqual(self.environment.cr.commits, 1)

    def test_a_failed_configuration_is_not_committed(self):
        _, _, status = self.configure(Website(None))
        self.assertEqual(status, 1)
        self.assertEqual(self.environment.cr.commits, 0)

    def test_evidence_reports_a_ga4_measurement_id(self):
        stdout, _, status = self.configure(Website("G-ABCDEF1234"))
        self.assertEqual(status, 0)
        self.assertEqual(json.loads(stdout)["analytics_tag_kind"], "ga4")

    def test_evidence_reports_an_unknown_tag(self):
        stdout, _, status = self.configure(Website("AW-123456789"))
        self.assertEqual(status, 0)
        self.assertEqual(json.loads(stdout)["analytics_tag_kind"], "other")

    def test_a_missing_tag_stops_the_deployment_unless_it_is_not_required(self):
        stdout, stderr, status = self.configure(Website(None))
        self.assertEqual(status, 1)
        self.assertEqual(stdout, "")
        self.assertIn("no analytics tag", stderr)
        self.assertIn("Google Tag Manager container", stderr)

        stdout, _, status = self.configure(Website(None), require_ga4="false")
        self.assertEqual(status, 0)
        self.assertEqual(json.loads(stdout)["analytics_tag_kind"], "none")

    def test_only_the_module_contact_menu_survives(self):
        module_menu = Menu(2)
        duplicate = Menu(1)
        inactive = Menu(3, group_ids=[99])
        stdout, _, status = self.configure(
            Website("G-ABCDEF1234"), [duplicate, module_menu, inactive], module_menu
        )
        self.assertEqual(status, 0)
        self.assertTrue(duplicate.group_ids)
        self.assertFalse(module_menu.group_ids)
        self.assertTrue(inactive.group_ids)
        self.assertEqual(json.loads(stdout)["website_id"], 7)


if __name__ == "__main__":
    unittest.main()
