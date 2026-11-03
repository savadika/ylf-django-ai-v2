---
id: SPEC-013
title: 修复干净检出的报告目录检查
status: done
owner: project-maintainer
created: 2026-11-03
updated: 2026-11-03
---

# 修复干净检出的报告目录检查

## 背景与问题

本地质量检查会生成 `ai/reports/`，因此目录通常已经存在。该目录又被
`.gitignore` 整体忽略，导致 GitHub Actions 全新检出时目录不存在，项目结构
测试 `test_ai_workspace_owns_engineering_surfaces` 在执行实际质量门禁前失败。

## 目标

- 干净 Git 检出也包含一个可追踪的 `ai/reports` 占位文件。
- 质量报告本身继续作为生成物被忽略。
- 增加回归测试，避免以后再次把该目录完全从版本控制中排除。

## 非目标

- 不提交 `report.json`、覆盖率 JSON 或其他生成报告。
- 不改变质量门禁、部署或业务行为。

## 用户故事

- 作为维护者，我希望本地已生成报告不会掩盖 GitHub Actions 的全新检出问题。

## 验收标准

- [x] AC-001 干净检出的仓库包含 `ai/reports/.gitkeep`，且该文件不会被 `.gitignore` 排除。
  验证：`test_reports_placeholder_survives_clean_checkout_ac_001` 与 `.gitignore` 检查。
- [x] AC-002 实际报告文件仍被忽略，`quick`、`full`、`release` 门禁通过。
  验证：项目结构测试和 `business\.venv\Scripts\python.exe ai/quality/quality.py release`。

## 约束与风险

- `.gitkeep` 只负责建立目录，不代表任何报告需要提交。
- `ai/reports/*` 的忽略规则与占位文件白名单顺序不能颠倒。

## 变更记录

| 日期 | 变更 | 作者 |
| --- | --- | --- |
| 2026-11-03 | 创建干净检出 CI 修复规格 | project-maintainer |
