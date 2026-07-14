Idle — no active task. Find work:
1. Inspect open PRs and their `requested_reviewers` field:
   `gitea_api GET 'repos/molecule-ai/molecule-ai-workspace-runtime/pulls?state=open&limit=50' | python3 -m json.tool`
2. List the first five unassigned open issues:
   `gitea_api GET 'repos/molecule-ai/molecule-ai-workspace-runtime/issues?state=open&type=issues&limit=50' | python3 -m json.tool`
3. Pick the highest-priority unassigned issue, self-assign, branch, implement.
4. If nothing: commit_memory "idle HH:MM — backlog empty, standing by"
