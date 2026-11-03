#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
BUSINESS_DIR="$(cd -- "$SCRIPT_DIR/.." && pwd)"
ENV_FILE="$BUSINESS_DIR/.env"
COMPOSE_FILE="$BUSINESS_DIR/docker-compose.yml"
MANIFEST_TOOL="$SCRIPT_DIR/release_manifest.py"
RELEASES_DIR="$BUSINESS_DIR/releases"
BACKUPS_DIR="$BUSINESS_DIR/backups/releases"
CURRENT_FILE="$RELEASES_DIR/current-release"
PREVIOUS_FILE="$RELEASES_DIR/previous-release"

MANIFEST_INPUT="${1:-}"
HEALTH_ATTEMPTS="${HEALTH_ATTEMPTS:-120}"
HEALTH_INTERVAL="${HEALTH_INTERVAL:-2}"

log() {
    printf '\033[1;34m==>\033[0m %s\n' "$*"
}

warn() {
    printf '\033[1;33m[!]\033[0m %s\n' "$*" >&2
}

die() {
    printf '\033[1;31m[x]\033[0m %s\n' "$*" >&2
    exit 1
}

usage() {
    cat <<'EOF'
用法：
  sudo bash business/scripts/deploy-release.sh <release-manifest.json>

脚本会先校验发布清单和备份数据库，然后拉取清单中的固定镜像并启动服务。
健康检查失败时会自动尝试恢复 previous-release。
EOF
}

if [[ "$MANIFEST_INPUT" == "-h" || "$MANIFEST_INPUT" == "--help" ]]; then
    usage
    exit 0
fi
[[ -n "$MANIFEST_INPUT" ]] || {
    usage >&2
    exit 2
}
[[ $EUID -eq 0 ]] || die "请使用 root 或 sudo 运行发布脚本"
[[ -f "$ENV_FILE" ]] || die "缺少 $ENV_FILE，请先执行 deploy-rocky.sh"
[[ -f "$COMPOSE_FILE" ]] || die "缺少 $COMPOSE_FILE"
[[ -f "$MANIFEST_TOOL" ]] || die "缺少发布清单工具：$MANIFEST_TOOL"
command -v docker >/dev/null 2>&1 || die "未安装 docker"
command -v python3 >/dev/null 2>&1 || die "未安装 python3"
command -v curl >/dev/null 2>&1 || die "未安装 curl"
command -v gzip >/dev/null 2>&1 || die "未安装 gzip"
command -v flock >/dev/null 2>&1 || die "未安装 flock"

mkdir -p /run/lock
exec 9>/run/lock/ylf-django-release.lock
flock -n 9 || die "已有另一个发布或回滚任务正在运行"

MANIFEST_INPUT="$(readlink -f -- "$MANIFEST_INPUT")"
[[ -f "$MANIFEST_INPUT" ]] || die "发布清单不存在：$MANIFEST_INPUT"
python3 "$MANIFEST_TOOL" validate "$MANIFEST_INPUT" >/dev/null

manifest_value() {
    python3 - "$MANIFEST_INPUT" "$1" <<'PY'
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

wait_for_dependencies() {
    local attempts="${1:-60}"
    local index
    for ((index = 1; index <= attempts; index++)); do
        if compose_prod exec -T db sh -c \
            'MYSQL_PWD="$MYSQL_ROOT_PASSWORD" mysqladmin ping -h 127.0.0.1 -uroot --silent' \
            >/dev/null 2>&1 &&
            compose_prod exec -T redis sh -c \
                'redis-cli --no-auth-warning -a "$REDIS_PASSWORD" ping' \
                2>/dev/null | grep -q PONG; then
            return 0
        fi
        sleep 2
    done
    return 1
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

mkdir -p "$RELEASES_DIR" "$BACKUPS_DIR/$RELEASE_ID"
STORED_MANIFEST="$RELEASES_DIR/${RELEASE_ID}.json"
install -m 0644 "$MANIFEST_INPUT" "$STORED_MANIFEST"

PREVIOUS_RELEASE=""
if [[ -s "$CURRENT_FILE" ]]; then
    PREVIOUS_RELEASE="$(tr -d '[:space:]' < "$CURRENT_FILE")"
fi

ROLLBACK_ACTIVE=0
on_error() {
    local code=$?
    trap - ERR
    if (( ROLLBACK_ACTIVE == 0 )); then
        ROLLBACK_ACTIVE=1
        warn "发布 $RELEASE_ID 失败，退出码 $code"
        compose_prod ps || true
        compose_prod logs --tail=120 backend frontend >&2 || true
        if [[ -n "$PREVIOUS_RELEASE" &&
              -f "$RELEASES_DIR/${PREVIOUS_RELEASE}.json" ]]; then
            warn "尝试自动回滚到 $PREVIOUS_RELEASE"
            if RELEASE_LOCK_HELD=1 bash "$SCRIPT_DIR/rollback-release.sh" \
                "$RELEASES_DIR/${PREVIOUS_RELEASE}.json" --auto; then
                warn "自动回滚成功；请根据日志修复 $RELEASE_ID 后重新发布"
            else
                warn "自动回滚失败，需要人工处理"
            fi
        else
            warn "没有可用的上一发布，停止新应用容器"
            compose_prod stop backend frontend >/dev/null 2>&1 || true
        fi
    fi
    exit "$code"
}
trap on_error ERR

log "校验 Compose 配置"
compose_prod config --quiet

log "启动数据库和缓存"
compose_prod up -d --no-build db redis
wait_for_dependencies 60 || die "MySQL 或 Redis 在 120 秒内未就绪"

log "备份 MySQL"
BACKUP_FILE="$BACKUPS_DIR/$RELEASE_ID/before-$(date +%Y%m%d-%H%M%S).sql.gz"
BACKUP_TEMP="${BACKUP_FILE}.tmp"
compose_prod exec -T db sh -c \
    'MYSQL_PWD="$MYSQL_ROOT_PASSWORD" exec mysqldump -uroot \
    --single-transaction --quick --lock-tables=false "$MYSQL_DATABASE"' |
    gzip -c > "$BACKUP_TEMP"
mv "$BACKUP_TEMP" "$BACKUP_FILE"
chmod 600 "$BACKUP_FILE"
log "数据库备份：$BACKUP_FILE"

log "拉取发布 $RELEASE_ID 的固定镜像"
compose_prod pull backend frontend

log "使用新镜像执行数据库迁移"
compose_prod run --rm --no-deps backend python manage.py migrate --noinput

log "启动应用"
compose_prod up -d --no-build --remove-orphans backend frontend

log "等待前后端健康"
if ! wait_for_health; then
    warn "应用在 $((HEALTH_ATTEMPTS * HEALTH_INTERVAL)) 秒内未通过健康检查"
    false
fi

if [[ -n "$PREVIOUS_RELEASE" && "$PREVIOUS_RELEASE" != "$RELEASE_ID" ]]; then
    printf '%s\n' "$PREVIOUS_RELEASE" > "$PREVIOUS_FILE"
fi
printf '%s\n' "$RELEASE_ID" > "$CURRENT_FILE"

trap - ERR
log "发布成功：$RELEASE_ID"
log "当前版本：$(cat "$CURRENT_FILE")"
if [[ -s "$PREVIOUS_FILE" ]]; then
    log "上一版本：$(cat "$PREVIOUS_FILE")"
fi
