# CI/CD 发布与回滚

## 发布模型

- 普通分支和 Pull Request 只运行质量检查。
- 推送 `v*` 标签后依次执行 `validate → release → publish → deploy`。
- `publish` 将前后端镜像推送到 GHCR，并使用 image digest 生成
  `release-manifest.json`。
- 当前生产服务器为 x86_64，CI 只构建 `linux/amd64` 镜像；若要支持 ARM64，
  需要重新启用并验证多架构构建。
- `publish` 同时生成 `deployment-bundle.tgz`，包含本次发布清单、生产 Compose
  及部署/回滚脚本，避免服务器继续依赖手工 `git pull`。
- `deploy` 默认关闭。只有仓库变量 `ENABLE_AUTO_DEPLOY=true` 时才连接生产
  服务器。
- 服务器不重新构建应用镜像。日常发布由
  `business/scripts/deploy-release.sh` 拉取清单中的固定镜像。

## 首次启用

1. 在 Rocky Linux 主机准备项目目录并完成一次基础部署：

```bash
sudo bash business/scripts/deploy-rocky.sh --host 你的服务器IP或域名
```

2. 在 GitHub 仓库中创建名为 `production` 的 Environment，建议配置 required
   reviewers。

3. 设置仓库变量：

```text
ENABLE_AUTO_DEPLOY=true
DEPLOY_PATH=/路径/到/ylf-django-v2
PRODUCTION_URL=https://你的域名
```

4. 设置 `production` Environment secrets：

```text
DEPLOY_HOST
DEPLOY_PORT
DEPLOY_USER
DEPLOY_SSH_KEY
DEPLOY_KNOWN_HOSTS
GHCR_USERNAME
GHCR_TOKEN
```

`DEPLOY_SSH_KEY` 是部署私钥。`DEPLOY_KNOWN_HOSTS` 可用
`ssh-keyscan -p <端口> <主机>` 生成。`GHCR_TOKEN` 只需要读取 packages 的
权限，用于服务器拉取私有镜像。

5. 首次发布：

```bash
git tag v1.0.0
git push origin v1.0.0
```

## 发布产物

GitHub Actions 的 `release-manifest` artifact 中包含：

- release id；
- 完整 commit SHA；
- 前后端镜像的 immutable digest；
- 来源 Git ref；
- 创建时间。

服务器把成功清单保存在 `business/releases/<release-id>.json`，当前和上一
版本分别记录在 `current-release` 与 `previous-release`。

## 人工部署

从 Actions artifact 下载发布清单后执行：

```bash
sudo bash business/scripts/deploy-release.sh /path/to/release-manifest.json
```

部署脚本会在任何应用切换前备份 MySQL 到
`business/backups/releases/<release-id>/`，然后拉取固定镜像、执行迁移、
启动新容器并检查 `/healthz/` 和前端首页。

## 回滚

回滚到上一成功版本：

```bash
sudo bash business/scripts/rollback-release.sh
```

回滚到指定版本：

```bash
sudo bash business/scripts/rollback-release.sh v1.0.0
```

回滚使用已有发布清单和固定镜像，不重新构建。若新版本执行了与旧代码不兼容
的数据库迁移，应用回滚后还需要人工从发布前备份恢复数据库。自动流程不会
静默恢复数据库，以免覆盖发布后新增的数据。

发布清单可用下面的命令校验：

```bash
python3 business/scripts/release_manifest.py validate release-manifest.json
```

## 数据库迁移约束

为保留回滚能力，破坏性数据库变更必须拆成多次发布：

1. 先增加可空字段或新表，保持旧代码可运行；
2. 发布读取新结构的应用版本；
3. 稳定后再单独发布删除旧结构的版本。

不要在一次发布中同时删除字段和切换应用代码。
