#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_PATH="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)/$(basename -- "${BASH_SOURCE[0]}")"
BUSINESS_DIR="$(cd -- "$(dirname -- "$SCRIPT_PATH")/.." && pwd)"
ENV_FILE="$BUSINESS_DIR/.env"
ENV_EXAMPLE="$BUSINESS_DIR/.env.example"
CREDENTIAL_FILE="$BUSINESS_DIR/.deploy-credentials"
COMPOSE_FILE="$BUSINESS_DIR/docker-compose.yml"
DEV_COMPOSE_FILE="$BUSINESS_DIR/docker-compose-dev.yml"

DEPLOY_HOST=""
FRONTEND_PORT=""
SERVER_PROTOCOL=""
ADMIN_USERNAME="${ADMIN_USERNAME:-admin}"
ADMIN_EMAIL="${ADMIN_EMAIL:-admin@example.com}"
ADMIN_PASSWORD="${ADMIN_PASSWORD:-}"
REGISTRY_MIRROR="${DOCKER_REGISTRY_MIRROR:-}"
BACKEND_PORT=""
SKIP_FIREWALL=0
RESET_ADMIN=0
ADMIN_ARGS_SET=0

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
  sudo bash business/scripts/deploy-rocky.sh [选项]

在 Rocky Linux 8/9/10 上安装 Docker、创建安全配置并启动生产环境。

选项：
  --host <域名或IP>          浏览器访问地址；默认自动识别本机 IPv4
  --frontend-port <端口>     前端端口，默认读取 .env 或使用 9530
  --protocol <http|https>    访问协议，默认 http（TLS 需外部反向代理）
  --admin-username <名称>    管理员用户名，默认 admin
  --admin-email <邮箱>       管理员邮箱，默认 admin@example.com
  --admin-password <密码>    管理员密码；不传则首次部署时自动生成
  --reset-admin              显式重新初始化管理员及密码
  --mirror <URL>             可选 Docker registry mirror，例如 https://mirror.example
  --skip-firewall            不修改 firewalld
  -h, --help                 显示帮助

示例：
  sudo bash business/scripts/deploy-rocky.sh --host 192.168.1.20
  sudo bash business/scripts/deploy-rocky.sh --host app.example.com --protocol https
  sudo bash business/scripts/deploy-rocky.sh --mirror https://docker.m.daocloud.io

重复执行会重新构建并启动服务，但不会自动轮换已有数据库密码或管理员密码。
EOF
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
    usage
    exit 0
fi

if [[ $EUID -ne 0 ]]; then
    if command -v sudo >/dev/null 2>&1; then
        exec sudo bash "$SCRIPT_PATH" "$@"
    fi
    die "请使用 root 运行，或安装 sudo 后执行：sudo bash $SCRIPT_PATH"
fi

while [[ $# -gt 0 ]]; do
    case "$1" in
        --host)
            DEPLOY_HOST="${2:-}"
            [[ -n "$DEPLOY_HOST" ]] || die "--host 需要非空值"
            shift 2
            ;;
        --frontend-port)
            FRONTEND_PORT="${2:-}"
            [[ -n "$FRONTEND_PORT" ]] || die "--frontend-port 需要非空值"
            shift 2
            ;;
        --protocol)
            SERVER_PROTOCOL="${2:-}"
            [[ "$SERVER_PROTOCOL" == "http" || "$SERVER_PROTOCOL" == "https" ]] || {
                die "--protocol 只能是 http 或 https"
            }
            shift 2
            ;;
        --admin-username)
            ADMIN_USERNAME="${2:-}"
            ADMIN_ARGS_SET=1
            shift 2
            ;;
        --admin-email)
            ADMIN_EMAIL="${2:-}"
            ADMIN_ARGS_SET=1
            shift 2
            ;;
        --admin-password)
            ADMIN_PASSWORD="${2:-}"
            ADMIN_ARGS_SET=1
            shift 2
            ;;
        --reset-admin)
            RESET_ADMIN=1
            ADMIN_ARGS_SET=1
            shift
            ;;
        --mirror)
            REGISTRY_MIRROR="${2:-}"
            [[ -n "$REGISTRY_MIRROR" ]] || die "--mirror 需要非空 URL"
            shift 2
            ;;
        --skip-firewall)
            SKIP_FIREWALL=1
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            die "未知参数：$1"
            ;;
    esac
done

if [[ -f "$CREDENTIAL_FILE" && "$RESET_ADMIN" -eq 0 && "$ADMIN_ARGS_SET" -eq 1 ]]; then
    die "管理员参数只能在首次部署或使用 --reset-admin 时指定"
fi

trap 'warn "部署在第 ${LINENO} 行失败，请根据上方错误检查。"' ERR

[[ -f /etc/os-release ]] || die "无法识别操作系统：缺少 /etc/os-release"
# shellcheck disable=SC1091
. /etc/os-release
[[ "${ID:-}" == "rocky" ]] || die "此脚本仅支持 Rocky Linux，当前系统：${PRETTY_NAME:-unknown}"

ROCKY_MAJOR="${VERSION_ID%%.*}"
if ! [[ "$ROCKY_MAJOR" =~ ^[0-9]+$ ]] || (( ROCKY_MAJOR < 8 )); then
    die "需要 Rocky Linux 8 或更高版本，当前为 ${VERSION_ID:-unknown}"
fi
if (( ROCKY_MAJOR > 10 )); then
    warn "Rocky Linux ${ROCKY_MAJOR} 尚未在脚本测试矩阵中，继续执行。"
fi

ARCH="$(uname -m)"
if [[ "$ARCH" != "x86_64" && "$ARCH" != "aarch64" ]]; then
    die "仅支持 x86_64 或 aarch64，当前架构：$ARCH"
fi

[[ -f "$COMPOSE_FILE" ]] || die "缺少生产编排文件：$COMPOSE_FILE"
[[ -f "$ENV_EXAMPLE" ]] || die "缺少环境变量模板：$ENV_EXAMPLE"

AVAILABLE_KB="$(df -Pk "$BUSINESS_DIR" | awk 'NR == 2 {print $4}')"
if [[ "$AVAILABLE_KB" =~ ^[0-9]+$ ]] && (( AVAILABLE_KB < 5 * 1024 * 1024 )); then
    die "业务目录可用空间不足 5GB，请先扩容磁盘。"
fi

log "安装 Rocky Linux 基础工具和 Docker CE"
dnf -y install dnf-plugins-core ca-certificates curl git openssl python3 tar firewalld

if ! rpm -q docker-ce >/dev/null 2>&1; then
    if ! dnf repolist | grep -q '^docker-ce-stable'; then
        dnf -y config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
    fi
    dnf -y install \
        docker-ce \
        docker-ce-cli \
        containerd.io \
        docker-buildx-plugin \
        docker-compose-plugin
else
    dnf -y install docker-compose-plugin docker-buildx-plugin
fi

systemctl enable --now docker
docker --version
docker compose version

if [[ -n "${SUDO_USER:-}" && "$SUDO_USER" != "root" ]]; then
    usermod -aG docker "$SUDO_USER"
    log "已将 $SUDO_USER 加入 docker 组；重新登录后可免 sudo 使用 Docker。"
fi

configure_registry_mirror() {
    [[ -n "$REGISTRY_MIRROR" ]] || return 0
    [[ "$REGISTRY_MIRROR" =~ ^https?://[^[:space:]]+$ ]] || {
        die "--mirror 必须是有效的 http(s) URL"
    }

    log "配置 Docker registry mirror：$REGISTRY_MIRROR"
    mkdir -p /etc/docker
    python3 - "$REGISTRY_MIRROR" <<'PY'
import json
import os
import stat
import sys
import tempfile

mirror = sys.argv[1].rstrip("/")
path = "/etc/docker/daemon.json"
data = {}
if os.path.exists(path):
    try:
        with open(path, encoding="utf-8") as handle:
            loaded = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"现有 {path} 无法解析，请先手工修复：{exc}")
    if not isinstance(loaded, dict):
        raise SystemExit(f"现有 {path} 根节点必须是 JSON 对象")
    data = loaded

mirrors = data.get("registry-mirrors")
if not isinstance(mirrors, list):
    mirrors = []
normalized = [item.rstrip("/") for item in mirrors if isinstance(item, str) and item.strip()]
if mirror not in normalized:
    normalized.insert(0, mirror)
data["registry-mirrors"] = normalized

mode = stat.S_IMODE(os.stat(path).st_mode) if os.path.exists(path) else 0o644
fd, temporary = tempfile.mkstemp(prefix="daemon.json.", dir="/etc/docker")
try:
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    os.chmod(temporary, mode)
    os.replace(temporary, path)
finally:
    if os.path.exists(temporary):
        os.unlink(temporary)
PY
    dockerd --validate --config-file=/etc/docker/daemon.json
    systemctl restart docker
}

configure_registry_mirror

random_hex() {
    openssl rand -hex "${1:-24}"
}

get_env_value() {
    local file="$1"
    local key="$2"
    grep -E "^${key}=" "$file" 2>/dev/null | tail -1 | cut -d= -f2-
}

set_env_value() {
    local key="$1"
    local value="$2"
    python3 - "$ENV_FILE" "$key" "$value" <<'PY'
import os
import stat
import sys
import tempfile

path, key, value = sys.argv[1:]
with open(path, encoding="utf-8") as handle:
    lines = handle.readlines()

prefix = f"{key}="
output = []
replaced = False
for line in lines:
    if line.startswith(prefix):
        if not replaced:
            output.append(f"{key}={value}\n")
            replaced = True
        continue
    output.append(line)
if not replaced:
    output.append(f"{key}={value}\n")

mode = stat.S_IMODE(os.stat(path).st_mode)
fd, temporary = tempfile.mkstemp(prefix=".env.", dir=os.path.dirname(path))
try:
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        handle.writelines(output)
    os.chmod(temporary, mode)
    os.replace(temporary, path)
finally:
    if os.path.exists(temporary):
        os.unlink(temporary)
PY
}

path_has_data() {
    local path="$1"
    [[ -d "$path" ]] && [[ -n "$(find "$path" -mindepth 1 -maxdepth 1 -print -quit 2>/dev/null)" ]]
}

DB_HAS_DATA=0
REDIS_HAS_DATA=0
path_has_data "$BUSINESS_DIR/db_data" && DB_HAS_DATA=1
path_has_data "$BUSINESS_DIR/redis_data" && REDIS_HAS_DATA=1

if [[ ! -f "$ENV_FILE" ]]; then
    cp "$ENV_EXAMPLE" "$ENV_FILE"
    log "已从 .env.example 创建 business/.env"
fi

ensure_secret() {
    local key="$1"
    local current
    current="$(get_env_value "$ENV_FILE" "$key" || true)"
    if [[ -n "$current" && "$current" != "change-me" ]]; then
        return 0
    fi

    case "$key" in
        MYSQL_ROOT_PASSWORD)
            (( DB_HAS_DATA == 0 )) || {
                die "检测到已有 db_data，但 $key 为空或仍为 change-me。为防止锁死数据库，脚本不会自动轮换该密码。"
            }
            ;;
        REDIS_PASSWORD)
            (( REDIS_HAS_DATA == 0 )) || {
                die "检测到已有 redis_data，但 $key 为空或仍为 change-me。为防止锁死 Redis，脚本不会自动轮换该密码。"
            }
            ;;
    esac

    set_env_value "$key" "$(random_hex 32)"
    log "已生成独立随机值：$key"
}

ensure_secret DJANGO_SECRET_KEY
ensure_secret JWT_SECRET_KEY
ensure_secret MYSQL_ROOT_PASSWORD
ensure_secret REDIS_PASSWORD

detect_server_ip() {
    local detected=""
    if command -v ip >/dev/null 2>&1; then
        detected="$(
            ip -4 route get 1.1.1.1 2>/dev/null |
                awk '{for (i = 1; i <= NF; i++) if ($i == "src") {print $(i + 1); exit}}'
        )"
    fi
    if [[ -z "$detected" ]] && command -v hostname >/dev/null 2>&1; then
        detected="$(
            hostname -I 2>/dev/null |
                tr ' ' '\n' |
                awk '$0 !~ /^127\./ && $0 != "" {print; exit}'
        )"
    fi
    printf '%s\n' "$detected"
}

is_valid_host() {
    [[ "$1" =~ ^[A-Za-z0-9]([A-Za-z0-9.-]*[A-Za-z0-9])?$ ]]
}

CURRENT_SERVER_HOST="$(get_env_value "$ENV_FILE" SERVER_HOST || true)"
if [[ -n "$DEPLOY_HOST" ]]; then
    SERVER_HOST="$DEPLOY_HOST"
elif [[ -n "$CURRENT_SERVER_HOST" && "$CURRENT_SERVER_HOST" != "127.0.0.1" && "$CURRENT_SERVER_HOST" != "localhost" ]]; then
    SERVER_HOST="$CURRENT_SERVER_HOST"
else
    SERVER_HOST="$(detect_server_ip)"
    [[ -n "$SERVER_HOST" ]] || SERVER_HOST="127.0.0.1"
fi
is_valid_host "$SERVER_HOST" || die "无效的服务器地址：$SERVER_HOST"

if [[ -z "$FRONTEND_PORT" ]]; then
    FRONTEND_PORT="$(get_env_value "$ENV_FILE" FRONTEND_PORT || true)"
    FRONTEND_PORT="${FRONTEND_PORT:-9530}"
fi
[[ "$FRONTEND_PORT" =~ ^[0-9]+$ ]] || die "前端端口必须是数字"
(( FRONTEND_PORT >= 1 && FRONTEND_PORT <= 65535 )) || die "前端端口必须在 1-65535 范围内"

BACKEND_PORT="$(get_env_value "$ENV_FILE" BACKEND_PORT || true)"
BACKEND_PORT="${BACKEND_PORT:-8002}"
[[ "$BACKEND_PORT" =~ ^[0-9]+$ ]] || die "后端端口必须是数字"
(( BACKEND_PORT >= 1 && BACKEND_PORT <= 65535 )) || die "后端端口必须在 1-65535 范围内"

if [[ -z "$SERVER_PROTOCOL" ]]; then
    SERVER_PROTOCOL="$(get_env_value "$ENV_FILE" SERVER_PROTOCOL || true)"
    SERVER_PROTOCOL="${SERVER_PROTOCOL:-http}"
fi
[[ "$SERVER_PROTOCOL" == "http" || "$SERVER_PROTOCOL" == "https" ]] || die "SERVER_PROTOCOL 只能是 http 或 https"

set_env_value SERVER_HOST "$SERVER_HOST"
set_env_value SERVER_PROTOCOL "$SERVER_PROTOCOL"
set_env_value FRONTEND_PORT "$FRONTEND_PORT"

CURRENT_ALLOWED="$(get_env_value "$ENV_FILE" DJANGO_ALLOWED_HOSTS || true)"
if ! tr ',' '\n' <<< "$CURRENT_ALLOWED" | sed 's/^ *//;s/ *$//' | grep -qxF "$SERVER_HOST"; then
    if [[ -n "$CURRENT_ALLOWED" ]]; then
        CURRENT_ALLOWED="${CURRENT_ALLOWED},${SERVER_HOST}"
    else
        CURRENT_ALLOWED="localhost,127.0.0.1,${SERVER_HOST}"
    fi
fi
set_env_value DJANGO_ALLOWED_HOSTS "$CURRENT_ALLOWED"

chmod 600 "$ENV_FILE"
if [[ -n "${SUDO_UID:-}" && -n "${SUDO_GID:-}" ]]; then
    chown "$SUDO_UID:$SUDO_GID" "$ENV_FILE"
fi

if (( SKIP_FIREWALL == 0 )); then
    log "配置 firewalld，仅开放前端端口 $FRONTEND_PORT/tcp"
    systemctl enable --now firewalld
    firewall-cmd --permanent --add-port="${FRONTEND_PORT}/tcp"
    firewall-cmd --reload
else
    warn "已跳过 firewalld 配置"
fi

ADMIN_INIT_NEEDED=1
if [[ -f "$CREDENTIAL_FILE" && "$RESET_ADMIN" -eq 0 && "$ADMIN_ARGS_SET" -eq 0 ]]; then
    ADMIN_USERNAME="$(get_env_value "$CREDENTIAL_FILE" ADMIN_USERNAME || true)"
    ADMIN_PASSWORD="$(get_env_value "$CREDENTIAL_FILE" ADMIN_PASSWORD || true)"
    ADMIN_EMAIL="$(get_env_value "$CREDENTIAL_FILE" ADMIN_EMAIL || true)"
    ADMIN_INIT_NEEDED=0
    [[ -n "$ADMIN_USERNAME" && -n "$ADMIN_PASSWORD" ]] || {
        die "现有 $CREDENTIAL_FILE 不完整；请使用 --reset-admin 重新初始化管理员。"
    }
fi

if (( ADMIN_INIT_NEEDED == 1 )); then
    [[ -n "$ADMIN_USERNAME" ]] || die "管理员用户名不能为空"
    [[ -n "$ADMIN_EMAIL" ]] || die "管理员邮箱不能为空"
    [[ "$ADMIN_PASSWORD" != *$'\n'* ]] || die "管理员密码不能包含换行"
    if [[ -z "$ADMIN_PASSWORD" ]]; then
        ADMIN_PASSWORD="$(random_hex 24)"
    fi
    (( ${#ADMIN_PASSWORD} >= 8 )) || die "管理员密码长度不能少于 8 位"
fi

compose_prod() {
    docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" "$@"
}

log "停止可能占用相同容器名的开发环境"
docker compose --env-file "$ENV_FILE" -f "$DEV_COMPOSE_FILE" down --remove-orphans >/dev/null 2>&1 || true

log "校验 Docker Compose 配置"
compose_prod config --quiet

log "构建并启动生产环境"
compose_prod up -d --build --remove-orphans

log "等待前端和后端就绪"
READY=0
for _ in $(seq 1 120); do
    if compose_prod ps --status running --services 2>/dev/null | grep -qx backend &&
       compose_prod exec -T backend python manage.py migrate --check >/dev/null 2>&1 &&
       curl -fsS --max-time 3 -H "Host: ${SERVER_HOST}" \
         "http://127.0.0.1:${BACKEND_PORT}/healthz/" >/dev/null 2>&1 &&
       curl -fsS --max-time 3 "http://127.0.0.1:${FRONTEND_PORT}/" >/dev/null 2>&1; then
        READY=1
        break
    fi
    sleep 2
done

if (( READY == 0 )); then
    compose_prod ps || true
    compose_prod logs --tail=120 backend frontend >&2 || true
    die "服务在 240 秒内未就绪。请检查上方日志或运行：cd $BUSINESS_DIR && docker compose logs -f"
fi

if (( ADMIN_INIT_NEEDED == 1 )); then
    log "初始化管理员账号"
    compose_prod exec -T backend python manage.py init_admin \
        --username "$ADMIN_USERNAME" \
        --password "$ADMIN_PASSWORD" \
        --email "$ADMIN_EMAIL"

    umask 077
    {
        printf 'ADMIN_USERNAME=%s\n' "$ADMIN_USERNAME"
        printf 'ADMIN_PASSWORD=%s\n' "$ADMIN_PASSWORD"
        printf 'ADMIN_EMAIL=%s\n' "$ADMIN_EMAIL"
    } > "$CREDENTIAL_FILE"
    chmod 600 "$CREDENTIAL_FILE"
    if [[ -n "${SUDO_UID:-}" && -n "${SUDO_GID:-}" ]]; then
        chown "$SUDO_UID:$SUDO_GID" "$CREDENTIAL_FILE"
    fi
else
    log "检测到已有管理员凭证，跳过管理员初始化"
fi

cat <<EOF

部署完成

访问地址：${SERVER_PROTOCOL}://${SERVER_HOST}:${FRONTEND_PORT}
管理员账号：${ADMIN_USERNAME}
管理员凭证：${CREDENTIAL_FILE}
环境配置：${ENV_FILE}

常用命令：
  查看状态：cd ${BUSINESS_DIR} && docker compose ps
  查看日志：cd ${BUSINESS_DIR} && docker compose logs -f backend frontend
  停止服务：cd ${BUSINESS_DIR} && docker compose down
  更新部署：sudo bash ${SCRIPT_PATH} --host ${SERVER_HOST}

注意：
  - 管理员密码保存在权限为 600 的凭证文件中，请妥善备份。
  - 重复执行不会自动轮换 MySQL/Redis 密码。
  - 公网部署请在前端端口前配置 HTTPS 证书和反向代理。
EOF
