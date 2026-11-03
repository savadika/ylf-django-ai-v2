# 实现计划

## 方案

新增 `business/scripts/deploy-rocky.sh`，按以下阶段执行：

1. 检查 Rocky Linux、架构、root 权限和磁盘空间。
2. 安装基础包，配置 Docker CE 仓库，安装并启用 Docker/Compose。
3. 可选写入 Docker registry mirror，重新启动并验证 Docker。
4. 创建或校验 `business/.env`，按需生成 Django、JWT、MySQL、Redis 独立随机密钥。
5. 写入服务器地址、允许 Host、前端端口，并收紧文件权限。
6. 停止冲突的开发 Compose，校验并启动生产 Compose。
7. 等待后端迁移和前端 HTTP 就绪，首次部署时初始化管理员。
8. 输出访问地址、凭证路径、日志、停止和更新命令。

删除被替代的 `setup-rocky.sh`、`bootstrap.sh`、`prod.sh`、`switch-docker-mirror.sh`，移除
Makefile 中的生产目标，并重写 README 和操作文档中的部署章节。保留 `dev.sh` 和开发编排。

## 影响面

- 后端：无运行时代码改动。
- 前端：无。
- 数据与迁移：无；部署脚本不修改已有数据库密码。
- 部署与配置：新增唯一 Rocky Linux 部署入口；生产 Compose、Dockerfile 和 Nginx 作为运行资产保留。

## 验证策略

- 使用 Python 回归测试固定新脚本入口、旧脚本删除、文档引用和关键安全命令。
- 若环境存在 Bash，则执行 `bash -n business/scripts/deploy-rocky.sh`；当前 Windows 环境没有 Bash 时明确记录未执行。
- 运行 `python ai/quality/quality.py quick` 和 full，记录仓库级结果。
- 在 Rocky Linux 主机按验收步骤实际执行首次部署和重复部署。

## 回滚方案

删除新脚本并恢复旧脚本即可回到原部署方式；已启动的 Compose 服务、数据库卷和 `.env` 不受脚本删除
影响。若部署在启动阶段失败，保留 `.env` 和容器日志用于诊断，不删除数据卷。
