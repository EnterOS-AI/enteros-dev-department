You just started. Set up your environment silently — do NOT contact other agents yet.

1. Configure ephemeral Gitea authentication, then clone or update your assigned repo:
   ```bash
   test -n "${GITEA_TOKEN:-}" || { echo "GITEA_TOKEN is required" >&2; exit 2; }
   gitea_git() (
     set +x
     git -c credential.helper= \
       -c 'credential.helper=!f() {
         test "$1" = get || exit 0
         protocol=
         host=
         while IFS="=" read -r key value; do
           case "$key" in
             protocol) protocol="$value" ;;
             host) host="$value" ;;
           esac
         done
         test "$protocol" = https && test "$host" = git.moleculesai.app || exit 0
         printf "%s\n" "username=oauth2" "password=$GITEA_TOKEN"
       }; f' "$@"
   )
   gitea_api() (
     set +x
     endpoint="$1"
     shift
     printf 'header = "Authorization: token %s"\n' "$GITEA_TOKEN" |
       curl --config - -fsS -A curl/8.4.0 "$@" "https://git.moleculesai.app/api/v1/$endpoint"
   )

   mkdir -p /workspace/repos
   REPO_URL="https://git.moleculesai.app/molecule-ai/molecule-controlplane.git"
   if [ -d /workspace/repos/molecule-controlplane/.git ]; then
     git -C /workspace/repos/molecule-controlplane remote set-url origin "$REPO_URL"
     gitea_git -C /workspace/repos/molecule-controlplane pull --ff-only
   else
     gitea_git clone "$REPO_URL" /workspace/repos/molecule-controlplane
   fi
   ln -sfn /workspace/repos/molecule-controlplane /workspace/repo
   ```

2. Read any checked-in agent or contributor guidance that actually exists:
   `find /workspace/repo -maxdepth 2 -type f \( -name AGENTS.md -o -name CLAUDE.md \) -print`
3. Read your role: `cat /configs/system-prompt.md`
4. Read the internal roadmap without assuming an SCM CLI is installed:
   `gitea_api 'repos/molecule-ai/internal/contents/PLAN.md?ref=main' | python3 -c 'import base64,json,sys; print(base64.b64decode(json.load(sys.stdin)["content"]).decode())' | head -100`
5. Save key conventions to memory.
6. Wait for tasks from your parent — do not initiate contact.
