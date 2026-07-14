#!/usr/bin/env bash
# local-e2e-setup.sh — bootstrap the local fixture for end-to-end
# testing of the dev-department composition (RFC internal#77).
#
# Composition shape evolved 2026-05-08:
#   - PR #5  (parent template): introduced dev-lead symlink + sibling-clone deploy.
#   - PR #6  (parent template, this PR's parent): replaced symlink with `!external`
#            resolver block. Composition now happens at platform import time.
#
# Effective state: only the parent template needs to be cloned. The dev tree
# is fetched on demand by the workspace-server's `!external` resolver into
# <orgBaseDir>/.external-cache/, populated when go tests call resolveYAMLIncludes.
#
# Optional: still clone molecule-dev-department as a sibling for symlink-
# based composition tests (TestLocalE2E_DevDepartmentExtraction +
# TestLocalE2E_FilesDirConsumption). Those tests skip gracefully if the
# symlink isn't created — they're regression coverage for the symlink path
# the resolver still supports, even though no production template uses it.
#
# Sets up (default):
#   /tmp/local-e2e-deploy/
#   └── molecule-dev/                  ← parent template (uses !external)
#
# Sets up (with --with-symlink for legacy tests):
#   /tmp/local-e2e-deploy/
#   ├── molecule-dev/
#   │   └── dev-lead → ../molecule-dev-department/dev-lead    (script-injected)
#   └── molecule-dev-department/
#
# After running, the canonical local-e2e test is exercisable:
#   cd <molecule-core>/workspace-server
#   go test -v -run TestLocalE2E_ExternalDevDepartment ./internal/handlers/
#
# Idempotent: re-running pulls latest. Pass --fresh to wipe and re-clone.

set -euo pipefail

ROOT="${LOCAL_E2E_ROOT:-/tmp/local-e2e-deploy}"
GITEA="${GITEA_URL:-https://git.moleculesai.app}"
TOKEN_PATH="${GITEA_TOKEN_FILE:-}"

PARENT_REPO="molecule-ai-org-template-molecule-dev"
PARENT_DIR_NAME="molecule-dev"
SUBTREE_REPO="molecule-dev-department"

WITH_SYMLINK=0
WIPE=0
for arg in "$@"; do
  case "$arg" in
    --fresh)        WIPE=1 ;;
    --with-symlink) WITH_SYMLINK=1 ;;
    -h|--help)
      sed -n '2,30p' "$0"
      exit 0 ;;
    *)
      echo "unknown flag: $arg" >&2
      exit 2 ;;
  esac
done

if [[ "$WIPE" == "1" ]]; then
  echo "[fresh] wiping ${ROOT}"
  rm -rf "${ROOT}"
fi

mkdir -p "${ROOT}"
cd "${ROOT}"

if [[ "${GITEA_TOKEN:+set}" != set ]]; then
  if [[ -z "${TOKEN_PATH}" || ! -f "${TOKEN_PATH}" ]]; then
    echo "ERROR: export GITEA_TOKEN or set GITEA_TOKEN_FILE explicitly" >&2
    exit 2
  fi
  GITEA_TOKEN=""
  IFS= read -r GITEA_TOKEN < "${TOKEN_PATH}"
fi
export GITEA_TOKEN

# The token remains in the environment and credential protocol only. The
# helper's command-line argument contains the variable name, never its value.
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

clone_or_pull() {
  local repo="$1" dir="$2"
  local url="${GITEA%/}/molecule-ai/${repo}.git"
  if [[ -d "${dir}/.git" ]]; then
    echo "[pull] ${dir}"
    # Ratchet any clone made by the older script back to a clean remote before
    # an authenticated operation can read or reuse it.
    git -C "${dir}" remote set-url origin "${url}"
    gitea_git -C "${dir}" pull --ff-only --quiet
  else
    echo "[clone] ${repo} → ${dir}"
    gitea_git clone --quiet "${url}" "${dir}"
  fi
}

clone_or_pull "${PARENT_REPO}" "${PARENT_DIR_NAME}"

if [[ "$WITH_SYMLINK" == "1" ]]; then
  clone_or_pull "${SUBTREE_REPO}" "${SUBTREE_REPO}"
  SYMLINK="${PARENT_DIR_NAME}/dev-lead"
  if [[ ! -L "${SYMLINK}" ]]; then
    echo "[symlink] creating ${SYMLINK} → ../${SUBTREE_REPO}/dev-lead (post-PR #6 the parent no longer ships one; injected for legacy tests)"
    ln -s "../${SUBTREE_REPO}/dev-lead" "${SYMLINK}"
  fi
  if [[ ! -f "${SYMLINK}/workspace.yaml" ]]; then
    echo "ERROR: ${SYMLINK}/workspace.yaml does not resolve — symlink target missing" >&2
    ls -la "${SYMLINK}" >&2
    exit 4
  fi
fi

unset GITEA_TOKEN

echo ""
echo "== ready =="
echo "  parent : ${ROOT}/${PARENT_DIR_NAME}"
if [[ "$WITH_SYMLINK" == "1" ]]; then
  echo "  subtree: ${ROOT}/${SUBTREE_REPO}"
  echo "  symlink: $(ls -la "${PARENT_DIR_NAME}/dev-lead" | awk '{print $NF}')"
fi
echo ""
echo "Run the canonical e2e (default — uses !external resolver, no fixture):"
echo "  cd <molecule-core>/workspace-server"
echo "  go test -v -run TestLocalE2E_ExternalDevDepartment ./internal/handlers/"
if [[ "$WITH_SYMLINK" == "1" ]]; then
  echo ""
  echo "Run the legacy symlink-path tests (regression coverage for symlink resolver):"
  echo "  go test -v -run TestLocalE2E_DevDepartmentExtraction ./internal/handlers/"
  echo "  go test -v -run TestLocalE2E_FilesDirConsumption ./internal/handlers/"
fi
