IMPORTANT: Check molecule-ai/internal repo for roadmap (PLAN.md), known issues, runbooks before starting work.

Cross-repo docs watch. Fire every 2 hours. Mandate: keep documentation in
lockstep with the live molecule-ai/* Gitea org, NOT just
molecule-core. Updates that match repository state are owned by Doc Specialist
alone — no marketing approval needed. Marketing only enters the picture for
promotional spin on top of factual changes (e.g. blog post for a major release).

## 1. SETUP — record the cycle window

```bash
LAST_TICK=$(recall_memory "doc-watch-last-tick" 2>/dev/null || python3 -c 'from datetime import datetime,timedelta,timezone; print((datetime.now(timezone.utc)-timedelta(hours=2)).isoformat().replace("+00:00","Z"))')
NOW_TS=$(date -u +%Y-%m-%dT%H:%M:%SZ)
echo "Window: $LAST_TICK → $NOW_TS"
```

## 2. ENUMERATE every Molecule-AI repo (live list, don't trust the prior cache)

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
```

Filter to repos that received commits since LAST_TICK — those are the ones
worth scanning. (Skipping idle repos keeps the cycle bounded.)

## 3. PER-REPO: list merged PRs in the window

For each repo with recent activity, set `REPO` from the corresponding
`/tmp/org-repos.jsonl` record and then query it:
```bash
REPO="${REPO:?set REPO to a repository name from the live inventory}"
gitea_api GET "repos/molecule-ai/$REPO/pulls?state=closed&limit=50" |
  LAST_TICK="$LAST_TICK" python3 -c 'import json,os,sys; print(json.dumps([p for p in json.load(sys.stdin) if p.get("merged_at") and p["merged_at"] >= os.environ["LAST_TICK"]], indent=2))'
```

For each merged PR, check `files`:
- Touches a public API (`workspace-server/internal/handlers/`, `workspace-server/internal/router/`) → the matching page under `content/docs/api-reference/` likely needs an update.
- Touches a standalone workspace or org template repository → docs site `org-template.mdx` or `concepts.mdx`.
- Touches a plugin repo → docs site `plugins.mdx` (and the plugin repo's own README).
- Touches a `kind: channel` plugin or the SDK channel contract → docs site
  `plugins/channel-plugins.mdx` and `channels.mdx`, plus the provider plugin's
  own README. Provider behavior and verification belong to that plugin repo.
- Reintroduces provider-specific channel code or native channel routes in Core →
  treat it as a cutover regression and file a blocking Core issue; do not
  document it as a supported integration.
- Touches a schedule / cron / workflow → docs site `schedules.mdx`.
- Touches `migrations/` → docs site `architecture.mdx` schema section + a callout in the daily changelog.
- Touches CI (`*.yml` in `.gitea/workflows/`) → typically internal-only; skip unless it changes a publicly documented release or deployment flow.
- Touches `controlplane/` (PRIVATE repo) → update `controlplane/README.md` and `controlplane/PLAN.md`. **NEVER mention controlplane internals in public docs site.** Per privacy rule.

## 4. WRITE THE DOCS PR

For each docs gap discovered:
1. Branch in the docs site repo: `docs/<short-topic>-from-pr-<repo>-<number>` (e.g. `docs/lark-channel-from-core-480`)
2. Edit the relevant MDX file. Include:
   - 1-paragraph what-changed prose
   - The new/changed config syntax in a fenced code block
   - A working example
   - Cross-link to the PR that introduced it (`See [#480](...)` etc.)
3. Run `npm run build` locally (the docs site is a Next.js app — link checker + MDX parse run during build). Skip the PR if build fails; fix the docs first.
4. Open PR with title `docs(<area>): pair PR <repo>#<n> — <topic>` and body referencing the originating PR. **Always branch + PR — never commit to main on any repo.**

## 5. TERMINOLOGY DRIFT CHECK

Quick grep on the merged PRs' diffs for any new concept names. Compare to:
```bash
recall_memory "canonical-terminology" 2>/dev/null
```
If the PR introduces a NEW term that wasn't in your terminology memory, add it.
If the PR uses a SYNONYM of an existing term, file a fix-up PR to align with
the canonical name and update the terminology memory in same cycle.

## 6. STUB BACKFILL — opportunistic

If you finished the per-PR pairings with cycle time to spare, pick the
oldest "Coming soon" stub from the docs site and backfill it. Track
remaining stubs in memory under `stubs-pending` so the next tick picks the
next-oldest, not the same one twice.

## 7. MEMORY UPDATE — end of cycle

```python
commit_memory(
  key="doc-watch-last-tick",
  value=NOW_TS,
)
commit_memory(
  key=f"doc-watch-cycle-{NOW_TS[:13]}",
  value={
    "repos_scanned": [...],
    "prs_paired": [{"repo": r, "pr": n, "docs_pr": dp} for ...],
    "terminology_drift_caught": [...],
    "stubs_backfilled": [...],
    "deferred_to_next_cycle": [...],
  },
)
```

## 8. ESCALATION

- **Marketing handoff**: only when a PR represents a customer-facing
  feature launch worth blog-post coverage. Use `delegate_task` to
  Marketing Lead with a link to your docs PR + a one-liner of why it's
  notable. Don't ask marketing for routine docs updates — those are
  yours alone per CEO directive 2026-04-16.
- **Cross-team blockers**: if a PR is so undocumentable that you need
  the original engineer's input (private API, complex behavior), use
  `delegate_task` to Dev Lead asking for a clarifying comment on the
  source PR.
- **Privacy violations**: if you spot a public PR that leaks
  controlplane internals (file paths, internal endpoints, schema
  details), open a Critical issue on molecule-controlplane and
  notify CP-Security via A2A; use Core-Security instead when the leak is in
  molecule-core, a runtime, or a plugin repository.

## DEFINITION OF DONE FOR THIS CYCLE

- Memory updated with `doc-watch-last-tick`
- Every PR merged in the window has either: a paired docs PR open, OR a memory
  note explaining why it didn't need one (CI-only, internal refactor, etc.)
- No tools/files touched on `main` directly (always branch + PR)
- Activity log entry summarising the cycle's output (PR count, docs PR URLs)

6. INTERNAL DOCS REPO — molecule-ai/internal (added 2026-04-18):
   This is the team's private knowledge base. You own keeping it current:
   - PLAN.md — product roadmap. Update when phases complete or priorities shift.
   - known-issues.md — update when issues are resolved or new ones discovered.
   - runbooks/ — operational playbooks. Update when domains, CI-on-merge workflows, registries, or workspace-fleet behavior change.
   - security/ — threat models and findings. Sync with Security Auditor's audit outputs.
   - historical/retrospectives/ — session retrospectives. Add entries after major incidents or milestones.
   - ecosystem-watch.md, ecosystem-research-outcomes.md — sync with Research Lead outputs.

   Every 2h check:
   gitea_api GET 'repos/molecule-ai/internal/pulls?state=open&limit=50' | python3 -m json.tool
   gitea_api GET 'repos/molecule-ai/internal/commits?limit=3' | python3 -m json.tool
   If internal docs are stale versus the checked platform and deployment state, open a PR to fix them.
   NEVER copy internal content to public repos (molecule-core, docs). Privacy rule applies.
