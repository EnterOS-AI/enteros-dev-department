IMPORTANT: Check molecule-ai/internal repo for roadmap (PLAN.md), known issues (known-issues.md), runbooks before starting work.

QA review cycle. Be thorough and incremental.

1. Pull latest on your assigned repos:
   cd /workspace/repos/molecule-controlplane && gitea_git pull --ff-only origin main

2. Check what you audited last time: use search_memory("qa audit").

3. See what changed since last audit:
   git log --oneline $(recall_memory "qa-last-sha" 2>/dev/null || echo "HEAD~10")..HEAD

4. Run test suite:
   cd /workspace/repos/molecule-controlplane && go test -race ./... 2>&1 | tail -20
   Record exit code. If tests fail, capture the failing test names.

5. Tenant isolation tests — verify these critical boundaries:
   - Multi-tenant data queries always filter by tenant_id (grep handlers for raw SQL without tenant_id WHERE clause)
   - Auth middleware attaches tenant context before any handler runs
   - No cross-tenant data leakage in list/get endpoints
   Run from the Go module root: `grep -RIn "SELECT.*FROM" --include="*.go" . | grep -v tenant | grep -v _test.go | grep -v migration`
   Any query hitting a tenant-scoped table WITHOUT a tenant_id filter is a P0 bug.

6. Check test coverage on recently changed files:
   cd /workspace/repos/molecule-controlplane
   go test -race -coverprofile=/tmp/controlplane-coverage.out ./...
   go tool cover -func=/tmp/controlplane-coverage.out | tail -1
   Flag any changed file with <70% coverage.

7. Review recent PRs for quality issues and test gaps:
   gitea_api GET 'repos/molecule-ai/molecule-controlplane/pulls?state=open&limit=50' | python3 -m json.tool
   For each PR: does it add/change code without adding/updating tests? Flag it.

8. Check for regressions (run builds, look for errors):
   cd /workspace/repos/molecule-controlplane && go build ./... 2>&1 | tail -10

9. Record findings to memory.

DELIVERABLE ROUTING (MANDATORY every cycle):
a. For each failing test or coverage regression: FILE A GITEA ISSUE.
b. delegate_task to Controlplane Lead with a summary.
c. If all clean: delegate_task with "qa clean on SHA <X>".
d. Save to memory key "qa-audit-latest" as secondary record.
