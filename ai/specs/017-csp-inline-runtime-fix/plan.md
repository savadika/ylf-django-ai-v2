# 实现计划

## 方案

删除 `vue.config.js` 中 `ScriptExtHtmlWebpackPlugin` 的生产配置，保留
`splitChunks` 和 `runtimeChunk('single')`。重新执行生产构建，检查
`dist/index.html` 中每个 `<script>` 都有 `src`。

## 影响面

- 后端：无。
- 前端：runtime 从内联 HTML 改为独立静态文件。
- 数据与迁移：无。
- 部署与配置：需要重新构建并发布前端镜像。

## 验证策略

新增安全头回归测试，直接检查构建配置和存在的 `dist/index.html`；运行生产
构建、quick、full 和 release。

## 回滚方案

恢复 `ScriptExtHtmlWebpackPlugin` 配置，但 CSP 也必须同时调整；默认不建议
回滚到内联 runtime。
