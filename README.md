# UniDjango Framework

这是从原项目提取出的可复用 Django/Vue 管理框架，业务与 AI 工程资产分区维护。

## 目录结构

```text
.
├── ai/                       # AI 规格、质量工具、报告和驾驶舱
├── business/                 # 全部业务运行时和部署资产
│   ├── UniDjango/            # Django 后端
│   ├── frontend/             # Vue 2 管理后台
│   ├── docker/               # MySQL 镜像
│   ├── docs/                 # 业务运维和需求文档
│   ├── scripts/              # 一键部署与开发启动脚本
│   ├── docker-compose.yml
│   ├── docker-compose-dev.yml
│   ├── Makefile
│   └── .env.example
└── AGENTS.md                 # AI 与开发者入口
```

## 工程开发入口

行为改动遵循“规格 → 实现 → 验证”三个闸门。开始开发前先读
[AGENTS.md](AGENTS.md) 和 [AI 工程工作区](ai/README.md)。业务代码位于 `business/`；
AI 规格、工具、文档和报告统一位于 `ai/`。完整边界见
[项目结构](ai/docs/PROJECT_STRUCTURE.md)，尚未规格化的需求记录在
[待完善清单](business/docs/BACKLOG.md)。

本机首次运行完整门禁需要安装 Python 和前端开发依赖：

```bash
py -3.12 -m venv business\.venv
business\.venv\Scripts\python.exe -m pip install -r business/UniDjango/requirements-dev.txt
cd business/frontend
npm.cmd ci
cd ../..
```

常用命令：

```bash
python ai/quality/quality.py quick
python ai/quality/quality.py full
python ai/quality/quality.py release
python ai/quality/quality.py serve
```

也可以使用 `make -C ai quality-quick`、`make -C ai quality-full`、
`make -C ai quality-release` 和 `make -C ai serve`。每轮结果写入
`ai/reports/report.json`，并刷新 [开发驾驶舱](ai/cockpit/index.html)。门禁细节见
[自动验证链](ai/docs/QUALITY_GATES.md)。

## Rocky Linux 一键部署

支持 Rocky Linux 8/9/10、`x86_64` 和 `aarch64`。在仓库根目录执行：

```bash
sudo bash business/scripts/deploy-rocky.sh --host 你的服务器IP或域名
```

脚本会自动完成：

- 安装 Git、curl、OpenSSL、Python、firewalld、Docker Engine 和 Compose 插件；
- 启动并启用 Docker，只开放前端访问端口；
- 创建 `business/.env`，分别生成 Django、JWT、MySQL、Redis 随机密钥；
- 构建并启动生产 Compose，等待前后端就绪；
- 首次部署时创建管理员，并把管理员凭证写入 `business/.deploy-credentials`；
- 重复执行时保留已有数据库密码和管理员密码。

可选项：

```bash
# Docker Hub 访问受限时指定 registry mirror
sudo bash business/scripts/deploy-rocky.sh \
  --host 你的服务器IP或域名 \
  --mirror https://你的镜像地址

# 自定义前端端口、管理员账号或显式重置管理员
sudo bash business/scripts/deploy-rocky.sh \
  --host 你的服务器IP或域名 \
  --frontend-port 9530 \
  --admin-username admin \
  --admin-email admin@example.com \
  --reset-admin
```

部署完成后，脚本会输出访问地址和管理命令。管理员密码不会打印到终端：

```bash
sudo cat business/.deploy-credentials
```

生产数据保存在 `business/db_data/`、`business/redis_data/` 和
`business/UniDjango/media/`，删除容器不会删除这些目录。公网部署仍需在前端端口前配置 HTTPS。

开发环境与生产部署相互独立：

```bash
make -C business dev
make -C business dev-down
```

## CI/CD 发布与回滚

推送 `v*` 标签后，GitHub Actions 会先运行 `release` 门禁，再把前后端固定
版本镜像推送到 GHCR，并生成 `release-manifest.json`。生产自动上线默认关闭；
只有设置仓库变量 `ENABLE_AUTO_DEPLOY=true` 并在受保护的 `production`
Environment 中配置 SSH 与 GHCR secrets 后才会执行。

服务器日常发布使用清单驱动的 `deploy-release.sh`，回滚使用
`rollback-release.sh`。发布清单由 `release_manifest.py` 生成和校验，部署前
会备份 MySQL，健康检查失败时自动恢复上一版本。

```bash
git tag v1.0.0
git push origin v1.0.0
```

完整的首次启用、secrets、人工部署和数据库恢复边界见
[CI/CD 发布与回滚](business/docs/RELEASE.md)。

完整说明见 [business/docs/OPERATION.md](business/docs/OPERATION.md)。
