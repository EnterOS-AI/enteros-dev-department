from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

import yaml


CI_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = CI_ROOT.parent
FIXTURES = Path(__file__).resolve().parent / "fixtures"


def load_validator():
    path = CI_ROOT / "scripts" / "validate-current-ops.py"
    spec = importlib.util.spec_from_file_location("validate_current_ops", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class CurrentOperationsContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.validator = load_validator()

    def test_unsafe_command_fixture_reports_each_regression(self) -> None:
        fixture = FIXTURES / "unsafe-active-instructions.md"
        unsafe_git = (
            'git clone "https://x-access-token:'
            + "${GITEA_TOKEN}"
            + '@git.moleculesai.app/molecule-ai/example.git"\n'
        )
        errors = self.validator.instruction_errors(
            Path("dev-lead/example/initial-prompt.md"),
            unsafe_git + fixture.read_text(encoding="utf-8"),
        )
        joined = "\n".join(errors)
        self.assertIn("unsafe-git-auth", joined)
        self.assertIn("unsupported-tea", joined)
        self.assertIn("unsupported-curl-jq", joined)
        self.assertIn("unsupported-jq", joined)

    def test_stale_stack_and_endpoint_fixtures_are_rejected(self) -> None:
        cases = [
            ("dev-lead/core-lead/core-be/system-prompt.md", "cd /workspace/repo/platform && go test ./...", "stale-core-layout"),
            ("dev-lead/core-lead/initial-prompt.md", "cat /workspace/repo/CLAUDE.md", "stale-root-guidance"),
            ("dev-lead/cp-lead/cp-qa/schedules/qa-review.md", "npm test -- --coverage", "stale-cp-stack"),
            ("dev-lead/integration-tester/schedules/e2e-test.md", "curl -sf http://localhost:8080/health", "stale-local-endpoint"),
            ("dev-lead/app-lead/app-fe/system-prompt.md", "Nextra/MDX docs site", "stale-docs-stack"),
        ]
        for relative, text, code in cases:
            with self.subTest(relative=relative):
                errors = self.validator.instruction_errors(Path(relative), text)
                self.assertTrue(any(code in error for error in errors), errors)

    def test_enabled_channel_without_literal_allowlist_fails_closed(self) -> None:
        doc = yaml.safe_load((FIXTURES / "fail-open-channel.yaml").read_text())
        errors = self.validator.channel_errors(Path("role/workspace.yaml"), doc)
        self.assertTrue(any("fail-open-channel" in error for error in errors), errors)

        doc["channels"][0]["allowed_users"] = ["${TELEGRAM_ALLOWED_USER_ID}"]
        errors = self.validator.channel_errors(Path("role/workspace.yaml"), doc)
        self.assertTrue(any("unexpanded-allowlist" in error for error in errors), errors)

        del doc["channels"][0]["allowed_users"]
        doc["channels"][0]["enabled"] = False
        self.assertEqual(
            self.validator.channel_errors(Path("role/workspace.yaml"), doc), []
        )

    def test_git_helper_must_disable_xtrace_inside_a_subshell(self) -> None:
        unsafe = """gitea_git() {
  set +x
  git -c 'credential.helper=!f() { printf "password=$GITEA_TOKEN\\n"; }; f' "$@"
}
"""
        errors = self.validator.git_helper_errors(
            Path("dev-lead/example/initial-prompt.md"), unsafe
        )
        self.assertTrue(any("unsafe-git-xtrace" in error for error in errors), errors)

        safe = unsafe.replace("gitea_git() {", "gitea_git() (").replace("\n}\n", "\n)\n")
        self.assertEqual(
            self.validator.git_helper_errors(
                Path("dev-lead/example/initial-prompt.md"), safe
            ),
            [],
        )

    def test_category_routes_only_target_existing_workspaces(self) -> None:
        doc = yaml.safe_load((FIXTURES / "dangling-routing.yaml").read_text())
        errors = self.validator.routing_errors(
            doc["category_routing"], set(doc["workspace_names"])
        )
        self.assertTrue(any("Missing Security Role" in error for error in errors), errors)

    def test_relative_link_cannot_escape_imported_files_dir(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            files_dir = root / "dev-lead" / "role"
            files_dir.mkdir(parents=True)
            (root / "dev-lead" / "SHARED_RULES.md").write_text("rules\n")
            prompt = files_dir / "system-prompt.md"
            prompt.write_text("[rules](../SHARED_RULES.md)\n")

            errors = self.validator.markdown_link_errors(
                root, prompt, files_dir
            )

            self.assertTrue(any("outside-files-dir" in error for error in errors), errors)

    def test_repository_contract_is_clean(self) -> None:
        errors = self.validator.validate_repository(REPO_ROOT)
        self.assertEqual(errors, [], "\n".join(errors))


if __name__ == "__main__":
    unittest.main()
