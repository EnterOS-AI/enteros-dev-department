# Triage Operator — Archived Handoff

The dated 2026-04-16 handoff was removed from the active workspace because its
repository names, hosting providers, local probes, issue state, credentials,
and deployment procedures no longer describe the platform. It is historical
incident evidence, not an operations runbook.

Do not infer current work or authority from this file. At the beginning of a
triage tick, establish live state from:

1. the assigned repositories and their checked-in contributor guidance;
2. the current Gitea issues, pull requests, commit statuses, and Actions runs;
3. `molecule-ai/internal` for the roadmap and current runbooks; and
4. the append-only role memory named by the runtime, when it exists.

Canonical SCM is `https://git.moleculesai.app`. Deployments are CI-on-merge.
Verify staging or production only through the applicable domain endpoint and
the exact commit's terminal workflow result. Production mutations still need
explicit human GO.

See `system-prompt.md`, `playbook.md`, and `philosophy.md` beside this file for
the active triage contract.
