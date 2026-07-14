Idle check. Quick scan:
1. List open PRs, then query the commit-status endpoint for each candidate:
   `gitea_api GET 'repos/molecule-ai/molecule-app/pulls?state=open&limit=20' | python3 -m json.tool`
2. Check if any team members need unblocking.
3. If CI-green PRs have approvals: merge them.
4. If nothing to do: commit_memory "idle HH:MM — team clear, no blockers"
