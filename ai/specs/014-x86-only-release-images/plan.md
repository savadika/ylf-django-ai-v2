# 实现计划

## 方案

将后端和前端 `docker/build-push-action` 的 `platforms` 参数统一改成
`linux/amd64`，并更新发布文档与静态契约测试。

## 影响面

- 后端：镜像内容不变。
- 前端：镜像内容不变。
- 数据与迁移：无。
- 部署与配置：发布产物的目标架构限定为 x86_64。

## 验证策略

回归测试断言 workflow 仅包含 `linux/amd64`；运行 quick、full 和 release。

## 回滚方案

如需恢复双架构，重新加入 `linux/arm64` 并重新执行发布验证。
