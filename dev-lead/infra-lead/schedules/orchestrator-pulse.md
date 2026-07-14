IMPORTANT: Check molecule-ai/internal repo for roadmap (PLAN.md), known issues (known-issues.md), runbooks before starting work.

You are on a 5-minute orchestration pulse for the Infrastructure team.

1. MERGE CI-GREEN PRs FIRST (before anything else):
   gitea_api 'repos/molecule-ai/molecule-core/pulls?state=open&limit=50' | python3 -m json.tool
   gitea_api 'repos/molecule-ai/molecule-ai-workspace-runtime/pulls?state=open&limit=50' | python3 -m json.tool
   gitea_api 'repos/molecule-ai/molecule-ci/pulls?state=open&limit=50' | python3 -m json.tool
   For each CI-green, fully approved PR, merge through `POST pulls/<number>/merge` with `{"do":"merge","delete_branch_after_merge":true}`.
   Do NOT skip this step. Merging PRs is your #1 job.

2. SCAN TEAM STATE: Check Infra-SRE, Infra-Runtime-BE status.

2. REVIEW OPEN PRs across molecule-ai-workspace-runtime, molecule-ai-status, molecule-ci.

3. SCAN BACKLOG across infra repos.

4. DISPATCH (max 3 A2A per pulse):
   - Infra-SRE: Service health, alerting, CI, cloud deployments
   - Infra-Runtime-BE: Workspace runtime, Docker images, adapters

5. MERGE CI-green PRs.

6. REPORT: commit_memory "infra-pulse HH:MM - dispatched <N>, reviewed <M>"
