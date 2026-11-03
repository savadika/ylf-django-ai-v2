---
id: SPEC-017
title: 修复 CSP 阻止内联 Webpack runtime
status: done
owner: project-maintainer
created: 2026-11-03
updated: 2026-11-03
---

# 修复 CSP 阻止内联 Webpack runtime

## 背景与问题

生产构建通过 `ScriptExtHtmlWebpackPlugin` 将 Webpack runtime 内联到
`dist/index.html`。生产 Nginx 的 CSP 只允许 `script-src 'self'`，浏览器因此
阻止内联 runtime，Vue 应用无法启动。

## 目标

- runtime 保持为独立、同源的 JavaScript 文件。
- 构建结果中所有可执行 `<script>` 标签都必须具有 `src`。
- 保持严格 CSP，不增加 `script-src 'unsafe-inline'`。

## 非目标

- 不修改 Nginx CSP 的其他指令。
- 不升级 Vue 或调整代码分包结构。

## 用户故事

- 作为用户，我希望打开部署后的首页时应用可以正常加载并被 CSP 允许执行。

## 验收标准

- [x] AC-001 生产构建不再配置 runtime 内联，并保留独立 runtime chunk。
  验证：`test_production_build_avoids_inline_runtime_scripts_ac_001`。
- [x] AC-002 构建后的 `dist/index.html` 中不存在不带 `src` 的 `<script>`，且 CSP 不包含脚本 `unsafe-inline`。
  验证：同一回归测试、生产构建和 release 门禁。

## 约束与风险

- 已部署的旧前端镜像仍包含内联脚本，必须重新构建并部署。
- 不采用 CSP hash，因为 runtime 的 hash 会随每次构建变化。

## 变更记录

| 日期 | 变更 | 作者 |
| --- | --- | --- |
| 2026-11-03 | 移除生产 runtime 内联 | project-maintainer |
