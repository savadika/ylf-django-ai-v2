#!/usr/bin/env python3
"""Create and validate immutable release manifests for SPEC-012."""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
import json
import os
from pathlib import Path
import re
import sys
import tempfile
from typing import Any


SCHEMA_VERSION = 1
RELEASE_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
COMMIT_RE = re.compile(r"^(?:[0-9a-fA-F]{40}|[0-9a-fA-F]{64})$")
DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
MAX_MANIFEST_BYTES = 64 * 1024
REQUIRED_FIELDS = {
    "schema_version",
    "release_id",
    "commit_sha",
    "source_ref",
    "backend_image",
    "frontend_image",
    "backend_digest",
    "frontend_digest",
    "created_at",
}


class ReleaseManifestError(ValueError):
    """Raised when a release manifest cannot be trusted."""


def _split_image(image: str, field: str) -> tuple[str, str]:
    if not isinstance(image, str) or image.count("@") != 1:
        raise ReleaseManifestError(f"{field} 必须是 image@sha256:<digest>")
    name, digest = image.rsplit("@", 1)
    if not name or any(char.isspace() for char in name):
        raise ReleaseManifestError(f"{field} 的镜像名无效")
    if not DIGEST_RE.fullmatch(digest):
        raise ReleaseManifestError(f"{field} 必须使用 sha256 digest")
    return name, digest


def _validate_created_at(value: str) -> None:
    try:
        timestamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (AttributeError, ValueError) as exc:
        raise ReleaseManifestError("created_at 必须是 ISO 8601 时间") from exc
    if timestamp.tzinfo is None:
        raise ReleaseManifestError("created_at 必须包含时区")


def validate_manifest(value: Any) -> dict[str, Any]:
    """Return a normalized manifest or raise on unsafe/incomplete data."""
    if not isinstance(value, dict):
        raise ReleaseManifestError("发布清单根节点必须是 JSON 对象")
    if set(value) != REQUIRED_FIELDS:
        missing = sorted(REQUIRED_FIELDS - set(value))
        extra = sorted(set(value) - REQUIRED_FIELDS)
        raise ReleaseManifestError(f"发布清单字段不匹配；缺少={missing}，多余={extra}")
    if value["schema_version"] != SCHEMA_VERSION:
        raise ReleaseManifestError(f"不支持的 schema_version：{value['schema_version']}")

    release_id = value["release_id"]
    if not isinstance(release_id, str) or not RELEASE_ID_RE.fullmatch(release_id):
        raise ReleaseManifestError("release_id 只能包含字母、数字、点、下划线和短横线")

    commit_sha = value["commit_sha"]
    if not isinstance(commit_sha, str) or not COMMIT_RE.fullmatch(commit_sha):
        raise ReleaseManifestError("commit_sha 必须是完整 Git SHA")

    source_ref = value["source_ref"]
    if (
        not isinstance(source_ref, str)
        or not source_ref
        or len(source_ref) > 256
        or "\n" in source_ref
        or "\r" in source_ref
    ):
        raise ReleaseManifestError("source_ref 无效")

    _, backend_digest = _split_image(value["backend_image"], "backend_image")
    _, frontend_digest = _split_image(value["frontend_image"], "frontend_image")
    if value["backend_digest"] != backend_digest:
        raise ReleaseManifestError("backend_digest 与 backend_image 不一致")
    if value["frontend_digest"] != frontend_digest:
        raise ReleaseManifestError("frontend_digest 与 frontend_image 不一致")
    _validate_created_at(value["created_at"])

    return {field: value[field] for field in sorted(REQUIRED_FIELDS)}


def build_manifest(
    *,
    release_id: str,
    commit_sha: str,
    backend_image: str,
    frontend_image: str,
    source_ref: str,
    created_at: str | None = None,
) -> dict[str, Any]:
    """Build a manifest from CI-provided immutable image references."""
    _, backend_digest = _split_image(backend_image, "backend_image")
    _, frontend_digest = _split_image(frontend_image, "frontend_image")
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "release_id": release_id,
        "commit_sha": commit_sha,
        "source_ref": source_ref,
        "backend_image": backend_image,
        "frontend_image": frontend_image,
        "backend_digest": backend_digest,
        "frontend_digest": frontend_digest,
        "created_at": created_at
        or datetime.now(UTC).isoformat(timespec="seconds"),
    }
    return validate_manifest(manifest)


def load_manifest(path: Path) -> dict[str, Any]:
    """Load a bounded JSON release manifest."""
    try:
        if path.stat().st_size > MAX_MANIFEST_BYTES:
            raise ReleaseManifestError("发布清单文件过大")
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ReleaseManifestError(f"发布清单不存在：{path}") from exc
    except UnicodeDecodeError as exc:
        raise ReleaseManifestError("发布清单必须是 UTF-8") from exc
    except json.JSONDecodeError as exc:
        raise ReleaseManifestError(f"发布清单不是合法 JSON：{exc}") from exc
    return validate_manifest(value)


def write_manifest(path: Path, manifest: dict[str, Any]) -> None:
    """Atomically write a validated manifest as UTF-8 JSON."""
    normalized = validate_manifest(manifest)
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=".release.", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(normalized, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    create = subparsers.add_parser("create", help="创建发布清单")
    create.add_argument("--release-id", required=True)
    create.add_argument("--commit-sha", required=True)
    create.add_argument("--source-ref", required=True)
    create.add_argument("--backend-image", required=True)
    create.add_argument("--frontend-image", required=True)
    create.add_argument("--output", type=Path, required=True)

    validate = subparsers.add_parser("validate", help="校验并输出规范化清单")
    validate.add_argument("manifest", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "create":
            manifest = build_manifest(
                release_id=args.release_id,
                commit_sha=args.commit_sha,
                source_ref=args.source_ref,
                backend_image=args.backend_image,
                frontend_image=args.frontend_image,
            )
            write_manifest(args.output, manifest)
            print(args.output)
            return 0

        manifest = load_manifest(args.manifest)
        print(json.dumps(manifest, ensure_ascii=False, sort_keys=True))
        return 0
    except (OSError, ReleaseManifestError) as exc:
        print(f"发布清单错误：{exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
