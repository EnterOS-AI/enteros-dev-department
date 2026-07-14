#!/usr/bin/env python3
"""Validate the importable dev-department against current operations contracts."""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any
from urllib.parse import unquote

import yaml


DEFAULT_ROOT = Path(__file__).resolve().parents[2]
IMPORT_RULES_MARKER = "## Critical operations contract (import-local)"
ALLOWED_CHANNEL_KEYS = {"type", "config", "allowed_users", "enabled"}
MARKDOWN_LINK = re.compile(r"(?<!!)\[[^]]+\]\(([^)]+)\)")
XTRACE_SAFE_GIT_HELPER = re.compile(r"gitea_git\(\)\s*\(\s*\n\s*set \+x\b")
BOOTSTRAP_REPOSITORIES = {
    "dev-lead/infra-lead/initial-prompt.md": "molecule-ai-workspace-runtime",
    "dev-lead/infra-lead/infra-runtime-be/initial-prompt.md": "molecule-ai-workspace-runtime",
    "dev-lead/infra-lead/infra-sre/initial-prompt.md": "molecule-ai-status",
    "dev-lead/sdk-lead/plugin-dev/initial-prompt.md": "molecule-ai-workspace-runtime",
}


class TemplateLoader(yaml.SafeLoader):
    """Parse platform-resolved tags such as ``!include`` as plain data."""


def _template_tag(loader: yaml.Loader, _tag_suffix: str, node: yaml.Node) -> Any:
    if isinstance(node, yaml.MappingNode):
        return loader.construct_mapping(node)
    if isinstance(node, yaml.SequenceNode):
        return loader.construct_sequence(node)
    return loader.construct_scalar(node)


TemplateLoader.add_multi_constructor("!", _template_tag)


def _load_yaml(path: Path) -> Any:
    return yaml.load(path.read_text(encoding="utf-8"), Loader=TemplateLoader)


def instruction_errors(relative: Path, text: str) -> list[str]:
    """Return current-operations violations in one active instruction file."""

    errors: list[str] = []
    relative_text = relative.as_posix()
    patterns: list[tuple[str, re.Pattern[str]]] = [
        (
            "unsafe-git-auth",
            re.compile(
                r"https?://[^\s\"']*(?:x-access-token|oauth2)?[^\s\"']*"
                r"\$\{?GITEA_TOKEN\}?[^\s\"']*@",
                re.IGNORECASE,
            ),
        ),
        ("unsupported-tea", re.compile(r"\btea\b")),
        ("unsupported-jq", re.compile(r"\bjq\b")),
        ("unsupported-curl-jq", re.compile(r"\bcurl\b[^\n]*\s--jq\b")),
        ("unsafe-default-curlrc", re.compile(r"\bcurl\s+--config\b")),
        ("unsafe-token-xtrace-probe", re.compile(r"\$\{GITEA_TOKEN:-\}")),
        (
            "unsafe-token-argv",
            re.compile(
                r"(?:-H|--header)\s+[\"'][^\"']*\$\{?GITEA_TOKEN\}?[^\"']*[\"']"
            ),
        ),
        (
            "stale-core-layout",
            re.compile(
                r"(?:/workspace/repo/platform\b|\bcd\s+platform\b|"
                r"\bplatform/internal/|\bplatform/server\b|platform/ \(Go\)|"
                r"\b(?:the\s+)?platform/\s+directory\b)"
            ),
        ),
        (
            "stale-runtime-root",
            re.compile(
                r"(?:\bPython\s+workspace-template\s+tests\b|"
                r"(?<!molecule-ai-)\bworkspace-template/|"
                r"\bworkspace/plugins_registry/)"
            ),
        ),
        (
            "stale-root-guidance",
            re.compile(r"(?:cat|read)\s+(?:the\s+)?/?workspace/repo/CLAUDE\.md", re.I),
        ),
        (
            "stale-local-endpoint",
            re.compile(r"https?://(?:localhost|host\.docker\.internal):8080\b"),
        ),
        ("stale-docs-stack", re.compile(r"\bNextra\b", re.IGNORECASE)),
        (
            "unpaginated-org-inventory",
            re.compile(r"orgs/molecule-ai/repos\?[^\s'\"]*limit=(?:100|[6-9][0-9])"),
        ),
        (
            "unqualified-ci-on-merge",
            re.compile(r"\bdeployments?\s+(?:are|is)\s+CI-on-merge\b", re.I),
        ),
        (
            "generic-delegation-target",
            re.compile(
                r"(?:delegate_task\s+to\s+(?:your\s+)?team lead\b|"
                r"tasks?\s+from\s+(?:your\s+)?team lead\b)",
                re.IGNORECASE,
            ),
        ),
        (
            "literal-gitea-endpoint-placeholder",
            re.compile(
                r"\bgitea_api\s+(?:GET|POST|PUT|PATCH|DELETE)\s+"
                r"[\"'][^\"']*<[^>\n]+>",
                re.IGNORECASE,
            ),
        ),
        (
            "bare-approval-tag",
            re.compile(
                r"\[(?:qa|security-auditor|uiux)-agent\]\s+(?:APPROVED|N/A)",
                re.IGNORECASE,
            ),
        ),
        (
            "stale-app-lead-name",
            re.compile(r"\bchild of App Lead\b"),
        ),
    ]
    if relative_text.startswith("dev-lead/cp-lead/"):
        patterns.append(
            (
                "stale-cp-stack",
                re.compile(
                    r"\bnpm\b|\bTypeScript\b|\bnode_modules\b|"
                    r"--include=[\"']?\*\.(?:ts|js)",
                    re.IGNORECASE,
                ),
            )
        )
    if relative_text == "dev-lead/sdk-lead/system-prompt.md":
        patterns.append(
            (
                "stale-sdk-release-destination",
                re.compile(r"publish\s+to\s+(?:public\s+)?PyPI/npm", re.IGNORECASE),
            )
        )
        patterns.append(
            (
                "stale-sdk-release-version-bump",
                re.compile(r"Release process:\s*version bump", re.IGNORECASE),
            )
        )

    for lineno, line in enumerate(text.splitlines(), 1):
        for code, pattern in patterns:
            if pattern.search(line):
                errors.append(f"{relative_text}:{lineno}: [{code}] {line.strip()}")
        if "owning security tag:" in line.lower():
            missing = [
                tag
                for tag in ("core-security-agent", "cp-security-agent")
                if f"[{tag}] APPROVED" not in line
            ]
            if missing:
                errors.append(
                    f"{relative_text}:{lineno}: "
                    f"[incomplete-security-approval-gate] missing APPROVED for {missing}"
                )
    if relative_text == "dev-lead/sdk-lead/system-prompt.md":
        release_lines = [
            line.strip()
            for line in text.splitlines()
            if line.strip().startswith("- Release process:")
        ]
        required = (
            "choose and document the release version and notes",
            "reviewed `main`",
            "explicit GO",
            "`sdk-v*` tag",
            "release version source of truth",
            "no committed release-only version bump",
            "private Gitea Python registry",
            "wheel and sdist",
            "verify the exact artifacts",
        )
        release_line = release_lines[0] if len(release_lines) == 1 else ""
        missing = [needle for needle in required if needle not in release_line]
        if len(release_lines) != 1:
            missing.append("exactly one release-process line")
        if missing:
            errors.append(
                f"{relative_text}: [missing-sdk-release-contract] missing {missing}"
            )
    return errors


def git_helper_errors(relative: Path, text: str) -> list[str]:
    """Require credential helpers to isolate xtrace changes in a subshell."""

    if "gitea_git" not in text:
        return [f"{relative}: [missing-ephemeral-git-helper]"]
    if not XTRACE_SAFE_GIT_HELPER.search(text):
        return [
            f"{relative}: [unsafe-git-xtrace] gitea_git must start a subshell "
            "and disable xtrace before credential expansion"
        ]
    return []


def bootstrap_errors(relative: Path, text: str) -> list[str]:
    """Require roles with a primary owned repository to bootstrap that repository."""

    relative_text = relative.as_posix()
    expected = BOOTSTRAP_REPOSITORIES.get(relative_text)
    if expected is None:
        return []
    required = [
        f"https://git.moleculesai.app/molecule-ai/{expected}.git",
        f"/workspace/repos/{expected}",
        f"ln -sfn /workspace/repos/{expected} /workspace/repo",
    ]
    missing = [needle for needle in required if needle not in text]
    if not missing:
        return []
    return [
        f"{relative_text}: [wrong-bootstrap-repo] expected {expected!r}; "
        f"missing {missing}"
    ]


def deployment_errors(relative: Path, text: str) -> list[str]:
    """Require repository-specific deployment truth in every system prompt."""

    relative_text = relative.as_posix()
    errors: list[str] = []
    if "Merge to `main` triggers CI deployment" in text:
        errors.append(f"{relative_text}: [unqualified-main-deploy]")
    lowered = text.lower()
    required = (
        "checked-in publisher workflow",
        "documentation publishing is manual",
        "molecule-app",
        "landingpage",
        "do not deploy",
    )
    for needle in required:
        if needle.lower() not in lowered:
            errors.append(
                f"{relative_text}: [missing-deployment-contract] {needle!r}"
            )
    return errors


def org_inventory_errors(relative: Path, text: str) -> list[str]:
    """Require every organization-wide repository inventory to exhaust pagination."""

    if "orgs/molecule-ai/repos" not in text:
        return []
    required = ("page=1", "while", "limit=50", "page=$((page + 1))")
    missing = [needle for needle in required if needle not in text]
    if not missing:
        return []
    return [
        f"{relative}: [unpaginated-org-inventory] missing pagination markers {missing}"
    ]


def plugin_audit_errors(relative: Path, text: str) -> list[str]:
    """Require the plugin audit to inspect the runtime-owned registry."""

    required = (
        "https://git.moleculesai.app/molecule-ai/molecule-ai-workspace-runtime.git",
        "/workspace/repos/molecule-ai-workspace-runtime",
        'gitea_git clone "$RUNTIME_URL" "$RUNTIME_DIR"',
        "molecule_runtime/plugins_registry/",
    )
    missing = [needle for needle in required if needle not in text]
    stale_core = "cd /workspace/repos/molecule-core" in text
    if not missing and not stale_core:
        return []
    return [
        f"{relative}: [stale-plugin-registry-repo] missing={missing} "
        f"stale_core={stale_core}"
    ]


def shared_rules_errors(text: str) -> list[str]:
    """Keep shared documentation routing aligned with current policy and roles."""

    errors: list[str] = []
    for stale in (
        "Molecule-AI/internal/marketing/",
        "Molecule-AI/internal/retrospectives/",
        "internal/marketing/",
        "internal/retrospectives/",
        "internal/devrel-drafts/",
    ):
        if stale in text:
            errors.append(f"SHARED_RULES.md: [stale-documentation-path] {stale!r}")
    for stale in ("app-docs-lead", "research-analyst", "devrel-engineer"):
        if stale in text:
            errors.append(f"SHARED_RULES.md: [stale-workspace-name] {stale!r}")
    if "/blob/main/" in text:
        errors.append("SHARED_RULES.md: [stale-gitea-link] '/blob/main/'")
    return errors


def channel_errors(relative: Path, document: Any) -> list[str]:
    """Reject importer-invalid or fail-open native-channel declarations."""

    if not isinstance(document, dict):
        return []
    channels = document.get("channels", [])
    if not isinstance(channels, list):
        return [f"{relative}: [invalid-channels] channels must be a list"]

    errors: list[str] = []
    for index, channel in enumerate(channels):
        label = f"{relative}:channels[{index}]"
        if not isinstance(channel, dict):
            errors.append(f"{label}: [invalid-channel] entry must be a mapping")
            continue
        unknown = sorted(set(channel) - ALLOWED_CHANNEL_KEYS)
        if unknown:
            errors.append(f"{label}: [invalid-channel-keys] importer ignores {unknown}")
        if not isinstance(channel.get("config"), dict):
            errors.append(f"{label}: [invalid-channel-config] config must be a mapping")

        enabled = channel.get("enabled", True)
        allowed_users = channel.get("allowed_users")
        if enabled is not False:
            if not isinstance(allowed_users, list) or not allowed_users:
                errors.append(
                    f"{label}: [fail-open-channel] enabled channel needs a non-empty "
                    "literal allowed_users list; disable it until molecule-core#4340"
                )
            elif any(not isinstance(item, str) or not item.strip() for item in allowed_users):
                errors.append(f"{label}: [invalid-allowlist] entries must be non-empty strings")
        if isinstance(allowed_users, list) and any(
            isinstance(item, str) and "${" in item for item in allowed_users
        ):
            errors.append(
                f"{label}: [unexpanded-allowlist] allowed_users does not support env "
                "expansion; see molecule-core#4340"
            )
    return errors


def routing_errors(routing: Any, workspace_names: set[str]) -> list[str]:
    """Ensure every category-routing target names a delivered workspace."""

    if not isinstance(routing, dict):
        return ["dev-department.yaml: [invalid-routing] category_routing must be a mapping"]
    errors: list[str] = []
    for category, targets in routing.items():
        if not isinstance(targets, list) or not targets:
            errors.append(f"category_routing.{category}: [invalid-routing] needs targets")
            continue
        for target in targets:
            if not isinstance(target, str) or target not in workspace_names:
                errors.append(
                    f"category_routing.{category}: [dangling-route] {target!r} is not a "
                    "workspace name"
                )
    return errors


def markdown_link_errors(root: Path, path: Path, files_dir: Path | None = None) -> list[str]:
    """Validate local Markdown targets and imported-files boundary containment."""

    errors: list[str] = []
    text = path.read_text(encoding="utf-8")
    for match in MARKDOWN_LINK.finditer(text):
        raw_target = match.group(1).strip().strip("<>")
        if not raw_target or raw_target.startswith(("#", "http://", "https://", "mailto:")):
            continue
        if raw_target in {"...", "…"}:
            continue
        target_text = unquote(raw_target.split("#", 1)[0].split("?", 1)[0])
        if not target_text or target_text.startswith("/") or "<" in target_text:
            continue
        target = (path.parent / target_text).resolve()
        line = text.count("\n", 0, match.start()) + 1
        relative = path.relative_to(root)
        if not target.exists():
            errors.append(
                f"{relative}:{line}: [broken-relative-link] {raw_target!r} does not exist"
            )
            continue
        if files_dir is not None and not target.is_relative_to(files_dir.resolve()):
            errors.append(
                f"{relative}:{line}: [outside-files-dir] {raw_target!r} is not delivered "
                f"with {files_dir.relative_to(root)}"
            )
    return errors


def _workspace_contract(root: Path) -> tuple[set[str], list[Path], list[str]]:
    names: set[str] = set()
    files_dirs: list[Path] = []
    errors: list[str] = []
    for workspace in sorted((root / "dev-lead").rglob("workspace.yaml")):
        document = _load_yaml(workspace)
        errors.extend(channel_errors(workspace.relative_to(root), document))
        if not isinstance(document, dict):
            continue
        name = document.get("name")
        if isinstance(name, str):
            names.add(name)
        declared = document.get("files_dir")
        if not isinstance(declared, str):
            errors.append(f"{workspace.relative_to(root)}: [missing-files-dir]")
            continue
        files_dir = (root / declared).resolve()
        files_dirs.append(files_dir)
        prompt = files_dir / "system-prompt.md"
        if not prompt.is_file():
            errors.append(
                f"{workspace.relative_to(root)}: [missing-system-prompt] {prompt}"
            )
        elif IMPORT_RULES_MARKER not in prompt.read_text(encoding="utf-8"):
            errors.append(
                f"{prompt.relative_to(root)}: [missing-import-local-rules] critical "
                "safety rules are not delivered inside this files_dir"
            )
    return names, files_dirs, errors


def _nearest_files_dir(path: Path, files_dirs: list[Path]) -> Path | None:
    candidates = [directory for directory in files_dirs if path.is_relative_to(directory)]
    return max(candidates, key=lambda item: len(item.parts), default=None)


def _require(text: str, relative: str, needles: list[str], errors: list[str]) -> None:
    for needle in needles:
        if needle not in text:
            errors.append(f"{relative}: [missing-current-contract] {needle!r}")


def _forbid(text: str, relative: str, needles: list[str], errors: list[str]) -> None:
    for needle in needles:
        if needle in text:
            errors.append(f"{relative}: [retired-instruction] {needle!r}")


def validate_repository(root: Path = DEFAULT_ROOT) -> list[str]:
    """Return every repository-level current-operations contract violation."""

    root = root.resolve()
    errors: list[str] = []
    names, files_dirs, workspace_errors = _workspace_contract(root)
    errors.extend(workspace_errors)

    manifest = _load_yaml(root / "dev-department.yaml")
    if isinstance(manifest, dict):
        defaults = manifest.get("defaults", {})
        routing = defaults.get("category_routing") if isinstance(defaults, dict) else None
        errors.extend(routing_errors(routing, names))

    active_paths = [root / "README.md", root / "SECRETS_MATRIX.md", root / "SHARED_RULES.md"]
    active_paths.extend(
        path
        for path in (root / "dev-lead").rglob("*")
        if path.is_file()
        and path.suffix.lower() in {".md", ".yaml", ".yml"}
    )
    active_paths.append(root / ".molecule-ci" / "scripts" / "local-e2e-setup.sh")
    for path in sorted(set(active_paths)):
        text = path.read_text(encoding="utf-8")
        errors.extend(instruction_errors(path.relative_to(root), text))
        errors.extend(org_inventory_errors(path.relative_to(root), text))
        if path.suffix.lower() == ".md":
            errors.extend(
                markdown_link_errors(root, path, _nearest_files_dir(path, files_dirs))
            )

    for initial in sorted((root / "dev-lead").rglob("initial-prompt.md")):
        text = initial.read_text(encoding="utf-8")
        errors.extend(bootstrap_errors(initial.relative_to(root), text))
        if "git clone" in text or "gitea_git clone" in text:
            errors.extend(git_helper_errors(initial.relative_to(root), text))
            if "remote set-url origin" not in text:
                errors.append(
                    f"{initial.relative_to(root)}: [missing-clean-remote-ratchet]"
                )
        if "gitea_api() (" in text:
            _require(
                text,
                initial.relative_to(root).as_posix(),
                [
                    'method="$1"',
                    'endpoint="$2"',
                    'case "$method" in',
                    '*://*',
                    '*%25*',
                    'cr=$(printf "\\\\r_")',
                    "*/../*",
                    "curl -q --config",
                    '--request "$method"',
                    '-- "$url"',
                ],
                errors,
            )

    for system_prompt in sorted((root / "dev-lead").rglob("system-prompt.md")):
        text = system_prompt.read_text(encoding="utf-8")
        errors.extend(deployment_errors(system_prompt.relative_to(root), text))
        _require(
            text,
            system_prompt.relative_to(root).as_posix(),
            [
                'method="$1"',
                'endpoint="$2"',
                'case "$method" in',
                '*://*',
                '*%25*',
                'cr=$(printf "\\\\r_")',
                "*/../*",
                "curl -q --config",
                '--request "$method"',
                '-- "$url"',
            ],
            errors,
        )

    local_setup = (root / ".molecule-ci" / "scripts" / "local-e2e-setup.sh").read_text()
    _require(
        local_setup,
        ".molecule-ci/scripts/local-e2e-setup.sh",
        ["credential.helper=!", "remote set-url origin", "gitea_git() ("],
        errors,
    )
    errors.extend(
        git_helper_errors(
            Path(".molecule-ci/scripts/local-e2e-setup.sh"), local_setup
        )
    )

    readme = (root / "README.md").read_text(encoding="utf-8")
    _forbid(
        readme,
        "README.md",
        ["via filesystem symlink at deploy time", "Operator-side deploy layout", ".github/workflows/", "scaffolded empty", "Phase 3c-2", "python .molecule-ci/"],
        errors,
    )
    _require(readme, "README.md", ["!external", ".gitea/workflows/validate.yml", "python3 .molecule-ci/"], errors)

    shared = (root / "SHARED_RULES.md").read_text(encoding="utf-8")
    _forbid(shared, "SHARED_RULES.md", ["GH_TOKEN", "GitHub App installation token", "Production AWS/Fly/Vercel keys", "molecule-monorepo/.github/workflows"], errors)
    _require(shared, "SHARED_RULES.md", ["https://git.moleculesai.app", "https://key.moleculesai.app", "registry.moleculesai.app", "PR targeting `main`"], errors)
    errors.extend(shared_rules_errors(shared))

    plugin_audit = (
        root
        / "dev-lead"
        / "sdk-lead"
        / "plugin-dev"
        / "schedules"
        / "plugin-ecosystem-audit.md"
    )
    errors.extend(
        plugin_audit_errors(
            plugin_audit.relative_to(root),
            plugin_audit.read_text(encoding="utf-8"),
        )
    )

    for path in active_paths:
        if not path.is_file():
            continue
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if re.search(r"--base\s+staging\b|\borigin\s+staging\b|/commits/staging/status", line, re.I):
                errors.append(
                    f"{path.relative_to(root)}:{lineno}: [retired-staging-branch] {line.strip()}"
                )
            if "molecule-monorepo" in line and not (
                "renamed from molecule-monorepo" in line
                or "then named `molecule-monorepo`" in line
                or (path.name == "SKILL.md" and line.lstrip().startswith("- `1.0.0`"))
            ):
                errors.append(
                    f"{path.relative_to(root)}:{lineno}: [retired-repo-name] {line.strip()}"
                )

    return sorted(set(errors))


def main() -> int:
    errors = validate_repository()
    if errors:
        for error in errors:
            print(f"::error::{error}")
        return 1
    print("OK: current operations contract is internally consistent")
    return 0


if __name__ == "__main__":
    sys.exit(main())
