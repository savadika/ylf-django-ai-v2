# 实现计划

## 方案

在 `deploy-rocky.sh` 中集中封装 Docker CE 仓库准备逻辑。优先下载阿里云
镜像的仓库定义和 GPG key，失败时尝试 Docker 官方源。下载使用 curl 重试，
成功后把仓库文件中的 `gpgkey` 改成本地 key 路径，再刷新 DNF 缓存并安装。
`DOCKER_CE_REPO_URL` 可显式覆盖首选仓库。

## 影响面

- 后端：无。
- 前端：无。
- 数据与迁移：无。
- 部署与配置：增强 Rocky Linux 首次安装和重复安装的 Docker 源可靠性。

## 验证策略

新增静态契约测试锁定重试、本地 key、镜像回退、环境变量覆盖和禁止跳过
签名；使用 Git Bash 执行 Shell 语法检查；运行完整质量门禁。

## 回滚方案

恢复原有的 `dnf config-manager --add-repo` 调用即可回滚；不会改变现有 Docker
软件包或数据。
