IMPORTANT: Check Molecule-AI/internal repo for roadmap (PLAN.md), known issues (known-issues.md), runbooks before starting work.

Recurring security audit. Be thorough and incremental.

1. SETUP:
   cd /workspace/repos/molecule-controlplane && git pull origin staging
   LAST_SHA=$(recall_memory "security-last-sha" 2>/dev/null || echo "HEAD~20")
   echo "Auditing range: $LAST_SHA..HEAD"

2. STATIC ANALYSIS — run on changed files:
   cd /workspace/repos/molecule-controlplane && npm audit 2>&1 | head -30
   Check for known CVEs in dependencies.

3. TENANT ISOLATION SECURITY — critical checks:
   a. Auth middleware: verify every route goes through tenant auth.
      grep -rn "router\.\(get\|post\|put\|delete\|patch\)" --include="*.ts" src/ | grep -v middleware | grep -v test | head -20
      Any route registered without auth middleware is a P0.
   b. Cross-tenant data access: verify all DB queries scope by tenant_id.
      grep -rn "SELECT.*FROM\|UPDATE.*SET\|DELETE.*FROM" --include="*.ts" --include="*.js" src/ | grep -v tenant_id | grep -v test | grep -v migration | head -20
   c. Tenant header spoofing: verify tenant_id comes from auth token, not request headers.
   d. Billing isolation: verify billing operations are scoped to the authenticated tenant.

4. SECRETS SCAN:
   cd /workspace/repos/molecule-controlplane
   grep -rn "password\|secret\|token\|api_key\|stripe" --include="*.ts" --include="*.js" | grep -v test | grep -v node_modules | grep -v ".env" | head -30
   git log --all -p $LAST_SHA..HEAD | grep -iE "(password|secret|token|api_key)\s*[:=]" | grep -v test | head -20

5. MANUAL REVIEW — check changed files for:
   - SQL injection: raw string concatenation in queries
   - Missing auth on new endpoints
   - Privilege escalation: admin-only routes accessible by tenant users
   - Webhook signature verification: all incoming webhooks (Stripe, GitHub) must verify signatures
   - Rate limiting: tenant-scoped rate limits on all write endpoints

6. OPEN-PR REVIEW:
   gh pr list --repo Molecule-AI/molecule-controlplane --state open --json number,title,files --limit 10
   For each open PR diff, check for injection/auth-bypass/tenant-leak patterns.

7. RECORD commit SHA: commit_memory "security-last-sha" with current HEAD.

DELIVERABLE ROUTING (MANDATORY):
a. File GitHub issues for CRITICAL/HIGH findings.
b. delegate_task to team lead with summary.
c. If clean: report "clean, audited <SHA_RANGE>".
d. Save to memory "security-audit-latest".
