# ======================================================================
# UniDjango 一键验证 / 常用命令
#
# 默认针对开发编排（docker-compose-dev.yml）操作后端容器。
# 生产部署统一使用 scripts/deploy-rocky.sh。
# 默认执行全部本地业务应用；指定范围：make test TEST=user
# ======================================================================

COMPOSE_FILE ?= docker-compose-dev.yml
COMPOSE      := docker compose -f $(COMPOSE_FILE)
DEV_COMPOSE  := docker compose -f docker-compose-dev.yml
BACKEND      := backend
PY           := $(COMPOSE) exec -T $(BACKEND) python manage.py
TEST         ?= user role menu department log
ARGS         ?=

.PHONY: help dev dev-up dev-down dev-logs up down logs check check-deploy migrate makemigrations test verify shell wait-db deploy

.DEFAULT_GOAL := help

help:
	@echo "UniDjango 常用命令（默认开发编排）："
	@echo "  make dev          启动开发环境"
	@echo "  make dev-down     停止开发环境"
	@echo "  make up           启动服务（默认开发环境）"
	@echo "  make down         停止服务（默认开发环境）"
	@echo "  make logs         查看后端日志"
	@echo "  make check        运行 Django 系统检查"
	@echo "  make check-deploy 运行部署安全检查 (check --deploy)"
	@echo "  make migrate      执行数据库迁移"
	@echo "  make makemigrations  生成迁移 (可加 APP=user)"
	@echo "  make test         运行测试 (可加 TEST=user)"
	@echo "  make verify       一键验证：check → migrate → test"
	@echo "  make shell        进入 Django shell"
	@echo "  make deploy       一键安装并部署到 Rocky Linux (ARGS='--host ...')"

dev: dev-up

dev-up:
	$(DEV_COMPOSE) up -d

dev-down:
	$(DEV_COMPOSE) down

dev-logs:
	$(DEV_COMPOSE) logs -f $(BACKEND)

up:
	$(DEV_COMPOSE) up -d

down:
	$(DEV_COMPOSE) down

logs:
	$(DEV_COMPOSE) logs -f $(BACKEND)

check:
	$(PY) check

check-deploy:
	$(PY) check --deploy

migrate:
	$(PY) migrate --noinput

makemigrations:
	$(PY) makemigrations $(APP)

test:
	$(PY) test $(TEST)

# 等待 MySQL 就绪（复用后端容器内的 wait-for-mysql.sh，之后只执行 true）
wait-db:
	$(COMPOSE) exec -T $(BACKEND) /wait-for-mysql.sh true

# 一键验证：先确保服务已启动并等待 MySQL，再依次执行 check → migrate → test
verify: up wait-db
	@echo "==> [1/3] Django 系统检查"
	$(PY) check
	@echo "==> [2/3] 数据库迁移"
	$(PY) migrate --noinput
	@echo "==> [3/3] 单元测试"
	$(PY) test
	@echo "✅ 全部通过：check + migrate + test"

shell:
	$(COMPOSE) exec $(BACKEND) python manage.py shell

deploy:
	sudo bash scripts/deploy-rocky.sh $(ARGS)
