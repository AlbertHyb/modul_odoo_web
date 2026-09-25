import io
import json
import os
import sys
import tempfile
import unicodedata
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).parents[1]
ODOO = ROOT / "deploy/odoo"
CLEANUP = ODOO / "cleanup_financa_legacy.py"
POSTFLIGHT = ODOO / "postflight_financa.py"
INVENTORY = ODOO / "financa_legacy.json"
PRODUCTION = ROOT / "deploy/server/financa-production-deploy.sh"

BLOCK_START = "# --- Financa legacy inventory helpers ---"
BLOCK_END = "# --- end Financa legacy inventory helpers ---"


def helper_block(script):
    text = script.read_text()
    start = text.index(BLOCK_START)
    end = text.index(BLOCK_END) + len(BLOCK_END)
    return text[start:end]


def helpers(script):
    namespace = {"json": json, "os": os, "sys": sys, "unicodedata": unicodedata}
    exec(compile(helper_block(script), str(script), "exec"), namespace)
    return namespace


class Stub:
    def __init__(self, **fields):
        self.__dict__.update(fields)

    def get_external_id(self):
        return {self.id: self.xmlid}


def menu(identifier, name, url="", page_url=None, xmlid=False, active=True):
    return Stub(
        id=identifier,
        name=name,
        url=url,
        page_id=Stub(id=identifier + 1000, url=page_url) if page_url else False,
        xmlid=xmlid,
        active=active,
    )


def page(identifier, url, website_id, xmlid=False, published=True):
    return Stub(
        id=identifier,
        url=url,
        website_id=Stub(id=website_id),
        xmlid=xmlid,
        is_published=published,
    )


class FinancaLegacyInventoryTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cleanup = helpers(CLEANUP)
        cls.postflight = helpers(POSTFLIGHT)

    def test_helper_blocks_are_identical_in_both_steps(self):
        self.assertEqual(helper_block(CLEANUP), helper_block(POSTFLIGHT))

    def test_inventory_catalogues_the_observed_legacy_content(self):
        inventory = self.cleanup["load_legacy_inventory"](INVENTORY)
        self.assertEqual(inventory["pages"], ["/our-services"])
        labels = {entry.get("name") for entry in inventory["menus"]}
        self.assertIn("Servicios", labels)
        self.assertIn("Noticias", labels)
        self.assertIn("Histórias de éxito", labels)
        self.assertIn("Sobre nosotros", labels)
        self.assertIn({"name": "Servicios", "url": "/our-services"}, inventory["menus"])

    def test_inventory_rejects_broken_documents(self):
        load = self.cleanup["load_legacy_inventory"]
        cases = {
            "missing file": None,
            "malformed json": "{",
            "not an object": "[]",
            "empty": "{}",
            "lists of the wrong type": '{"menus": "x", "pages": []}',
            "menu entry without a name or url": '{"menus": [{}]}',
            "menu entry with a non string label": '{"menus": [{"name": 5}]}',
            "page entry that is not absolute": '{"pages": ["our-services"]}',
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "inventory.json"
            for name, document in cases.items():
                with self.subTest(name):
                    path.unlink(missing_ok=True)
                    if document is not None:
                        path.write_text(document)
                    with self.assertRaises(ValueError):
                        load(path)

    def test_menu_matching_ignores_accents_and_case(self):
        matches = self.cleanup["legacy_menu_matches"]
        self.assertTrue(matches(menu(1, "Histórias de éxito"), {"name": "Historias de exito"}))
        self.assertTrue(matches(menu(1, "HistORIAS   DE EXITO"), {"name": "Histórias de éxito"}))
        self.assertFalse(matches(menu(1, "Sobre nosotros"), {"name": "Historias de exito"}))

    def test_menu_matching_uses_the_url_and_the_linked_page(self):
        matches = self.cleanup["legacy_menu_matches"]
        self.assertTrue(matches(menu(1, "Servicios", url="/our-services"), {"url": "/our-services"}))
        self.assertTrue(matches(menu(2, "Servicios", page_url="/our-services"), {"url": "/our-services"}))
        self.assertFalse(matches(menu(3, "Contacto", url="/contactus"), {"url": "/our-services"}))
        self.assertFalse(matches(menu(4, "Noticias"), {"url": "/our-services"}))

    def test_module_records_are_never_legacy(self):
        selection = self.cleanup["legacy_menus"]
        inventory = {"menus": [{"name": "Servicios"}], "pages": []}
        records = [
            menu(1, "Servicios", xmlid="financa_website.menu_financa_services"),
            menu(2, "Servicios"),
        ]
        self.assertEqual([record.id for record in selection(records, inventory)], [2])

    def test_pages_require_the_target_website_and_no_module_owner(self):
        selection = self.cleanup["legacy_pages"]
        inventory = {"menus": [], "pages": ["/our-services"]}
        records = [
            page(1, "/our-services", website_id=7),
            page(2, "/our-services", website_id=False),
            page(3, "/our-services", website_id=8),
            page(4, "/our-services", website_id=7, xmlid="financa_website.financa_homepage"),
            page(5, "/contactus", website_id=7),
        ]
        self.assertEqual([record.id for record in selection(records, inventory, 7)], [1])


class FinancaLegacyDeploymentContractTest(unittest.TestCase):
    def test_production_pipeline_sanitizes_before_the_gate(self):
        script = PRODUCTION.read_text()
        self.assertIn('legacy_inventory="$release/deploy/odoo/financa_legacy.json"', script)
        self.assertIn('[[ -f "$legacy_inventory" ]]', script)
        self.assertIn('-e FINANCA_LEGACY_INVENTORY="$legacy_inventory"', script)
        self.assertEqual(script.count("cleanup_financa_legacy.py"), 1)
        order = [
            "run_module_action\n",
            "cleanup_financa_legacy.py",
            "configure_financa.py",
            "postflight_financa.py",
        ]
        positions = [script.index(token) for token in order]
        self.assertEqual(positions, sorted(positions))

    def test_cleanup_only_deactivates_and_unpublishes(self):
        cleanup = CLEANUP.read_text()
        self.assertIn('INVENTORY = os.environ["FINANCA_LEGACY_INVENTORY"]', cleanup)
        self.assertIn('menu.write({"active": False})', cleanup)
        self.assertIn('page.write({"is_published": False})', cleanup)
        self.assertIn('menu.write({"parent_id": root_menu.id})', cleanup)
        self.assertNotIn("unlink", cleanup)
        self.assertIn('"changed"', cleanup)
        self.assertIn('"shared_legacy_pages"', cleanup)

    def test_postflight_gates_the_navigation_and_the_legacy_content(self):
        postflight = POSTFLIGHT.read_text()
        self.assertIn('LEGACY_INVENTORY = os.environ["FINANCA_LEGACY_INVENTORY"]', postflight)
        self.assertIn("load_legacy_inventory(LEGACY_INVENTORY)", postflight)
        for key in (
            "financa_website.menu_financa_services",
            "financa_website.menu_financa_odoo",
            "financa_website.menu_financa_diagnosis",
            "financa_website.menu_financa_process",
            "financa_website.menu_financa_contact",
            "financa_website.menu_financa_login",
        ):
            self.assertIn(key, postflight)
        self.assertIn("no longer top-level navigation items", postflight)
        self.assertIn("catalogued legacy content is still live", postflight)
        self.assertIn("duplicate a Financa navigation label", postflight)
        self.assertIn('"legacy_gate"', postflight)


class FakeRecord:
    def __init__(self, model, **values):
        self._model = model
        self.__dict__.update(values)

    def write(self, values):
        for name, value in values.items():
            target = self._model.relations.get(name)
            if target and isinstance(value, int):
                value = self._model.env[target].by_id(value)
            self.__dict__[name] = value
        return True

    def get_external_id(self):
        return {self.id: self._model.xmlids.get(self.id) or False}


def iter_records(value):
    if isinstance(value, Recordset):
        return list(value._records)
    if isinstance(value, FakeRecord):
        return [value]
    return []


def field_value(record, name):
    value = getattr(record, name, False)
    return value.id if isinstance(value, FakeRecord) else value


def domain_matches(record, domain):
    for name, operator, expected in domain:
        actual = field_value(record, name)
        if operator == "=" and actual != expected:
            return False
        if operator == "!=" and actual == expected:
            return False
        if operator == "in" and actual not in expected:
            return False
    return True


class Recordset:
    def __init__(self, model, records):
        self._model = model
        self._records = list(records)

    def __iter__(self):
        return iter(self._records)

    def __len__(self):
        return len(self._records)

    def __bool__(self):
        return bool(self._records)

    def __contains__(self, item):
        return any(record.id == item.id for record in self._records)

    def __or__(self, other):
        records = list(self._records)
        known = [record.id for record in records]
        for record in iter_records(other):
            if record.id not in known:
                known.append(record.id)
                records.append(record)
        return Recordset(self._model, records)

    def __sub__(self, other):
        removed = {record.id for record in iter_records(other)}
        return Recordset(self._model, [r for r in self._records if r.id not in removed])

    def __getattr__(self, name):
        records = self.__dict__.get("_records", [])
        if len(records) == 1:
            return getattr(records[0], name)
        raise AttributeError(name)

    def ensure_one(self):
        assert len(self._records) == 1, f"expected one record, found {len(self._records)}"
        return self._records[0]

    def sudo(self):
        return self

    def browse(self, ids=()):
        return self._model.browse(ids)

    def search(self, domain):
        return self._model.search(domain)


class FakeModel:
    def __init__(self, env, name):
        self.env = env
        self.name = name
        self.records = []
        self.xmlids = {}
        self.relations = {}

    def add(self, xmlid=None, **values):
        record = FakeRecord(self, **values)
        self.records.append(record)
        if xmlid:
            self.xmlids[record.id] = xmlid
        return record

    def sudo(self):
        return self

    def browse(self, ids=()):
        return Recordset(self, [self.by_id(identifier) for identifier in ids or []])

    def search(self, domain):
        return Recordset(self, [r for r in self.records if domain_matches(r, domain)])

    def by_id(self, identifier):
        return next(record for record in self.records if record.id == identifier)


class FakeEnv:
    MODELS = ("ir.ui.view", "website", "website.menu", "website.page", "website.rewrite")
    RELATIONS = {
        "website.menu": {
            "website_id": "website",
            "parent_id": "website.menu",
            "page_id": "website.page",
        },
        "website.page": {"website_id": "website"},
        "website.rewrite": {"website_id": "website"},
    }

    def __init__(self):
        self.models = {name: FakeModel(self, name) for name in self.MODELS}
        for name, relations in self.RELATIONS.items():
            self.models[name].relations = dict(relations)

    def __getitem__(self, name):
        return self.models[name]

    def ref(self, xmlid, raise_if_not_found=True):
        model = self.models["website.menu"]
        for identifier, key in model.xmlids.items():
            if key == xmlid:
                return model.by_id(identifier)
        if raise_if_not_found:
            raise KeyError(xmlid)
        return False


def build_production_like_env():
    """Recreate the production database: the new module plus the previous site's menu tree."""
    env = FakeEnv()
    website = env["website"].add(
        id=1,
        name="Financa Consultores",
        domain="https://financa.mx",
        cookies_bar=True,
        google_analytics_key="G-TEST",
    )
    root = env["website.menu"].add(
        id=100,
        name="Financa Consultores",
        url="",
        active=True,
        parent_id=False,
        page_id=False,
        child_id=Recordset(env["website.menu"], []),
        website_id=website,
    )
    website.menu_id = root

    def add_menu(identifier, name, url="", parent=None, xmlid=None, page_id=False):
        record = env["website.menu"].add(
            id=identifier,
            name=name,
            url=url,
            active=True,
            parent_id=parent if parent is not None else False,
            page_id=page_id,
            child_id=Recordset(env["website.menu"], []),
            website_id=website,
            xmlid=xmlid,
        )
        if parent is not None:
            parent.child_id = parent.child_id | record
        return record

    def add_page(identifier, url, published, key, owner=None):
        return env["website.page"].add(
            id=identifier,
            url=url,
            is_published=published,
            website_id=owner if owner is not None else website,
            view_id=env["ir.ui.view"].add(id=identifier + 500, key=key),
            key=key,
        )

    legacy_landing = add_page(202, "/our-services", True, False)
    add_menu(101, "Inicio", url="/")
    add_menu(102, "Servicios", url="/our-services", page_id=legacy_landing)
    noticias = add_menu(103, "Noticias", url="/noticias")
    add_menu(104, "Histórias de éxito", url="/casos", parent=noticias)
    add_menu(105, "Sobre nosotros", url="/nosotros", parent=noticias)
    add_menu(
        106,
        "Proceso",
        url="/#proceso",
        parent=noticias,
        xmlid="financa_website.menu_financa_process",
    )
    add_menu(110, "Ecosistema", url="/#ecosistema", parent=root, xmlid="financa_website.menu_financa_services")
    add_menu(111, "Odoo ERP", url="/#odoo-erp", parent=root, xmlid="financa_website.menu_financa_odoo")
    add_menu(112, "Diagnóstico", url="/#diagnostico", parent=root, xmlid="financa_website.menu_financa_diagnosis")
    add_menu(113, "Contacto", url="/contactus", parent=root, xmlid="financa_website.menu_financa_contact")
    add_menu(114, "Acceso a clientes", url="/web/login", parent=root, xmlid="financa_website.menu_financa_login")

    add_page(200, "/", True, "financa_website.financa_homepage")
    add_page(201, "/aviso-de-privacidad", False, "financa_website.financa_privacy_page")
    add_page(203, "/our-services", True, False, owner=False)

    env["website.rewrite"].add(
        id=300,
        url_from="/financa-consultores",
        url_to="/",
        redirect_type="301",
        active=True,
        website_id=website,
    )
    return env


def run_step(script, environment):
    """Execute one deployment step against a fake Odoo env.

    Returns (stdout, stderr, exit code), so a gate failure is an observable
    result instead of an exception escaping the test.
    """
    stdout, stderr = io.StringIO(), io.StringIO()
    status = 0
    with tempfile.TemporaryDirectory() as directory:
        inventory = Path(directory) / "financa_legacy.json"
        inventory.write_text(INVENTORY.read_text())
        variables = {
            "FINANCA_DOMAIN": "https://financa.mx",
            "FINANCA_LEGACY_INVENTORY": str(inventory),
        }
        with mock.patch.dict(os.environ, variables):
            try:
                with redirect_stdout(stdout), redirect_stderr(stderr):
                    exec(compile(script.read_text(), str(script), "exec"), {"env": environment})
            except SystemExit as exit_error:
                status = exit_error.code
    return stdout.getvalue(), stderr.getvalue(), status


class FinancaLegacyRuntimeTest(unittest.TestCase):
    def test_cleanup_neutralizes_the_legacy_tree_and_keeps_the_module_navigation(self):
        environment = build_production_like_env()
        stdout, _, status = run_step(CLEANUP, environment)
        self.assertEqual(status, 0)
        evidence = json.loads(stdout)
        menu = environment["website.menu"].by_id

        self.assertTrue(evidence["changed"])
        self.assertEqual(
            {entry["id"] for entry in evidence["deactivated_menus"]}, {102, 103, 104, 105}
        )
        self.assertEqual([entry["id"] for entry in evidence["reparented_menus"]], [106])
        self.assertEqual([entry["id"] for entry in evidence["unpublished_pages"]], [202])

        self.assertFalse(menu(102).active)
        self.assertFalse(menu(103).active)
        self.assertFalse(menu(104).active)
        self.assertFalse(menu(105).active)
        self.assertTrue(menu(101).active)
        self.assertEqual(menu(106).parent_id, environment["website"].by_id(1).menu_id)
        self.assertEqual(menu(110).parent_id, environment["website"].by_id(1).menu_id)
        self.assertFalse(environment["website.page"].by_id(202).is_published)
        self.assertTrue(environment["website.page"].by_id(200).is_published)
        self.assertEqual(
            [entry["id"] for entry in evidence["audit"]["remaining_foreign_active_menus"]], [101]
        )
        self.assertEqual(
            [entry["url"] for entry in evidence["audit"]["shared_legacy_pages"]], ["/our-services"]
        )

    def test_cleanup_is_idempotent(self):
        environment = build_production_like_env()
        run_step(CLEANUP, environment)
        stdout, _, status = run_step(CLEANUP, environment)
        self.assertEqual(status, 0)
        evidence = json.loads(stdout)
        self.assertFalse(evidence["changed"])
        self.assertEqual(evidence["deactivated_menus"], [])
        self.assertEqual(evidence["reparented_menus"], [])
        self.assertEqual(evidence["unpublished_pages"], [])

    def test_postflight_accepts_the_sanitized_website(self):
        environment = build_production_like_env()
        run_step(CLEANUP, environment)
        stdout, _, status = run_step(POSTFLIGHT, environment)
        self.assertEqual(status, 0)
        report = json.loads(stdout)
        self.assertEqual(report["legacy_gate"]["active_legacy_menus"], 0)
        self.assertEqual(report["legacy_gate"]["published_legacy_pages"], 0)
        self.assertEqual(report["legacy_gate"]["duplicate_menu_labels"], 0)

    def test_postflight_rejects_an_unsanitized_website(self):
        environment = build_production_like_env()
        _, stderr, status = run_step(POSTFLIGHT, environment)
        self.assertEqual(status, 1)
        self.assertIn("POST-FLIGHT FAILED", stderr)

    def test_postflight_rejects_catalogued_content_that_came_back(self):
        environment = build_production_like_env()
        run_step(CLEANUP, environment)
        environment["website.menu"].by_id(102).write({"active": True})
        stdout, stderr, status = run_step(POSTFLIGHT, environment)
        self.assertEqual(status, 1)
        self.assertEqual(stdout, "")
        self.assertIn("catalogued legacy content is still live", stderr)
        self.assertIn("menu 102:Servicios", stderr)

    def test_postflight_rejects_a_module_menu_that_left_the_top_level(self):
        environment = build_production_like_env()
        run_step(CLEANUP, environment)
        noticias = environment["website.menu"].by_id(103)
        noticias.write({"active": True})
        environment["website.menu"].by_id(113).write({"parent_id": noticias})
        stdout, stderr, status = run_step(POSTFLIGHT, environment)
        self.assertEqual(status, 1)
        self.assertEqual(stdout, "")
        self.assertIn("no longer top-level navigation items", stderr)

    def test_postflight_rejects_a_foreign_menu_duplicating_a_financa_label(self):
        environment = build_production_like_env()
        run_step(CLEANUP, environment)
        environment["website.menu"].add(
            id=120,
            name="Acceso a clientes",
            url="/portal",
            active=True,
            parent_id=False,
            page_id=False,
            child_id=Recordset(environment["website.menu"], []),
            website_id=environment["website"].by_id(1),
            xmlid=None,
        )
        stdout, stderr, status = run_step(POSTFLIGHT, environment)
        self.assertEqual(status, 1)
        self.assertEqual(stdout, "")
        self.assertIn("duplicate a Financa navigation label", stderr)


if __name__ == "__main__":
    unittest.main()
