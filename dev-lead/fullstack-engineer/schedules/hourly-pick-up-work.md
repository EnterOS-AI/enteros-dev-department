IMPORTANT: Check molecule-ai/internal for the roadmap, known issues, and runbooks before starting work.

Independent work cycle for molecule-core (Go + Canvas). Find work, write code,
push a topic branch, open a PR, and return to main. FULL CYCLE REQUIRED.

STEP 1 — CHECK CURRENT STATE:
  cd /workspace/repo
  If a previous topic branch has unpushed work, finish and push it first.
  If it has no PR, open one targeting main. Then:
    git switch main
    git pull --ff-only

STEP 2 — FIND WORK (prefer cross-cutting issues):
  tea issue list --repo molecule-ai/molecule-core --state open --json number,title,labels,assignees --jq '.[] | select(.assignees | length == 0) | select(.title | test("fullstack|api.*canvas|websocket|endpoint.*ui|handler.*component"; "i")) | "#\(.number) \(.title)"'
  Also consider issues that touch both workspace-server/ and canvas/.

STEP 3 — SELF-ASSIGN:
  tea issue edit <NUMBER> --repo molecule-ai/molecule-core --add-assignee @me

STEP 4 — WRITE CODE:
  git switch -c fix/issue-N-description
  Write code on both sides if needed.
  Run tests:
    cd workspace-server && go test -race ./...
    cd ../canvas && npm test && npm run build
  git add <changed-files>
  git commit -m "fix: description (closes #N)"

STEP 5 — PUSH + OPEN PR:
  git fetch origin main
  git rebase origin/main
  git push -u origin <branch>
  tea pr create --base main --title "fix: description" --body "Closes #N"

STEP 6 — RETURN TO MAIN:
  git switch main
  git pull --ff-only

RULES: All PRs target main. Never push directly to main. Both test suites must
pass. Merge commits only.
