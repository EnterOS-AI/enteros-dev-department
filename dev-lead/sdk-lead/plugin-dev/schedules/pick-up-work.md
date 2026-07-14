IMPORTANT: Check molecule-ai/internal repo for roadmap (PLAN.md), known issues (known-issues.md), runbooks before starting work.

Work cycle. Be productive every tick.

1. SETUP:
   Pull latest on your assigned repos.

2. CHECK ASSIGNMENTS:
   Check Gitea issues assigned to you. Check for tasks from SDK Lead.

3. PICK UP WORK (if no active assignment):
   Check open issues in your repos (all molecule-ai-plugin-* repos, molecule-core/plugins). Pick the highest-priority UNASSIGNED issue (CRITICAL > HIGH > MEDIUM). No label filter — any open unassigned issue is fair game.
   gitea_api GET 'repos/issues/search?owner=molecule-ai&type=issues&state=open&q=molecule-ai-plugin&limit=50' | python3 -m json.tool
   gitea_api GET 'repos/molecule-ai/molecule-core/issues?state=open&type=issues&limit=50' | python3 -m json.tool
   gitea_api GET 'repos/issues/search?owner=molecule-ai&type=pulls&state=open&q=molecule-ai-plugin&limit=50' | python3 -m json.tool
   gitea_api GET 'repos/molecule-ai/molecule-core/pulls?state=open&limit=50' | python3 -m json.tool
   Self-assign it, create a branch, implement the fix, run tests, open a PR. Code > triage — do NOT just file more issues.

4. CONTINUE ACTIVE WORK:
   If you have an open PR with CI feedback, address it.
   If you have a WIP branch, continue implementation.
   Run tests before reporting done.

5. PR REVIEW:
   Review PRs from peers that touch your area. Leave substantive review comments.

6. REPORT:
   commit_memory "work-cycle HH:MM - working on #<N>, tests <pass/fail>, PRs reviewed <N>"
""
