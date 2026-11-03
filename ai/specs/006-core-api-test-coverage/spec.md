---
id: SPEC-006
title: 用户角色菜单部门核心 API 测试覆盖
status: done
owner: project-maintainer
created: 2026-11-02
updated: 2026-11-02
---

# 用户角色菜单部门核心 API 测试覆盖

## 背景与问题

`user`、`role`、`menu`、`department` 是系统权限链路的核心，但现有测试主要覆盖少量序列化器、
模型关联和工具函数。仓库质量门禁从根目录执行 Django 测试时只发现工具测试，没有执行这些应用的
测试；单独执行时，HTTPS 安全设置又会让使用普通 HTTP 测试客户端的登录和认证用例得到 301。

结果是覆盖率数字不能证明核心 API 可用，CRUD、权限拒绝、登录鉴权、角色授权和菜单树等关键路径
缺少可重复的行为证据。

## 目标

- 通过真实 REST API 接缝测试用户、角色、菜单、部门四个模块的主要成功与失败路径。
- 为每个测试类准备独立、可读的测试用户、角色和权限数据，不依赖生产数据库或外部 Redis。
- 覆盖登录、JWT 鉴权、CRUD、分页筛选、角色授权、菜单树和关联数据清理。
- 让 `python ai/quality/quality.py full` 的 `backend-tests` 门禁实际发现并执行四个业务应用测试。
- 将四个模块及共享鉴权/工具层的后端覆盖率提高到可审计的水平。
- 验证前端用户、角色、菜单、部门 API 适配器的 URL、HTTP 方法和请求参数契约。

## 非目标

- 不新增业务功能，不改变现有接口路径和响应信封格式。
- 不重写前端页面，也不修复本次范围外的既有前端 lint 错误。
- 不连接真实 MySQL、Redis、生产账号或外部服务。

## 用户故事

- 作为维护者，我希望核心系统管理 API 有完整回归测试，从而在改动权限逻辑时及时发现破坏。
- 作为后端开发者，我希望测试用户和权限夹具可复用，从而快速编写可读的接口测试。
- 作为发布负责人，我希望质量门禁真正执行应用测试，从而避免“测试通过”但业务测试根本没跑。

## 验收标准

- [x] AC-001 用户、角色、菜单、部门的主要 REST 端点都有鉴权、成功路径和关键失败路径测试。
  验证：`manage.py test user role menu department` 与 `verification.md` 中的用例清单。
- [x] AC-002 用户登录与 JWT、角色菜单授权、菜单树和删除关联清理均有端到端行为测试。
  验证：四个应用的 Django `TestCase` 与覆盖报告。
- [x] AC-003 测试使用独立测试用户/角色/权限夹具，可在内存 SQLite 和本地缓存中重复执行。
  验证：测试连续运行两次且结果一致，无外部数据库或 Redis 依赖。
- [x] AC-004 质量门禁的 `backend-tests` 明确指定全部本地业务应用，工具测试能验证该命令组成。
  验证：`python -m unittest ai.quality.tests.test_cli` 与 full 门禁报告。
- [x] AC-005 四个模块及共享权限/菜单工具的后端行覆盖率不低于 75%，全量应用测试通过。
  验证：`coverage run ...`、`coverage report` 和 `verification.md`。
- [x] AC-006 前端四个 API 适配器的全部导出函数都有契约测试，覆盖 URL、HTTP 方法和请求数据。
  验证：`npm run test:unit -- --runInBand` 与前端覆盖率摘要。

## 约束与风险

- `test_settings.SECURE_SSL_REDIRECT=True` 保留，用于生产安全检查；接口测试客户端必须显式模拟 HTTPS。
- JWT 注销和登录锁定使用 Django cache；测试统一使用 locmem，不连接 Redis。
- 测试必须通过 API 观察行为，避免只调用 ViewSet/Serializer 私有实现。
- 前端 API 测试替换系统边界 `@/utils/request`，只验证对外请求契约，不模拟组件内部实现。
- 前端 lint 已清零；当前 full 为 10/10，后端和前端测试均通过。

## 变更记录

| 日期 | 变更 | 作者 |
| --- | --- | --- |
| 2026-11-02 | 创建核心 API 测试覆盖规格 | project-maintainer |
