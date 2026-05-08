#!/usr/bin/env bash
# local-e2e-setup.sh — bootstrap the local sibling-clone fixture for
# end-to-end testing of the dev-department extraction (RFC internal#77).
#
# Sets up:
#   /tmp/local-e2e-deploy/
#   ├── molecule-dev/                  ← parent template (symlink wires dev-lead)
#   └── molecule-dev-department/       ← extracted dev tree
#
# After running, both Go tests are exercisable:
#   cd <molecule-core>/workspace-server
#   go test -v -run TestLocalE2E_DevDepartmentExtraction ./internal/handlers/
#   go test -v -run TestLocalE2E_FilesDirConsumption ./internal/handlers/
#
# Idempotent: re-running pulls latest from both repos. Pass --fresh to
# wipe and re-clone.

set -euo pipefail

ROOT="${LOCAL_E2E_ROOT:-/tmp/local-e2e-deploy}"
GITEA="${GITEA_URL:-https://git.moleculesai.app}"
TOKEN_PATH="${HOME}/.molecule-ai/gitea-token"

PARENT_REPO="molecule-ai-org-template-molecule-dev"
PARENT_DIR_NAME="molecule-dev"   # dir name parent expects (matches operator convention)
SUBTREE_REPO="molecule-dev-department"

if [[ "${1:-}" == "--fresh" ]]; then
  echo "[fresh] wiping ${ROOT}"
  rm -rf "${ROOT}"
fi

mkdir -p "${ROOT}"
cd "${ROOT}"

if [[ ! -f "${TOKEN_PATH}" ]]; then
  echo "ERROR: gitea token not at ${TOKEN_PATH}" >&2
  exit 2
fi
TOKEN="$(cat "${TOKEN_PATH}")"

clone_or_pull() {
  local repo="$1" dir="$2"
  local url="https://oauth2:${TOKEN}@${GITEA#https://}/molecule-ai/${repo}.git"
  if [[ -d "${dir}/.git" ]]; then
    echo "[pull] ${dir}"
    git -C "${dir}" pull --ff-only --quiet
  else
    echo "[clone] ${repo} → ${dir}"
    git clone --quiet "${url}" "${dir}"
  fi
}

clone_or_pull "${PARENT_REPO}"  "${PARENT_DIR_NAME}"
clone_or_pull "${SUBTREE_REPO}" "${SUBTREE_REPO}"

# Sanity: parent's dev-lead symlink target resolves to subtree's dev-lead.
SYMLINK="${PARENT_DIR_NAME}/dev-lead"
if [[ ! -L "${SYMLINK}" ]]; then
  echo "ERROR: ${SYMLINK} is not a symlink — parent template's PR #5 (slim) may not be deployed yet" >&2
  exit 3
fi
if [[ ! -f "${SYMLINK}/workspace.yaml" ]]; then
  echo "ERROR: ${SYMLINK}/workspace.yaml does not resolve — symlink target missing" >&2
  ls -la "${SYMLINK}" >&2
  exit 4
fi

echo ""
echo "== ready =="
echo "  parent : ${ROOT}/${PARENT_DIR_NAME}"
echo "  subtree: ${ROOT}/${SUBTREE_REPO}"
echo "  symlink: $(ls -la "${SYMLINK}" | awk '{print $NF}')"
echo ""
echo "Run tests:"
echo "  cd <molecule-core>/workspace-server"
echo "  go test -v -run TestLocalE2E_ ./internal/handlers/"
