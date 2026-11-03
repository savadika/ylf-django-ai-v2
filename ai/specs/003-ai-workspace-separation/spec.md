---
id: SPEC-003
title: 业务代码与 AI 工程工作区分离
status: done
owner: project-maintainer
created: 2026-11-02
updated: 2026-11-02
---

# 业务代码与 AI 工程工作区分离

## 背景与问题

当前规格、质量验证器、AI 文档和质量报告散落在仓库根目录，与 Django、Vue 和部署代码并列。
维护者难以区分产品运行时代码与 AI 辅助工程系统，也不利于后续单独替换或停用 AI 工作流。

## 目标

- 将业务运行时限制在 `UniDjango/`、`frontend/` 和部署配置中。
- 将 AI 规格、质量工具、测试、文档、报告和驾驶舱集中到顶层 `ai/`。
- 保留工具强制要求的根目录适配入口，并让它们只承担发现和转发职责。
- 更新所有命令、文档链接、CI、pre-commit 和驾驶舱路径。

## 非目标

- 不改变 Django 接口、模型、迁移或 Vue 业务页面。
- 不改变质量门禁内容、覆盖率阈值或验证档位。
- 不移动 `.agents/`、`.claude/`、`.github/` 等必须从仓库根发现的工具目录。

## 用户故事

- 作为项目维护者，我希望打开仓库就能分清产品代码与 AI 工程资产。
- 作为 AI 编码代理，我希望从根入口进入统一 AI 工作区，并找到规格和质量命令。

## 验收标准

- [x] AC-001 顶层 `ai/` 集中包含规格、质量工具、质量测试、AI 文档、报告和驾驶舱。
  验证：`ai/docs/PROJECT_STRUCTURE.md` 与结构测试。
- [x] AC-002 业务目录不再包含 AI 规格、质量脚本、质量策略或 AI 报告。
  验证：结构测试与仓库路径检查。
- [x] AC-003 根目录 AI 发现入口继续有效，并指向 `ai/` 工作区和新的质量命令。
  验证：`AGENTS.md`、`.pre-commit-config.yaml`、GitHub Actions 与 CLI 测试。
- [x] AC-004 迁移后的 quick 门禁通过，报告和驾驶舱生成到 `ai/`。
  验证：`python ai/quality/quality.py quick`。
- [x] AC-005 迁移后的 full 门禁可执行；若依赖缺失，报告保留真实失败原因。
  验证：`python ai/quality/quality.py full`。

## 约束与风险

- Codex、Claude、GitHub Actions 和 pre-commit 对入口路径有固定要求，因此这些根目录适配文件不能完全移动。
- 当前环境缺少 Django、Ruff、coverage、ESLint 和 Jest，full 的恢复条件与 SPEC-001 相同。
- 根目录没有 Git 元数据，文件移动通过补丁执行，必须逐个验证导入、链接和测试路径。

## 变更记录

| 日期 | 变更 | 作者 |
| --- | --- | --- |
| 2026-11-02 | 创建 AI 工作区分离规格 | project-maintainer |
| 2026-11-02 | 业务资产后续由 SPEC-004 迁入 `business/` | project-maintainer |
