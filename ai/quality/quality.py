#!/usr/bin/env python
"""Unified quality gate and engineering cockpit entry point."""

from __future__ import annotations

import argparse
import ast
from functools import partial
from http.server import ThreadingHTTPServer
import json
from pathlib import Path
import shutil
import sys
from typing import Any


AI_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = AI_ROOT.parent
QUALITY_ROOT = AI_ROOT / "quality"
BUSINESS_ROOT = REPO_ROOT / "business"
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from ai.quality.qualitylib import (  # noqa: E402
    Gate,
    build_cockpit,
    load_specs,
    run_gates,
    validate_docs,
)
from ai.quality.qualitylib.runner import Command, write_report  # noqa: E402
from ai.quality.qualitylib.test_runner import CoreTestRunner  # noqa: E402
from ai.quality.qualitylib.test_server import CockpitRequestHandler  # noqa: E402


PROFILES = {
    "quick": (
        "tool-tests",
        "specs",
        "docs",
        "python-syntax",
    ),
    "full": (
        "tool-tests",
        "specs",
        "docs",
        "python-syntax",
        "backend-lint",
        "backend-check",
        "migrations",
        "backend-tests",
        "frontend-lint",
        "frontend-tests",
    ),
    "release": (
        "tool-tests",
        "specs",
        "docs",
        "python-syntax",
        "backend-lint",
        "backend-check",
        "migrations",
        "backend-tests",
        "frontend-lint",
        "frontend-tests",
        "frontend-build",
        "deploy-check",
    ),
}


def _configure_console() -> None:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8", errors="replace")


def load_policy() -> dict[str, Any]:
    """Load and minimally validate the quality policy."""
    path = QUALITY_ROOT / "policy.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or data.get("schema_version") != 1:
        raise ValueError("ai/quality/policy.json: schema_version 必须为 1")
    coverage = data.get("coverage", {})
    for key in ("backend_min_percent", "frontend_min_percent"):
        if not isinstance(coverage.get(key), (int, float)):
            raise ValueError(f"ai/quality/policy.json: coverage.{key} 必须是数字")
    return data


def _format_issues(title: str, issues: list[str], success: str) -> tuple[bool, str]:
    if issues:
        return False, title + "\n" + "\n".join(f"- {issue}" for issue in issues)
    return True, success


def _spec_checker(root: Path):
    def check() -> tuple[bool, str]:
        validation = load_specs(root)
        done = sum(record.status == "done" for record in validation.records)
        return _format_issues(
            "规格检查未通过：",
            validation.issues,
            f"规格检查通过：{len(validation.records)} 个规格，{done} 个已完成。",
        )

    return check


def _docs_checker(root: Path, policy: dict[str, Any]):
    def check() -> tuple[bool, str]:
        validation = validate_docs(root, policy)
        return _format_issues(
            "文档检查未通过：",
            validation.issues,
            (
                f"文档检查通过：{len(validation.markdown_files)} 个 Markdown 文件，"
                f"{validation.links_checked} 个本地链接。"
            ),
        )

    return check


def _syntax_checker(root: Path):
    def check() -> tuple[bool, str]:
        issues: list[str] = []
        files = 0
        for path in sorted(
            {
                *root.glob("*.py"),
                *root.glob("ai/quality/**/*.py"),
                *root.glob("business/UniDjango/**/*.py"),
            }
        ):
            if "__pycache__" in path.parts:
                continue
            files += 1
            try:
                source = path.read_text(encoding="utf-8")
                ast.parse(source, filename=str(path))
            except UnicodeDecodeError as exc:
                issues.append(f"{path}: 不是有效的 UTF-8 ({exc})")
            except SyntaxError as exc:
                issues.append(
                    f"{path}:{exc.lineno}: Python 语法错误 ({exc.msg})"
                )
            except OSError as exc:
                issues.append(f"{path}: 无法读取 ({exc})")
        return _format_issues(
            "Python 语法检查未通过：",
            issues,
            f"Python 语法检查通过：{files} 个文件。",
        )

    return check


def _python_command(runtime: str, root: Path, parts: list[str]) -> list[str]:
    if runtime == "local":
        return [sys.executable, *parts]
    if runtime == "docker":
        return [
            "docker",
            "compose",
            "-f",
            str(BUSINESS_ROOT / "docker-compose-dev.yml"),
            "run",
            "--rm",
            "--no-deps",
            "-v",
            f"{root}:/workspace",
            "-w",
            "/workspace",
            "--entrypoint",
            "python",
            "backend",
            *parts,
        ]
    raise ValueError(f"不支持的后端运行时：{runtime}")


def _frontend_command(
    runtime: str,
    root: Path,
    local_tool: str,
    args: list[str],
    env: dict[str, str] | None = None,
) -> Command:
    frontend = BUSINESS_ROOT / "frontend"
    command_env = {
        "NODE_OPTIONS": "--openssl-legacy-provider",
        **(env or {}),
    }
    if runtime == "local":
        node = shutil.which("node") or "node"
        tool = frontend / "node_modules" / local_tool
        return Command(
            label=local_tool,
            argv=[node, str(tool), *args],
            cwd=frontend,
            env=command_env,
        )
    if runtime == "docker":
        package = {
            "eslint/bin/eslint.js": "eslint",
            "@vue/cli-service/bin/vue-cli-service.js": "vue-cli-service",
        }.get(local_tool, local_tool)
        return Command(
            label=local_tool,
            argv=[
                "docker",
                "compose",
                "-f",
                str(BUSINESS_ROOT / "docker-compose-dev.yml"),
                "exec",
                "-T",
                "frontend",
                "npx",
                package,
                *args,
            ],
            cwd=root,
            env=command_env,
        )
    raise ValueError(f"不支持的前端运行时：{runtime}")


def _backend_gate(
    name: str,
    description: str,
    root: Path,
    runtime: str,
    commands: list[tuple[str, list[str], dict[str, str] | None]],
) -> Gate:
    return Gate(
        name=name,
        description=description,
        commands=[
            Command(
                label=label,
                argv=_python_command(runtime, root, parts),
                cwd=root,
                env=env or {},
            )
            for label, parts, env in commands
        ],
    )


def gates_for_profile(
    mode: str,
    root: Path,
    policy: dict[str, Any],
    backend_runtime: str = "local",
    frontend_runtime: str = "local",
) -> list[Gate]:
    """Create the requested profile with runtime and policy substitutions."""
    backend_min = policy["coverage"]["backend_min_percent"]
    frontend_min = policy["coverage"]["frontend_min_percent"]
    deploy_environment = {
        "DEBUG": "False",
        "DJANGO_SECRET_KEY": (
            "quality-release-check-only-secret-key-0123456789abcdef0123456789"
        ),
        "JWT_SECRET_KEY": (
            "quality-release-check-only-jwt-key-0123456789abcdef0123456789"
        ),
        "DJANGO_ALLOWED_HOSTS": "example.com",
        "TRUSTED_PROXY_COUNT": "1",
        "DJANGO_SECURE_SSL_REDIRECT": "True",
        "DJANGO_SECURE_HSTS_SECONDS": "31536000",
        "DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS": "True",
        "DJANGO_SECURE_HSTS_PRELOAD": "True",
        "DJANGO_CSRF_COOKIE_SECURE": "True",
    }
    registry = {
        "tool-tests": Gate(
            name="tool-tests",
            description="验证器的单元测试",
            commands=[
                Command(
                    label="quality tooling tests",
                    argv=[
                        sys.executable,
                        "-m",
                        "unittest",
                        "discover",
                        "-s",
                        "ai/quality/tests",
                        "-t",
                        ".",
                        "-p",
                        "test_*.py",
                    ],
                    cwd=root,
                )
            ],
        ),
        "specs": Gate(
            name="specs",
            description="规格四件套、编号与证据追踪",
            checker=_spec_checker(root),
        ),
        "docs": Gate(
            name="docs",
            description="必需文档、UTF-8 与本地 Markdown 链接",
            checker=_docs_checker(root, policy),
        ),
        "python-syntax": Gate(
            name="python-syntax",
            description="Python 源码语法",
            checker=_syntax_checker(root),
        ),
        "backend-lint": _backend_gate(
            "backend-lint",
            "Ruff 关键正确性规则",
            root,
            backend_runtime,
            [
                (
                    "ruff",
                    [
                        "-m",
                        "ruff",
                        "check",
                        "--config",
                        "ai/quality/pyproject.toml",
                        "business/UniDjango",
                        "ai/quality",
                    ],
                    None,
                )
            ],
        ),
        "backend-check": _backend_gate(
            "backend-check",
            "Django 系统检查",
            root,
            backend_runtime,
            [
                (
                    "Django check",
                    [
                        "business/UniDjango/manage.py",
                        "check",
                        "--settings=UniDjango.test_settings",
                    ],
                    None,
                )
            ],
        ),
        "migrations": _backend_gate(
            "migrations",
            "模型迁移漂移检查",
            root,
            backend_runtime,
            [
                (
                    "Django migration check",
                    [
                        "business/UniDjango/manage.py",
                        "makemigrations",
                        "--check",
                        "--dry-run",
                        "--settings=UniDjango.test_settings",
                    ],
                    None,
                )
            ],
        ),
        "backend-tests": _backend_gate(
            "backend-tests",
            f"Django 全量测试与后端覆盖率（≥{backend_min}%）",
            root,
            backend_runtime,
            [
                (
                    "coverage erase",
                    ["-m", "coverage", "erase"],
                    {"COVERAGE_RCFILE": "ai/quality/pyproject.toml"},
                ),
                (
                    "Django tests",
                    [
                        "-m",
                        "coverage",
                        "run",
                        "business/UniDjango/manage.py",
                        "test",
                        "user",
                        "role",
                        "menu",
                        "department",
                        "log",
                        "cockpit",
                        "--settings=UniDjango.test_settings",
                    ],
                    {"COVERAGE_RCFILE": "ai/quality/pyproject.toml"},
                ),
                (
                    "coverage threshold",
                    ["-m", "coverage", "report", f"--fail-under={backend_min}"],
                    {"COVERAGE_RCFILE": "ai/quality/pyproject.toml"},
                ),
                (
                    "coverage JSON",
                    [
                        "-m",
                        "coverage",
                        "json",
                        "-o",
                        "ai/reports/backend-coverage.json",
                    ],
                    {"COVERAGE_RCFILE": "ai/quality/pyproject.toml"},
                ),
            ],
        ),
        "frontend-lint": Gate(
            name="frontend-lint",
            description="Vue/JavaScript lint",
            commands=[
                _frontend_command(
                    frontend_runtime,
                    root,
                    "eslint/bin/eslint.js",
                    ["--ext", ".js,.vue", "src"],
                )
            ],
        ),
        "frontend-tests": Gate(
            name="frontend-tests",
            description=f"Jest 全量测试与前端覆盖率（≥{frontend_min}%）",
            commands=[
                _frontend_command(
                    frontend_runtime,
                    root,
                    "@vue/cli-service/bin/vue-cli-service.js",
                    [
                        "test:unit",
                        "--coverage",
                        "--coverageReporters=json-summary",
                        "--coverageReporters=text-summary",
                        "--coverageThreshold="
                        + json.dumps(
                            {"global": {"lines": frontend_min}},
                            separators=(",", ":"),
                        ),
                    ],
                )
            ],
        ),
        "frontend-build": Gate(
            name="frontend-build",
            description="Vue 生产构建",
            commands=[
                _frontend_command(
                    frontend_runtime,
                    root,
                    "@vue/cli-service/bin/vue-cli-service.js",
                    ["build"],
                )
            ],
        ),
        "deploy-check": _backend_gate(
            "deploy-check",
            "Django 生产安全部署检查",
            root,
            backend_runtime,
            [
                (
                    "Django deploy check",
                    [
                        "business/UniDjango/manage.py",
                        "check",
                        "--deploy",
                        "--fail-level",
                        "WARNING",
                        "--settings=UniDjango.test_settings",
                    ],
                    deploy_environment,
                )
            ],
        ),
    }
    return [registry[name] for name in PROFILES[mode]]


def _parse_skips(values: list[str] | None) -> set[str]:
    result: set[str] = set()
    for value in values or []:
        result.update(item.strip() for item in value.split(",") if item.strip())
    return result


def create_parser() -> argparse.ArgumentParser:
    """Create the public command-line parser."""
    parser = argparse.ArgumentParser(
        description="运行 UniDjango 质量门禁或生成开发驾驶舱。"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    for mode in ("quick", "full", "release"):
        command = subparsers.add_parser(mode, help=f"运行 {mode} 质量门禁")
        command.add_argument(
            "--backend-runtime",
            choices=("local", "docker"),
            default="local",
            help="后端验证运行时（默认 local）",
        )
        command.add_argument(
            "--frontend-runtime",
            choices=("local", "docker"),
            default="local",
            help="前端验证运行时（默认 local）",
        )
        command.add_argument(
            "--skip",
            action="append",
            metavar="GATE",
            help="显式跳过门禁；可重复或使用逗号分隔",
        )
    subparsers.add_parser("cockpit", help="仅根据现有数据刷新驾驶舱")
    serve = subparsers.add_parser("serve", help="生成并启动驾驶舱本地服务")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8765)
    return parser


def _run_profile(args: argparse.Namespace, root: Path, policy: dict[str, Any]) -> int:
    gates = gates_for_profile(
        args.command,
        root,
        policy,
        backend_runtime=args.backend_runtime,
        frontend_runtime=args.frontend_runtime,
    )
    skipped = _parse_skips(args.skip)
    known = {gate.name for gate in gates}
    unknown = sorted(skipped - known)
    if unknown:
        print(f"未知门禁：{', '.join(unknown)}", file=sys.stderr)
        return 2

    print(f"UniDjango quality: {args.command}")
    report = run_gates(
        gates,
        mode=args.command,
        runtimes={
            "backend": args.backend_runtime,
            "frontend": args.frontend_runtime,
        },
        skipped=skipped,
    )
    report_path = AI_ROOT / "reports" / "report.json"
    write_report(report, report_path)
    cockpit_path = build_cockpit(root)
    print(
        f"\n结果：{report.status.upper()}，{report.duration_seconds:.2f}s\n"
        f"报告：{report_path}\n驾驶舱：{cockpit_path}"
    )
    return 0 if report.status != "failed" else 1


def main(argv: list[str] | None = None) -> int:
    """Run the requested command and return a process exit code."""
    _configure_console()
    parser = create_parser()
    args = parser.parse_args(argv)
    try:
        policy = load_policy()
        if args.command in PROFILES:
            return _run_profile(args, REPO_ROOT, policy)
        if args.command == "cockpit":
            output = build_cockpit(REPO_ROOT)
            print(f"驾驶舱已生成：{output}")
            return 0
        if args.command == "serve":
            output = build_cockpit(REPO_ROOT)
            directory = output.parent
            handler = partial(
                CockpitRequestHandler,
                directory=str(directory),
                test_runner=CoreTestRunner(REPO_ROOT),
            )
            server = ThreadingHTTPServer((args.host, args.port), handler)
            print(f"驾驶舱：http://{args.host}:{args.port}/")
            print("按 Ctrl+C 停止。")
            try:
                server.serve_forever()
            except KeyboardInterrupt:
                print("\n已停止。")
            finally:
                server.server_close()
            return 0
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"quality.py: {exc}", file=sys.stderr)
        return 2
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
