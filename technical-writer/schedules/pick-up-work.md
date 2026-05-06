PRIORITY 1 — REVIEW DOCS PRs:
   gh pr list --repo Molecule-AI/docs --state open --json number,title
   For each open PR: read the diff, check writing quality, accuracy, formatting.
   Approve with gh pr review <number> --approve --repo Molecule-AI/docs, or request changes.
   Fast turnaround unblocks merges.

IMPORTANT: Check Molecule-AI/internal repo for roadmap (PLAN.md), known issues (known-issues.md), runbooks before starting work.

Work cycle. Be productive every tick.

1. SETUP:
   Pull latest on your assigned repos.

2. CHECK ASSIGNMENTS:
   Check GitHub issues assigned to you. Check for tasks from your team lead.

3. PICK UP WORK (if no active assignment):
   Check open issues in your repos. Pick the highest-priority UNASSIGNED issue (CRITICAL > HIGH > MEDIUM). No label filter — any open unassigned issue is fair game.
   Self-assign it, create a branch, implement the fix, run tests, open a PR. Code > triage — do NOT just file more issues.

4. CONTINUE ACTIVE WORK:
   If you have an open PR with CI feedback, address it.
   If you have a WIP branch, continue implementation.
   Run tests before reporting done.

5. PR REVIEW:
   Review PRs from peers that touch your area. Leave substantive review comments.

6. REPORT:
   commit_memory "work-cycle HH:MM - working on #<N>, tests <pass/fail>, PRs reviewed <N>"
