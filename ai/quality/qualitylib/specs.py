"""Parse and validate the repository's Markdown specifications."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
import re
from typing import Any


SPEC_DIR_RE = re.compile(r"^(?P<number>\d{3})-(?P<slug>[a-z0-9]+(?:-[a-z0-9]+)*)$")
AC_RE = re.compile(r"^\s*-\s*\[([ xX])\]\s+(AC-\d{3})\s+(.*)$")
TASK_RE = re.compile(r"^\s*-\s*\[([ xX])\]\s+(T\d{3})\s+(.*)$")
VERIFICATION_ROW_RE = re.compile(
    r"^\|\s*(AC-\d{3})\s*\|\s*([^|]+?)\s*\|\s*(.*?)\s*\|\s*$"
)
REQUIRED_FILES = ("spec.md", "plan.md", "tasks.md", "verification.md")
REQUIRED_SECTIONS = ("目标", "非目标", "验收标准")
VALID_STATUSES = {
    "draft",
    "approved",
    "in-progress",
    "blocked",
    "done",
    "superseded",
}


@dataclass
class AcceptanceCriterion:
    """One traceable acceptance criterion."""

    identifier: str
    text: str
    checked: bool
    verification: str = ""


@dataclass
class TaskItem:
    """One independently deliverable task."""

    identifier: str
    text: str
    checked: bool


@dataclass
class SpecRecord:
    """Normalized data used by validation and dashboard rendering."""

    directory: Path
    identifier: str = ""
    title: str = ""
    status: str = ""
    owner: str = ""
    created: str = ""
    updated: str = ""
    acceptance: list[AcceptanceCriterion] = field(default_factory=list)
    tasks: list[TaskItem] = field(default_factory=list)
    verification: dict[str, str] = field(default_factory=dict)

    @property
    def name(self) -> str:
        """Return the stable directory name."""
        return self.directory.name

    @property
    def acceptance_done(self) -> int:
        """Return the number of completed acceptance criteria."""
        return sum(item.checked for item in self.acceptance)

    @property
    def tasks_done(self) -> int:
        """Return the number of completed tasks."""
        return sum(item.checked for item in self.tasks)

    def as_dict(self) -> dict[str, Any]:
        """Return serializable data for reports and dashboards."""
        return {
            "name": self.name,
            "id": self.identifier,
            "title": self.title,
            "status": self.status,
            "owner": self.owner,
            "created": self.created,
            "updated": self.updated,
            "acceptance": [
                {
                    "id": item.identifier,
                    "text": item.text,
                    "checked": item.checked,
                    "verification": item.verification,
                }
                for item in self.acceptance
            ],
            "tasks": [
                {
                    "id": item.identifier,
                    "text": item.text,
                    "checked": item.checked,
                }
                for item in self.tasks
            ],
            "verification": dict(self.verification),
        }


@dataclass
class SpecValidation:
    """Result of validating every specification directory."""

    records: list[SpecRecord]
    issues: list[str]

    @property
    def passed(self) -> bool:
        """Return whether validation has no issues."""
        return not self.issues

    def as_dict(self) -> dict[str, Any]:
        """Return a report-friendly representation."""
        return {
            "passed": self.passed,
            "records": [record.as_dict() for record in self.records],
            "issues": list(self.issues),
        }


def _read_text(path: Path, issues: list[str]) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        issues.append(f"{path}: 缺少文件")
    except UnicodeDecodeError as exc:
        issues.append(f"{path}: 不是有效的 UTF-8 ({exc})")
    except OSError as exc:
        issues.append(f"{path}: 无法读取 ({exc})")
    return ""


def _parse_front_matter(text: str) -> dict[str, str]:
    if not text.startswith("---"):
        return {}
    lines = text.splitlines()
    try:
        end = lines.index("---", 1)
    except ValueError:
        return {}
    metadata: dict[str, str] = {}
    for line in lines[1:end]:
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        metadata[key.strip()] = value.strip().strip("\"'")
    return metadata


def _parse_sections(text: str) -> dict[str, str]:
    sections: dict[str, list[str]] = {}
    current: str | None = None
    for line in text.splitlines():
        match = re.match(r"^##\s+(.+?)\s*$", line)
        if match:
            current = match.group(1).strip()
            sections.setdefault(current, [])
            continue
        if current:
            sections[current].append(line)
    return {name: "\n".join(lines).strip() for name, lines in sections.items()}


def _parse_acceptance(section: str) -> list[AcceptanceCriterion]:
    items: list[AcceptanceCriterion] = []
    lines = section.splitlines()
    for index, line in enumerate(lines):
        match = AC_RE.match(line)
        if not match:
            continue
        details = [match.group(3).strip()]
        cursor = index + 1
        while cursor < len(lines):
            candidate = lines[cursor]
            if AC_RE.match(candidate) or candidate.startswith("## "):
                break
            if candidate.strip():
                details.append(candidate.strip())
            cursor += 1
        detail_text = " ".join(details)
        verification = ""
        verification_match = re.search(r"验证[：:]\s*(.+)$", detail_text)
        if verification_match:
            verification = verification_match.group(1).strip()
        items.append(
            AcceptanceCriterion(
                identifier=match.group(2),
                text=detail_text.split(" 验证")[0].split(" 驗證")[0].strip(),
                checked=match.group(1).lower() == "x",
                verification=verification,
            )
        )
    return items


def _parse_tasks(text: str) -> list[TaskItem]:
    items: list[TaskItem] = []
    for line in text.splitlines():
        match = TASK_RE.match(line)
        if match:
            items.append(
                TaskItem(
                    identifier=match.group(2),
                    text=match.group(3).strip(),
                    checked=match.group(1).lower() == "x",
                )
            )
    return items


def _parse_verification(text: str) -> dict[str, str]:
    rows: dict[str, str] = {}
    for line in text.splitlines():
        match = VERIFICATION_ROW_RE.match(line)
        if match:
            rows[match.group(1)] = match.group(2).strip().upper()
    return rows


def _parse_date(value: str, field_name: str, path: Path, issues: list[str]) -> str:
    if not value:
        issues.append(f"{path}: front matter 缺少 {field_name}")
        return value
    try:
        date.fromisoformat(value)
    except ValueError:
        issues.append(f"{path}: {field_name} 必须是 YYYY-MM-DD")
    return value


def parse_spec(directory: Path) -> tuple[SpecRecord, list[str]]:
    """Parse one specification directory and return normalized data and issues."""
    issues: list[str] = []
    record = SpecRecord(directory=directory)
    directory_match = SPEC_DIR_RE.match(directory.name)
    if not directory_match:
        issues.append(f"{directory}: 目录名必须符合 NNN-kebab-case")

    texts = {
        name: _read_text(directory / name, issues)
        for name in REQUIRED_FILES
    }
    metadata = _parse_front_matter(texts["spec.md"])
    record.identifier = metadata.get("id", "")
    record.title = metadata.get("title", "")
    record.status = metadata.get("status", "")
    record.owner = metadata.get("owner", "")
    record.created = _parse_date(
        metadata.get("created", ""), "created", directory / "spec.md", issues
    )
    record.updated = _parse_date(
        metadata.get("updated", ""), "updated", directory / "spec.md", issues
    )

    if record.status not in VALID_STATUSES:
        issues.append(
            f"{directory / 'spec.md'}: status 必须是 {', '.join(sorted(VALID_STATUSES))}"
        )
    if not record.title:
        issues.append(f"{directory / 'spec.md'}: 缺少 title")
    if not record.owner:
        issues.append(f"{directory / 'spec.md'}: 缺少 owner")

    number = directory_match.group("number") if directory_match else ""
    if record.identifier and number and record.identifier != f"SPEC-{number}":
        issues.append(
            f"{directory / 'spec.md'}: id {record.identifier} 与目录编号 SPEC-{number} 不一致"
        )

    sections = _parse_sections(texts["spec.md"])
    for section_name in REQUIRED_SECTIONS:
        if section_name not in sections:
            issues.append(f"{directory / 'spec.md'}: 缺少章节 ## {section_name}")
    record.acceptance = _parse_acceptance(sections.get("验收标准", ""))
    if not record.acceptance:
        issues.append(f"{directory / 'spec.md'}: 验收标准中至少需要一个 AC 项")

    seen_acceptance: set[str] = set()
    for item in record.acceptance:
        if item.identifier in seen_acceptance:
            issues.append(
                f"{directory / 'spec.md'}: 验收项 {item.identifier} 重复"
            )
        seen_acceptance.add(item.identifier)
        if not item.verification:
            issues.append(
                f"{directory / 'spec.md'}: {item.identifier} 缺少“验证：”说明"
            )

    record.tasks = _parse_tasks(texts["tasks.md"])
    if not record.tasks:
        issues.append(f"{directory / 'tasks.md'}: 至少需要一个 T 任务")
    seen_tasks: set[str] = set()
    for item in record.tasks:
        if item.identifier in seen_tasks:
            issues.append(
                f"{directory / 'tasks.md'}: 任务 {item.identifier} 重复"
            )
        seen_tasks.add(item.identifier)
    if record.tasks and "完成定义" not in _parse_sections(texts["tasks.md"]):
        issues.append(f"{directory / 'tasks.md'}: 缺少章节 ## 完成定义")

    record.verification = _parse_verification(texts["verification.md"])
    acceptance_ids = {item.identifier for item in record.acceptance}
    verification_ids = set(record.verification)
    for missing in sorted(acceptance_ids - verification_ids):
        issues.append(
            f"{directory / 'verification.md'}: 缺少 {missing} 的证据行"
        )
    for extra in sorted(verification_ids - acceptance_ids):
        issues.append(
            f"{directory / 'verification.md'}: {extra} 不在验收标准中"
        )
    valid_evidence_statuses = {"PASS", "FAIL", "PENDING", "BLOCKED"}
    for identifier, evidence_status in record.verification.items():
        if evidence_status not in valid_evidence_statuses:
            issues.append(
                f"{directory / 'verification.md'}: {identifier} 状态无效 ({evidence_status})"
            )

    if record.status == "done":
        if any(not item.checked for item in record.acceptance):
            issues.append(f"{directory}: done 规格仍有未完成验收项")
        if any(not item.checked for item in record.tasks):
            issues.append(f"{directory}: done 规格仍有未完成任务")
        for identifier in sorted(acceptance_ids):
            if record.verification.get(identifier) != "PASS":
                issues.append(
                    f"{directory / 'verification.md'}: done 规格的 {identifier} 必须为 PASS"
                )
    return record, issues


def load_specs(root: Path) -> SpecValidation:
    """Load and validate all numbered specifications in the AI workspace."""
    specs_root = root / "ai" / "specs"
    issues: list[str] = []
    records: list[SpecRecord] = []
    if not specs_root.is_dir():
        return SpecValidation([], [f"{specs_root}: 规格目录不存在"])

    directories = sorted(
        (
            path
            for path in specs_root.iterdir()
            if path.is_dir() and path.name[:1].isdigit()
        ),
        key=lambda path: path.name,
    )
    if not directories:
        return SpecValidation([], [f"{specs_root}: 至少需要一个规格目录"])

    expected = 1
    for directory in directories:
        match = SPEC_DIR_RE.match(directory.name)
        if match:
            actual = int(match.group("number"))
            if actual != expected:
                issues.append(
                    f"{directory}: 规格编号应为 {expected:03d}，实际为 {actual:03d}"
                )
            expected = actual + 1
        record, record_issues = parse_spec(directory)
        records.append(record)
        issues.extend(record_issues)
    return SpecValidation(records, issues)
