# 实现计划

## 方案

继续复用 GitHub Actions 现成的质量门禁。tag 流水线先运行 `release`，再构建
后端和前端镜像并推送到 GHCR。构建结果与发布清单保存在同一个 artifact
中，部署 job 通过受保护的 `production` 环境读取 SSH 和 GHCR 凭证。

服务器侧新增两个职责单一的脚本：

- `deploy-release.sh`：校验清单、备份数据库、拉取 digest 镜像、启动、健康
  检查、记录版本；失败时调用回滚脚本恢复上一版。
- `rollback-release.sh`：从本地 release 清单取出固定镜像，禁止构建，重新
  启动并做同样的健康检查。

生产 Compose 使用 `${BACKEND_IMAGE}` 和 `${FRONTEND_IMAGE}`，不再把应用
镜像固定为 `latest`。发布清单生成器使用 Python 标准库，便于 CI 和服务端
共同校验。

## 影响面

- 后端：无业务代码和接口变更。
- 前端：无业务代码和接口变更。
- 数据与迁移：部署前新增 MySQL 备份；不自动执行数据库回滚。
- 部署与配置：新增 release workflow job、发布清单工具、部署和回滚脚本，
  修改生产 Compose、环境变量模板和运维文档。

## 验证策略

- 用静态契约测试锁定 workflow、Compose、脚本和文档中的关键安全边界。
- 用 Python 单元测试验证发布清单生成、校验和拒绝非法 digest。
- 在 CI 中用 Docker Buildx 实际构建发布镜像；在真实 Rocky 主机启用
  `ENABLE_AUTO_DEPLOY` 后执行首次自动部署和人工回滚演练。
- 运行 quick、full 和 release 门禁，保留 `ai/reports/report.json`。

## 回滚方案

发布脚本在切换前把当前 manifest 记录为 previous，成功后更新 current。
健康检查失败时自动用 previous 重启固定镜像。数据库若发生不兼容迁移，应用
回滚后仍需由运维人员从发布前备份恢复；这是显式高风险操作，不在自动流程中
静默执行。
