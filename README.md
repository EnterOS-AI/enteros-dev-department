# molecule-ai/molecule-dev-department

Importable engineering subtree for Molecule AI organization templates.

This repository is not a standalone organization template. A parent template
loads one or more workspace roots from this repository with the platform's
`!external` resolver. The parent owns the organization identity and any
non-engineering workspaces; this repository owns the `dev-lead/` tree.

## Why a separate repository

The engineering tree had grown large enough that keeping it in a parent
template made reachability, ownership, and reuse harder to verify. Keeping it
separate:

- makes the engineering department reusable by multiple parent templates;
- gives the subtree its own review and release cadence;
- lets CI reject orphaned workspaces and unsafe cross-tree traversal; and
- keeps parent templates focused on organization-level composition.

The extraction design and its history are recorded in
[internal#77](https://git.moleculesai.app/molecule-ai/internal/issues/77).

## Import contract

Parent templates import a workspace root directly from this repository. Pin an
immutable tag or commit and bump it deliberately after validating the new tree:

```yaml
workspaces:
  - !external
    repo: molecule-ai/molecule-dev-department
    ref: v1.0.0
    path: dev-lead/workspace.yaml
```

The platform fetches the named repository and resolves `path` inside that
checkout. Parent-template defaults still apply to the imported workspaces; the
workspace files and their relative `children:` paths remain owned here. No
operator-side sibling clone or filesystem link is part of the contract.

## Repository layout

```text
.
├── dev-department.yaml
├── dev-lead/
│   └── workspace.yaml
├── .gitea/workflows/
│   └── validate.yml
└── .molecule-ci/scripts/
    ├── validate-tree.py
    ├── validate-current-ops.py
    └── check-secrets.py
```

`dev-department.yaml` documents defaults and points to the same Dev Lead root
for local tree validation. Parent templates normally import
`dev-lead/workspace.yaml` through `!external`.

## Validate locally

Run the same gates as `.gitea/workflows/validate.yml`:

```bash
python .molecule-ci/scripts/validate-tree.py --strict
python .molecule-ci/scripts/validate-current-ops.py
python .molecule-ci/scripts/check-secrets.py
```

The tree validator walks `dev-department.yaml -> roots -> children`, including
`!include` directives, and rejects orphan workspaces, duplicate parent claims,
missing workspace files, and unsafe `..` traversal. The operations-contract
validator rejects retired branch, repository, secrets, deployment, and channel
instructions. The secrets scan checks committed files for credential material.

## References

- [internal#77](https://git.moleculesai.app/molecule-ai/internal/issues/77) — extraction RFC and decision history
- [molecule-core#102](https://git.moleculesai.app/molecule-ai/molecule-core/pulls/102) — historical filesystem-resolution test from the earlier design

## License

MIT — see [LICENSE](./LICENSE).
