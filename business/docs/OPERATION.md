# UniDjango 操作与部署

业务代码、容器和部署资产都位于 `business/`。以下命令从仓库根目录执行。

## 1. Rocky Linux 一键部署

支持 Rocky Linux 8/9/10、`x86_64` 和 `aarch64`。首次部署：

```bash
sudo bash business/scripts/deploy-rocky.sh --host 你的服务器IP或域名
```

脚本会自动：

1. 安装 `git`、`curl`、OpenSSL、Python、firewalld 和必要系统工具；
2. 添加 Docker CE 仓库，安装 Docker Engine、Buildx 和 Compose 插件；
3. 启动并启用 Docker，把执行 `sudo` 的普通用户加入 `docker` 组；
4. 创建 `business/.env`，分别生成 Django、JWT、MySQL、Redis 随机密钥；
5. 自动识别或写入访问 IP/域名，只开放前端端口；
6. 停止冲突的开发编排，构建并启动生产编排；
7. 等待前端和后端就绪，首次部署时初始化管理员；
8. 将管理员凭证写入 `business/.deploy-credentials`。

### 1.1 可选参数

```bash
sudo bash business/scripts/deploy-rocky.sh \
  --host 192.168.1.20 \
  --frontend-port 9530
```

```bash
sudo bash business/scripts/deploy-rocky.sh \
  --host app.example.com \
  --protocol https
```

```bash
# Docker Hub 访问受限时指定可信镜像代理
sudo bash business/scripts/deploy-rocky.sh \
  --host 192.168.1.20 \
  --mirror https://docker.m.daocloud.io
```

其他参数：

- `--admin-username`：管理员用户名，默认 `admin`
- `--admin-email`：管理员邮箱，默认 `admin@example.com`
- `--admin-password`：管理员密码；不传则自动生成
- `--reset-admin`：显式重置管理员和密码
- `--skip-firewall`：不修改 firewalld

查看完整帮助：

```bash
sudo bash business/scripts/deploy-rocky.sh --help
```

### 1.2 管理员凭证

管理员密码不会输出到终端：

```bash
sudo cat business/.deploy-credentials
```

凭证文件和 `business/.env` 的权限都是 `600`，并已加入 `.gitignore`。

### 1.3 重复部署和更新

修改代码后，重新执行同一个命令：

```bash
sudo bash business/scripts/deploy-rocky.sh --host 你的服务器IP或域名
```

脚本会保留已有的 MySQL、Redis、Django、JWT 密钥和管理员密码，只重新构建并启动服务。

已有 `business/.deploy-credentials` 时，任何管理员参数都必须和
`--reset-admin` 一起使用。只传 `--admin-email`、`--admin-username` 或
`--admin-password` 会在任何配置写入前终止，避免非预期重置密码。

如果检测到已有数据库目录但密码仍是空值或 `change-me`，脚本会终止而不会自动轮换密码，
避免把现有数据库锁死。

## 2. 日常运维

```bash
cd business
docker compose ps
docker compose logs -f backend frontend
docker compose restart backend
docker compose down
```

重新启动已部署服务：

```bash
cd business
docker compose up -d
```

部署脚本通过以下公开健康接口确认数据库和缓存均可用：

```text
http://127.0.0.1:8002/healthz/
```

生产编排只在宿主机回环地址暴露后端；健康接口同时要求数据库 `SELECT 1`
和缓存读写成功，任一依赖失败都会返回 HTTP 503。

### 2.1 数据目录

```text
business/
├── db_data/                 MySQL 数据
├── redis_data/              Redis 数据
├── UniDjango/media/         上传文件
├── .env                     环境变量和随机密钥
└── .deploy-credentials      管理员凭证
```

删除容器不会自动删除这些目录。迁移服务器前必须同时备份以上数据。

### 2.2 端口

| 服务 | 默认端口 | 暴露方式 |
|---|---:|---|
| 前端 | `9530` | Docker 发布到宿主机 |
| 后端 | `8002` | 仅绑定宿主机回环地址 |
| MySQL | `3309` | 仅绑定宿主机回环地址 |
| Redis | `6380` | 仅绑定宿主机回环地址 |

生产请求链路：

```text
浏览器
  └─> 前端端口 :9530
        ├─> Nginx 静态资源
        ├─> /prod-api/ -> backend:8000
        └─> /media/ -> 上传文件
```

## 3. 开发环境

开发环境继续使用 `docker-compose-dev.yml`：

```bash
make -C business dev
```

或：

```bash
cd business
docker compose -f docker-compose-dev.yml up -d
```

开发环境使用 Django `runserver` 和 Vue dev server，并挂载源码支持热重载。

运行全部后端业务测试：

```bash
make -C business test
```

只测试某个模块：

```bash
make -C business test TEST=user
```

停止开发环境：

```bash
make -C business dev-down
```

开发环境与生产环境共用容器名，不能同时运行。一键部署会先停止冲突的开发容器。

## 4. 安全和网络

- 生产公网必须在前端端口前配置 HTTPS 证书和反向代理；部署脚本不自动申请证书。
- Docker Hub 镜像代理需要由运维选择可信来源，脚本不会默认写入第三方镜像。
- MySQL、Redis 和后端端口在生产编排中只绑定 `127.0.0.1`，外部只访问前端端口。
- JWT 默认有效 8 小时，可通过 `JWT_EXPIRATION_SECONDS` 调整；密码修改或管理员重置后，
  该用户已有令牌立即失效。
- 浏览器只在当前标签页的 `sessionStorage` 保存 JWT，关闭标签页后不会自动恢复。
- 生产 Nginx 统一发送 CSP、HSTS、禁止 iframe、MIME 嗅探保护和 referrer 策略。
- `.env` 和管理员凭证不能提交到 Git，也不能放入工单、聊天记录或构建日志。
- 建议定期备份数据库、Redis 和媒体目录，并验证恢复流程。

## 5. CI/CD 发布与回滚

日常生产发布不再在服务器执行 `git pull` 后重新构建。推送 `v*` 标签后，CI
会运行 release 门禁、构建并推送固定 digest 镜像、生成
`release-manifest.json`。设置 `ENABLE_AUTO_DEPLOY=true` 后，受保护的
`production` Environment 会调用 `business/scripts/deploy-release.sh` 完成
备份、部署和健康检查。

人工回滚使用 `business/scripts/rollback-release.sh`。发布清单可通过
`business/scripts/release_manifest.py` 校验。完整配置、必需 secrets 和数据库
恢复边界见 [CI/CD 发布与回滚](RELEASE.md)。

## 6. Docker CE 安装源容错

`deploy-rocky.sh` 会优先下载阿里云 Docker CE 仓库和 GPG key，失败时自动
回退 Docker 官方源。下载使用 curl 重试，GPG key 保存到本地后写入仓库文件，
DNF 仍执行完整签名校验。

如需指定内部可信镜像仓库：

```bash
sudo DOCKER_CE_REPO_URL=https://mirrors.example/docker-ce.repo \
  bash business/scripts/deploy-rocky.sh --host 你的服务器IP或域名
```

如果两个来源都失败，先检查：

```bash
curl -I https://mirrors.aliyun.com/docker-ce/linux/centos/docker-ce.repo
curl -I https://download.docker.com/linux/centos/docker-ce.repo
dnf repolist
```
