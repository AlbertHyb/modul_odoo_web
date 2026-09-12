import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]
SCRIPT = ROOT / "deploy/server/financa-staging-deploy.sh"
WORKFLOW = ROOT / ".github/workflows/deploy-staging.yml"


class StagingCdContractTest(unittest.TestCase):
    def test_deploy_is_staging_only_and_uses_forced_command(self):
        script = SCRIPT.read_text()
        self.assertIn("SSH_ORIGINAL_COMMAND", script)
        self.assertIn("origin staging", script)
        self.assertIn("requested SHA is not the current origin/staging tip", script)
        self.assertNotIn("origin/master", script)
        self.assertNotIn(" -i financa_website", script)

    def test_deploy_renders_backups_updates_and_checks_health(self):
        script = SCRIPT.read_text()
        self.assertIn("render_financa_staging_artifact.py", script)
        self.assertIn("systemctl start --wait financa-staging-backup.service", script)
        self.assertIn("-u financa_website --stop-after-init", script)
        self.assertIn("mv -Tf", script)
        self.assertIn("Restoring the prior release symlink", script)
        self.assertIn("http://127.0.0.1:8069/web/login", script)
        self.assertIn("https://staging.financa.mx/web/login", script)

    def test_workflow_runs_only_for_staging_and_uses_secret_ssh_material(self):
        workflow = WORKFLOW.read_text()
        self.assertIn("branches: [staging]", workflow)
        self.assertIn("STAGING_SSH_PRIVATE_KEY", workflow)
        self.assertIn("STAGING_SSH_KNOWN_HOSTS", workflow)
        self.assertIn("deploy $GITHUB_SHA", workflow)
        self.assertIn("StrictHostKeyChecking=yes", workflow)


if __name__ == "__main__":
    unittest.main()
