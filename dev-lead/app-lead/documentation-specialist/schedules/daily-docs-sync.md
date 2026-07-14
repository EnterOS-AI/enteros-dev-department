IMPORTANT: Check molecule-ai/internal repo for roadmap (PLAN.md), known issues, runbooks before starting work.

MULTIMEDIA — when publishing docs, consider audio supplements:
- TTS: Generate audio versions of key documentation pages for accessibility.

Daily documentation maintenance. Two parallel objectives:
(1) keep the public docs site current with the platform repo,
(2) backfill stub pages on the docs site one at a time.

SETUP:
  cd /workspace/repo && git pull 2>/dev/null || true
  cd /workspace/docs && git pull 2>/dev/null || true
  cd /workspace/controlplane && git pull 2>/dev/null || true

1a. PAIR RECENT PLATFORM PRS (last 24h):
   cd /workspace/repo
   tea pr list --repo molecule-ai/molecule-core --state merged \
     --search "merged:>$(date -u -d '24 hours ago' +%Y-%m-%dT%H:%M:%SZ)" \
     --json number,title,files
   For each merged PR that touches a public surface
   (workspace-server/internal/handlers/, canvas/, docs/, or README.md):
   - Identify which docs page(s) on the public site cover that surface.
   - If a docs page exists but is stale → update it with examples
     from the PR diff. Open a PR to molecule-ai/docs with the change.
   - If NO docs page exists for the new surface → propose one
     (add to content/docs/meta.json + new .mdx file). Open a PR.
   - Link the originating molecule-core PR in the docs PR body. Do not use a
     cross-repository `Closes` claim unless the tracker is configured for it.

1b. PAIR RECENT CONTROLPLANE PRS (last 24h):
   cd /workspace/controlplane
   tea pr list --repo molecule-ai/molecule-controlplane --state merged \
     --search "merged:>$(date -u -d '24 hours ago' +%Y-%m-%dT%H:%M:%SZ)" \
     --json number,title,files
   ⚠️  PRIVATE REPO. Two cases:
   (i) Internal-only change (handler, schema, deployment configuration,
       billing logic): update README.md + PLAN.md + any
       docs/internal/*.md inside molecule-controlplane itself.
       Open the PR against molecule-ai/molecule-controlplane.
       NEVER mention these changes in /workspace/docs.
   (ii) Customer-facing change (new tier, new region, new SLA,
       pricing change, signup flow change): write a sanitized
       description for the PUBLIC docs site (e.g. "We now offer
       EU-region tenants" — not an internal file path, secret name,
       or provisioner implementation detail). Open a
       PR against molecule-ai/docs.
   When unsure which category a change falls into: default to
   INTERNAL-only and ask PM for explicit approval before publishing.

2. BACKFILL ONE STUB PAGE:
   cd /workspace/docs
   grep -l "Coming soon" content/docs/*.mdx | head -1
   Pick the highest-priority stub (one of: org-template, plugins,
   channels, schedules, architecture, api-reference, self-hosting,
   observability, troubleshooting). Write 300-800 words of
   hand-crafted, example-rich content based on:
   - The actual code in /workspace/repo/workspace-server/internal/handlers/
   - The actual source repository for any template being documented
   - The actual source repository for any plugin being documented
   Cite file paths so readers can follow the source. Open a PR.

3. LINK + ANCHOR CHECK:
   Use the browser-automation plugin to crawl
   https://doc.moleculesai.app (or the local dev server if the
   site isn't deployed yet — `cd /workspace/docs && npm install
   && npm run build && npm run start`). Report broken links and
   missing anchors back to PM.

4. ROUTING:
   delegate_task to PM with audit_summary metadata:
   - category: docs
   - severity: info
   - issues: [list of PR numbers opened to molecule-ai/docs]
   - top_recommendation: one-line summary
   If nothing to do today, PM-message a one-line "clean".

5. MEMORY:
   Save key 'docs-sync-latest' with timestamp + list of stub
   pages still pending + count of paired PRs this cycle.
