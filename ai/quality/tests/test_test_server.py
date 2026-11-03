"""SPEC-007 AC-003: local HTTP boundary for cockpit core tests."""

from functools import partial
from http.server import ThreadingHTTPServer
import json
import tempfile
import threading
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from ai.quality.qualitylib.test_runner import TestRunBusy
from ai.quality.qualitylib.test_server import CockpitRequestHandler


class FakeRunner:
    def __init__(self):
        self.calls = 0

    def run(self):
        self.calls += 1
        return {
            "status": "passed",
            "duration_seconds": 1.25,
            "suites": [
                {"name": "backend-core", "status": "passed", "tests": 91},
                {"name": "frontend-unit", "status": "passed", "tests": 56},
            ],
        }


class CockpitTestServerTests(unittest.TestCase):
    def start_server(self, runner):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        handler = partial(
            CockpitRequestHandler,
            directory=temporary.name,
            test_runner=runner,
        )
        server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        return f"http://127.0.0.1:{server.server_port}"

    def test_authorized_post_runs_core_tests_and_returns_json(self) -> None:
        runner = FakeRunner()
        base_url = self.start_server(runner)
        request = Request(
            f"{base_url}/api/core-tests/run",
            method="POST",
            headers={"X-Cockpit-Test-Run": "1"},
        )

        with urlopen(request, timeout=2) as response:
            payload = json.loads(response.read())

        self.assertEqual(response.status, 200)
        self.assertEqual(payload["status"], "passed")
        self.assertEqual(payload["suites"][0]["tests"], 91)
        self.assertEqual(runner.calls, 1)

    def test_post_without_dedicated_header_is_forbidden(self) -> None:
        runner = FakeRunner()
        base_url = self.start_server(runner)
        request = Request(
            f"{base_url}/api/core-tests/run",
            method="POST",
        )

        with self.assertRaises(HTTPError) as raised:
            urlopen(request, timeout=2)

        self.assertEqual(raised.exception.code, 403)
        raised.exception.close()
        self.assertEqual(runner.calls, 0)

    def test_concurrent_http_request_gets_conflict_response(self) -> None:
        class BusyRunner:
            def run(self):
                raise TestRunBusy("already running")

        base_url = self.start_server(BusyRunner())
        request = Request(
            f"{base_url}/api/core-tests/run",
            method="POST",
            headers={"X-Cockpit-Test-Run": "1"},
        )

        with self.assertRaises(HTTPError) as raised:
            urlopen(request, timeout=2)

        self.assertEqual(raised.exception.code, 409)
        raised.exception.close()


if __name__ == "__main__":
    unittest.main()
