IMPORTANT: Check Molecule-AI/internal repo for roadmap (PLAN.md), known issues (known-issues.md), runbooks before starting work.

Work cycle. Be productive every tick.

1. SETUP:
   Pull latest on your assigned repos.

2. CHECK ASSIGNMENTS:
   gh issue list --repo Molecule-AI/molecule-core --assignee @me --state open --json number,title,labels
   Check for tasks from your team lead via search_memory("delegated-task").

3. PICK UP WORK (if no active assignment):
   gh issue list --repo Molecule-AI/molecule-core --state open --json number,title,labels,assignees --jq '.[] | select(.assignees | length == 0)' | head -20
   Pick the highest-priority UNASSIGNED issue (CRITICAL > HIGH > MEDIUM). No label filter — any open unassigned issue is fair game.
   Self-assign it, create a branch off staging, implement the fix, run tests, open a PR targeting staging (--merge flag only). Code > triage — do NOT just file more issues.

4. CONTINUE ACTIVE WORK:
   If you have an open PR with CI feedback, address it.
   If you have a WIP branch, continue implementation.
   Run tests before reporting done.

5. PR REVIEW:
   Review PRs from peers that touch your area. Leave substantive review comments.

6. REPORT:
   commit_memory "work-cycle HH:MM - working on #<N>, tests <pass/fail>, PRs reviewed <N>"
