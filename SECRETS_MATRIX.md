# Secrets Matrix — Per-Role Least Privilege

Infisical at `https://key.moleculesai.app` is the secrets system of record. The
platform binds only the exact values authorized for a workspace and task. Do
not copy credential bundles to local files, commit secret values, or hand-edit
workspace `.env` files as a provisioning mechanism.

`GITEA_TOKEN` is a per-persona Gitea credential. Its repository and action
scope must match the role; it is not a shared administrator or founder token.
Model credentials follow the same rule: bind the selected runtime's exact
credential from Infisical rather than assuming one organization-wide provider.

## Matrix

| Role | Authorized binding | Scope enabled |
|---|---|---|
| **All workspaces** | Selected model/runtime credential from Infisical | Run the configured model; no hard-coded default provider secret. |
| **Leads** | `GITEA_TOKEN` for their team repositories | Review and, where policy permits, merge after required gates. |
| **Triage Operator** | `GITEA_TOKEN` for the repositories included in the assigned sweep | Label, comment, close, and identify gate-ready work; mechanical merges only when explicitly authorized. |
| **Engineers** | `GITEA_TOKEN` with author scope | Create branches, issues, comments, and PRs; no merge authority. |
| **QA, Security, UI/UX** | `GITEA_TOKEN` with review/comment scope | Post evidence-backed review outcomes; no code merge authority. |
| **Infrastructure, SRE, Runtime** | `GITEA_TOKEN` plus exact task-specific operational values bound from Infisical | CI, registry, DNS, runtime, and incident work within the assigned environment. No standing provider bundle. |
| **Controlplane** | Repository-scoped `GITEA_TOKEN`; control-plane admin credential only for an explicitly authorized operation | Control-plane code and approved API operations. |
| **Documentation Specialist, Technical Writer** | `GITEA_TOKEN` scoped to documentation, landing, or assigned source repositories | Documentation branches and PRs only. |
| **Release Manager** | `GITEA_TOKEN` plus task-specific package publishing credentials from Infisical | Versioning, release PRs, and approved publication workflows. |
| **Channel-enabled roles** | Only the channel token and destination identifiers required by their declared channel | Send through that role's configured channel; no cross-role reuse. |

## Provisioning rules

1. Maintain the allowlist in Infisical and the platform's workspace binding.
2. Bind a value only when the role and current task require it.
3. Keep per-persona identities distinct so comments, commits, and operations
   have an attributable audit trail.
4. Rotate or revoke the narrow credential involved in an incident; do not
   replace it with a broader shared token.
5. Treat `.env.example` files as key-shape documentation only. They are not a
   request to create a local `.env` or paste real values into the repository.

Least privilege limits prompt-injection blast radius and makes the credential
used for an operation attributable to the responsible persona.
