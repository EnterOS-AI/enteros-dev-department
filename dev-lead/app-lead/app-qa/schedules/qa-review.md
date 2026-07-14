IMPORTANT: Check molecule-ai/internal repo for roadmap (PLAN.md), known issues (known-issues.md), runbooks before starting work.

QA review cycle. Be thorough and incremental.

1. Pull latest on your assigned repos:
   cd /workspace/repos/molecule-app && gitea_git pull --ff-only origin main

2. Check what you audited last time: use search_memory("qa audit").

3. See what changed since last audit:
   git log --oneline $(recall_memory "qa-last-sha" 2>/dev/null || echo "HEAD~10")..HEAD

4. Run ALL test suites and record results:
   cd /workspace/repos/molecule-app && npm test 2>&1 | tail -20
   Record exit code. If tests fail, capture the failing test names.

5. Run E2E tests:
   cd /workspace/repos/molecule-app && npx playwright test --reporter=list 2>&1 | tail -30

6. Check test coverage on recently changed files:
   cd /workspace/repos/molecule-app && npm test -- --coverage 2>&1 | grep "All files"
   Flag any file with <80% line coverage that was changed since last audit.

7. Accessibility check:
   Review test output for axe-core / a11y violations. If the project has
   accessibility tests, run them explicitly and report any new violations.

8. Review recent PRs for quality issues and test gaps:
   gitea_api 'repos/molecule-ai/molecule-app/pulls?state=open&limit=50' | python3 -m json.tool
   For each PR: does it add/change code without adding/updating tests? Flag it.

9. Check for regressions (run builds, look for errors):
   cd /workspace/repos/molecule-app && npm run build 2>&1 | tail -20

10. Record findings to memory.

DELIVERABLE ROUTING (MANDATORY every cycle):
a. For each failing test or coverage regression: FILE A GITEA ISSUE.
b. delegate_task to your team lead with a summary.
c. If all clean: delegate_task with "qa clean on SHA <X>".
d. Save to memory key "qa-audit-latest" as secondary record.
