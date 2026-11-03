---
id: SPEC-001
title: 工程化长期复用基线
status: done
owner: project-maintainer
created: 2026-11-02
updated: 2026-11-02
---

# 工程化长期复用基线

## 背景与问题

项目已有 Django 后端、Vue 前端和部分回归测试，但编码约定、规格流程、全量验证和项目状态视图
分散在开发者记忆中。随着功能和 AI 协作次数增加，容易出现规格缺失、测试范围不完整、迁移漂移
以及“本地通过但无法复核”的问题。

## 目标

- 新成员和 AI 能从仓库文档确定编码规则、规格流程和交付标准。
- 行为改动有可追踪的规格、任务、验收项和验证证据。
- 一条命令覆盖静态检查、后端测试、前端测试、迁移和发布构建。
- 项目状态、规格进度和质量结果可以在浏览器中直接查看。

## 非目标

- 本次不重写现有业务模块，也不追求立即达到 100% 代码覆盖率。
- 本次不接入外部项目管理、代码托管或监控平台。
- 驾驶舱不读取生产数据库和真实密钥。

## 用户故事

- 作为项目维护者，我希望在开发前明确行为边界，从而减少返工。
- 作为 AI 编码代理，我希望从固定入口读取规则和验证命令，从而稳定交付。
- 作为开发者，我希望一次查看规格进度与质量门禁，从而快速判断项目是否可合并或发布。

## 验收标准

- [x] AC-001 仓库根目录存在 AI 可发现的编码约定、规格流程和验证入口。
  验证：`python ai/quality/quality.py quick` 与 `ai/docs/CODING_STANDARDS.md`。
- [x] AC-002 活动规格具备 spec、plan、tasks、verification 四件套，验收项可追踪到证据。
  验证：`python ai/quality/quality.py quick` 与 `ai/reports/report.json`。
- [x] AC-003 quick、full、release 三档验证链可执行，并能生成机器可读报告。
  验证：`python ai/quality/quality.py --help`、脚本单元测试与 CI 工作流。
- [x] AC-004 full 档覆盖 Django 全量测试、前端 lint/全量单元测试和覆盖率阈值。
  验证：`.github/workflows/quality.yml` 与 `ai/reports/report.json` 的 gate 列表。
- [x] AC-005 开发驾驶舱由仓库真实数据和最近验证报告生成，静态 HTML 可直接浏览。
  验证：`python ai/quality/quality.py cockpit` 与 `ai/cockpit/index.html`。
- [x] AC-006 提交前与持续集成均自动运行质量门禁，失败结果可定位。
  验证：`.pre-commit-config.yaml`、`.github/workflows/quality.yml` 和报告 detail。

## 约束与风险

- 当前环境可能没有 Docker、Python 依赖或 Node 依赖；验证器必须给出可执行的失败提示。
- 初始覆盖率阈值作为防回退基线，后续按功能风险逐步提高。
- CI 供应商绑定为 GitHub Actions；迁移到其他平台时复用同一个 Python 验证入口。
- 当前依赖环境已可执行 full；后续依赖缺失时必须恢复环境而不是跳过门禁。

## 变更记录

| 日期 | 变更 | 作者 |
| --- | --- | --- |
| 2026-11-02 | 创建工程化基线规格 | project-maintainer |
