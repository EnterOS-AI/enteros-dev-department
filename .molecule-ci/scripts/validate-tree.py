#!/usr/bin/env python3
"""
validate-tree.py — orphan / reachability / shape lint for an org-template tree.

Walks the manifest (org.yaml or dev-department.yaml) → roots → recursive
`children:` (and `!include`) → builds the set of reachable workspace
folders → compares against the filesystem → reports violations.

Catches the failure modes that motivated the RFC (internal#77):

  1. Orphan workspace folders (folder exists, no parent claims it).
  2. Cross-tree `..` traversal in `children:` paths (atomization rule).
  3. Two parents claiming the same child workspace (graph not a tree).
  4. Generic errors (missing !include target, parse failures).

Usage:

    .molecule-ci/scripts/validate-tree.py [--strict] [<manifest>]

Exits non-zero on orphans, duplicate parents, or generic errors. By
default cross-tree `..` refs print as warnings — extracted trees that
retain a transitional `teams/*.yaml` composition layer pre-atomization
will have these. Pass `--strict` (or set
`MOLECULE_VALIDATE_TREE_STRICT=1`) to also error on `..`. With no
manifest arg, defaults to the first of {dev-department.yaml, org.yaml}
found in cwd.

A "workspace folder" is identified by any of:
  - a workspace.yaml file inside it (atomized shape), or
  - a system-prompt.md / initial-prompt.md file (transitional shape;
    workspace is declared in a parent yaml's children: with
    files_dir: <this folder>).

Standard library only — runs on every CI runner without `pip install`
beyond PyYAML.

Refs: internal#77 (Phase 3b — task #223).
"""

from __future__ import annotations

import os
import sys
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
    of resolving them. We do resolution explicitly so we can also track
    the parent→child edge for the orphan/duplicate check."""


def _include_constructor(loader: yaml.Loader, node: yaml.Node) -> dict:
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
        self.parent_of: dict[str, str] = {}
        self.cross_tree_refs: list[tuple[str, str]] = []
        self.duplicates: list[tuple[str, str, str]] = []
        self.errors: list[str] = []

    def add_edge(self, parent_folder: str, child_folder: str) -> None:
        if child_folder in self.parent_of:
            self.duplicates.append((child_folder, self.parent_of[child_folder], parent_folder))
        else:
            self.parent_of[child_folder] = parent_folder

    def reachable(self) -> set[str]:
        return set(self.parent_of.keys())

    def has_hard_violations(self, strict: bool) -> bool:
        hard = bool(self.duplicates or self.errors)
        if strict:
            hard = hard or bool(self.cross_tree_refs)
        return hard


def _walk_workspace_node(
    node: Any,
    yaml_dir: Path,
    repo_root: Path,
    parent_folder: str | None,
    report: TreeReport,
    skip_files_dir_register: bool = False,
) -> None:
    """Walk a workspace-shaped dict / list / !include sentinel recursively.

    skip_files_dir_register: when True, the next dict-level files_dir
    won't add a parent→child edge — used after !include has already
    registered the workspace folder for the loaded yaml's content."""
    if node is None:
        return

    # Top-level YAML doc may have `workspaces:` or `roots:` listing the roots.
    if isinstance(node, dict) and ("workspaces" in node or "roots" in node):
        roots = node.get("roots") or node.get("workspaces") or []
        for child in roots:
            _walk_workspace_node(child, yaml_dir, repo_root, parent_folder=None, report=report)
        return

    # !include sentinel.
    if isinstance(node, dict) and "__include__" in node:
        rel = node["__include__"]
        target = (yaml_dir / rel).resolve()
        try:
            target.relative_to(repo_root.resolve())
        except ValueError:
            report.errors.append(
                f"!include {rel!r} (from {yaml_dir.name}) resolves outside repo root: {target}"
            )
            return
        if not target.exists():
            report.errors.append(f"!include {rel!r} (from {yaml_dir.name}): target does not exist: {target}")
            return

        try:
            sub = _yaml_load(target)
        except yaml.YAMLError as e:
            report.errors.append(f"yaml parse {target}: {e}")
            return

        # Identify the workspace folder this !include refers to:
        #   1. include targets a workspace.yaml — its parent dir is the folder.
        #   2. include targets a yaml whose top-level dict has files_dir —
        #      that files_dir is the folder.
        #   3. include targets a transparent composition file (no files_dir,
        #      no workspace.yaml) — recurse without registering.
        child_folder: str | None = None
        if target.name == "workspace.yaml":
            child_folder = str(target.parent.resolve().relative_to(repo_root.resolve()))
        elif isinstance(sub, dict) and sub.get("files_dir"):
            fd = sub["files_dir"]
            fd_resolved = (repo_root / fd).resolve()
            try:
                child_folder = str(fd_resolved.relative_to(repo_root.resolve()))
            except ValueError:
                report.errors.append(
                    f"!include {rel!r} declares files_dir {fd!r} outside repo root"
                )
                return

        # Cross-tree `..` ref check on the path the user wrote.
        if child_folder is not None and parent_folder is not None:
            if rel.startswith("..") or "/.." in rel:
                report.cross_tree_refs.append((parent_folder, rel))

        if child_folder is not None:
            report.add_edge(parent_folder or "<root>", child_folder)

        _walk_workspace_node(
            sub,
            yaml_dir=target.parent,
            repo_root=repo_root,
            parent_folder=child_folder if child_folder is not None else parent_folder,
            report=report,
            # !include already registered child_folder; suppress inline
            # re-registration when the loaded yaml's top dict has the
            # same files_dir.
            skip_files_dir_register=child_folder is not None,
        )
        return

    # Inline workspace-shaped dict.
    if isinstance(node, dict):
        files_dir = node.get("files_dir")
        current_folder = parent_folder
        if files_dir:
            fd_resolved = (repo_root / files_dir).resolve()
            try:
                this_folder = str(fd_resolved.relative_to(repo_root.resolve()))
            except ValueError:
                report.errors.append(f"files_dir {files_dir!r} escapes repo root")
                return
            if not skip_files_dir_register:
                report.add_edge(parent_folder or "<root>", this_folder)
            current_folder = this_folder
        for child in node.get("children") or []:
            _walk_workspace_node(child, yaml_dir, repo_root, current_folder, report)
        return

    if isinstance(node, list):
        for child in node:
            _walk_workspace_node(child, yaml_dir, repo_root, parent_folder, report)
        return


# ---------- Filesystem scan ----------


NON_WORKSPACE_DIRS = {
    ".git", ".github", ".molecule-ci", "docs", "scripts", "tests", "fixtures",
    "teams",  # composition layer, not workspace folders
    "node_modules", "__pycache__", ".cache", ".venv", "venv",
}

WORKSPACE_FOLDER_MARKERS = {
    "workspace.yaml", "system-prompt.md", "initial-prompt.md",
}


def _is_workspace_folder(filenames: list[str]) -> bool:
    return any(m in filenames for m in WORKSPACE_FOLDER_MARKERS)


def _scan_workspace_folders(repo_root: Path) -> set[str]:
    found: set[str] = set()
    for dirpath, dirnames, filenames in os.walk(repo_root, followlinks=False):
        dirnames[:] = [d for d in dirnames if d not in NON_WORKSPACE_DIRS]
        if _is_workspace_folder(filenames):
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
    args = sys.argv[1:]
    strict = False
    if "--strict" in args:
        strict = True
        args = [a for a in args if a != "--strict"]
    if os.environ.get("MOLECULE_VALIDATE_TREE_STRICT") == "1":
        strict = True
    if len(args) > 1:
        sys.stderr.write("usage: validate-tree.py [--strict] [<manifest>]\n")
        return 2
    manifest = Path(args[0]) if args else _find_manifest()
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

    print(f"=== validate-tree.py report — manifest: {manifest} ===")
    print(f"  filesystem workspace folders : {len(fs_workspaces)}")
    print(f"  reachable from manifest      : {len(reachable)}")
    print(f"  orphans                      : {len(orphans)}")
    print(f"  cross-tree '..' refs         : {len(report.cross_tree_refs)}")
    print(f"  duplicate-parent claims      : {len(report.duplicates)}")
    print(f"  generic errors               : {len(report.errors)}")
    print()

    if orphans:
        print("ORPHANS (workspace folder exists but no parent claims it):")
        for o in orphans:
            print(f"  - {o}")
        print()
    if report.cross_tree_refs:
        sev = "ERROR" if strict else "WARN"
        print(f"CROSS-TREE '..' REFS [{sev}] (atomization rule):")
        for parent, path in report.cross_tree_refs:
            print(f"  - parent={parent}  path={path}")
        if not strict:
            print("  (warn-only without --strict; pre-atomization extracted trees keep")
            print("   transitional `..` refs in teams/*.yaml; Phase 3c-3 removes them)")
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

    fail = bool(orphans) or report.has_hard_violations(strict)
    if fail:
        print("FAIL — see above")
        return 1
    suffix = " (strict)" if strict else ""
    print(f"OK — tree is clean{suffix}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
