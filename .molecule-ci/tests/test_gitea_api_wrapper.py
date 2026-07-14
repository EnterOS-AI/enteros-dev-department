from __future__ import annotations

import os
import re
import stat
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
FUNCTION = re.compile(r"gitea_api\(\) \(\n.*?\n\)", re.DOTALL)


class GiteaAPIWrapperTests(unittest.TestCase):
    def test_all_imported_prompts_use_one_shell_valid_wrapper(self) -> None:
        snippets = set()
        for workspace in (ROOT / "dev-lead").rglob("workspace.yaml"):
            text = workspace.read_text(encoding="utf-8")
            match = re.search(r"^files_dir:\s*(.+)$", text, re.MULTILINE)
            self.assertIsNotNone(match, workspace)
            prompt = ROOT / match.group(1).strip() / "system-prompt.md"
            function = FUNCTION.search(prompt.read_text(encoding="utf-8"))
            self.assertIsNotNone(function, prompt)
            snippets.add(function.group(0))
        self.assertEqual(len(snippets), 1)

        snippet = snippets.pop()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fake_bin = root / "bin"
            fake_bin.mkdir()
            fake_curl = fake_bin / "curl"
            fake_curl.write_text(
                "#!/bin/sh\n"
                "for arg in \"$@\"; do printf '<%s>\\n' \"$arg\" >> \"$CURL_ARGV_LOG\"; done\n"
                "cat > \"$CURL_CONFIG_LOG\"\n"
                "printf '{\"ok\":true}\\n'\n"
            )
            fake_curl.chmod(fake_curl.stat().st_mode | stat.S_IXUSR)
            script = root / "probe.sh"
            script.write_text(
                snippet
                + "\ngitea_api 'repos/molecule-ai/internal' -X POST --data-binary '{}'\n"
            )

            sentinel = "dummy-api-token-must-not-leak"
            argv_log = root / "argv.log"
            config_log = root / "config.log"
            env = os.environ.copy()
            env.update(
                PATH=f"{fake_bin}:{env['PATH']}",
                GITEA_TOKEN=sentinel,
                CURL_ARGV_LOG=str(argv_log),
                CURL_CONFIG_LOG=str(config_log),
            )
            result = subprocess.run(
                ["bash", "-x", str(script)],
                text=True,
                capture_output=True,
                env=env,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(
                config_log.read_bytes(),
                f'header = "Authorization: token {sentinel}"\n'.encode(),
            )
            self.assertNotIn(sentinel, argv_log.read_text())
            self.assertNotIn(sentinel, result.stdout + result.stderr)
            argv = argv_log.read_text()
            self.assertIn("<POST>", argv)
            self.assertIn("<--data-binary>", argv)
            self.assertIn(
                "<https://git.moleculesai.app/api/v1/repos/molecule-ai/internal>",
                argv,
            )


if __name__ == "__main__":
    unittest.main()
