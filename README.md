# molecule-ai/molecule-dev-department

**Importable engineering-tree subtree** for Molecule AI org templates.

This repo is **not a standalone org template**. It is designed to be
grafted into a parent template (e.g. `molecule-ai-org-template-molecule-dev`)
via filesystem symlink at deploy time. The parent template owns the org
identity, top-level workspaces (PM, Marketing, Research, …), and
imports this repo's `dev-lead/` subtree as its engineering org.

## Why a separate repo

`molecule-ai-org-template-molecule-dev` had grown to ~60 workspace
folders + 11 `teams/*.yaml` composition files + 17 *orphaned* folders
that no `!include` chain reached. The orphan accumulation was a sign
the structure had outgrown a single repo.

Splitting the dev tree out:

- Atomizes engineering as a self-contained unit that other org templates
  can reuse (one link to add the whole department).
- Makes orphan accumulation impossible — the validator (CI gate) walks
  the manifest → roots → children and fails on any folder not reachable.
- Lets the dev tree evolve on its own cadence without churning the
  parent template.
- Keeps the parent template's structure focused on org identity (PM,
  Marketing, Research) and removes the ~50% of mass that's dev-specific.

Full design rationale: [internal#77 RFC](https://git.moleculesai.app/molecule-ai/internal/issues/77)

## Subtree contract

This repo is consumed by parent templates via this convention:

1. **Operator-side deploy layout** clones both repos as siblings under
   `/org-templates/`:

   ```
   /org-templates/
     molecule-ai-org-template-molecule-dev/   ← parent template
     molecule-dev-department/                 ← THIS repo
   ```

2. **Parent template** has a relative directory symlink at its root
   (or under `teams/`):

   ```
   parent-template/
     org.yaml
     dev → ../molecule-dev-department/        ← symlink
   ```

3. **Parent's `org.yaml`** imports the subtree:

   ```yaml
   workspaces:
     - !include teams/pm.yaml
     - !include teams/marketing.yaml
     - !include dev/dev-lead/workspace.yaml   ← into the symlinked subtree
   ```

4. **Workspace `files_dir:` paths inside this repo** use the symlink
   prefix (`dev/<workspace-name>`) so they resolve correctly when the
   subtree is imported via the parent. This means the subtree is **not
   directly importable as a standalone org template** — by design.

The platform's org importer (`workspace-server/internal/handlers/org_include.go`)
follows symlinks at the OS layer (`os.ReadFile` is symlink-aware) while
its security check (`filepath.Abs` / `filepath.Rel`) operates on path
strings (passes for symlinked paths because the link's path is inside
the parent root). The contract is pinned by tests in
[molecule-core PR #102](https://git.moleculesai.app/molecule-ai/molecule-core/pulls/102).

## Repo layout

```
.
├── dev-department.yaml         ← manifest: defaults + category_routing + roots
├── .molecule-ci/scripts/
│   └── validate-tree.py        ← orphan / reachability lint (CI gate)
├── .github/workflows/
│   └── validate.yml            ← runs validate-tree.py on every PR
├── README.md                   ← this file
├── LICENSE                     ← MIT
└── <workspace-folders>         ← scaffolded empty; populated by Phase 3c-2
```

After Phase 3c-2 (extract dev tree with git history) the repo will
contain the dev-lead/ workspace tree with nested sub-teams. After
Phase 3c-3 (move documentation-specialist + triage-operator into the
tree per Hongming Q1+Q2) those workspaces will live under
`dev-lead/app-docs/documentation-specialist/` and `dev-lead/triage-operator/`
respectively.

## Validating locally

```bash
.molecule-ci/scripts/validate-tree.py
# OK — tree is clean

# Or with explicit manifest:
.molecule-ci/scripts/validate-tree.py dev-department.yaml
```

The validator:

- Walks `dev-department.yaml → roots → children` recursively, including
  through `!include` directives.
- Lists every directory containing `workspace.yaml`.
- Reports orphans (filesystem dirs not reachable from manifest),
  cross-tree `..` traversal in `children:` paths, duplicate parents,
  and missing `workspace.yaml`.
- Exits non-zero on any violation.

CI runs the same script via `.github/workflows/validate.yml` on every
push and PR — orphan accumulation is caught at PR time, not at deploy
time.

## Phase status

| Phase | Status | Where |
|---|---|---|
| 1 — Investigate platform org importer | ✓ done | internal#77 comment 1886 |
| 2 — Design (SSOT, alternatives, security, versioning) | ✓ done | internal#77 |
| 3a — Platform `external:` ref support | parked (deferred) | task #222 |
| 3b — Validator + CI gate | ✓ done | this commit |
| 3c-1 — Scaffold this repo | ✓ done | this commit |
| 3c-2 — Extract dev tree with history | pending | task #224 |
| 3c-3 — Atomize structure + move doc-spec + triage-op | pending | task #224 |
| 3d — Slim parent template + wire symlink + delete orphans | pending | task #225 |
| 4 — End-to-end verify on staging | pending | task #226 |

## Refs

- [internal#77](https://git.moleculesai.app/molecule-ai/internal/issues/77) — extraction RFC
- [molecule-core#102](https://git.moleculesai.app/molecule-ai/molecule-core/pulls/102) — symlink-resolution test
- Hongming GO 2026-05-08 ("you own this feature and repos, start")

## License

MIT — see [LICENSE](./LICENSE)
