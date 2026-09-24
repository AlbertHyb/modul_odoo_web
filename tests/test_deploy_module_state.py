import contextlib
import io
import runpy
import unittest
from pathlib import Path
from types import SimpleNamespace


ROOT = Path(__file__).parents[1]
SCRIPT = ROOT / "deploy/odoo/module_state_financa.py"


class Recordset(list):
    def ensure_one(self):
        if len(self) != 1:
            raise AssertionError("expected one module")
        return self[0]


class ModuleModel:
    def __init__(self, state):
        self.records = [] if state is None else [SimpleNamespace(state=state)]

    def sudo(self):
        return self

    def search(self, domain):
        self.domain = domain
        return Recordset(self.records)


class FakeEnv:
    def __init__(self, state):
        self.model = ModuleModel(state)

    def __getitem__(self, name):
        if name != "ir.module.module":
            raise AssertionError(name)
        return self.model


class ModuleStateTest(unittest.TestCase):
    def action_for(self, state):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            runpy.run_path(SCRIPT, init_globals={"env": FakeEnv(state)})
        return output.getvalue().strip()

    def test_install_for_new_or_uninstalled_module(self):
        self.assertEqual(self.action_for(None), "FINANCA_MODULE_ACTION=install")
        self.assertEqual(self.action_for("uninstalled"), "FINANCA_MODULE_ACTION=install")

    def test_update_only_for_installed_module(self):
        self.assertEqual(self.action_for("installed"), "FINANCA_MODULE_ACTION=update")

    def test_rejects_transitional_state(self):
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            self.action_for("to upgrade")


if __name__ == "__main__":
    unittest.main()
