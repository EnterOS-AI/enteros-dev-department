You just started. Set up your environment silently — do NOT contact other agents yet.

1. Clone your assigned repos:
   mkdir -p /workspace/repos
   git clone "https://x-access-token:${GITHUB_TOKEN}@github.com/Molecule-AI/molecule-app.git" /workspace/repos/molecule-app 2>/dev/null || (cd /workspace/repos/molecule-app && git pull)
   ln -sfn /workspace/repos/molecule-app /workspace/repo

2. Read project conventions: cat /workspace/repo/CLAUDE.md
3. Read your role: cat /configs/system-prompt.md
4. Check internal roadmap: gh repo clone Molecule-AI/internal /tmp/internal 2>/dev/null && cat /tmp/internal/PLAN.md | head -100
5. Save key conventions to memory.
6. Wait for tasks from your parent — do not initiate contact.
