"""Run the repository's core regression suites from the local cockpit."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import threading
import time
from typing import Any

from .api_scope import api_scope_payload


CommandRunner = Callable[..., subprocess.CompletedProcess[str]]
MAX_SUITE_OUTPUT = 20_000


class TestRunBusy(RuntimeError):
    """Raised when another core test run is already active."""


def _bounded_output(output: str) -> str:
    if len(output) <= MAX_SUITE_OUTPUT:
        return output
    marker = "\n... output truncated ...\n"
    retained = MAX_SUITE_OUTPUT - len(marker)
    head = retained // 2
    tail = retained - head
    return output[:head] + marker + output[-tail:]


class CoreTestRunner:
    """Execute the backend and frontend core suites with one operation."""

    def __init__(
        self,
        root: Path,
        *,
        command_runner: CommandRunner | None = None,
        timeout_seconds: int = 180,
    ) -> None:
        self.root = root
        self.timeout_seconds = timeout_seconds
        self._command_runner = command_runner or self._run_process
        self._run_lock = threading.Lock()

    @staticmethod
    def _run_process(
        argv: list[str],
        *,
        cwd: Path,
        env: dict[str, str],
        timeout: int,
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            argv,
            cwd=cwd,
            env=env,
            timeout=timeout,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )

    def _backend_python(self) -> str:
        windows = self.root / "business" / ".venv" / "Scripts" / "python.exe"
        posix = self.root / "business" / ".venv" / "bin" / "python"
        if windows.is_file():
            return str(windows)
        if posix.is_file():
            return str(posix)
        return sys.executable

    def run(self) -> dict[str, Any]:
        if not self._run_lock.acquire(blocking=False):
            raise TestRunBusy("core regression tests are already running")
        try:
            return self._run_suites()
        finally:
            self._run_lock.release()

    def _run_suites(self) -> dict[str, Any]:
        started = time.monotonic()
        frontend = self.root / "business" / "frontend"
        suites = [
            {
                "name": "backend-core",
                "argv": [
                    self._backend_python(),
                    str(self.root / "business" / "UniDjango" / "manage.py"),
                    "test",
                    "user",
                    "role",
                    "menu",
                    "department",
                    "log",
                    "--settings=UniDjango.test_settings",
                ],
                "cwd": self.root,
                "env": os.environ.copy(),
                "pattern": r"Ran\s+(\d+)\s+tests?",
            },
            {
                "name": "frontend-unit",
                "argv": [
                    shutil.which("node") or "node",
                    str(
                        frontend
                        / "node_modules"
                        / "@vue"
                        / "cli-service"
                        / "bin"
                        / "vue-cli-service.js"
                    ),
                    "test:unit",
                    "--runInBand",
                ],
                "cwd": frontend,
                "env": {
                    **os.environ.copy(),
                    "NODE_OPTIONS": "--openssl-legacy-provider",
                },
                "pattern": r"Tests:\s+(\d+)\s+passed",
            },
        ]

        results = []
        for suite in suites:
            suite_started = time.monotonic()
            try:
                process = self._command_runner(
                    suite["argv"],
                    cwd=suite["cwd"],
                    env=suite["env"],
                    timeout=self.timeout_seconds,
                )
                return_code = process.returncode
                output = "\n".join(
                    part for part in (process.stdout, process.stderr) if part
                )
            except subprocess.TimeoutExpired as exc:
                return_code = -1
                output = (
                    f"{suite['name']} timed out after "
                    f"{self.timeout_seconds} seconds"
                )
                if exc.output:
                    output += f"\n{exc.output}"
            except OSError as exc:
                return_code = -1
                output = f"{suite['name']} could not start: {exc}"
            output = _bounded_output(output)
            count_match = re.search(suite["pattern"], output)
            results.append(
                {
                    "name": suite["name"],
                    "status": "passed" if return_code == 0 else "failed",
                    "tests": int(count_match.group(1)) if count_match else 0,
                    "duration_seconds": round(time.monotonic() - suite_started, 3),
                    "output": output,
                }
            )

        failed = any(suite["status"] == "failed" for suite in results)
        return {
            "status": "failed" if failed else "passed",
            "started_at": datetime.now().astimezone().isoformat(timespec="seconds"),
            "duration_seconds": round(time.monotonic() - started, 3),
            "api_scope": api_scope_payload(),
            "suites": results,
        }
