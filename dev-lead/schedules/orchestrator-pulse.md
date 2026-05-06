IMPORTANT: Check Molecule-AI/internal repo for roadmap (PLAN.md), known issues, runbooks before starting work.

Orchestrator check-in (every 2h). Light-touch coordination only — engineers drive their own work now.

STEP 1 — TEAM OUTPUT CHECK (do NOT delegate — just observe):
  Check PRs across all team repos:
  for repo in molecule-core molecule-controlplane molecule-app molecule-tenant-proxy molecule-ai-workspace-runtime docs molecule-ci; do
    gh pr list --repo Molecule-AI/$repo --state open --json number,title,author,createdAt --limit 5 2>/dev/null
  done
  Engineers in scope: Backend (1/2/3), Frontend (1/2/3), Fullstack, DevOps,
  Platform, SRE, QA (1/2/3), Security (1/2), Offensive Security, UIUX.
  Check: are they opening PRs? If no new PRs from a role in 2h, note idle.

STEP 2 — BLOCKER SCAN:
  Check if any engineer has posted a blocker in Slack or via A2A.
  Only intervene if someone is genuinely blocked (not just idle — they have their own crons).

STEP 3 — CROSS-TEAM DEPENDENCY:
  If Frontend needs a Backend endpoint, or Backend needs a DevOps config, coordinate the handoff.
  Only delegate_task for genuine cross-team dependencies — NOT for routine work.

STEP 4 — MERGE TEAM PRs (per SHARED_RULES.md rule 9 — you ARE the merger for Dev team PRs):
  for repo in molecule-core molecule-controlplane molecule-app molecule-tenant-proxy molecule-ai-workspace-runtime docs molecule-ci; do
    gh pr list --repo Molecule-AI/$repo --state open --base staging --json number,title,statusCheckRollup,reviews 2>/dev/null
  done
  For EACH PR authored by your team:
  - Verify all 4 gates from rule 10 are present:
    1. All required CI checks green (`gh pr checks <N>`)
    2. `[qa-agent] APPROVED` (or N/A waiver for docs)
    3. `[security-auditor-agent] APPROVED` (or N/A waiver)
    4. `[uiux-agent] APPROVED` (or N/A waiver)
  - If ALL four gates pass: `gh pr merge <N> --merge --delete-branch`
  - If any gate missing/failing: leave a `[dev-lead-agent] BLOCKED ON: <gate>` comment, ping the responsible reviewer, do NOT merge
  - For high-blast-radius PRs (auth, billing, schema migrations, data deletion): ask PM first via `delegate_task` before merging
  - For trivial PRs (typo, lint, doc-only): may waive QA/Security/UIUX with `[dev-lead-agent] WAIVE-REVIEW: <reason>` — use sparingly

STEP 5 — REPORT (brief):
  Who shipped what since last pulse. Who is blocked and on what. PRs merged this cycle.
  Do NOT delegate routine work to engineers — they have their own pick-up-work crons.

RULES:
- Engineers self-organize via hourly work crons. Your job is unblocking + merging.
- All PRs target staging. Merge-commits only (`--merge`, never `--squash` or `--rebase`).
- You ARE the merger for Dev team PRs (rule 9). Do not delegate the merge — you own that gate.
- Escalate to PM only for cross-team trade-offs or CEO-level decisions (rule 12).
