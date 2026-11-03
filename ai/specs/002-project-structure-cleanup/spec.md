---
id: SPEC-002
title: 项目结构梳理与无效文件清理
status: done
owner: project-maintainer
created: 2026-11-02
updated: 2026-11-02
---

# 项目结构梳理与无效文件清理

## 背景与问题

仓库由 Django 后端、Vue 2 前端、Docker 部署和 AI 工程工具组合而成。前端仍保留上游管理模板的演示页面、
未被加载的 mock 服务和旧 CI 配置，本机验证还产生了可删除的环境与字节码缓存。这些内容扩大了目录噪声，
也让维护者难以判断哪些文件属于真实产品能力。

## 目标

- 用一份项目结构文档说明顶层目录、业务模块、工程工具和生成物边界。
- 删除未被代码、配置、迁移或文档引用的脚手架演示和过期文件。
- 保留动态菜单、业务页面、部署、迁移、测试和 AI 协作能力。
- 用自动化结构检查防止已删除的演示入口重新混入。

## 非目标

- 不重构 Django 应用边界，不修改业务接口、模型或迁移。
- 不删除当前可用的业务页面、AI 技能库或部署文件。
- 不改变前端构建工具链或 UI 设计。

## 用户故事

- 作为项目维护者，我希望打开仓库就能分辨产品代码、工程工具和生成物。
- 作为 AI 编码代理，我希望避免把模板演示页误认为业务模块。

## 验收标准

- [x] AC-001 仓库提供项目结构文档，覆盖后端、前端、规格、质量工具、部署和生成物。
  验证：`python ai/quality/quality.py quick` 与 `ai/docs/PROJECT_STRUCTURE.md`。
- [x] AC-002 未接入的模板演示页面、mock 服务、旧 Travis 配置和上游模板文档被删除。
  验证：`ai/quality/tests/test_project_structure.py`。
- [x] AC-003 初始化系统需要的业务页面、动态路由、Docker/Nginx 和 AI 技能入口继续存在。
  验证：`ai/quality/tests/test_project_structure.py` 与前端引用检查。
- [x] AC-004 清理后 quick 门禁通过，驾驶舱同步反映新的规格和代码资产。
  验证：`python ai/quality/quality.py quick` 与 `ai/cockpit/index.html`。
- [x] AC-005 清理后的前端依赖锁文件一致，并能完成 lint、Jest 和生产构建。
  验证：`npm ci`、`npm run lint`、`npm run test:unit -- --coverage` 与 `npm run build:prod`。

## 约束与风险

- 菜单组件路径由数据库驱动；本次只删除初始化命令未使用的演示组件，保留 `system/index` 兼容映射。
- 当前锁文件环境下 lint、Jest 和生产构建均已通过；Python 字节码目录仍是生成物。
- full 全部门禁已通过，后续如构建失败应恢复失败状态，不能用静态检查替代真实构建。

## 变更记录

| 日期 | 变更 | 作者 |
| --- | --- | --- |
| 2026-11-02 | 创建项目结构清理规格 | project-maintainer |
