IMPORTANT: Check molecule-ai/internal for the roadmap, known issues, and runbooks before starting work.

Audit the current `molecule-ai/molecule-dev-department` template source. Catch
stale prompts, invalid imports, missing schedules, and unsupported config before
a parent template bumps its pinned `!external` reference.

1. CHECK SCHEDULE EXECUTION:
   Use the authorized platform/admin interface and current domain endpoints to
   inspect each imported workspace schedule's last terminal run. Compare the
   observed timestamp with its cron interval. More than two intervals behind is
   stale; file an evidence-backed issue against the owning repository. Do not
   assume a local container or direct database surface represents production.

2. CHECK TEMPLATE SOURCE:
   tea repo clone molecule-ai/molecule-dev-department /workspace/dev-department 2>/dev/null || (cd /workspace/dev-department && git pull --ff-only)
   cd /workspace/dev-department
   python .molecule-ci/scripts/validate-tree.py --strict
   python .molecule-ci/scripts/validate-current-ops.py
   python .molecule-ci/scripts/check-secrets.py

3. CHECK SYSTEM PROMPTS AGAINST CURRENT REPOS:
   find dev-lead -name system-prompt.md -print0 | while IFS= read -r -d '' file; do
     printf '%s %s\n' "$(git log -1 --format='%ar' -- "$file")" "$file"
   done
   Age alone is not a defect. Spot-check operational claims against the live
   Gitea repository, checked-in workflows, current domains, and current source
   paths; file exact mismatches.

4. CHECK ROLE-SPECIFIC PLUGINS AND SCHEDULES:
   Inspect each `workspace.yaml` together with `dev-department.yaml` defaults.
   Verify schedule `prompt_file` paths exist and role-specific plugins match the
   responsibility described by that workspace. Do not invent a missing plugin
   solely from a role name.

5. CHECK CHANNEL SHAPE:
   Each channel may use only `type`, `config`, `allowed_users`, and `enabled`.
   Confirm `${VAR}` references live under `config` and that the corresponding
   exact values are bound from Infisical. Category routing belongs in the
   organization/defaults config, not on channel entries.

6. ROUTING:
   Delegate an evidence-backed summary to PM with audit_summary metadata
   (`category=template`, severity, issues, and top_recommendation). If clean,
   send one concise clean result with the validated commit SHA.
