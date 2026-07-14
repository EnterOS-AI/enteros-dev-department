You just started. Set up your environment silently — do NOT contact other agents yet.

1. Configure ephemeral Gitea authentication, then clone or update your assigned repo:
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
     if [ "$#" -lt 2 ] || [ "$#" -gt 3 ]; then
       echo "usage: gitea_api METHOD RELATIVE_ENDPOINT [JSON_BODY]" >&2
       return 2
     fi
     method="$1"
     endpoint="$2"
     body="${3-}"
     case "$method" in
       GET|POST|PUT|PATCH|DELETE) ;;
       *) echo "gitea_api: unsupported method" >&2; return 2 ;;
     esac
     endpoint_lower="${endpoint,,}"
     cr=$(printf "\\r_"); cr="${cr%_}"
     lf=$(printf "\\n_"); lf="${lf%_}"
     case "$endpoint" in
       ""|-*|/*|*\\*|*"$cr"*|*"$lf"*)
         echo "gitea_api: unsafe relative endpoint" >&2
         return 2
         ;;
     esac
     case "$endpoint_lower" in
       *://*|//*|*%0d*|*%0a*|*%25*|*%2e*|*%2f*|*%5c*)
         echo "gitea_api: unsafe relative endpoint" >&2
         return 2
         ;;
     esac
     case "/$endpoint/" in
       */../*|*/./*)
         echo "gitea_api: path traversal is not allowed" >&2
         return 2
         ;;
     esac
     case "${GITEA_TOKEN-}" in
       ""|*"$cr"*|*"$lf"*)
         echo "gitea_api: missing or invalid GITEA_TOKEN" >&2
         return 2
         ;;
     esac
     url="https://git.moleculesai.app/api/v1/$endpoint"
     if [ "$#" -eq 3 ]; then
       case "$method" in
         POST|PUT|PATCH) ;;
         *) echo "gitea_api: JSON body is not allowed for $method" >&2; return 2 ;;
       esac
       case "$body" in --*) echo "gitea_api: curl options are not JSON bodies" >&2; return 2 ;; esac
       exec 3<<<"header = \"Authorization: token $GITEA_TOKEN\"
   header = \"Content-Type: application/json\""
       printf "%s" "$body" |
         curl -q --config /dev/fd/3 -fsS -A curl/8.4.0 \
           --request "$method" --data-binary @- -- "$url"
     else
       printf "header = \"Authorization: token %s\"\n" "$GITEA_TOKEN" |
         curl -q --config - -fsS -A curl/8.4.0 --request "$method" -- "$url"
     fi
   )

   mkdir -p /workspace/repos
   REPO_URL="https://git.moleculesai.app/molecule-ai/molecule-ai-workspace-runtime.git"
   if [ -d /workspace/repos/molecule-ai-workspace-runtime/.git ]; then
     git -C /workspace/repos/molecule-ai-workspace-runtime remote set-url origin "$REPO_URL"
     gitea_git -C /workspace/repos/molecule-ai-workspace-runtime pull --ff-only
   else
     gitea_git clone "$REPO_URL" /workspace/repos/molecule-ai-workspace-runtime
   fi
   ln -sfn /workspace/repos/molecule-ai-workspace-runtime /workspace/repo
   ```

2. Read any checked-in agent or contributor guidance that actually exists:
   `find /workspace/repo -maxdepth 2 -type f \( -name AGENTS.md -o -name CLAUDE.md \) -print`
3. Read your role: `cat /configs/system-prompt.md`
4. Read the internal roadmap without assuming an SCM CLI is installed:
   `gitea_api GET 'repos/molecule-ai/internal/contents/PLAN.md?ref=main' | python3 -c 'import base64,json,sys; print(base64.b64decode(json.load(sys.stdin)["content"]).decode())' | head -100`
5. Save key conventions to memory.
6. Wait for tasks from your parent — do not initiate contact.
