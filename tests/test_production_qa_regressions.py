import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]
SCRIPT = ROOT / "deploy/server/financa-production-deploy.sh"


class ProductionQaRegressionTest(unittest.TestCase):
    def test_mutating_failures_call_rollback_explicitly(self):
        script = SCRIPT.read_text()
        self.assertEqual(script.count("rollback 1"), 3)
        self.assertNotIn('wait_for_health "$local_health" || die', script)
        self.assertNotIn('wait_for_health "$public_health" || die', script)
        self.assertNotIn("|| die 'backup hook did not return", script)

    def test_root_executes_only_installed_trusted_deploy_files(self):
        script = SCRIPT.read_text()
        self.assertIn('compose=(docker compose --env-file "$COMPOSE_ENV_FILE" -f "$COMPOSE_FILE")', script)
        self.assertIn('validate_root_file "$COMPOSE_FILE"', script)
        self.assertIn('validate_root_executable "$FINANCA_VERIFY_BIN"', script)
        self.assertNotIn('python3 "$repo/deploy/ci/verify_financa_artifact.py"', script)

    def test_artifact_comes_from_a_clean_checkout_and_becomes_root_owned(self):
        script = SCRIPT.read_text()
        self.assertIn("status --porcelain --untracked-files=all", script)
        self.assertIn('git -C "$repo" archive "$sha"', script)
        self.assertIn('staged_release="$render_root/$sha"', script)
        self.assertIn('chown -R root:root "$staged_release"', script)
        self.assertIn('chmod -R go-w "$staged_release"', script)


if __name__ == "__main__":
    unittest.main()
