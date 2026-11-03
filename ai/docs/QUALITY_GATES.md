# 自动验证链

质量验证由一个入口驱动：`python ai/quality/quality.py <profile>`。命令会依次执行门禁，
生成 `ai/reports/report.json`，并刷新 `ai/cockpit/index.html`。任何必需门禁失败时进程返回非零状态。

## 验证档位

| 档位 | 适用场景 | 包含内容 |
| --- | --- | --- |
| `quick` | 编辑过程中的快速反馈、pre-commit | 工具测试、规格校验、文档链接、Python 语法 |
| `full` | 合并前的完整回归 | quick + Ruff 关键规则 + Django 系统检查 + 迁移漂移 + 后端全量测试与覆盖率 + 前端 lint + 前端全量单元测试与覆盖率 |
| `release` | 发布候选版本 | full + 前端生产构建 + Django 生产部署安全检查 |

默认使用本机运行时。也可以在已启动的开发容器中执行：

```bash
python ai/quality/quality.py full --backend-runtime docker --frontend-runtime docker
```

本机后端验证使用 Python 3.12 和 `business/.venv`，安装 `business/UniDjango/requirements-dev.txt`。测试使用
`UniDjango.test_settings`，数据库是内存 SQLite，缓存是本地内存，不需要 MySQL 或 Redis。
前端验证需要先在 `business/frontend/` 执行 `npm ci`。缺少依赖时门禁必须失败，报告会保留退出码和
原始错误，不能把未执行的门禁显示成通过。

开发后端镜像已通过 `INSTALL_DEV=true` 安装 Ruff、coverage 和 pre-commit；使用 Docker 后端
运行时会在临时容器中挂载完整仓库。前端 Docker 运行时要求 `frontend` 开发服务已经启动。

## 门禁规则

- `specs`：活动规格目录必须包含四件套；状态和日期合法；验收项与任务编号唯一；
  每项 `AC-xxx` 必须在 `verification.md` 中有证据；状态为 `done` 时所有检查项必须完成。
- `docs`：必需入口文档存在；文档使用 UTF-8；仓库内 Markdown 链接可解析。
- `backend-lint`：只启用 Python 语法和未定义名称等关键规则，作为逐步收紧 Ruff 的基线。
- `migrations`：执行 `makemigrations --check --dry-run`，模型变更必须有迁移。
- `backend-tests`：运行 Django 全部应用测试；覆盖率阈值来自 `ai/quality/policy.json`。
- `frontend-tests`：运行全部 Jest 用例；覆盖率收集包含页面、状态管理、路由、请求层和布局，
  阈值来自同一策略文件。
- `frontend-build`：使用生产模式编译，捕获只在打包阶段出现的错误。
- `deploy-check`：使用生产安全变量执行 `manage.py check --deploy`。

## 失败处理

1. 先读门禁输出的最后一段和 `ai/reports/report.json` 中的 `detail`。
2. 依赖缺失时按文档安装依赖；不要通过跳过门禁让报告变绿。
3. 覆盖率下降时先补行为测试；确需调整阈值时在规格和 `ai/quality/policy.json` 中同时说明原因。
4. 有意暂时跳过某个门禁时使用 CLI 的 `--skip`，报告会把状态标为 `skipped`，不会显示为通过。

常用命令：

```bash
python ai/quality/quality.py quick
python ai/quality/quality.py full
python ai/quality/quality.py release
python ai/quality/quality.py cockpit
python ai/quality/quality.py serve --port 8765
```

每个质量档位都会继续执行后续门禁，尽量在一轮中暴露全部问题。只有所有非跳过门禁通过时，
报告状态才是 `passed`；使用 `--skip` 后总状态为 `partial`，并保留被跳过门禁的名称。

CI 使用 `.github/workflows/quality.yml` 在 PR 和主分支推送时运行 `full`，标签构建时运行
`release`。本地可安装 `pre-commit` 后执行 `pre-commit install`，使每次提交先运行 `quick`。
