# 验证记录

| 验收项 | 状态 | 证据 |
| --- | --- | --- |
| AC-001 | PASS | `python ai/quality/quality.py quick`：`docs` 门禁检查必需文档、UTF-8 与本地链接并通过。 |
| AC-002 | PASS | quick 的 `specs` 门禁通过；`test_specs.py` 覆盖四件套、编号、重复项和证据映射。 |
| AC-003 | PASS | `test_runner.py` 覆盖通过/失败/跳过与报告写入；full 已执行并生成 `ai/reports/report.json`。 |
| AC-004 | PASS | `full` 10/10 通过：Django 91 项、前端 lint 0 错误、Jest 56 项和覆盖率阈值均通过。 |
| AC-005 | PASS | `python ai/quality/quality.py cockpit` 生成 `ai/cockpit/index.html`；`test_cockpit.py` 覆盖未验证和失败转义。 |
| AC-006 | PASS | `.pre-commit-config.yaml` 执行 quick；GitHub Actions 执行 full/release；CLI 测试校验 profile 门禁组成。 |
