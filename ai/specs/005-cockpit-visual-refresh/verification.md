# 验证记录

| 验收项 | 状态 | 证据 |
| --- | --- | --- |
| AC-001 | PASS | `python -m unittest ai.quality.tests.test_cockpit`：4 项通过；1440px Chrome 布局检查显示状态区顶部 105px、指标区顶部 452px，内容区 636px，核心状态位于首屏。 |
| AC-002 | PASS | 390px Chrome 布局检查：视口 390px、文档 `clientWidth=375` 且 `scrollWidth=375`，hero/指标/规格均重排为单列，横向溢出为 `false`。 |
| AC-003 | PASS | `test_cockpit.py` 覆盖未验证态、失败态、HTML 转义；实际生成页 HTTP 返回 200，并保留规格、门禁、覆盖率、资产、命令及失败详情。 |
| AC-004 | PASS | `test_dashboard_assets_remain_self_contained_ac_004` 通过；生成 HTML 无外部 `<script src>`、`<link>`、`@import` 或 `http(s)://` 资源地址。 |

## 质量门禁

- `python ai/quality/quality.py quick`：PASS（4/4 门禁）。
- `python ai/quality/quality.py full`：PASS（10/10 门禁）。
- `business\.venv\Scripts\python.exe -m ruff check --config ai/quality/pyproject.toml ai/quality`：
  PASS，本次修改的 Python 工具代码无 Ruff 问题。
