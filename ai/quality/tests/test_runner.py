"""Tests for command execution and report persistence."""

import json
from pathlib import Path
import sys
import tempfile
import unittest

from ai.quality.qualitylib.runner import Command, Gate, run_gates, write_report


class QualityRunnerTests(unittest.TestCase):
    """SPEC-001 AC-003 gate orchestration and report cases."""

    def test_commands_pass_and_report_contains_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            gate = Gate(
                name="example",
                description="example gate",
                commands=[
                    Command(
                        label="print",
                        argv=[sys.executable, "-c", "print('evidence')"],
                        cwd=root,
                    )
                ],
            )

            report = run_gates(
                [gate],
                mode="quick",
                runtimes={"backend": "local", "frontend": "local"},
                echo=lambda _: None,
            )

            self.assertEqual(report.status, "passed")
            self.assertIn("evidence", report.gates[0].detail)

    def test_failure_is_retained_and_written(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            gate = Gate(
                name="failure",
                description="failing gate",
                commands=[
                    Command(
                        label="fail",
                        argv=[
                            sys.executable,
                            "-c",
                            "import sys; print('bad'); sys.exit(7)",
                        ],
                        cwd=root,
                    )
                ],
            )

            report = run_gates(
                [gate],
                mode="full",
                runtimes={"backend": "local", "frontend": "local"},
                echo=lambda _: None,
            )
            output = root / "ai" / "reports" / "report.json"
            write_report(report, output)
            data = json.loads(output.read_text(encoding="utf-8"))

            self.assertEqual(report.status, "failed")
            self.assertIn("返回 7", report.gates[0].detail)
            self.assertEqual(data["gates"][0]["status"], "failed")
            self.assertEqual(data["schema_version"], 1)

    def test_skip_is_partial_not_passed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)

            report = run_gates(
                [Gate(name="skipped", description="skipped")],
                mode="quick",
                runtimes={"backend": "local", "frontend": "local"},
                skipped={"skipped"},
                echo=lambda _: None,
            )

            self.assertEqual(report.status, "partial")
            self.assertEqual(report.gates[0].status, "skipped")

    def test_checker_exception_becomes_failed_gate(self) -> None:
        def broken_checker() -> tuple[bool, str]:
            raise RuntimeError("checker exploded")

        with tempfile.TemporaryDirectory() as temporary:
            report = run_gates(
                [Gate(name="broken", description="broken", checker=broken_checker)],
                mode="quick",
                runtimes={"backend": "local", "frontend": "local"},
                echo=lambda _: None,
            )

            self.assertEqual(report.status, "failed")
            self.assertIn("checker exploded", report.gates[0].detail)


if __name__ == "__main__":
    unittest.main()
