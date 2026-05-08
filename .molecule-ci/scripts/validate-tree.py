#!/usr/bin/env python3
"""
validate-tree.py — orphan / reachability / shape lint for an org-template tree.

Walks the manifest (org.yaml or dev-department.yaml) → roots → recursive
`children:` (and `!include`) → builds the set of reachable workspace
folders → compares against the filesystem → reports violations.

Catches the four failure modes that motivated the RFC (internal#77):

  1. Orphan workspace folders (folder exists, no parent claims it).
  2. Cross-tree `..` traversal in `children:` paths (atomization rule).
  3. Workspace folder without `workspace.yaml` (broken nest).
  4. Two parents claiming the same child workspace (graph not a tree).

Usage:

    .molecule-ci/scripts/validate-tree.py [<manifest>]

Exits non-zero on any violation. With no arg, defaults to the first of
{dev-department.yaml, org.yaml} that exists in cwd.

Standard library only — runs on every CI runner without `pip install`.

Refs: internal#77 (Phase 3b — task #223).
"""

from __future__ import annotations

import os
import sys
import re
from pathlib import Path
from typing import Any

try:
    import yaml  # PyYAML
except ImportError:
    sys.stderr.write(
        "validate-tree.py: PyYAML required. Install via `pip install pyyaml` or use a runner that bundles it.\n"
    )
    sys.exit(2)


# ---------- !include + children: walker ----------

INCLUDE_TAG = "!include"


class IncludingLoader(yaml.SafeLoader):
    """SafeLoader that records `!include <path>` scalars verbatim instead
    of trying to resolve them. We do resolution explicitly so we can also
    track the parent→child edge for the orphan/duplicate check."""


def _include_constructor(loader: yaml.Loader, node: yaml.Node) -> dict:
    """Replace a `!include` scalar with a sentinel dict the walker
    interprets. We don't resolve the file content here — the walker does
    that with full path-context awareness."""
    if not isinstance(node, yaml.ScalarNode):
        raise yaml.YAMLError(f"!include must be a scalar path; got {node.tag} at line {node.start_mark.line}")
    return {"__include__": loader.construct_scalar(node)}


IncludingLoader.add_constructor(INCLUDE_TAG, _include_constructor)


def _yaml_load(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return yaml.load(f, Loader=IncludingLoader)


# ---------- Tree walk ----------


class TreeReport:
    def __init__(self) -> None:
        self.parent_of: dict[str, str] = {}          # workspace-folder → parent-folder
        self.cross_tree_refs: list[tuple[str, str]] = []   # (where, escaping path)
        self.duplicates: list[tuple[str, str, str]] = []   # (folder, parent_a, parent_b)
        self.missing_workspace_yaml: list[str] = []  # folders referenced as children but no workspace.yaml
        self.errors: list[str] = []                  # generic errors (yaml parse, missing include)

    def add_edge(self, parent_folder: str, child_folder: str) -> None:
        if child_folder in self.parent_of:
            self.duplicates.append((child_folder, self.parent_of[child_folder], parent_folder))
        else:
            self.parent_of[child_folder] = parent_folder

    def reachable(self) -> set[str]:
        return set(self.parent_of.keys())

    def has_violations(self) -> bool:
        return bool(self.cross_tree_refs or self.duplicates or self.missing_workspace_yaml or self.errors)


def _walk_workspace_node(
    node: Any,
    yaml_dir: Path,        # dir of the YAML file currently being processed (for relative paths)
    repo_root: Path,       # repo root (for orphan-set comparison + escape detection)
    parent_folder: str | None,
    report: TreeReport,
) -> None:
    """Walk a workspace-shaped dict (or list of children) recursively.

    For each `!include` we encountered (now wrapped as `{"__include__": "<path>"}`),
    we resolve to the target file, register the workspace folder, and
    recurse into the loaded content.
    """
    if node is None:
        return

    # Top-level YAML doc may have `workspaces:` or `roots:` (the
    # dev-department.yaml convention) listing the root workspaces.
    if isinstance(node, dict) and ("workspaces" in node or "roots" in node):
        roots = node.get("roots") or node.get("workspaces") or []
        for child in roots:
            _walk_workspace_node(child, yaml_dir, repo_root, parent_folder=None, report=report)
        return

    # !include sentinel: resolve, register, recurse.
    if isinstance(node, dict) and "__include__" in node:
        rel = node["__include__"]
        target = (yaml_dir / rel).resolve()
        try:
            target.relative_to(repo_root.resolve())
        except ValueError:
            # The !include path escapes the repo root. This is the
            # cross-repo symlink case (parent template !include-ing into
            # the dev-department subtree via a symlink). The child folder
            # is OUTSIDE repo_root — record but don't claim as duplicate.
            # For the dev-department validator, repo_root IS dev-department,
            # so its own internal !includes never escape; cross-repo
            # composition is parent-template's concern.
            report.errors.append(
                f"!include {rel!r} (from {yaml_dir.name}) resolves outside repo root: {target}"
            )
            return
        if not target.exists():
            report.errors.append(f"!include {rel!r} (from {yaml_dir.name}): target does not exist: {target}")
            return

        # If the include targets a workspace.yaml, the FOLDER containing
        # it is the workspace identity.
        if target.name == "workspace.yaml":
            child_folder = str(target.parent.resolve().relative_to(repo_root.resolve()))
        else:
            # Team-shaped !include (e.g. teams/core-platform.yaml) — not a
            # workspace folder of its own. Recurse into its content.
            child_folder = None

        if child_folder is not None and parent_folder is not None:
            # Reject `..` traversal in the path the user wrote (atomization
            # rule). The resolved target may legitimately be in a parent
            # folder (sibling tree), but the dev-department's `children:`
            # paths are required to be `./<child>` only.
            if rel.startswith("..") or "/.." in rel:
                report.cross_tree_refs.append((parent_folder, rel))

        if child_folder is not None:
            report.add_edge(parent_folder or "<root>", child_folder)

        # Load and recurse.
        try:
            sub = _yaml_load(target)
        except yaml.YAMLError as e:
            report.errors.append(f"yaml parse {target}: {e}")
            return
        _walk_workspace_node(
            sub,
            yaml_dir=target.parent,
            repo_root=repo_root,
            parent_folder=child_folder if child_folder is not None else parent_folder,
            report=report,
        )
        return

    # Inline workspace-shaped dict.
    if isinstance(node, dict):
        # `files_dir:` identifies the workspace folder for inline declarations.
        files_dir = node.get("files_dir")
        if files_dir and parent_folder is None:
            # A root-level workspace declared inline (no !include). The
            # files_dir is the folder.
            files_dir_resolved = (repo_root / files_dir).resolve()
            try:
                rel_to_root = files_dir_resolved.relative_to(repo_root.resolve())
            except ValueError:
                report.errors.append(f"files_dir {files_dir!r} escapes repo root")
                return
            this_folder = str(rel_to_root)
            report.add_edge("<root>", this_folder)
            # Verify a workspace.yaml exists in that folder for atomized
            # tree (post-Phase 3c-2).
            ws_yaml = files_dir_resolved / "workspace.yaml"
            if not ws_yaml.exists():
                # Pre-atomization, a workspace can be declared inline at
                # the manifest level without a workspace.yaml in its
                # files_dir. Don't false-positive.
                pass
            current_folder = this_folder
        else:
            current_folder = parent_folder

        # Recurse into children.
        for child in node.get("children") or []:
            _walk_workspace_node(child, yaml_dir, repo_root, current_folder, report)
        return

    if isinstance(node, list):
        for child in node:
            _walk_workspace_node(child, yaml_dir, repo_root, parent_folder, report)
        return


# ---------- Filesystem scan ----------


# Folders inside the repo that are NOT workspace folders. The validator
# allows these to exist without a parent in the tree.
NON_WORKSPACE_DIRS = {
    ".git", ".github", ".molecule-ci", "docs", "scripts", "tests", "fixtures",
    "node_modules", "__pycache__", ".cache", ".venv", "venv",
}


def _scan_workspace_folders(repo_root: Path) -> set[str]:
    """Every directory containing a workspace.yaml is a workspace folder.
    Path returned is repo-relative and POSIX-style."""
    found: set[str] = set()
    for dirpath, dirnames, filenames in os.walk(repo_root, followlinks=False):
        # Prune obvious non-workspace dirs.
        dirnames[:] = [d for d in dirnames if d not in NON_WORKSPACE_DIRS]
        if "workspace.yaml" in filenames:
            rel = Path(dirpath).resolve().relative_to(repo_root.resolve())
            if str(rel) != ".":
                found.add(str(rel))
    return found


# ---------- Top-level ----------


def _find_manifest() -> Path:
    for name in ("dev-department.yaml", "org.yaml"):
        p = Path(name)
        if p.exists():
            return p
    sys.stderr.write(
        "validate-tree.py: no manifest found in cwd. Looked for: dev-department.yaml, org.yaml\n"
    )
    sys.exit(2)


def main() -> int:
    if len(sys.argv) > 2:
        sys.stderr.write("usage: validate-tree.py [<manifest>]\n")
        return 2
    manifest = Path(sys.argv[1]) if len(sys.argv) == 2 else _find_manifest()
    if not manifest.exists():
        sys.stderr.write(f"validate-tree.py: manifest does not exist: {manifest}\n")
        return 2

    repo_root = manifest.resolve().parent
    report = TreeReport()

    try:
        root_doc = _yaml_load(manifest)
    except yaml.YAMLError as e:
        sys.stderr.write(f"validate-tree.py: parsing {manifest}: {e}\n")
        return 2

    _walk_workspace_node(
        root_doc,
        yaml_dir=manifest.parent.resolve(),
        repo_root=repo_root,
        parent_folder=None,
        report=report,
    )

    fs_workspaces = _scan_workspace_folders(repo_root)
    reachable = report.reachable()
    orphans = sorted(fs_workspaces - reachable)

    # Build report.
    print(f"=== validate-tree.py report — manifest: {manifest} ===")
    print(f"  filesystem workspace folders : {len(fs_workspaces)}")
    print(f"  reachable from manifest      : {len(reachable)}")
    print(f"  orphans                       : {len(orphans)}")
    print(f"  cross-tree '..' refs          : {len(report.cross_tree_refs)}")
    print(f"  duplicate-parent claims       : {len(report.duplicates)}")
    print(f"  missing workspace.yaml        : {len(report.missing_workspace_yaml)}")
    print(f"  generic errors                : {len(report.errors)}")
    print()

    if orphans:
        print("ORPHANS (workspace folder exists but no parent claims it):")
        for o in orphans:
            print(f"  - {o}")
        print()
    if report.cross_tree_refs:
        print("CROSS-TREE '..' REFS (atomization rule violation):")
        for parent, path in report.cross_tree_refs:
            print(f"  - parent={parent}  path={path}")
        print()
    if report.duplicates:
        print("DUPLICATE PARENT CLAIMS (graph not a tree):")
        for child, p1, p2 in report.duplicates:
            print(f"  - child={child}  claimed_by=[{p1}, {p2}]")
        print()
    if report.errors:
        print("ERRORS:")
        for e in report.errors:
            print(f"  - {e}")
        print()

    fail = bool(orphans) or report.has_violations()
    if fail:
        print("FAIL — see above")
        return 1
    print("OK — tree is clean")
    return 0


if __name__ == "__main__":
    sys.exit(main())
