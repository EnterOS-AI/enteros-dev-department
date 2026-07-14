You just started as Dev Lead. Set up silently — do NOT contact other agents.
1. Clone or update Core with a clean remote and ephemeral credential helper:
   ```bash
   test -n "${GITEA_TOKEN:+set}" || { echo "GITEA_TOKEN is required" >&2; exit 2; }
   gitea_git() (
     set +x
     git -c credential.helper= \
       -c 'credential.helper=!f() {
         test "$1" = get || exit 0
         protocol=
         host=
         while IFS="=" read -r key value; do
           case "$key" in protocol) protocol="$value" ;; host) host="$value" ;; esac
         done
         test "$protocol" = https && test "$host" = git.moleculesai.app || exit 0
         printf "%s\n" "username=oauth2" "password=$GITEA_TOKEN"
       }; f' "$@"
   )
   REPO_URL=https://git.moleculesai.app/molecule-ai/molecule-core.git
   if [ -d /workspace/repo/.git ]; then
     git -C /workspace/repo remote set-url origin "$REPO_URL"
     gitea_git -C /workspace/repo pull --ff-only
   else
     gitea_git clone "$REPO_URL" /workspace/repo
   fi
   ```
2. Read the checked-in Core guidance that exists: `README.md`, `CONTRIBUTING.md`, and `workspace-server/docs/`.
3. Read /configs/system-prompt.md
4. Run: cd /workspace/repo && git log --oneline -5
5. Use commit_memory to save the architecture summary and recent changes
6. Wait for tasks from PM.
