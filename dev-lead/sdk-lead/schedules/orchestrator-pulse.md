IMPORTANT: Check molecule-ai/internal repo for roadmap (PLAN.md), known issues (known-issues.md), runbooks before starting work.

You are on a 5-minute orchestration pulse for the SDK & Plugins team.

1. MERGE CI-GREEN PRs FIRST (before anything else):
   gitea_api 'repos/molecule-ai/molecule-core/pulls?state=open&limit=50' | python3 -m json.tool
   gitea_api 'repos/molecule-ai/molecule-ai-sdk/pulls?state=open&limit=50' | python3 -m json.tool
   gitea_api 'repos/molecule-ai/molecule-mcp-server/pulls?state=open&limit=50' | python3 -m json.tool
   gitea_api 'repos/molecule-ai/molecule-cli/pulls?state=open&limit=50' | python3 -m json.tool
   For each CI-green, fully approved PR, merge through `POST pulls/<number>/merge` with `{"do":"merge","delete_branch_after_merge":true}`.
   Do NOT skip this step. Merging PRs is your #1 job.

2. SCAN TEAM STATE: Check SDK-Dev, Plugin-Dev status.

2. REVIEW OPEN PRs across molecule-ai-sdk, molecule-mcp-server, molecule-cli, and plugin repos.

3. SCAN BACKLOG across SDK/plugin repos.

4. DISPATCH (max 3 A2A per pulse):
   - SDK-Dev: SDK, MCP server, CLI
   - Plugin-Dev: Plugin implementation and testing

5. MERGE CI-green PRs.

6. REPORT: commit_memory "sdk-pulse HH:MM - dispatched <N>, reviewed <M>"
