---
id: SPEC-010
title: 前端 Lint 清零与完整质量门禁闭环
status: done
owner: project-maintainer
created: 2026-11-02
updated: 2026-11-02
---

# 前端 Lint 清零与完整质量门禁闭环

## 背景与问题

当前 `full` 质量门禁为 9/10，唯一失败项是前端 lint。该失败同时阻塞 SPEC-001、002、005、006
的最终验收，使已经实现的工程能力仍显示为 `blocked`。

## 目标

- 清除 `business/frontend/src` 的 ESLint 错误，并尽可能清除可自动修复的警告。
- 保持现有前端行为与 56 项前端测试通过。
- 运行完整 `full` 门禁并达到 10/10。
- 在前端 lint 通过后将 SPEC-001、002、005、006 更新为 `done`，同步验收项和验证证据。

## 非目标

- 不升级 Vue 2、Element UI、Axios 或 Webpack。
- 不新增业务功能，不改变后端接口或数据库结构。
- 不为既有页面补充大规模组件测试。

## 验收标准

- [x] AC-001 前端 ESLint 不再报告 errors，自动修复后仍无未处理或静默降级规则。
  验证：`eslint --ext .js,.vue src` 与输出。
- [x] AC-002 前端 Jest 全量测试继续通过，覆盖率不低于现有阈值。
  验证：`quality.py full` 的 `frontend-tests` 门禁。
- [x] AC-003 `full` 10/10 门禁全部通过。
  验证：`ai/reports/report.json` 与命令输出。
- [x] AC-004 SPEC-001、002、005、006 更新为 `done`，所有验收项和证据保持一致。
  验证：`python ai/quality/quality.py quick` 和 `verification.md`。

## 约束与风险

- 自动修复属于机械格式变更，人工修改只用于未使用变量、直接 API 调用和常量循环等语义问题。
- 必须保留用户/角色/菜单/部门的现有请求路径和测试行为。
- 如 lint 修复暴露真实回归，应先补测试再修改实现。

## 变更记录

| 日期 | 变更 | 作者 |
| --- | --- | --- |
| 2026-11-02 | 创建质量门禁闭环规格 | project-maintainer |
