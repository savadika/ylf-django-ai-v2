---
id: SPEC-004
title: 业务代码迁入统一 business 工作区
status: done
owner: project-maintainer
created: 2026-11-02
updated: 2026-11-02
---

# 业务代码迁入统一 business 工作区

## 背景与问题

AI 工程资产已集中到 `ai/`，但 Django、Vue、部署脚本、Compose、Makefile 和业务文档仍分散在仓库根目录。
这与“业务归 business、AI 归 ai”的目标不一致。

## 目标

- 将全部业务运行时、业务文档和业务运维资产迁入 `business/`。
- 保持 `ai/` 为唯一的 AI 工程工作区。
- 根目录仅保留 Git、编辑器、AI 发现和项目入口等固定协议文件。
- 更新质量工具、CI、Dev Container、文档链接和运行命令。

## 非目标

- 不修改 Django 接口、模型、迁移或 Vue 页面行为。
- 不移动 `.git*`、`AGENTS.md`、`.agents/`、`.claude/`、`.github/`、`.devcontainer/` 和
  `skills-lock.json` 等固定入口。
- 不改变质量门禁内容和覆盖率阈值。

## 用户故事

- 作为项目维护者，我希望根目录一眼看到 `business/` 和 `ai/` 两个边界。
- 作为开发者，我希望业务启动和运维命令集中在 `business/`。
- 作为 AI 编码代理，我希望从根入口进入 AI 工作区，并准确找到业务根目录。

## 验收标准

- [x] AC-001 `business/` 包含 `UniDjango`、`frontend`、`docker`、`docs`、`scripts`、
  Compose、Makefile 和 `.env.example`。
  验证：`ai/quality/tests/test_project_structure.py`。
- [x] AC-002 根目录不再包含上述业务目录和文件，固定协议入口保留。
  验证：`ai/quality/tests/test_project_structure.py`。
- [x] AC-003 质量工具、CI、Dev Container、脚本和文档全部使用 `business/` 新路径。
  验证：`python ai/quality/quality.py quick` 与路径引用检查。
- [x] AC-004 迁移后业务代码和 AI 代码的测试、报告与驾驶舱仍可运行。
  验证：`python ai/quality/quality.py quick` 与 `python ai/quality/quality.py full`。

## 约束与风险

- 当前没有 Git 元数据，移动后不能依赖本地版本历史回滚。
- Docker 和真实前后端依赖未安装，full 的业务执行仍可能受环境限制，但必须保留真实失败。
- 所有移动均在已校验的当前工作区内执行，不覆盖已有目标。

## 变更记录

| 日期 | 变更 | 作者 |
| --- | --- | --- |
| 2026-11-02 | 创建业务工作区迁移规格 | project-maintainer |
