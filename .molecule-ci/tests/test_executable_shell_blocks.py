from __future__ import annotations

import re
import subprocess
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
FENCED_BLOCK = re.compile(
    r"^(?P<indent>[ \t]*)```(?P<language>[^\n`]*)\n"
    r"(?P<body>.*?)^(?P=indent)```[ \t]*$",
    re.MULTILINE | re.DOTALL,
)
SHELL_LANGUAGE = {"bash", "sh", "shell", "zsh"}
SHELL_LINE = re.compile(
    r"^\s*(?:#|:|[A-Za-z_][A-Za-z0-9_]*=|"
    r"gitea_api\b|gitea_git\b|git\b|grep\b|curl\b|python3\b|bash\b|"
    r"cd\b|mkdir\b|commit_memory\b|logger\b|test\b|for\b|while\b|if\b)",
    re.MULTILINE,
)
ANGLE_PLACEHOLDER = re.compile(r"<[A-Za-z][^>\n]*>")


class ExecutableShellBlockTests(unittest.TestCase):
    def test_all_operational_shell_fences_parse_without_placeholders(self) -> None:
        failures: list[str] = []
        checked = 0
        for path in sorted(REPO_ROOT.rglob("*.md")):
            if ".git" in path.parts:
                continue
            text = path.read_text(encoding="utf-8")
            for index, match in enumerate(FENCED_BLOCK.finditer(text), 1):
                language = match.group("language").strip().lower()
                body = match.group("body")
                if not language:
                    failures.append(
                        f"{path.relative_to(REPO_ROOT)}: shell block {index}: "
                        "unlabeled fence; label it so operational shell cannot evade checks"
                    )
                if language not in SHELL_LANGUAGE and not (
                    not language and SHELL_LINE.search(body)
                ):
                    continue
                checked += 1
                placeholders = ANGLE_PLACEHOLDER.findall(body)
                if placeholders:
                    failures.append(
                        f"{path.relative_to(REPO_ROOT)}: shell block {index}: "
                        f"literal placeholders {placeholders}"
                    )
                result = subprocess.run(
                    ["bash", "-n"],
                    input=body,
                    text=True,
                    capture_output=True,
                    check=False,
                )
                if result.returncode:
                    failures.append(
                        f"{path.relative_to(REPO_ROOT)}: shell block {index}: "
                        f"{result.stderr.strip()}"
                    )

        self.assertGreaterEqual(checked, 70)
        self.assertEqual(failures, [], "\n".join(failures))


if __name__ == "__main__":
    unittest.main()
