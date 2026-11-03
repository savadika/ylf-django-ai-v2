"""SPEC-007 AC-002: cockpit core test runner behavior."""

from pathlib import Path
import subprocess
import threading
import unittest

from ai.quality.qualitylib.test_runner import CoreTestRunner, TestRunBusy


class CoreTestRunnerTests(unittest.TestCase):
    def test_runs_backend_and_frontend_suites_and_parses_counts(self) -> None:
        calls = []

        def fake_run(argv, *, cwd, env, timeout):
            calls.append((argv, cwd, env, timeout))
            if any(argument.endswith("manage.py") for argument in argv):
                output = "Ran 91 tests in 1.2s\nOK"
            else:
                output = "Tests:       56 passed, 56 total"
            return subprocess.CompletedProcess(argv, 0, output, "")

        runner = CoreTestRunner(Path("C:/repo"), command_runner=fake_run)
        result = runner.run()

        self.assertEqual(result["status"], "passed")
        self.assertEqual(
            [(suite["name"], suite["tests"]) for suite in result["suites"]],
            [("backend-core", 91), ("frontend-unit", 56)],
        )
        self.assertEqual(
            sum(len(group["endpoints"]) for group in result["api_scope"]),
            40,
        )
        self.assertEqual(len(calls), 2)

    def test_timeout_is_reported_without_hiding_the_other_suite(self) -> None:
        def fake_run(argv, *, cwd, env, timeout):
            if any(argument.endswith("manage.py") for argument in argv):
                raise subprocess.TimeoutExpired(argv, timeout)
            return subprocess.CompletedProcess(
                argv,
                0,
                "Tests:       56 passed, 56 total",
                "",
            )

        result = CoreTestRunner(Path("C:/repo"), command_runner=fake_run).run()

        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["suites"][0]["status"], "failed")
        self.assertIn("timed out", result["suites"][0]["output"])
        self.assertEqual(result["suites"][1]["tests"], 56)

    def test_concurrent_run_is_rejected_while_suite_is_active(self) -> None:
        started = threading.Event()
        release = threading.Event()

        def fake_run(argv, *, cwd, env, timeout):
            started.set()
            release.wait(timeout=2)
            output = (
                "Ran 91 tests in 1s\nOK"
                if any(argument.endswith("manage.py") for argument in argv)
                else "Tests:       56 passed, 56 total"
            )
            return subprocess.CompletedProcess(argv, 0, output, "")

        runner = CoreTestRunner(Path("C:/repo"), command_runner=fake_run)
        first_result = {}
        worker = threading.Thread(
            target=lambda: first_result.update(runner.run()),
        )
        worker.start()
        self.assertTrue(started.wait(timeout=1))

        with self.assertRaises(TestRunBusy):
            runner.run()

        release.set()
        worker.join(timeout=2)
        self.assertEqual(first_result["status"], "passed")

    def test_failure_output_is_capped_to_keep_http_responses_bounded(self) -> None:
        def fake_run(argv, *, cwd, env, timeout):
            if any(argument.endswith("manage.py") for argument in argv):
                return subprocess.CompletedProcess(
                    argv,
                    1,
                    "FAILED\n" + ("diagnostic-" * 5000),
                    "",
                )
            return subprocess.CompletedProcess(
                argv,
                0,
                "Tests:       56 passed, 56 total",
                "",
            )

        result = CoreTestRunner(Path("C:/repo"), command_runner=fake_run).run()

        self.assertEqual(result["status"], "failed")
        self.assertLessEqual(len(result["suites"][0]["output"]), 20_000)
        self.assertIn("output truncated", result["suites"][0]["output"])


if __name__ == "__main__":
    unittest.main()
