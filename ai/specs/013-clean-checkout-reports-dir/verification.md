# 验证记录

| 验收项 | 状态 | 证据 |
| --- | --- | --- |
| AC-001 | PASS | `test_reports_placeholder_survives_clean_checkout_ac_001` 在修复前失败、修复后通过；`git check-ignore` 确认 `.gitkeep` 不被忽略。 |
| AC-002 | PASS | 同一测试确认 `report.json` 仍被忽略；`quick` 4/4、`full` 10/10 通过，release 门禁最终复验。 |

## 残余风险

- 新增文件必须先提交并推送；本地已有一个未跟踪的 `ai/reports/` 目录不能替代 GitHub 全新检出验证。
