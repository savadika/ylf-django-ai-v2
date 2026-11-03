#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
BUSINESS_DIR="$(cd -- "$SCRIPT_DIR/.." && pwd)"
ENV_FILE="$BUSINESS_DIR/.env"
COMPOSE_FILE="$BUSINESS_DIR/docker-compose.yml"
MANIFEST_TOOL="$SCRIPT_DIR/release_manifest.py"
RELEASES_DIR="$BUSINESS_DIR/releases"
CURRENT_FILE="$RELEASES_DIR/current-release"
PREVIOUS_FILE="$RELEASES_DIR/previous-release"

TARGET_INPUT="${1:-}"
AUTO_MODE="${2:-}"
HEALTH_ATTEMPTS="${HEALTH_ATTEMPTS:-120}"
HEALTH_INTERVAL="${HEALTH_INTERVAL:-2}"

log() {
    printf '\033[1;34m==>\033[0m %s\n' "$*"
}

die() {
    printf '\033[1;31m[x]\033[0m %s\n' "$*" >&2
    exit 1
}

usage() {
    cat <<'EOF'
用法：
  sudo bash business/scripts/rollback-release.sh [release-id|manifest.json]

不传参数时使用 previous-release。回滚只恢复应用镜像，不自动恢复数据库。
EOF
}

if [[ "$TARGET_INPUT" == "-h" || "$TARGET_INPUT" == "--help" ]]; then
    usage
    exit 0
fi
[[ $EUID -eq 0 ]] || die "请使用 root 或 sudo 运行回滚脚本"
[[ -f "$ENV_FILE" ]] || die "缺少 $ENV_FILE"
[[ -f "$COMPOSE_FILE" ]] || die "缺少 $COMPOSE_FILE"
[[ -f "$MANIFEST_TOOL" ]] || die "缺少发布清单工具：$MANIFEST_TOOL"
command -v python3 >/dev/null 2>&1 || die "未安装 python3"
command -v curl >/dev/null 2>&1 || die "未安装 curl"
command -v flock >/dev/null 2>&1 || die "未安装 flock"

if [[ "${RELEASE_LOCK_HELD:-0}" != "1" ]]; then
    mkdir -p /run/lock
    exec 9>/run/lock/ylf-django-release.lock
    flock -n 9 || die "已有另一个发布或回滚任务正在运行"
fi

if [[ -z "$TARGET_INPUT" ]]; then
    [[ -s "$PREVIOUS_FILE" ]] || die "没有 previous-release，不能自动选择回滚版本"
    TARGET_INPUT="$(tr -d '[:space:]' < "$PREVIOUS_FILE")"
fi

if [[ -f "$TARGET_INPUT" ]]; then
    MANIFEST_FILE="$(readlink -f -- "$TARGET_INPUT")"
else
    MANIFEST_FILE="$RELEASES_DIR/${TARGET_INPUT}.json"
fi
[[ -f "$MANIFEST_FILE" ]] || die "找不到回滚发布清单：$MANIFEST_FILE"
python3 "$MANIFEST_TOOL" validate "$MANIFEST_FILE" >/dev/null

manifest_value() {
    python3 - "$MANIFEST_FILE" "$1" <<'PY'
import json
import sys

with open(sys.argv[1], encoding="utf-8") as handle:
    print(json.load(handle)[sys.argv[2]])
PY
}

RELEASE_ID="$(manifest_value release_id)"
BACKEND_IMAGE="$(manifest_value backend_image)"
FRONTEND_IMAGE="$(manifest_value frontend_image)"
export BACKEND_IMAGE FRONTEND_IMAGE

get_env_value() {
    local key="$1"
    grep -E "^${key}=" "$ENV_FILE" 2>/dev/null | tail -1 | cut -d= -f2-
}

SERVER_HOST="$(get_env_value SERVER_HOST)"
BACKEND_PORT="$(get_env_value BACKEND_PORT)"
FRONTEND_PORT="$(get_env_value FRONTEND_PORT)"
SERVER_HOST="${SERVER_HOST:-127.0.0.1}"
BACKEND_PORT="${BACKEND_PORT:-8002}"
FRONTEND_PORT="${FRONTEND_PORT:-9530}"

compose_prod() {
    docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" "$@"
}

wait_for_health() {
    local index
    for ((index = 1; index <= HEALTH_ATTEMPTS; index++)); do
        if compose_prod ps --status running --services 2>/dev/null |
            grep -qx backend &&
            compose_prod ps --status running --services 2>/dev/null |
                grep -qx frontend &&
            curl -fsS --max-time 5 -H "Host: ${SERVER_HOST}" \
                "http://127.0.0.1:${BACKEND_PORT}/healthz/" >/dev/null 2>&1 &&
            curl -fsS --max-time 5 \
                "http://127.0.0.1:${FRONTEND_PORT}/" >/dev/null 2>&1; then
            return 0
        fi
        sleep "$HEALTH_INTERVAL"
    done
    return 1
}

FORMER_CURRENT=""
if [[ -s "$CURRENT_FILE" ]]; then
    FORMER_CURRENT="$(tr -d '[:space:]' < "$CURRENT_FILE")"
fi

log "回滚到发布 $RELEASE_ID"
compose_prod config --quiet
compose_prod pull backend frontend
compose_prod up -d --no-build --remove-orphans backend frontend

if ! wait_for_health; then
    compose_prod ps || true
    compose_prod logs --tail=120 backend frontend >&2 || true
    die "回滚版本 $RELEASE_ID 未通过健康检查"
fi

if [[ -n "$FORMER_CURRENT" && "$FORMER_CURRENT" != "$RELEASE_ID" ]]; then
    printf '%s\n' "$FORMER_CURRENT" > "$PREVIOUS_FILE"
fi
printf '%s\n' "$RELEASE_ID" > "$CURRENT_FILE"

if [[ "$AUTO_MODE" == "--auto" ]]; then
    log "自动回滚成功：$RELEASE_ID"
else
    log "人工回滚成功：$RELEASE_ID"
fi
