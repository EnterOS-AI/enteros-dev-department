from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCANNER = ROOT / ".molecule-ci" / "scripts" / "check-secrets.py"
FIXTURES = Path(__file__).resolve().parent / "fixtures"


class SecretScannerTests(unittest.TestCase):
    def run_scanner(self, root: Path) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        env["GITHUB_WORKSPACE"] = str(root)
        return subprocess.run(
            [sys.executable, str(SCANNER)],
            text=True,
            capture_output=True,
            env=env,
            check=False,
        )

    @staticmethod
    def credential() -> str:
        return "ghp_" + ("A" * 36)

    def test_scans_molecule_ci_without_disclosing_matched_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / ".molecule-ci" / "generated.py"
            target.parent.mkdir()
            credential = self.credential()
            target.write_text(f'TOKEN = "{credential}"\n', encoding="utf-8")

            result = self.run_scanner(root)

            self.assertEqual(result.returncode, 1)
            self.assertIn("file=.molecule-ci/generated.py,line=1", result.stdout)
            self.assertIn("github-pat", result.stdout)
            self.assertNotIn(credential, result.stdout + result.stderr)
            self.assertNotIn(credential[:20], result.stdout + result.stderr)

    def test_scans_dot_env_example(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / "dev-lead" / ".env.example"
            target.parent.mkdir()
            template = (FIXTURES / "secret.env.example.in").read_text(encoding="utf-8")
            target.write_text(
                template.replace("TOKEN_VALUE", self.credential()),
                encoding="utf-8",
            )

            result = self.run_scanner(root)

            self.assertEqual(result.returncode, 1)
            self.assertIn("file=dev-lead/.env.example,line=1", result.stdout)

    def test_redacts_generic_pkcs8_private_key_header(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / "key.pem"
            header = "-----BEGIN " + "PRIVATE KEY-----"
            target.write_text(header + "\nnot-a-real-key\n", encoding="utf-8")

            result = self.run_scanner(root)

            self.assertEqual(result.returncode, 1)
            self.assertIn("private-key", result.stdout)
            self.assertNotIn(header, result.stdout + result.stderr)

    def test_clean_tree_passes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / ".molecule-ci").mkdir()
            (root / ".molecule-ci" / "safe.py").write_text(
                'TOKEN = "${GITEA_TOKEN}"\n', encoding="utf-8"
            )

            result = self.run_scanner(root)

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("No secrets detected", result.stdout)


if __name__ == "__main__":
    unittest.main()
