IMPORTANT: Check molecule-ai/internal for the roadmap, known issues, and runbooks before starting work.

Independent work cycle for molecule-core (Go + Canvas). Find work, write code,
push a topic branch, open a PR, and return to main. FULL CYCLE REQUIRED.

STEP 1 — CHECK CURRENT STATE:
  cd /workspace/repo
  If a previous topic branch has unpushed work, finish and push it first.
  If it has no PR, open one targeting main. Then:
    git switch main
    gitea_git pull --ff-only

STEP 2 — FIND WORK (prefer cross-cutting issues):
  gitea_api GET 'repos/molecule-ai/molecule-core/issues?state=open&type=issues&limit=50' | python3 -m json.tool
  Also consider issues that touch both workspace-server/ and canvas/.

STEP 3 — SELF-ASSIGN:
  PAYLOAD=$(MOL_AGENT_PERSONA="${MOL_AGENT_PERSONA:?}" python3 -c 'import json,os; print(json.dumps({"assignees":[os.environ["MOL_AGENT_PERSONA"]]}))')
  ISSUE_NUMBER="${ISSUE_NUMBER:?set ISSUE_NUMBER to the numeric issue number}"
  gitea_api PATCH "repos/molecule-ai/molecule-core/issues/$ISSUE_NUMBER" "$PAYLOAD"

STEP 4 — WRITE CODE:
  TOPIC_SLUG="${TOPIC_SLUG:?set TOPIC_SLUG to a short branch-safe description}"
  SUMMARY="${SUMMARY:?set SUMMARY to the commit and PR summary}"
  git switch -c "fix/issue-$ISSUE_NUMBER-$TOPIC_SLUG"
  Write code on both sides if needed.
  Run tests:
    cd workspace-server && go test -race ./...
    cd ../canvas && npm test && npm run build
  cd /workspace/repo
  git status --short
  git add -p
  git commit -m "fix: $SUMMARY (closes #$ISSUE_NUMBER)"

STEP 5 — PUSH + OPEN PR:
  gitea_git fetch origin main
  git rebase origin/main
  gitea_git push -u origin HEAD
  BRANCH=$(git branch --show-current)
  PAYLOAD=$(BRANCH="$BRANCH" SUMMARY="$SUMMARY" ISSUE_NUMBER="$ISSUE_NUMBER" python3 -c 'import json,os; print(json.dumps({"base":"main","head":os.environ["BRANCH"],"title":"fix: "+os.environ["SUMMARY"],"body":"Closes #"+os.environ["ISSUE_NUMBER"]}))')
  gitea_api POST 'repos/molecule-ai/molecule-core/pulls' "$PAYLOAD"

STEP 6 — RETURN TO MAIN:
  git switch main
  gitea_git pull --ff-only

RULES: All PRs target main. Never push directly to main. Both test suites must
pass. Merge commits only.
