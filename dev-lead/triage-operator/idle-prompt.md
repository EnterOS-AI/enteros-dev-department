You have no active task. Sweep for mergeable PRs:

1. **Check all open PRs for merge readiness:**
   ```
   gitea_api 'repos/molecule-ai/molecule-core/pulls?state=open&limit=20' |
     python3 -m json.tool
   ```
   For each non-draft PR, fetch `pulls/<n>/reviews` and
   `commits/<head_sha>/status`. Merge only after every role gate passes, using
   `POST pulls/<n>/merge` with `{"do":"merge","delete_branch_after_merge":true}`.
   If CI is green but approval is missing, flag it to Dev Lead.

2. Check other org repos for stale PRs:
   `gitea_api 'repos/issues/search?owner=molecule-ai&type=pulls&state=open&sort=updated&limit=10' | python3 -m json.tool`

Pick ONE action. Under 90 seconds.
