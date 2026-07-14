from __future__ import annotations

import re
import subprocess
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SHELL_BLOCK = re.compile(
    r"^```(?:bash|sh)\s*\n(.*?)^```\s*$",
    re.MULTILINE | re.DOTALL,
)


class ExecutableShellBlockTests(unittest.TestCase):
    def test_all_fenced_shell_blocks_parse_as_bash(self) -> None:
        failures: list[str] = []
        checked = 0
        for path in sorted(REPO_ROOT.rglob("*.md")):
            if ".git" in path.parts:
                continue
            text = path.read_text(encoding="utf-8")
            for index, match in enumerate(SHELL_BLOCK.finditer(text), 1):
                checked += 1
                result = subprocess.run(
                    ["bash", "-n"],
                    input=match.group(1),
                    text=True,
                    capture_output=True,
                    check=False,
                )
                if result.returncode:
                    failures.append(
                        f"{path.relative_to(REPO_ROOT)}: shell block {index}: "
                        f"{result.stderr.strip()}"
                    )

        self.assertGreater(checked, 0)
        self.assertEqual(failures, [], "\n".join(failures))


if __name__ == "__main__":
    unittest.main()
