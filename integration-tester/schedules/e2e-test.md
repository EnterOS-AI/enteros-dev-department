IMPORTANT: Check Molecule-AI/internal repo for roadmap (PLAN.md), known issues (known-issues.md), runbooks before starting work.

Cross-repo E2E test cycle. Run every 30 minutes.

1. SETUP: Pull latest from molecule-core, molecule-controlplane, molecule-tenant-proxy, molecule-app, molecule-ai-workspace-runtime.

2. SMOKE TESTS — verify all services are reachable:
   Platform health:    curl -sf http://localhost:8080/health && echo "OK" || echo "FAIL: platform health"
   Scheduler liveness: curl -sf http://localhost:8080/admin/liveness && echo "OK" || echo "FAIL: liveness"
   WebSocket upgrade:  curl -sf -o /dev/null -w "%{http_code}" -H "Upgrade: websocket" -H "Connection: Upgrade" http://localhost:8080/ws
   If ANY smoke test fails: file a P0 issue immediately, skip remaining tests, report to Dev Lead.

3. E2E FLOW TESTS — run the full workspace lifecycle:
   a. Workspace create:   POST /workspaces with a test template, verify 201 response
   b. Workspace provision: poll GET /workspaces/:id until status=running (timeout 120s)
   c. Heartbeat:          POST /workspaces/:id/heartbeat, verify 200
   d. A2A message:        POST /workspaces/:id/a2a with a test message, verify 200 + valid response body
   e. Workspace delete:   DELETE /workspaces/:id, verify 200
   f. Verify deleted:     GET /workspaces/:id should return 404
   Record pass/fail for each step. Any failure = file a GitHub issue with the step that failed + response body.

4. SCHEDULER TEST — verify cron fires:
   curl -sf http://localhost:8080/admin/liveness | jq '.scheduler_status'
   Check that the scheduler reports recent fire timestamps (within last 30 minutes).

5. CHANNEL TEST — verify Slack integration:
   If Slack channel is configured: POST /channels/:id/test and verify 200 + message delivered.
   If not configured: skip and note in report.

6. CONTRACT TESTS: API schema compatibility, WebSocket protocol, A2A message format.
   Verify response shapes match expected schemas for key endpoints.

7. REPORT: File issues for failures. delegate_task to Dev Lead with summary including:
   - Per-step pass/fail for the E2E flow
   - Latency for workspace create-to-running
   - Any contract mismatches
