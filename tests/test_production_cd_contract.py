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
PRODUCTION_COMPOSE = ROOT / "deploy/compose/compose.production.yaml"

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
            self.assertIn("docker compose --project-name odoo --env-file", script)

        self.assertIn("pg_dump", backup)
        self.assertIn("filestore.tar.gz", backup)
        self.assertIn("manifest.sha256", backup)
        self.assertIn("pg_restore", restore)
        self.assertIn("sha256sum -c manifest.sha256", restore)
        self.assertIn("recovery point is for another database", restore)

    def test_production_compose_reuses_existing_docker_resources(self):
        compose = PRODUCTION_COMPOSE.read_text()
        self.assertIn("name: odoo", compose)
        self.assertNotIn("build:", compose)
        self.assertNotIn("/srv/financa-production/data", compose)
        self.assertNotIn("ODOO_DATA_DIR", compose)
        self.assertIn("image: odoo-odoo", compose)
        self.assertIn("name: odoo_default", compose)
        self.assertEqual(compose.count("external: true"), 5)
        for service in ("db:", "odoo:", "caddy:"):
            self.assertIn(f"  {service}", compose)
        self.assertIn("POSTGRES_PASSWORD_FILE: /run/secrets/postgres_password", compose)
        self.assertIn("PASSWORD_FILE: /run/secrets/postgres_password", compose)
        self.assertIn(":/mnt/extra-addons:ro", compose)
        self.assertIn(":/mnt/extra-addons/financa_website:ro", compose)
        self.assertIn("odoo_odoo-db-data", compose)
        self.assertIn("odoo_odoo-web-data", compose)
        self.assertIn("odoo_caddy_data", compose)
        self.assertIn("odoo_caddy_config", compose)
        self.assertIn("/etc/financa-production/Caddyfile:/etc/caddy/Caddyfile:ro", compose)
        self.assertIn("/etc/financa-production/odoo-resolv.conf:/etc/resolv.conf:ro", compose)
        self.assertNotIn("/home/deploy/odoo", compose)
        self.assertIn('"127.0.0.1:${ODOO_PORT:-8069}:8069"', compose)
        self.assertIn('"${ODOO_BIND_IP:?ODOO_BIND_IP must be set}:8069:8069"', compose)
        self.assertIn("--proxy-mode", compose)
        self.assertIn('"80:80"', compose)
        self.assertIn('"443:443"', compose)
        deploy = SCRIPT.read_text()
        self.assertIn("exactly caddy, db and odoo services", deploy)
        for script in (deploy, BACKUP.read_text(), RESTORE.read_text()):
            self.assertIn("docker compose --project-name odoo", script)
        self.assertNotIn("stop caddy", deploy)
        self.assertNotIn("stop db", deploy)
        self.assertNotIn("up -d --force-recreate --no-deps caddy", deploy)
        self.assertNotIn("up -d --force-recreate --no-deps db", deploy)

    def test_restore_uses_the_odoo_volume_only_after_its_guard(self):
        restore = RESTORE.read_text()
        backup = BACKUP.read_text()
        for script in (backup, restore):
            self.assertNotIn("ODOO_DATA_DIR", script)
            self.assertIn("/var/lib/odoo/filestore", script)
        self.assertIn("odoo must be stopped before restore", restore)
        self.assertLess(restore.index("odoo must be stopped before restore"), restore.index("pg_restore"))
        self.assertIn("target database does not exist", restore)
        self.assertIn('pg_restore -U "$POSTGRES_USER" --clean --if-exists -d "$database"', restore)
        self.assertNotIn("--create", restore)
        self.assertLess(restore.index('test -d "$staged/$2"'), restore.index("pg_restore"))
        self.assertIn('if ! mv "$staged/$database" "$base/$database"; then', restore)
        self.assertIn('test ! -e "$base/$database" && test -e "$previous" && mv "$previous" "$base/$database"', restore)
        self.assertLess(
            restore.index('test ! -e "$previous"'),
            restore.index("pg_restore"),
        )

    def test_r2_retention_is_enforced_by_bucket_policy_not_a_local_variable(self):
        backup = BACKUP.read_text()
        environment = (ROOT / "deploy/server/financa-production-deploy.env.example").read_text()
        self.assertNotIn("R2_RETENTION_DAYS", backup)
        self.assertNotIn("R2_RETENTION_DAYS", environment)

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
