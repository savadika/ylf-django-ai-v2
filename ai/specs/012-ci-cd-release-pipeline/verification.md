# 验证记录

| 验收项 | 状态 | 证据 |
| --- | --- | --- |
| AC-001 | PASS | `ReleasePipelineContractTests` 验证 release→publish 顺序、GHCR、digest 和禁止 `latest`；当前 x86_64 单架构由 SPEC-014 约束。 |
| AC-002 | PASS | `test_release_manifest_round_trip_ac_002`、非法 release id 和未固定 digest 拒绝测试通过；workflow 上传 `release-manifest` 与 `deployment-bundle` artifact。 |
| AC-003 | PASS | 部署脚本契约测试确认清单校验、`mysqldump`、固定镜像 pull、`--no-build`、迁移、健康检查及 current/previous 记录；本机无 Bash/Docker，真实 Shell 与容器执行待 CI/Rocky 主机。 |
| AC-004 | PASS | 契约测试验证健康失败调用 `rollback-release.sh`，人工回滚只消费清单且禁止现场构建；失败分支返回非零。 |
| AC-005 | PASS | workflow 静态契约验证 `ENABLE_AUTO_DEPLOY=true`、`production` environment、SSH/GHCR secrets 和 deploy 并发锁。 |
| AC-006 | PASS | README、OPERATION 与 RELEASE 文档通过 `docs` 门禁，并包含首次启用、发布、回滚、secrets 和数据库恢复边界。 |
| AC-007 | PASS | `test_release_check_fails_warnings_ac_007` 通过；release 使用 `--fail-level WARNING`，`deploy-check` 输出 0 issues、0 silenced。 |

## 质量门禁

- `business\.venv\Scripts\python.exe ai/quality/quality.py quick`：PASS，4/4。
- `business\.venv\Scripts\python.exe ai/quality/quality.py full`：PASS，10/10。
- `business\.venv\Scripts\python.exe ai/quality/quality.py release`：PASS，12/12。
- 发布工具测试 67 项通过、2 项因无 Bash 跳过；后端 100 项、前端 72 项通过。
- Manifest CLI 创建与校验往返成功；workflow 和 Compose YAML 解析成功。
- 未执行：Bash 语法、Docker Buildx 发布镜像构建、GHCR 推送和真实 Rocky Linux SSH 部署。当前 Windows 工作区没有 Bash/Docker，也没有生产环境 secrets；需推送版本标签并配置 `production` Environment 后完成端到端验证。
