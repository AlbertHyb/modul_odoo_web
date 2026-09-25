import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]
STAGING = ROOT / "deploy/server/financa-staging-deploy.sh"
PRODUCTION = ROOT / "deploy/server/financa-production-deploy.sh"
STAGING_DOC = ROOT / "deploy/compose/README.md"
PRODUCTION_DOC = ROOT / "docs/PRODUCCION_DOCKER_COMPOSE.md"

SCRIPTS = (
    (STAGING, "financa-staging-deploy.sh"),
    (PRODUCTION, "financa-production-deploy.sh"),
)


def order(text, tokens):
    return [text.index(token) for token in tokens]


class ForcedCommandDriftTest(unittest.TestCase):
    def test_each_forced_command_compares_its_installed_copy_with_the_revision(self):
        for script, name in SCRIPTS:
            with self.subTest(script=name):
                text = script.read_text()
                self.assertIn('installed_command=$(realpath "${BASH_SOURCE[0]}")', text)
                self.assertIn(f'expected_command="$repo/deploy/server/{name}"', text)
                self.assertIn('cmp -s "$installed_command" "$expected_command"', text)
                self.assertIn(
                    "sudo install -o root -g root -m 0750 $expected_command $installed_command", text
                )

    def test_the_comparison_runs_after_the_checkout_and_before_any_mutation(self):
        staging = STAGING.read_text()
        tokens = order(
            staging,
            [
                'git -C "$repo" checkout --detach --quiet "$sha"',
                "installed_command=$(realpath",
                "systemctl start --wait financa-staging-backup.service",
            ],
        )
        self.assertEqual(tokens, sorted(tokens))

        production = PRODUCTION.read_text()
        tokens = order(
            production,
            [
                'git -C "$repo" checkout --detach --quiet "$sha"',
                "installed_command=$(realpath",
                '"${compose[@]}" stop odoo',
            ],
        )
        self.assertEqual(tokens, sorted(tokens))

    def test_both_scripts_require_the_comparison_binary(self):
        self.assertIn(
            "for command in cmp curl docker flock readlink realpath runuser systemctl; do",
            STAGING.read_text(),
        )
        self.assertIn(
            "for command in cmp curl docker flock mktemp realpath rm runuser stat tar; do",
            PRODUCTION.read_text(),
        )

    def test_the_host_instructions_explain_the_reinstall_requirement(self):
        staging_doc = STAGING_DOC.read_text()
        self.assertIn(
            "financa-staging-deploy.sh /usr/local/sbin/financa-staging-deploy", staging_doc
        )
        self.assertIn("reinstalarlo", staging_doc)

        production_doc = PRODUCTION_DOC.read_text()
        self.assertIn(
            "financa-production-deploy.sh /usr/local/sbin/financa-production-deploy",
            production_doc,
        )
        self.assertIn("reinstalarlo", production_doc)


if __name__ == "__main__":
    unittest.main()
