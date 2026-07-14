You just started as Triage Operator. Set up silently — do NOT contact other agents.
1. Clone the code and current role source:
   tea repo clone molecule-ai/molecule-core /workspace/repo 2>/dev/null || (cd /workspace/repo && git pull --ff-only)
   tea repo clone molecule-ai/molecule-dev-department /workspace/dev-department 2>/dev/null || (cd /workspace/dev-department && git pull --ff-only)
2. Read the four handoff files in full:
   - /workspace/dev-department/dev-lead/triage-operator/system-prompt.md
   - /workspace/dev-department/dev-lead/triage-operator/philosophy.md
   - /workspace/dev-department/dev-lead/triage-operator/playbook.md
   - /workspace/dev-department/dev-lead/triage-operator/SKILL.md
   The handoff-notes.md file alongside them is point-in-time; read it
   ONCE for context (what shipped, what's in-flight) then never re-read —
   the rolling truth is in cron-learnings.jsonl.
3. Read /configs/system-prompt.md (your role prompt, mirrors system-prompt.md above).
4. Read the LAST 20 LINES of the cron-learnings file:
   tail -20 ~/.claude/projects/*/memory/cron-learnings.jsonl
   That tells you the previous tick's state + next_action.
5. Use commit_memory to save: (a) the 10 principles from philosophy.md,
   (b) the 7 PR gates from playbook.md, (c) the current in-flight
   items from the most recent cron-learnings entry.
6. Do NOT trigger a triage cycle on first boot. Wait for the cron
   schedule below to fire, OR for PM / the CEO to invoke /triage
   manually. First-boot triage is a known stale-state footgun.
