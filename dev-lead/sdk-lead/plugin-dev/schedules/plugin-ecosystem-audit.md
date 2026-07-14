Plugin ecosystem audit. Run this EVERY cycle — you own every molecule-ai-plugin-* repo.

## Step 1: Discover all plugin repos (NEVER use a hardcoded list)
```bash
gitea_api 'orgs/molecule-ai/repos?limit=100' |
  python3 -c 'import json,sys; rows=json.load(sys.stdin); print("\n".join(sorted("{} {}".format(r["name"], r["updated_at"]) for r in rows if r["name"].startswith("molecule-ai-plugin-"))))'
```
Save the count. If it changed since last cycle, investigate new repos.

## Step 2: Health check each repo
For each plugin repo discovered above:
```bash
REPO="<name>"
# CI status
gitea_api "repos/molecule-ai/$REPO/actions/runs?limit=1" | python3 -m json.tool
# Open issues
gitea_api "repos/molecule-ai/$REPO/issues?state=open&type=issues&limit=5" | python3 -m json.tool
# Open PRs
gitea_api "repos/molecule-ai/$REPO/pulls?state=open&limit=5" | python3 -m json.tool
# Last commit age
gitea_api "repos/molecule-ai/$REPO/commits?limit=1" |
  python3 -c 'import json,sys; rows=json.load(sys.stdin); print(rows[0]["commit"]["committer"]["date"] if rows else "no commits")'
```

## Step 3: Triage and act
- **CI red**: fix it NOW — clone, diagnose, push fix
- **Open issues > 0**: self-assign the highest-priority one, start working
- **Stale PR**: review it, approve or request changes
- **Last commit > 7 days**: check if the plugin is feature-complete or abandoned. If abandoned, file an issue.
- **No README or empty README**: write one
- **No tests**: add basic tests

## Step 4: Core pipeline check
```bash
cd /workspace/repos/molecule-core
gitea_git pull --ff-only
# Check for plugin pipeline changes
git log --oneline --since="24 hours ago" -- workspace/plugins_registry/
```
If pipeline changed, verify all plugins still install correctly.

## Step 5: Report
```
commit_memory "plugin-audit HH:MM — N repos, CI: X green / Y red, issues: Z open, acted on: <list>"
```

RULE: Do NOT just report numbers. If something is broken, FIX IT in this cycle.
