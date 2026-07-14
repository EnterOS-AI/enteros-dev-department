IMPORTANT: Check molecule-ai/internal for the roadmap, known issues, and runbooks before starting work.

Release-readiness cycle. Run every 30 minutes.

1. CHECK CURRENT MAIN:
   git fetch origin main
   MAIN_SHA=$(git rev-parse origin/main)
   Query the Gitea commit status for that exact SHA. Record each required check
   and its terminal conclusion; do not treat a queued or missing check as green.

2. CHECK BLOCKERS:
   tea issue list --repo molecule-ai/molecule-core --label "P0,P1" --state open --json number,title
   Confirm the required security and integration evidence is current. If a
   blocker exists, report the evidence and stop release preparation.

3. VERIFY RELEASE TOPOLOGY:
   Inspect the target repository's checked-in Gitea Actions workflows. Record
   the event that publishes a release, the registry/package destination, and
   any human authorization required. Do not assume every repository deploys on
   merge or has a production publisher.

4. PREPARE A RELEASE PR WHEN ASSIGNED:
   git switch main
   git pull --ff-only
   git switch -c release/<version>
   Update version and changelog files, run repository tests, push the branch,
   and open a PR targeting main. Never push or merge directly to main.

5. VERIFY AFTER AN AUTHORIZED MERGE OR TAG:
   Follow the exact Actions run to a terminal conclusion. Verify the expected
   artifact in its registry and the applicable user-visible/system-visible
   endpoint. A green build without an artifact or live result is incomplete.

6. REPORT to Dev Lead with the commit, PR/tag, check conclusions, artifact, and
   endpoint evidence. If publication is manual or absent, say so explicitly.
