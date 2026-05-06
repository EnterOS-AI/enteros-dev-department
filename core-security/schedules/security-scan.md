IMPORTANT: Check Molecule-AI/internal repo for roadmap (PLAN.md), known issues (known-issues.md), runbooks before starting work.

Recurring security audit. Be thorough and incremental.

1. SETUP:
   cd /workspace/repos/molecule-core && git pull origin staging
   LAST_SHA=$(recall_memory "security-last-sha" 2>/dev/null || echo "HEAD~20")
   echo "Auditing range: $LAST_SHA..HEAD"

2. STATIC ANALYSIS — run on changed files:
   Go SAST:  cd /workspace/repos/molecule-core/workspace-server && gosec ./... 2>&1 | head -50
   Python:   cd /workspace/repos/molecule-core/workspace && bandit -r . 2>&1 | head -50
   CodeQL (if configured): gh api repos/Molecule-AI/molecule-core/code-scanning/alerts --jq '.[0:5]'

3. SECRETS SCAN — check for hardcoded credentials:
   cd /workspace/repos/molecule-core
   grep -rn "password\|secret\|token\|api_key" --include="*.go" --include="*.ts" --include="*.py" | grep -v test | grep -v _test | grep -v vendor | head -30
   git log --all -p $LAST_SHA..HEAD | grep -iE "(password|secret|token|api_key)\s*[:=]" | grep -v test | head -20
   Any match outside of config structs / env-var reads is a CRITICAL finding.

4. MANUAL REVIEW — check changed files for:
   - SQL injection: raw string concatenation in queries (no parameterized queries)
   - Path traversal: user input in file paths without sanitization
   - Missing auth: new HTTP handlers without auth middleware
   - Command injection: os/exec or subprocess with user input
   - XSS: unescaped user input in HTML responses
   - Timing-safe comparisons: password/token checks must use constant-time compare

5. AUTH BOUNDARY CHECK:
   Verify every new handler in platform/internal/handlers/ is registered behind
   the auth middleware. Grep for new HandlerFunc registrations and cross-check
   with router middleware chain.

6. LIVE API CHECKS: CanCommunicate bypass, CORS headers, rate limit enforcement.
   Teardown any DAST tooling after checks complete.

7. OPEN-PR REVIEW:
   gh pr list --repo Molecule-AI/molecule-core --state open --json number,title,files --limit 10
   For each open PR diff, check for injection/exec/unsafe patterns.

8. RECORD commit SHA: commit_memory "security-last-sha" with current HEAD.

DELIVERABLE ROUTING (MANDATORY):
a. File GitHub issues for CRITICAL/HIGH findings.
b. delegate_task to team lead with summary.
c. If clean: report "clean, audited <SHA_RANGE>".
d. Save to memory "security-audit-latest".
