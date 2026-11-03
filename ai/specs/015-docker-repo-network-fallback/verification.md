# 验证记录

| 验收项 | 状态 | 证据 |
| --- | --- | --- |
| AC-001 | PASS | `test_docker_repo_network_fallback_ac_001` 验证 curl 重试、`rpm --import`、本地 key 路径和 DNF 重试参数；Bash 语法检查通过。 |
| AC-002 | PASS | 同一测试验证环境变量覆盖、阿里云→官方源回退顺序，并断言不存在 `--nogpgcheck`。 |
| AC-003 | PASS | README 与 OPERATION 包含回退说明、`DOCKER_CE_REPO_URL`、排查命令，并通过 docs 门禁。 |

## 质量门禁

- `business\.venv\Scripts\python.exe ai/quality/quality.py quick`：PASS，4/4。
- `business\.venv\Scripts\python.exe ai/quality/quality.py full`：PASS，10/10。
- `business\.venv\Scripts\python.exe ai/quality/quality.py release`：最终复验。

## 残余风险

- 当前 Windows 工作区不能执行真实 `dnf` 和 `rpm --import`，需要在 Rocky Linux
  服务器上重新上传脚本并验证镜像源回退与安装事务。
