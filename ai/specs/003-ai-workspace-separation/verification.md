# 验证记录

| 验收项 | 状态 | 证据 |
| --- | --- | --- |
| AC-001 | PASS | `test_project_structure.py` 校验 `ai/specs`、`ai/quality`、`ai/docs`、`ai/reports` 和 `ai/cockpit`。 |
| AC-002 | PASS | 结构测试确认旧的 `specs/`、`quality/`、`scripts/quality*`、根 `pyproject.toml` 和 `.quality` 无活动文件。 |
| AC-003 | PASS | AGENTS、pre-commit 和 GitHub Actions 均指向 `ai/quality/quality.py`。 |
| AC-004 | PASS | `python ai/quality/quality.py quick` 的 27 个工具测试和全部门禁通过。 |
| AC-005 | PASS | full 已通过新入口执行，并将依赖缺失造成的失败保留到 `ai/reports/report.json`。 |
