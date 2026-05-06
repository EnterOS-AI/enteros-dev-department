IMPORTANT: Check Molecule-AI/internal repo for roadmap (PLAN.md), known issues (known-issues.md), runbooks before starting work.

Release cycle check. Run every 30 minutes.

1. CHECK STAGING VS MAIN:
   git fetch origin staging main
   Compare staging ahead count. If 0, report "staging=main" and stop.

2. REVIEW STAGING HEALTH:
   a. CI status: gh api repos/Molecule-AI/molecule-core/commits/staging/status --jq '.state'
   b. P0/P1 blockers: gh issue list --repo Molecule-AI/molecule-core --label "P0,P1" --state open --json number,title
      If any P0/P1 open: STOP. Do not promote. Report blockers.
   c. Security audit: recall_memory "security-audit-latest" — must be within last 6 hours.

3. HEALTH CHECKS (run before any promotion):
   Platform health:    curl -sf http://localhost:8080/health || echo "HEALTH ENDPOINT DOWN"
   Scheduler liveness: curl -sf http://localhost:8080/admin/liveness || echo "LIVENESS DOWN"
   Unhealthy containers: docker ps --filter "health=unhealthy" --format "{{.Names}}"
   If ANY health check fails: STOP promotion. File a GitHub issue if not already tracked.

4. ERROR RATE CHECK:
   Query recent activity_logs for error ratio over the last 30 minutes.
   Rollback criteria: >5% error rate OR health endpoint down >60s OR any unhealthy container.
   If rollback criteria met: do NOT promote. Report to Dev Lead with specifics.

5. PROMOTE (if all gates pass — staging ahead, CI green, no P0/P1, health OK, error rate <5%):
   Merge staging into main (merge commit, never squash/rebase).
   Tag release with semantic version. Generate changelog.

6. REPORT to Dev Lead with release summary.
