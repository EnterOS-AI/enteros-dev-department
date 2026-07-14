IMPORTANT: Check molecule-ai/internal repo for roadmap (PLAN.md), known issues (known-issues.md), runbooks before starting work.

Recurring security audit. Be thorough and incremental.

1. SETUP:
   cd /workspace/repos/molecule-controlplane && gitea_git pull --ff-only origin main
   LAST_SHA=$(recall_memory "security-last-sha" 2>/dev/null || echo "HEAD~20")
   echo "Auditing range: $LAST_SHA..HEAD"

2. STATIC ANALYSIS — Control Plane is Go:
   cd /workspace/repos/molecule-controlplane
   go vet ./...
   go list -m all
   Check changed `go.mod`/`go.sum` dependencies against the configured CI
   vulnerability scan; do not assume a JavaScript package audit exists.

3. TENANT ISOLATION SECURITY — critical checks:
   a. Auth middleware: verify every route goes through tenant auth.
      rg -n 'router\.(GET|POST|PUT|DELETE|PATCH)' cmd internal | head -20
      Any route registered without auth middleware is a P0.
   b. Cross-tenant data access: verify all DB queries scope by tenant_id.
      rg -n 'SELECT.*FROM|UPDATE.*SET|DELETE.*FROM' internal cmd | grep -v tenant_id | grep -v _test.go | grep -v migrations | head -20
   c. Tenant header spoofing: verify tenant_id comes from auth token, not request headers.
   d. Billing isolation: verify billing operations are scoped to the authenticated tenant.

4. SECRETS SCAN:
   cd /workspace/repos/molecule-controlplane
   rg -n -i 'password|secret|token|api_key|stripe' --glob '*.go' --glob '!**/*_test.go' | head -30
   git log --all -p $LAST_SHA..HEAD | grep -iE "(password|secret|token|api_key)\s*[:=]" | grep -v test | head -20

5. MANUAL REVIEW — check changed files for:
   - SQL injection: raw string concatenation in queries
   - Missing auth on new endpoints
   - Privilege escalation: admin-only routes accessible by tenant users
   - Webhook signature verification: all incoming webhooks (Stripe, Gitea, or another configured integration) must verify signatures
   - Rate limiting: tenant-scoped rate limits on all write endpoints

6. OPEN-PR REVIEW:
   gitea_api GET 'repos/molecule-ai/molecule-controlplane/pulls?state=open&limit=50' | python3 -m json.tool
   For each open PR diff, check for injection/auth-bypass/tenant-leak patterns.

7. RECORD commit SHA: commit_memory "security-last-sha" with current HEAD.

DELIVERABLE ROUTING (MANDATORY):
a. File Gitea issues for CRITICAL/HIGH findings.
b. delegate_task to Controlplane Lead with summary.
c. If clean: report "clean, audited <SHA_RANGE>".
d. Save to memory "security-audit-latest".
