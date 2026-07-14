#!/usr/bin/env python3
"""Reject retired operational instructions in the live dev-department template.

Point-in-time handoff notes and explicitly labelled rename history are allowed.
The active prompts, schedules, and workspace declarations must match the current
Gitea/domain/Infisical operating model and the org importer's channel shape.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[2]
ERRORS: list[str] = []


class TemplateLoader(yaml.SafeLoader):
    """Parse past platform-resolved tags such as !include."""


def _template_tag(loader: yaml.Loader, tag_suffix: str, node: yaml.Node) -> Any:
    if isinstance(node, yaml.MappingNode):
        return loader.construct_mapping(node)
    if isinstance(node, yaml.SequenceNode):
        return loader.construct_sequence(node)
    return loader.construct_scalar(node)


TemplateLoader.add_multi_constructor("!", _template_tag)


def _read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def _forbid(relative: str, needles: list[str]) -> None:
    text = _read(relative)
    for needle in needles:
        if needle in text:
            ERRORS.append(f"{relative}: retired instruction remains: {needle!r}")


def _require(relative: str, needles: list[str]) -> None:
    text = _read(relative)
    for needle in needles:
        if needle not in text:
            ERRORS.append(f"{relative}: required current contract missing: {needle!r}")


def _check_branch_policy() -> None:
    retired_branch_patterns = (
        re.compile(r"--base\s+staging\b", re.IGNORECASE),
        re.compile(r"\borigin\s+staging\b", re.IGNORECASE),
        re.compile(r"\bbranch(?:es)?\s+(?:from|off)\s+`?staging`?", re.IGNORECASE),
        re.compile(r"\bPRs?\s+(?:target|targeting|merge to)\s+`?staging`?", re.IGNORECASE),
        re.compile(r"\bstaging(?:-to-|\s*(?:→|->)\s*)main\b", re.IGNORECASE),
        re.compile(r"\bmerge\s+staging\s+into\s+main\b", re.IGNORECASE),
        re.compile(r"/commits/staging/status"),
    )
    for path in ROOT.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in {".md", ".yaml", ".yml"}:
            continue
        if ".git" in path.parts or path.name == "handoff-notes.md":
            continue
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if any(pattern.search(line) for pattern in retired_branch_patterns):
                ERRORS.append(
                    f"{path.relative_to(ROOT)}:{lineno}: "
                    f"retired staging-branch instruction: {line.strip()}"
                )


def _check_retired_monorepo_name() -> None:
    for path in ROOT.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in {".md", ".yaml", ".yml"}:
            continue
        if ".git" in path.parts or path.name == "handoff-notes.md":
            continue
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if "molecule-monorepo" not in line:
                continue
            historical = (
                "renamed from molecule-monorepo" in line
                or "then named `molecule-monorepo`" in line
            )
            changelog = path.name == "SKILL.md" and line.lstrip().startswith("- `1.0.0`")
            if not historical and not changelog:
                ERRORS.append(
                    f"{path.relative_to(ROOT)}:{lineno}: active retired repo name: {line.strip()}"
                )


def _check_channels() -> None:
    allowed_keys = {"type", "config", "allowed_users", "enabled"}
    for path in ROOT.rglob("workspace.yaml"):
        doc = yaml.load(path.read_text(encoding="utf-8"), Loader=TemplateLoader)
        if not isinstance(doc, dict):
            continue
        channels = doc.get("channels", [])
        if not isinstance(channels, list):
            ERRORS.append(f"{path.relative_to(ROOT)}: channels must be a list")
            continue
        for index, channel in enumerate(channels):
            label = f"{path.relative_to(ROOT)}: channels[{index}]"
            if not isinstance(channel, dict):
                ERRORS.append(f"{label} must be a mapping")
                continue
            unknown = sorted(set(channel) - allowed_keys)
            if unknown:
                ERRORS.append(f"{label} has importer-ignored keys: {unknown}")
            if not isinstance(channel.get("config"), dict):
                ERRORS.append(f"{label} must provide a config mapping")


def main() -> int:
    _forbid(
        "README.md",
        [
            "via filesystem symlink at deploy time",
            "Operator-side deploy layout",
            ".github/workflows/",
            "scaffolded empty",
            "Phase 3c-2",
            "python .molecule-ci/",
        ],
    )
    _require(
        "README.md",
        ["!external", ".gitea/workflows/validate.yml", "python3 .molecule-ci/"],
    )

    _forbid("dev-department.yaml", ["gitops-style symlink", "Phase 3c-"])
    _require("dev-department.yaml", ["!external"])

    _forbid(
        "SECRETS_MATRIX.md",
        [
            "GH_TOKEN",
            "operator SSOT",
            "Per-agent GitHub Apps",
            "AWS_ACCESS_KEY_ID",
            "FLY_API_TOKEN",
            "VERCEL_TOKEN",
        ],
    )
    _require("SECRETS_MATRIX.md", ["Infisical", "GITEA_TOKEN"])

    _forbid("dev-lead/.env.example", ["GH_TOKEN", "unified credentials file"])
    _require("dev-lead/.env.example", ["Infisical", "GITEA_TOKEN"])

    deployment_files = [
        "dev-lead/system-prompt.md",
        "dev-lead/infra-lead/system-prompt.md",
        "dev-lead/infra-lead/infra-sre/system-prompt.md",
        "dev-lead/infra-lead/infra-sre/workspace.yaml",
        "dev-lead/app-lead/system-prompt.md",
        "dev-lead/app-lead/app-fe/system-prompt.md",
        "dev-lead/app-lead/app-fe/workspace.yaml",
        "dev-lead/integration-tester/system-prompt.md",
        "dev-lead/cp-lead/cp-be/system-prompt.md",
        "dev-lead/triage-operator/system-prompt.md",
        "dev-lead/triage-operator/philosophy.md",
        "dev-lead/triage-operator/SKILL.md",
    ]
    for relative in deployment_files:
        _forbid(
            relative,
            ["Railway", "Vercel", "EC2", "3.131.96.216", "fly status", "fly logs"],
        )

    retired_layouts = {
        "dev-lead/system-prompt.md": ["`platform/`", "`workspace-template/`"],
        "dev-lead/fullstack-engineer/system-prompt.md": ["`platform/`"],
        "dev-lead/fullstack-engineer/schedules/pick-up-work.md": ["platform/ (Go)"],
        "dev-lead/core-lead/core-security/schedules/security-scan.md": [
            "platform/internal/handlers/"
        ],
        "dev-lead/core-lead/core-devops/system-prompt.md": [".github/workflows/"],
        "dev-lead/schedules/hourly-template-fitness-audit.md": [
            "org-templates/molecule-dev",
            "host.docker.internal",
            "python .molecule-ci/",
        ],
        "dev-lead/triage-operator/initial-prompt.md": ["org-templates/molecule-dev"],
        "dev-lead/triage-operator/workspace.yaml": ["org-templates/molecule-dev"],
        "dev-lead/triage-operator/schedules/hourly-triage.md": [
            "org-templates/molecule-dev"
        ],
        "dev-lead/app-lead/documentation-specialist/initial-prompt.md": [
            "platform/internal/handlers/"
        ],
        "dev-lead/app-lead/documentation-specialist/schedules/daily-docs-sync.md": [
            "platform/internal/handlers/",
            "/workspace/repo/org-templates/",
            "/workspace/repo/plugins/",
        ],
        "dev-lead/app-lead/documentation-specialist/schedules/cross-repo-docs-watch-every-2h.md": [
            "platform/internal/handlers/",
            "workspace-configs-templates",
            ".github/workflows/",
        ],
        "dev-lead/app-lead/documentation-specialist/schedules/daily-changelog.md": [
            "content/docs/changelog.mdx",
            "--limit 60",
        ],
        "dev-lead/app-lead/documentation-specialist/system-prompt.md": [
            "40+ repos",
            "47 repos",
            "48 repos",
            ".github/profile/README.md",
        ],
    }
    for relative, needles in retired_layouts.items():
        _forbid(relative, needles)

    _require(
        "dev-lead/app-lead/documentation-specialist/initial-prompt.md",
        ["molecule-ai/molecule-core", "workspace-server/internal/handlers/"],
    )
    _require(
        "dev-lead/app-lead/documentation-specialist/schedules/daily-changelog.md",
        ["content/docs/changelog/YYYY-MM.mdx", "manual production publish"],
    )
    _require(
        "dev-lead/schedules/hourly-template-fitness-audit.md",
        [
            "molecule-ai/molecule-dev-department",
            "python3 .molecule-ci/scripts/validate-current-ops.py",
        ],
    )

    _forbid(
        "SHARED_RULES.md",
        [
            "GH_TOKEN",
            "GitHub App installation token",
            "Production AWS/Fly/Vercel keys",
            "molecule-monorepo/.github/workflows",
        ],
    )
    _require(
        "SHARED_RULES.md",
        [
            "https://git.moleculesai.app",
            "https://key.moleculesai.app",
            "registry.moleculesai.app",
            "PR targeting `main`",
        ],
    )

    _check_branch_policy()
    _check_retired_monorepo_name()
    _check_channels()

    if ERRORS:
        for error in ERRORS:
            print(f"::error::{error}")
        return 1
    print("OK: current operations contract is internally consistent")
    return 0


if __name__ == "__main__":
    sys.exit(main())
