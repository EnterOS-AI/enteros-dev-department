**Internal-first rule (SHARED_RULES §Content Worker Workflow).** When
you have content ready to publish, open the PR against
`molecule-ai/internal` (path: `internal/<area>/<slug>.md`) — **NOT** the
public repo. Ping your lead; they mirror to the public repo if
approved. This is the rule; do not push docs/landingpage PRs yourself.

Idle — no active task. Find work:
1. Inspect open PRs and their `requested_reviewers` field:
   `gitea_api 'repos/molecule-ai/docs/pulls?state=open&limit=50' | python3 -m json.tool`
2. List the first five unassigned open issues:
   `gitea_api 'repos/molecule-ai/docs/issues?state=open&type=issues&limit=50' | python3 -m json.tool`
3. Pick the highest-priority unassigned issue, self-assign, branch, implement.
4. If nothing: commit_memory "idle HH:MM — backlog empty, standing by"
