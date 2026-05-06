IMPORTANT: Check Molecule-AI/internal repo for roadmap (PLAN.md), known issues (known-issues.md), runbooks before starting work.

QA review cycle. Be thorough and incremental.

1. Pull latest on your assigned repos:
   cd /workspace/repos/molecule-controlplane && git pull origin staging

2. Check what you audited last time: use search_memory("qa audit").

3. See what changed since last audit:
   git log --oneline $(recall_memory "qa-last-sha" 2>/dev/null || echo "HEAD~10")..HEAD

4. Run test suite:
   cd /workspace/repos/molecule-controlplane && npm test 2>&1 | tail -20
   Record exit code. If tests fail, capture the failing test names.

5. Tenant isolation tests — verify these critical boundaries:
   - Multi-tenant data queries always filter by tenant_id (grep handlers for raw SQL without tenant_id WHERE clause)
   - Auth middleware attaches tenant context before any handler runs
   - No cross-tenant data leakage in list/get endpoints
   Run: grep -rn "SELECT.*FROM" --include="*.ts" --include="*.js" src/ | grep -v tenant | grep -v test | grep -v migration
   Any query hitting a tenant-scoped table WITHOUT a tenant_id filter is a P0 bug.

6. Check test coverage on recently changed files:
   cd /workspace/repos/molecule-controlplane && npm test -- --coverage 2>&1 | grep "All files"
   Flag any changed file with <70% coverage.

7. Review recent PRs for quality issues and test gaps:
   gh pr list --repo Molecule-AI/molecule-controlplane --state merged --search "merged:>$(date -u -d '6 hours ago' +%Y-%m-%dT%H:%M:%SZ)" --json number,title,files --limit 10
   For each PR: does it add/change code without adding/updating tests? Flag it.

8. Check for regressions (run builds, look for errors):
   cd /workspace/repos/molecule-controlplane && npm run build 2>&1 | tail -10

9. Record findings to memory.

DELIVERABLE ROUTING (MANDATORY every cycle):
a. For each failing test or coverage regression: FILE A GITHUB ISSUE.
b. delegate_task to your team lead with a summary.
c. If all clean: delegate_task with "qa clean on SHA <X>".
d. Save to memory key "qa-audit-latest" as secondary record.
