IMPORTANT: Check Molecule-AI/internal repo for roadmap (PLAN.md), known issues (known-issues.md), runbooks before starting work.

QA review cycle. Be thorough and incremental.

1. Pull latest on your assigned repos:
   cd /workspace/repos/molecule-core && git pull origin staging

2. Check what you audited last time: use search_memory("qa audit").

3. See what changed since last audit:
   git log --oneline $(recall_memory "qa-last-sha" 2>/dev/null || echo "HEAD~10")..HEAD

4. Run Go test suite (workspace-server):
   cd /workspace/repos/molecule-core/workspace-server && go test -race -count=1 ./... 2>&1 | tail -30
   Record exit code. If tests fail, capture the failing test names and package paths.

5. Run Canvas test suite:
   cd /workspace/repos/molecule-core/canvas && npm test 2>&1 | tail -20

6. Run Python workspace tests:
   cd /workspace/repos/molecule-core/workspace && python -m pytest 2>&1 | tail -20

7. Check test coverage on recently changed files:
   For Go: cd /workspace/repos/molecule-core/workspace-server && go test -coverprofile=cover.out ./... 2>&1 | grep -E "^ok|FAIL"
   For Canvas: cd /workspace/repos/molecule-core/canvas && npm test -- --coverage 2>&1 | grep "All files"
   Flag any changed file with <70% coverage.

8. Review recent PRs for quality issues and test gaps:
   gh pr list --repo Molecule-AI/molecule-core --state merged --search "merged:>$(date -u -d '6 hours ago' +%Y-%m-%dT%H:%M:%SZ)" --json number,title,files --limit 10
   For each PR: does it add/change code without adding/updating tests? Flag it.

9. Check for regressions (run builds, look for errors):
   cd /workspace/repos/molecule-core/workspace-server && go build ./... 2>&1 | tail -10
   cd /workspace/repos/molecule-core/canvas && npm run build 2>&1 | tail -10

10. Record findings to memory.

DELIVERABLE ROUTING (MANDATORY every cycle):
a. For each failing test or coverage regression: FILE A GITHUB ISSUE.
b. delegate_task to your team lead with a summary.
c. If all clean: delegate_task with "qa clean on SHA <X>".
d. Save to memory key "qa-audit-latest" as secondary record.
