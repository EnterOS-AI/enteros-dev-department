IMPORTANT: Check molecule-ai/internal repo for roadmap (PLAN.md), known issues (known-issues.md), runbooks before starting work.

Cross-repo E2E test cycle. Run every 30 minutes.

1. SETUP: Pull latest from molecule-core, molecule-controlplane, molecule-tenant-proxy, molecule-app, molecule-ai-workspace-runtime.

2. SMOKE TESTS — verify the domain-routed control planes are reachable:
   Production (read-only): `curl -fsS -A curl/8.4.0 https://api.moleculesai.app/health | python3 -c 'import json,sys; d=json.load(sys.stdin); raise SystemExit(0 if d == {"service":"molecule-cp","status":"ok"} else 1)'`
   Staging: `curl -fsS -A curl/8.4.0 https://staging-api.moleculesai.app/health | python3 -c 'import json,sys; d=json.load(sys.stdin); raise SystemExit(0 if d == {"service":"molecule-cp","status":"ok"} else 1)'`
   Resolve the dedicated staging test tenant through the authorized staging
   admin API, then probe `https://<tenant-slug>.moleculesai.app/health` and its
   documented WebSocket URL. Never substitute a local port as staging evidence.
   If ANY smoke test fails: file a P0 issue immediately, skip remaining tests, report to Dev Lead.

3. E2E FLOW TESTS — run the full workspace lifecycle against the dedicated
   staging test tenant only; never create/delete a production tenant:
   a. Workspace create:   POST /workspaces with a test template, verify 201 response
   b. Workspace provision: poll GET /workspaces/:id until status=running (timeout 120s)
   c. Heartbeat:          POST /workspaces/:id/heartbeat, verify 200
   d. A2A message:        POST /workspaces/:id/a2a with a test message, verify 200 + valid response body
   e. Workspace delete:   DELETE /workspaces/:id, verify 200
   f. Verify deleted:     GET /workspaces/:id should return 404
   Record pass/fail for each step. Any failure = file a Gitea issue with the step that failed + response body.

4. SCHEDULER TEST — verify a dedicated staging schedule fires and records a
   timestamp within the last 30 minutes through the tenant domain. The retired
   local `/admin/liveness` probe is not a current control-plane endpoint.

5. CHANNEL PLUGIN TEST — verify the provider-owned staging bridge:
   If a dedicated staging provider fixture, allowlisted sender, and destination
   are provisioned, run the channel plugin repository's documented staging
   canary/E2E. Verify authorized provider input reaches the workspace through
   the authenticated runtime socket/A2A contract and that the correlated reply
   returns through the plugin. The plugin owns provider authentication,
   allowlists, delivery, and replay handling; Core does not expose a native
   provider test endpoint. If the fixture is absent, skip and record the exact
   missing prerequisite. Never substitute production credentials or destinations.

6. CONTRACT TESTS: API schema compatibility, WebSocket protocol, A2A message format.
   Verify response shapes match expected schemas for key endpoints.

7. REPORT: File issues for failures. delegate_task to Dev Lead with summary including:
   - Per-step pass/fail for the E2E flow
   - Latency for workspace create-to-running
   - Any contract mismatches
