"""Validate required documentation, UTF-8 text, and local Markdown links."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Any
from urllib.parse import unquote


MARKDOWN_LINK_RE = re.compile(r"!?\[[^\]\n]*\]\(([^)\n]+)\)")
FENCED_CODE_RE = re.compile(r"```.*?```", re.DOTALL)
INLINE_CODE_RE = re.compile(r"`[^`\n]*`")
IGNORED_DIRECTORIES = {
    ".git",
    ".quality",
    ".venv",
    "__pycache__",
    "build",
    "dist",
    "node_modules",
}


@dataclass
class DocValidation:
    """Result of validating documentation and links."""

    issues: list[str]
    markdown_files: list[Path]
    links_checked: int

    @property
    def passed(self) -> bool:
        """Return whether no documentation issue was found."""
        return not self.issues

    def as_dict(self) -> dict[str, Any]:
        """Return report-friendly data."""
        return {
            "passed": self.passed,
            "markdown_files": len(self.markdown_files),
            "links_checked": self.links_checked,
            "issues": list(self.issues),
        }


def _markdown_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for path in root.rglob("*.md"):
        relative_parts = path.relative_to(root).parts
        if any(part in IGNORED_DIRECTORIES for part in relative_parts):
            continue
        files.append(path)
    return sorted(files)


def _link_target(raw_target: str) -> str:
    target = raw_target.strip()
    if target.startswith("<") and ">" in target:
        return target[1 : target.index(">")]
    return target.split(maxsplit=1)[0]


def _is_external(target: str) -> bool:
    lowered = target.lower()
    return (
        not target
        or target.startswith("#")
        or target.startswith("//")
        or bool(re.match(r"^[a-z][a-z0-9+.-]*:", lowered))
    )


def validate_docs(root: Path, policy: dict[str, Any]) -> DocValidation:
    """Validate configured files and every repository-local Markdown link."""
    issues: list[str] = []
    for relative in policy.get("required_docs", []):
        path = root / relative
        if not path.is_file():
            issues.append(f"{relative}: 必需文档不存在")
    for relative in policy.get("required_scripts", []):
        path = root / relative
        if not path.is_file():
            issues.append(f"{relative}: 必需脚本不存在")

    files = _markdown_files(root)
    links_checked = 0
    for path in files:
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError as exc:
            issues.append(f"{path}: 不是有效的 UTF-8 ({exc})")
            continue
        except OSError as exc:
            issues.append(f"{path}: 无法读取 ({exc})")
            continue

        searchable = INLINE_CODE_RE.sub("", FENCED_CODE_RE.sub("", text))
        for line_number, line in enumerate(searchable.splitlines(), start=1):
            for match in MARKDOWN_LINK_RE.finditer(line):
                target = _link_target(match.group(1))
                if _is_external(target):
                    continue
                links_checked += 1
                without_fragment = unquote(target.split("#", 1)[0].split("?", 1)[0])
                resolved = (path.parent / without_fragment).resolve()
                try:
                    resolved.relative_to(root.resolve())
                except ValueError:
                    issues.append(
                        f"{path}:{line_number}: 链接越过仓库根目录 ({target})"
                    )
                    continue
                if not resolved.exists():
                    issues.append(
                        f"{path}:{line_number}: 本地链接目标不存在 ({target})"
                    )
    return DocValidation(issues, files, links_checked)
