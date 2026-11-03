# 实现计划

## 方案

以真实 HTTP URL 为测试接缝，使用 `APIClient`、JWT Authorization 头和显式 HTTPS scheme 调用
`/user`、`/role`、`/menu`、`/department`。测试准备阶段通过 ORM 创建用户、角色、菜单和关联，
但断言只观察 API 响应或 API 后续可观察结果。

新增测试专用夹具模块，提供测试用户、权限菜单、JWT 客户端和响应信封断言。按模块垂直扩展：
先补认证/CRUD 主路径，再补唯一性、密码、非法角色、非法菜单、权限拒绝和关联清理，最后用覆盖率
报告回头补未覆盖分支。

质量门禁的 Django 测试命令显式列出 `user role menu department log`，避免依赖当前工作目录的
默认测试发现行为。新增 CLI 测试固定这一行为。

前端为 `src/api/user.js`、`role.js`、`menu.js`、`department.js` 的公开导出写契约测试。测试
替换 `@/utils/request` 这一系统边界，断言每个调用生成的 URL、method、params/data，不读取组件
内部状态。Jest 覆盖率收集范围加入 `src/api`，让覆盖率报告包含这些适配器。

## 影响面

- 后端：四个应用测试、测试夹具、测试设置中的 JWT 密钥长度；质量测试命令。
- 前端：新增四个 API 适配器契约测试，并调整 Jest 覆盖率收集范围。
- 数据与迁移：无生产数据或迁移变更。
- 部署与配置：无生产配置变更；测试客户端模拟 HTTPS。

## 验证策略

- 每次新增行为测试先运行对应模块，确认失败原因或缺口，再补实现或测试夹具。
- 运行 `business/.venv/Scripts/python.exe business/UniDjango/manage.py test user role menu department log`
  验证业务测试可重复通过。
- 使用 coverage 配置生成四模块报告，检查行覆盖率和未覆盖行，针对性补齐关键分支。
- 运行 `python -m unittest ai.quality.tests.test_cli` 验证门禁命令包含本地业务应用。
- 运行前端 Jest 全量测试与覆盖率阈值，验证四个 API 适配器契约。
- 运行 quick 和 full；记录 full 中本次范围内外的真实结果。

## 回滚方案

测试和测试夹具可直接回退，不影响数据库结构。若显式测试标签导致旧环境不兼容，可恢复质量命令
并保留单独的模块测试命令；生产认证和权限实现无需回滚。
