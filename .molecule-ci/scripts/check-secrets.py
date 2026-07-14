#!/usr/bin/env python3
"""Scan every committed text file for credential-shaped values.

Findings intentionally contain only a rule identifier and source location. The
matched bytes are never returned or printed, so a detection cannot turn a
credential leak into a CI-log leak.
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path


RULES: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("anthropic-key", re.compile(r"sk-ant-[A-Za-z0-9]{50,}")),
    ("github-pat", re.compile(r"ghp_[A-Za-z0-9]{36,}")),
    ("aws-access-key", re.compile(r"AKIA[A-Z0-9]{16}")),
    (
        "aws-secret-key",
        re.compile(
            r"(?i)(?:aws_secret_access_key|secret_access_key)\s*[:=]\s*"
            r"[\"']?[A-Za-z0-9/+=]{40}[\"']?"
        ),
    ),
    ("stripe-secret-key", re.compile(r"sk_(?:test|live)_[A-Za-z0-9]{24,}")),
    ("bearer-token", re.compile(r"Bearer\s+[A-Za-z0-9_.-]{20,}")),
    (
        "private-key",
        re.compile(r"-----BEGIN (?:(?:RSA|EC|DSA|OPENSSH) )?PRIVATE KEY-----"),
    ),
    (
        "gitea-bare-token",
        re.compile(
            r"(?i)(?:"
            r"(?:GITEA_TOKEN|GIT_HTTP_PASSWORD|SCM_TOKEN|ACCESS_TOKEN)"
            r"\s*[:=]\s*[\"']?[0-9a-f]{40}\b|"
            r"Authorization\s*:\s*token\s+[0-9a-f]{40}\b|"
            r"https://[^\s/@:]+:[0-9a-f]{40}@git\.moleculesai\.app(?:/|\b)"
            r")"
        ),
    ),
)

SKIP_DIRS = {".git", "node_modules", "__pycache__"}


def check_file(path: Path, root: Path) -> list[tuple[Path, int, str]]:
    """Return redacted ``(relative path, line, rule)`` findings for ``path``."""

    try:
        data = path.read_bytes()
    except OSError:
        return []
    if b"\0" in data:
        return []

    text = data.decode("utf-8", errors="ignore")
    relative = path.relative_to(root)
    findings: list[tuple[Path, int, str]] = []
    for lineno, line in enumerate(text.splitlines(), 1):
        for rule, pattern in RULES:
            if pattern.search(line):
                findings.append((relative, lineno, rule))
    return findings


def scan(root: Path) -> list[tuple[Path, int, str]]:
    """Scan all text-like files below ``root``, including dot directories/files."""

    findings: list[tuple[Path, int, str]] = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(directory for directory in dirnames if directory not in SKIP_DIRS)
        for filename in sorted(filenames):
            findings.extend(check_file(Path(dirpath) / filename, root))
    return findings


def main() -> int:
    root = Path(os.environ.get("GITHUB_WORKSPACE", ".")).resolve()
    findings = scan(root)
    if not findings:
        print("::notice::No secrets detected")
        return 0

    print("::error::Potential secrets found; values are redacted")
    for relative, lineno, rule in findings:
        print(
            f"::error file={relative},line={lineno},title=Potential secret::"
            f"{rule}: credential-shaped value detected"
        )
    return 1


if __name__ == "__main__":
    sys.exit(main())
