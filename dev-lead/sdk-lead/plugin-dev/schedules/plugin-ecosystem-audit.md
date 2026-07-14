Plugin ecosystem audit. Run this EVERY cycle — you own every molecule-ai-plugin-* repo.

## Step 1: Discover all plugin repos (NEVER use a hardcoded list)
```bash
: > /tmp/org-repos.jsonl
page=1
while :; do
  PAGE_JSON=$(gitea_api GET "orgs/molecule-ai/repos?page=$page&limit=50") || exit 1
  COUNT=$(printf '%s' "$PAGE_JSON" | python3 -c 'import json,sys; print(len(json.load(sys.stdin)))') || exit 1
  [ "$COUNT" -eq 0 ] && break
  printf '%s' "$PAGE_JSON" |
    python3 -c 'import json,sys; [print(json.dumps(row, separators=(",", ":"))) for row in json.load(sys.stdin)]' \
    >> /tmp/org-repos.jsonl
  [ "$COUNT" -lt 50 ] && break
  page=$((page + 1))
done
python3 -c 'import json,sys; rows=(json.loads(line) for line in open(sys.argv[1], encoding="utf-8")); print("\n".join(sorted("{} {}".format(r["name"], r["updated_at"]) for r in rows if r["name"].startswith("molecule-ai-plugin-"))))' /tmp/org-repos.jsonl
```
Save the count. If it changed since last cycle, investigate new repos.

## Step 2: Health check each repo
For each plugin repo discovered above:
```bash
REPO="${REPO:?set REPO to a plugin repository name from the live inventory}"
# CI status
gitea_api GET "repos/molecule-ai/$REPO/actions/runs?limit=1" | python3 -m json.tool
# Open issues
gitea_api GET "repos/molecule-ai/$REPO/issues?state=open&type=issues&limit=5" | python3 -m json.tool
# Open PRs
gitea_api GET "repos/molecule-ai/$REPO/pulls?state=open&limit=5" | python3 -m json.tool
# Last commit age
gitea_api GET "repos/molecule-ai/$REPO/commits?limit=1" |
  python3 -c 'import json,sys; rows=json.load(sys.stdin); print(rows[0]["commit"]["committer"]["date"] if rows else "no commits")'
```

## Step 3: Triage and act
- **CI red**: fix it NOW — clone, diagnose, push fix
- **Open issues > 0**: self-assign the highest-priority one, start working
- **Stale PR**: review it, approve or request changes
- **Last commit > 7 days**: check if the plugin is feature-complete or abandoned. If abandoned, file an issue.
- **No README or empty README**: write one
- **No tests**: add basic tests

## Step 4: Runtime plugin pipeline check
```bash
RUNTIME_DIR=/workspace/repos/molecule-ai-workspace-runtime
RUNTIME_URL=https://git.moleculesai.app/molecule-ai/molecule-ai-workspace-runtime.git
mkdir -p /workspace/repos
if [ -d "$RUNTIME_DIR/.git" ]; then
  git -C "$RUNTIME_DIR" remote set-url origin "$RUNTIME_URL"
  gitea_git -C "$RUNTIME_DIR" pull --ff-only
else
  gitea_git clone "$RUNTIME_URL" "$RUNTIME_DIR"
fi
cd "$RUNTIME_DIR"
# Check for plugin pipeline changes
git log --oneline --since="24 hours ago" -- molecule_runtime/plugins_registry/
```
If pipeline changed, verify all plugins still install correctly.

## Step 5: Report
```bash
PLUGIN_COUNT="${PLUGIN_COUNT:?set PLUGIN_COUNT from the live inventory}"
GREEN_COUNT="${GREEN_COUNT:?set GREEN_COUNT from the CI checks}"
RED_COUNT="${RED_COUNT:?set RED_COUNT from the CI checks}"
OPEN_ISSUE_COUNT="${OPEN_ISSUE_COUNT:?set OPEN_ISSUE_COUNT from the issue checks}"
ACTED_ON="${ACTED_ON:-none}"
commit_memory "plugin-audit $(date -u +%H:%M) — $PLUGIN_COUNT repos, CI: $GREEN_COUNT green / $RED_COUNT red, issues: $OPEN_ISSUE_COUNT open, acted on: $ACTED_ON"
```

RULE: Do NOT just report numbers. If something is broken, FIX IT in this cycle.
