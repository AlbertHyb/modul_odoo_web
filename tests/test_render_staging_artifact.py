import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]
SCRIPT = ROOT / "deploy/ci/render_financa_staging_artifact.py"
STAGING_DOMAIN = "https://staging.financa.mx"


class RenderStagingArtifactTest(unittest.TestCase):
    def render(self, output, domain=STAGING_DOMAIN):
        return subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--source",
                str(ROOT),
                "--output",
                str(output),
                "--commit",
                "test-commit",
                "--domain",
                domain,
            ],
            capture_output=True,
            text=True,
        )

    def test_renders_staging_domain_without_changing_checkout(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            output = Path(temporary_directory) / "artifact"
            result = self.render(output)
            self.assertEqual(result.returncode, 0, result.stderr)
            manifest = json.loads((output / "artifact-manifest.json").read_text())
            self.assertEqual(manifest["domain"], STAGING_DOMAIN)
            homepage = (output / "financa_website/views/homepage.xml").read_text()
            self.assertIn(STAGING_DOMAIN, homepage)
            self.assertNotIn("__FINANCA_DOMAIN__", homepage)
            self.assertNotIn("https://financa-mx", homepage)

    def test_rejects_symbolic_links_in_the_artifact_source(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            source = Path(temporary_directory) / "source"
            source.mkdir()
            (source / "financa_website").symlink_to(ROOT / "financa_website", target_is_directory=True)
            (source / "deploy").mkdir()
            (source / "deploy" / "odoo").symlink_to(ROOT / "deploy" / "odoo", target_is_directory=True)
            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--source",
                    str(source),
                    "--output",
                    str(Path(temporary_directory) / "artifact"),
                    "--commit",
                    "test-commit",
                ],
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("symbolic link", result.stderr)

    def test_rejects_any_domain_other_than_staging(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            result = self.render(Path(temporary_directory) / "artifact", "https://financa-mx")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("only https://staging.financa.mx is valid", result.stderr)


if __name__ == "__main__":
    unittest.main()
