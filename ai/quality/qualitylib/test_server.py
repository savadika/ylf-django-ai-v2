"""HTTP boundary for cockpit actions that must stay local and explicit."""

from __future__ import annotations

from http.server import SimpleHTTPRequestHandler
import ipaddress
import json
from pathlib import Path
from urllib.parse import urlsplit

from .test_runner import CoreTestRunner, TestRunBusy


CORE_TEST_PATH = "/api/core-tests/run"
CORE_TEST_HEADER = "X-Cockpit-Test-Run"


class CockpitRequestHandler(SimpleHTTPRequestHandler):
    """Serve static cockpit assets and the guarded local test action."""

    def __init__(
        self,
        *args,
        directory: str | None = None,
        test_runner: CoreTestRunner | None = None,
        **kwargs,
    ) -> None:
        self.test_runner = test_runner or CoreTestRunner(Path.cwd())
        super().__init__(*args, directory=directory, **kwargs)

    def _send_json(self, status: int, payload: dict) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _request_is_local(self) -> bool:
        try:
            return ipaddress.ip_address(self.client_address[0]).is_loopback
        except ValueError:
            return False

    def do_POST(self) -> None:
        if urlsplit(self.path).path != CORE_TEST_PATH:
            self.send_error(404)
            return
        if not self._request_is_local() or self.headers.get(CORE_TEST_HEADER) != "1":
            self._send_json(
                403,
                {
                    "status": "forbidden",
                    "message": "核心测试只能从本机驾驶舱启动",
                },
            )
            return

        try:
            result = self.test_runner.run()
        except TestRunBusy:
            self._send_json(
                409,
                {
                    "status": "busy",
                    "message": "已有核心测试正在运行",
                },
            )
            return
        except Exception as exc:
            self.log_error("核心测试运行失败: %s", exc)
            self._send_json(
                500,
                {
                    "status": "failed",
                    "message": "核心测试启动失败",
                },
            )
            return

        self._send_json(200, result)
