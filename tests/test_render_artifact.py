import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]
SCRIPT = ROOT / "deploy/ci/render_financa_artifact.py"
STAGING_DOMAIN = "https://staging.financa.mx"
PRODUCTION_DOMAIN = "https://financa.example.mx"
TOKEN = "__FINANCA_DOMAIN__"
TEMPLATE_PATHS = (
    "financa_website/data/redirects.xml",
    "financa_website/views/homepage.xml",
    "financa_website/views/legal.xml",
    "financa_website/views/thank_you.xml",
    "deploy/odoo/preflight_financa.py",
)


class RenderArtifactTest(unittest.TestCase):
    def render(self, output, environment="staging", domain=STAGING_DOMAIN, source=None):
        return subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--source",
                str(ROOT if source is None else source),
                "--output",
                str(output),
                "--commit",
                "test-commit",
                "--environment",
                environment,
                "--domain",
                domain,
            ],
            capture_output=True,
            text=True,
        )

    def write_source(self, source):
        """Write the smallest source tree every template path accepts."""
        for relative_path in TEMPLATE_PATHS:
            path = source / relative_path
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(f"<!-- {TOKEN} -->\n" if path.suffix == ".xml" else f'EXPECTED = "{TOKEN}"\n')
        return source

    def test_renders_staging_domain_without_changing_checkout(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            output = Path(temporary_directory) / "artifact"
            result = self.render(output)
            self.assertEqual(result.returncode, 0, result.stderr)
            manifest = json.loads((output / "artifact-manifest.json").read_text())
            self.assertEqual(manifest["domain"], STAGING_DOMAIN)
            self.assertEqual(manifest["environment"], "staging")
            self.assertEqual(manifest["commit"], "test-commit")
            homepage = (output / "financa_website/views/homepage.xml").read_text()
            self.assertIn(STAGING_DOMAIN, homepage)
            self.assertNotIn(TOKEN, homepage)
            self.assertNotIn("https://financa-mx", homepage)

    def test_renders_production_domain_supplied_by_the_pipeline(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            output = Path(temporary_directory) / "artifact"
            result = self.render(output, environment="production", domain=PRODUCTION_DOMAIN)
            self.assertEqual(result.returncode, 0, result.stderr)
            manifest = json.loads((output / "artifact-manifest.json").read_text())
            self.assertEqual(manifest["domain"], PRODUCTION_DOMAIN)
            self.assertEqual(manifest["environment"], "production")
            for relative_path in TEMPLATE_PATHS:
                rendered = (output / relative_path).read_text()
                self.assertIn(PRODUCTION_DOMAIN, rendered, relative_path)
                self.assertNotIn(TOKEN, rendered, relative_path)
                self.assertNotIn(STAGING_DOMAIN, rendered, relative_path)
            preflight = (output / "deploy/odoo/preflight_financa.py").read_text()
            self.assertIn(f'EXPECTED_MODULE_DOMAIN = "{PRODUCTION_DOMAIN}"', preflight)

    def test_rejects_symbolic_links_in_the_artifact_source(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            source = Path(temporary_directory) / "source"
            source.mkdir()
            (source / "financa_website").symlink_to(ROOT / "financa_website", target_is_directory=True)
            (source / "deploy").mkdir()
            (source / "deploy" / "odoo").symlink_to(ROOT / "deploy" / "odoo", target_is_directory=True)
            result = self.render(Path(temporary_directory) / "artifact", source=source)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("symbolic link", result.stderr)

    def test_rejects_any_domain_other_than_staging(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            result = self.render(Path(temporary_directory) / "artifact", domain="https://financa-mx")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("only https://staging.financa.mx is valid for staging", result.stderr)

    def test_production_refuses_the_staging_host(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            result = self.render(
                Path(temporary_directory) / "artifact",
                environment="production",
                domain=STAGING_DOMAIN,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("is the staging host", result.stderr)

    def test_rejects_a_domain_with_a_path_or_port(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            result = self.render(
                Path(temporary_directory) / "artifact",
                environment="production",
                domain=f"{PRODUCTION_DOMAIN}/home",
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("without path, query or port", result.stderr)

    def test_rejects_a_host_that_is_not_the_target(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            source = self.write_source(Path(temporary_directory) / "source")
            stray = source / "financa_website/views/legacy.xml"
            stray.write_text('<odoo><field name="url">https://financa-mx</field></odoo>\n')
            result = self.render(Path(temporary_directory) / "artifact", source=source)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("unexpected absolute host https://financa-mx", result.stderr)

    def test_rejects_a_host_in_a_scanned_asset(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            source = self.write_source(Path(temporary_directory) / "source")
            stray = source / "financa_website/static/src/js/legacy.js"
            stray.parent.mkdir(parents=True, exist_ok=True)
            stray.write_text("var container = 'https://www.googletagmanager.com/gtm.js?id=GTM-TEST';\n")
            result = self.render(Path(temporary_directory) / "artifact", source=source)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("unexpected absolute host https://www.googletagmanager.com", result.stderr)

    def test_rejects_a_template_without_the_token(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            source = self.write_source(Path(temporary_directory) / "source")
            (source / "financa_website/views/legal.xml").write_text("<odoo/>\n")
            result = self.render(Path(temporary_directory) / "artifact", source=source)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("template token missing from financa_website/views/legal.xml", result.stderr)


if __name__ == "__main__":
    unittest.main()
