"""Execute quality gates and persist machine-readable evidence."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
import json
import os
from pathlib import Path
import subprocess
import time
from typing import Callable


Checker = Callable[[], tuple[bool, str]]
MAX_DETAIL_CHARS = 20_000


@dataclass
class Command:
    """One non-shell command executed as part of a gate."""

    label: str
    argv: list[str]
    cwd: Path
    env: dict[str, str] = field(default_factory=dict)


@dataclass
class Gate:
    """A named quality gate made from a checker or one or more commands."""

    name: str
    description: str
    commands: list[Command] = field(default_factory=list)
    checker: Checker | None = None


@dataclass
class GateResult:
    """Serializable outcome of one quality gate."""

    name: str
    status: str
    duration_seconds: float
    detail: str = ""
    commands: list[list[str]] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        """Return whether the gate passed."""
        return self.status == "passed"

    def as_dict(self) -> dict[str, object]:
        """Return report-friendly data."""
        return {
            "name": self.name,
            "status": self.status,
            "duration_seconds": round(self.duration_seconds, 3),
            "detail": self.detail,
            "commands": self.commands,
        }


@dataclass
class QualityReport:
    """Complete result of one validation profile."""

    mode: str
    status: str
    started_at: str
    finished_at: str
    duration_seconds: float
    runtimes: dict[str, str]
    gates: list[GateResult]

    def as_dict(self) -> dict[str, object]:
        """Return the stable `ai/reports/report.json` schema."""
        return {
            "schema_version": 1,
            "mode": self.mode,
            "status": self.status,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "duration_seconds": round(self.duration_seconds, 3),
            "runtimes": dict(self.runtimes),
            "gates": [gate.as_dict() for gate in self.gates],
        }


def _clip(value: str) -> str:
    if len(value) <= MAX_DETAIL_CHARS:
        return value
    return "... output truncated ...\n" + value[-MAX_DETAIL_CHARS:]


def _append_detail(current: str, label: str, output: str) -> str:
    section = f"[{label}]\n{output.strip()}" if output.strip() else f"[{label}]"
    return f"{current}\n\n{section}".strip()


def _command_display(argv: list[str]) -> str:
    return subprocess.list2cmdline(argv)


def _execute_gate(gate: Gate, echo: Callable[[str], None]) -> GateResult:
    started = time.monotonic()
    commands: list[list[str]] = []
    details = ""
    status = "passed"

    if gate.checker is not None:
        try:
            passed, detail = gate.checker()
            details = detail
            status = "passed" if passed else "failed"
        except Exception as exc:  # The report must survive a faulty checker.
            details = f"{type(exc).__name__}: {exc}"
            status = "failed"
    elif gate.commands:
        for command in gate.commands:
            commands.append(command.argv)
            display = _command_display(command.argv)
            echo(f"  $ {display}")
            environment = os.environ.copy()
            environment.update(
                {
                    "PYTHONUNBUFFERED": "1",
                    "PYTHONUTF8": "1",
                    "PYTHONIOENCODING": "utf-8",
                }
            )
            environment.update(command.env)
            try:
                completed = subprocess.run(
                    command.argv,
                    cwd=command.cwd,
                    env=environment,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=1_800,
                    check=False,
                )
                output = "\n".join(
                    part for part in (completed.stdout, completed.stderr) if part
                )
                if output.strip():
                    echo(output.rstrip())
                details = _append_detail(details, command.label, output)
                if completed.returncode != 0:
                    status = "failed"
                    details = _append_detail(
                        details,
                        "退出码",
                        f"{command.label} 返回 {completed.returncode}",
                    )
                    break
            except FileNotFoundError:
                status = "failed"
                details = _append_detail(
                    details,
                    "依赖缺失",
                    f"找不到命令 {command.argv[0]}；请按 ai/docs/QUALITY_GATES.md 安装依赖",
                )
                break
            except subprocess.TimeoutExpired:
                status = "failed"
                details = _append_detail(details, "超时", f"{command.label} 超过 30 分钟")
                break
            except OSError as exc:
                status = "failed"
                details = _append_detail(details, "命令失败", str(exc))
                break
    else:
        status = "failed"
        details = "门禁没有定义检查器或命令"

    if status == "passed" and not details:
        details = "检查通过"
    return GateResult(
        name=gate.name,
        status=status,
        duration_seconds=time.monotonic() - started,
        detail=_clip(details),
        commands=commands,
    )


def run_gates(
    gates: list[Gate],
    mode: str,
    runtimes: dict[str, str],
    skipped: set[str] | None = None,
    echo: Callable[[str], None] = print,
) -> QualityReport:
    """Run gates in order while retaining all evidence, including failures."""
    skipped = skipped or set()
    started_clock = time.monotonic()
    started_at = datetime.now(UTC).isoformat()
    results: list[GateResult] = []

    for index, gate in enumerate(gates, start=1):
        echo(f"[{index}/{len(gates)}] {gate.name} - {gate.description}")
        if gate.name in skipped:
            results.append(
                GateResult(
                    name=gate.name,
                    status="skipped",
                    duration_seconds=0.0,
                    detail="由 --skip 显式跳过",
                )
            )
            echo("  SKIPPED")
            continue
        result = _execute_gate(gate, echo)
        results.append(result)
        echo(f"  {result.status.upper()} ({result.duration_seconds:.2f}s)")

    failed = any(result.status == "failed" for result in results)
    has_skips = any(result.status == "skipped" for result in results)
    status = "failed" if failed else ("partial" if has_skips else "passed")
    finished_at = datetime.now(UTC).isoformat()
    return QualityReport(
        mode=mode,
        status=status,
        started_at=started_at,
        finished_at=finished_at,
        duration_seconds=time.monotonic() - started_clock,
        runtimes=dict(runtimes),
        gates=results,
    )


def write_report(report: QualityReport, path: Path) -> None:
    """Atomically write a UTF-8 quality report."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(report.as_dict(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)
