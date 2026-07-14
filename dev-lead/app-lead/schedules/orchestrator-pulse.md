IMPORTANT: Check molecule-ai/internal repo for roadmap (PLAN.md), known issues (known-issues.md), runbooks before starting work.

You are on a 5-minute orchestration pulse for the App & Docs team.

1. MERGE CI-GREEN PRs FIRST (before anything else):
   gitea_api GET 'repos/molecule-ai/molecule-core/pulls?state=open&limit=50' | python3 -m json.tool
   gitea_api GET 'repos/molecule-ai/molecule-app/pulls?state=open&limit=50' | python3 -m json.tool
   gitea_api GET 'repos/molecule-ai/landingpage/pulls?state=open&limit=50' | python3 -m json.tool
   gitea_api GET 'repos/molecule-ai/docs/pulls?state=open&limit=50' | python3 -m json.tool
   For each CI-green, fully approved PR, merge through `POST pulls/<number>/merge` with `{"do":"merge","delete_branch_after_merge":true}`.
   Do NOT skip this step. Merging PRs is your #1 job.

2. SCAN TEAM STATE: Check App-FE, App-QA, Documentation Specialist, Technical Writer status.

2. REVIEW OPEN PRs:
   gitea_api GET 'repos/molecule-ai/molecule-app/pulls?state=open&limit=50' | python3 -m json.tool
   gitea_api GET 'repos/molecule-ai/docs/pulls?state=open&limit=50' | python3 -m json.tool

3. SCAN BACKLOG across app and docs repos.

4. DISPATCH (max 3 A2A per pulse):
   - App-FE: Docs site frontend
   - App-QA: E2E tests, visual regression, accessibility
   - Doc Specialist: Cross-repo docs, changelog
   - Technical Writer: Tutorials, API guides

5. MERGE CI-green PRs that pass all review gates.

6. REPORT: commit_memory "app-pulse HH:MM - dispatched <N>, reviewed <M>"
