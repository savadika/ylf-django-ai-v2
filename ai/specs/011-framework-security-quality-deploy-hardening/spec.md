---
id: SPEC-011
title: 个人中心、认证安全、前端覆盖与部署幂等加固
status: done
owner: project-maintainer
created: 2026-11-03
updated: 2026-11-03
---

# 个人中心、认证安全、前端覆盖与部署幂等加固

## 背景与问题

当前框架的个人中心复用管理员用户 CRUD 接口，普通用户没有 `system:user:edit`
时无法修改自己的头像或密码。JWT 默认有效七天，前端长期保存在 `localStorage`，
密码修改和重新初始化管理员不会使旧令牌失效，生产 Nginx 也未发送 CSP 等安全头。

前端覆盖率只统计 API、工具和少量组件，排除了页面、路由、状态管理和请求层，
使报告无法反映真实风险。Rocky Linux 部署脚本在已有管理员凭证时，只要传入任一
管理员参数就会重新生成密码，与“仅首次部署或显式重置时修改管理员”冲突。

## 目标

- 提供仅当前登录用户可用的个人资料接口，普通用户无需用户管理权限即可修改头像和密码。
- 缩短 JWT 有效期，并让密码修改或管理员重置立即使该用户已有令牌失效。
- 将前端令牌限制在当前标签页，并为生产前端响应增加基础安全头。
- 让前端覆盖率统计覆盖页面、路由、状态管理和请求层，并补充关键流程测试。
- 修复部署脚本管理员参数的非预期重置，并通过健康检查验证数据库、缓存和 HTTP 服务。

## 非目标

- 不在本次迁移 Vue 2、Element UI 或 Axios 的版本。
- 不引入 OIDC、刷新令牌、多设备会话管理或企业单点登录。
- 不替代 Rocky Linux 真实主机安装验收；该证据仍由 SPEC-008 跟踪。

## 用户故事

- 作为普通用户，我希望独立修改自己的头像和密码，从而不依赖管理员权限。
- 作为安全负责人，我希望密码变更后旧令牌立即失效，并减少 XSS 可持久窃取令牌的风险。
- 作为维护者，我希望前端覆盖率暴露核心页面和状态代码，从而尽早发现回归。
- 作为运维人员，我希望重复部署且只调整管理员邮箱时不会意外重置密码。

## 验收标准

- [x] AC-001 已登录用户无需 `system:user:edit` 即可通过个人资料接口修改自己的头像和密码，且不能借该接口修改其他用户。
  验证：`business\.venv\Scripts\python.exe business/UniDjango/manage.py test user --settings=UniDjango.test_settings`。
- [x] AC-002 JWT 使用可配置且不超过八小时的默认有效期；密码变更后携带旧版本的令牌返回 401，新登录令牌可正常使用。
  验证：`JwtAuthTests`、`JwtMiddlewareTests` 和 `UserProfileApiTests`。
- [x] AC-003 前端只在当前标签页保存登录令牌，生产镜像的 Nginx 配置包含 CSP、frame、MIME sniffing 和 referrer 安全头。
  验证：Jest 令牌存储测试、Nginx 配置静态测试和 `release` 生产构建。
- [x] AC-004 前端覆盖率统计包含 `src/views`、`src/store`、`src/router`、`src/permission.js`、请求层和布局层，关键认证与动态路由流程有自动化测试。
  验证：`ai/quality/tests/test_cli.py` 与 `business/frontend` Jest 覆盖率报告。
- [x] AC-005 已有管理员凭证时，传入管理员参数但未传 `--reset-admin` 会在任何写入前失败；只有首次部署或显式重置才会更新管理员密码。
  验证：`test_rocky_deployment.py`。
- [x] AC-006 部署脚本使用数据库、缓存和 HTTP 均成功的 `/healthz/` 作为后端就绪条件，失败时保持非零退出。
  验证：健康接口 Django 测试、部署脚本静态测试和 `full` 门禁。

## 约束与风险

- 新字段 `token_version` 需要数据库迁移；旧令牌没有版本字段时按版本 `0` 兼容。
- 修改密码后当前浏览器必须重新登录；这是有意的安全行为。
- 生产 CSP 需要兼容 Vue 2 和 Element UI 的内联样式，因此只对样式允许 `unsafe-inline`。
- Rocky Linux 实机安装、断网和重复部署证据仍无法在当前 Windows 工作区生成。

## 变更记录

| 日期 | 变更 | 作者 |
| --- | --- | --- |
| 2026-11-03 | 创建规格 | project-maintainer |
| 2026-11-03 | 完成实现、自动化验证和文档同步 | project-maintainer |
