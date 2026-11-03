# 验证记录

| 验收项 | 状态 | 证据 |
| --- | --- | --- |
| AC-001 | PASS | `test_rocky_deployment.py` 通过；四个旧脚本已删除，Makefile 旧 `prod` 目标已移除，仅保留 `deploy-rocky.sh` 和开发 `dev.sh`。 |
| AC-002 | BLOCKED | 静态测试确认脚本包含 Docker CE/Compose、独立随机密钥、firewalld 和生产 Compose 启动逻辑；当前环境无 Bash/Docker/Rocky，未执行真实安装。 |
| AC-003 | BLOCKED | 静态测试确认 `db_data`/`redis_data` 保护、`600` 配置权限、管理员凭证复用，以及已有凭证时管理员参数必须配合 `--reset-admin`；待 Rocky 主机重复执行验证。 |
| AC-004 | BLOCKED | 静态测试确认 240 秒就绪检查同时验证迁移、`/healthz/` 和前端 HTTP，失败时输出日志并非零退出；待 Rocky 主机断网/失败场景验证。 |
| AC-005 | PASS | README、`OPERATION.md` 和工程结构文档只引用新入口；`quick` 4/4 通过，结构测试共 47 项（1 项 Bash 检查因环境缺失跳过）。 |

## 质量门禁

- `business\.venv\Scripts\python.exe ai/quality/quality.py quick`：PASS，4/4 门禁。
- `business\.venv\Scripts\python.exe ai/quality/quality.py full`：PASS，10/10 门禁；后端 100 项、前端 72 项测试通过。
- `business\.venv\Scripts\python.exe ai/quality/quality.py release`：PASS，12/12 门禁；生产构建通过。
- `bash -n business/scripts/deploy-rocky.sh`：未执行，当前 Windows 环境没有 Bash；脚本回归测试会自动在具备 Bash 的环境执行该项。
