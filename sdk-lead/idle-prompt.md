Idle check. Quick scan:
1. gh pr list --repo Molecule-AI/molecule-sdk-python --state open --json number,title,statusCheckRollup | head -20
2. Check if any team members need unblocking.
3. If CI-green PRs have approvals: merge them.
4. If nothing to do: commit_memory "idle HH:MM — team clear, no blockers"
