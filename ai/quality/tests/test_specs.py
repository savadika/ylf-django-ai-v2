"""Tests for specification parsing and traceability."""

from pathlib import Path
import tempfile
import unittest

from ai.quality.qualitylib.specs import load_specs, parse_spec


SPEC_TEXT = """---
id: SPEC-001
title: Example
status: {status}
owner: tester
created: 2026-11-02
updated: 2026-11-02
---

# Example

## 目标

- Deliver a result.

## 非目标

- Nothing else.

## 验收标准

- [{mark}] AC-001 The observable result exists.
  验证：`python -m unittest`
"""

TASKS_TEXT = """# 任务

- [x] T001 Implement the result.

## 完成定义

- [x] Evidence exists.
"""

VERIFICATION_TEXT = """# 验证记录

| 验收项 | 状态 | 证据 |
| --- | --- | --- |
| AC-001 | {evidence} | `python -m unittest` |
"""


def create_spec(
    root: Path,
    *,
    status: str = "in-progress",
    checked: bool = False,
    evidence: str = "PENDING",
    verification_text: str | None = None,
) -> Path:
    """Create a compact specification fixture."""
    directory = root / "ai" / "specs" / "001-example"
    directory.mkdir(parents=True)
    (directory / "spec.md").write_text(
        SPEC_TEXT.format(status=status, mark="x" if checked else " "),
        encoding="utf-8",
    )
    (directory / "plan.md").write_text("# 实现计划\n", encoding="utf-8")
    (directory / "tasks.md").write_text(TASKS_TEXT, encoding="utf-8")
    (directory / "verification.md").write_text(
        verification_text or VERIFICATION_TEXT.format(evidence=evidence),
        encoding="utf-8",
    )
    return directory


class SpecificationValidationTests(unittest.TestCase):
    """SPEC-001 AC-002 specification traceability cases."""

    def test_in_progress_spec_is_traceable_while_incomplete(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            create_spec(root)

            result = load_specs(root)

            self.assertTrue(result.passed, result.issues)
            self.assertEqual(result.records[0].acceptance_done, 0)
            self.assertEqual(result.records[0].tasks_done, 1)

    def test_done_spec_requires_checked_items_and_pass_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            create_spec(root, status="done", checked=False, evidence="PENDING")

            result = load_specs(root)

            self.assertFalse(result.passed)
            self.assertTrue(any("未完成验收项" in issue for issue in result.issues))
            self.assertTrue(any("必须为 PASS" in issue for issue in result.issues))

    def test_missing_evidence_and_duplicate_ac_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            directory = create_spec(
                root,
                verification_text=(
                    "# 验证记录\n\n"
                    "| 验收项 | 状态 | 证据 |\n"
                    "| --- | --- | --- |\n"
                    "| AC-002 | PASS | unrelated |\n"
                ),
            )
            spec_path = directory / "spec.md"
            spec_path.write_text(
                spec_path.read_text(encoding="utf-8")
                + "\n- [ ] AC-001 Duplicate.\n  验证：duplicate\n",
                encoding="utf-8",
            )

            record, issues = parse_spec(directory)

            self.assertEqual(len(record.acceptance), 2)
            self.assertTrue(any("AC-001 重复" in issue for issue in issues))
            self.assertTrue(any("缺少 AC-001 的证据行" in issue for issue in issues))

    def test_spec_numbers_must_be_contiguous(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            create_spec(root)
            second = root / "ai" / "specs" / "003-second"
            second.mkdir()
            for name in ("spec.md", "plan.md", "tasks.md", "verification.md"):
                (second / name).write_text("", encoding="utf-8")

            result = load_specs(root)

            self.assertTrue(any("规格编号应为 002" in issue for issue in result.issues))


if __name__ == "__main__":
    unittest.main()
