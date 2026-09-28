import hashlib
import json
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]
WORKFLOW = ROOT / ".github/workflows/deploy-production.yml"
SCRIPT = ROOT / "deploy/server/financa-production-deploy.sh"
VERIFIER = ROOT / "deploy/ci/verify_financa_artifact.py"
BACKUP = ROOT / "deploy/server/financa-production-r2-backup.sh"
RESTORE = ROOT / "deploy/server/financa-production-r2-restore.sh"

class ProductionCdContractTest(unittest.TestCase):
    def test_workflow_is_manual_protected_and_separate_from_staging(self):
        workflow = WORKFLOW.read_text()
        self.assertIn("workflow_dispatch:", workflow)
        self.assertNotIn("push:", workflow)
        self.assertNotIn("pull_request:", workflow)
        self.assertIn("environment: production", workflow)
        self.assertIn("needs: validate", workflow)
        self.assertIn("cancel-in-progress: false", workflow)
        self.assertIn("timeout-minutes: 30", workflow)
        self.assertIn('"deploy $GITHUB_SHA"', workflow)
        self.assertNotIn("STAGING_", workflow)
        for name in (
            "PRODUCTION_SSH_HOST",
            "PRODUCTION_SSH_PORT",
            "PRODUCTION_SSH_USER",
            "PRODUCTION_DOMAIN",
            "PRODUCTION_SSH_PRIVATE_KEY",
            "PRODUCTION_SSH_KNOWN_HOSTS",
        ):
            self.assertIn(name, workflow)

    def test_server_deploy_has_production_gates(self):
        script = SCRIPT.read_text()
        for contract in (
            "SSH_ORIGINAL_COMMAND",
            "origin/master",
            "current origin/master tip",
            "FINANCA_VERIFY_BIN",
            "--environment production",
            "docker compose",
            "FINANCA_BACKUP_BIN",
            "FINANCA_RESTORE_BIN",
            "flock -n",
            "-i financa_website",
            "-u financa_website",
            "module_state_financa.py",
            "preflight_financa.py",
            "cleanup_financa_legacy.py",
            "FINANCA_LEGACY_INVENTORY",
            "mv -Tf",
            "--max-time 10",
            "for _ in {1..12}",
            "RECOVERY FAILED: Odoo remains stopped",
        ):
            self.assertIn(contract, script)

    def test_r2_hooks_create_and_restore_one_paired_recovery_point(self):
        backup = BACKUP.read_text()
        restore = RESTORE.read_text()

        for script in (backup, restore):
            self.assertIn("R2_ENDPOINT", script)
            self.assertIn("R2_BUCKET", script)
            self.assertIn("R2_AWS_PROFILE", script)
            self.assertIn("--endpoint-url", script)
            self.assertIn("docker compose --env-file", script)

        self.assertIn("pg_dump", backup)
        self.assertIn("filestore.tar.gz", backup)
        self.assertIn("manifest.sha256", backup)
        self.assertIn("pg_restore", restore)
        self.assertIn("sha256sum -c manifest.sha256", restore)
        self.assertIn("recovery point is for another database", restore)

    def test_r2_hooks_are_valid_bash(self):
        for script in (BACKUP, RESTORE):
            result = subprocess.run(
                ["bash", "-n", str(script)],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)

    def test_verifier_accepts_exact_payload_and_rejects_changes(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            artifact = Path(temporary_directory)
            payload = artifact / "financa_website/__manifest__.py"
            payload.parent.mkdir()
            payload.write_text("{}\n")
            digest = hashlib.sha256(payload.read_bytes()).hexdigest()
            manifest = {
                "commit": "a" * 40,
                "domain": "https://financa.example.mx",
                "environment": "production",
                "files": {"financa_website/__manifest__.py": digest},
            }
            (artifact / "artifact-manifest.json").write_text(json.dumps(manifest))

            self.assertEqual(self.verify(artifact).returncode, 0)
            payload.write_text("changed\n")
            self.assertNotEqual(self.verify(artifact).returncode, 0)
            payload.write_text("{}\n")
            (artifact / "unexpected.txt").write_text("extra\n")
            self.assertNotEqual(self.verify(artifact).returncode, 0)

    def verify(self, artifact):
        return subprocess.run(
            [
                "python3",
                str(VERIFIER),
                "--artifact",
                str(artifact),
                "--commit",
                "a" * 40,
                "--environment",
                "production",
                "--domain",
                "https://financa.example.mx",
            ],
            capture_output=True,
            text=True,
            check=False,
        )


if __name__ == "__main__":
    unittest.main()
