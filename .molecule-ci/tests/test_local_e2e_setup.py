from __future__ import annotations

import os
import stat
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SETUP = ROOT / ".molecule-ci" / "scripts" / "local-e2e-setup.sh"


FAKE_GIT = r'''#!/bin/sh
set -eu
for arg in "$@"; do
  printf '<%s>\n' "$arg" >> "$GIT_ARGV_LOG"
done

seen_clone=0
url=
directory=
for arg in "$@"; do
  if [ "$seen_clone" = 1 ]; then
    case "$arg" in
      -*) continue ;;
    esac
    if [ -z "$url" ]; then
      url=$arg
    elif [ -z "$directory" ]; then
      directory=$arg
      break
    fi
  elif [ "$arg" = clone ]; then
    seen_clone=1
  fi
done

if [ -n "$directory" ]; then
  mkdir -p "$directory/.git"
  printf '[remote "origin"]\n\turl = %s\n' "$url" > "$directory/.git/config"
fi
'''


class LocalE2ESetupTests(unittest.TestCase):
    def test_git_credentials_never_reach_argv_logs_or_remote(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            home = root / "home"
            token_dir = home / ".molecule-ai"
            token_dir.mkdir(parents=True)
            sentinel = "dummy-token-must-never-appear"
            (token_dir / "gitea-token").write_text(sentinel + "\n")

            fake_bin = root / "bin"
            fake_bin.mkdir()
            fake_git = fake_bin / "git"
            fake_git.write_text(FAKE_GIT)
            fake_git.chmod(fake_git.stat().st_mode | stat.S_IXUSR)

            argv_log = root / "git-argv.log"
            deploy_root = root / "deploy"
            env = os.environ.copy()
            env.update(
                HOME=str(home),
                PATH=f"{fake_bin}:{env['PATH']}",
                GIT_ARGV_LOG=str(argv_log),
                GITEA_TOKEN_FILE=str(token_dir / "gitea-token"),
                LOCAL_E2E_ROOT=str(deploy_root),
            )
            env.pop("GITEA_TOKEN", None)

            first = subprocess.run(
                ["bash", "-x", str(SETUP)],
                text=True,
                capture_output=True,
                env=env,
                check=False,
            )
            exported_env = env.copy()
            exported_env["GITEA_TOKEN"] = sentinel
            exported_env.pop("GITEA_TOKEN_FILE", None)
            second = subprocess.run(
                ["bash", "-x", str(SETUP)],
                text=True,
                capture_output=True,
                env=exported_env,
                check=False,
            )

            self.assertEqual(first.returncode, 0, first.stdout + first.stderr)
            self.assertEqual(second.returncode, 0, second.stdout + second.stderr)
            observed = (
                argv_log.read_text()
                + (deploy_root / "molecule-dev" / ".git" / "config").read_text()
                + first.stdout
                + first.stderr
                + second.stdout
                + second.stderr
            )
            self.assertNotIn(sentinel, observed)
            self.assertIn(
                "https://git.moleculesai.app/molecule-ai/molecule-ai-org-template-molecule-dev.git",
                observed,
            )
            remote = (deploy_root / "molecule-dev" / ".git" / "config").read_text()
            self.assertNotIn("@git.moleculesai.app", remote)

    def test_refuses_implicit_shared_token_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            token_dir = root / "home" / ".molecule-ai"
            token_dir.mkdir(parents=True)
            (token_dir / "gitea-token").write_text("must-not-be-read\n")
            env = os.environ.copy()
            env.update(HOME=str(root / "home"), LOCAL_E2E_ROOT=str(root / "deploy"))
            env.pop("GITEA_TOKEN", None)
            env.pop("GITEA_TOKEN_FILE", None)

            result = subprocess.run(
                ["bash", str(SETUP)],
                text=True,
                capture_output=True,
                env=env,
                check=False,
            )

            self.assertEqual(result.returncode, 2)
            self.assertIn("export GITEA_TOKEN or set GITEA_TOKEN_FILE", result.stderr)


if __name__ == "__main__":
    unittest.main()
