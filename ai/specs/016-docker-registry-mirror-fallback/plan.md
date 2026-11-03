# 实现计划

## 方案

为 `deploy-rocky.sh` 增加默认 mirror 列表和统一的 Registry v2 探测函数。
`--mirror` 指定的地址优先，其后追加默认 mirror。配置 `daemon.json` 时保留
现有 mirror，并把可达 mirror 去重前置。若所有 mirror 和 Docker Hub 直连都
不可达，在 Compose 构建前失败并给出明确提示。

## 影响面

- 后端：无。
- 前端：无。
- 数据与迁移：无。
- 部署与配置：自动维护 Docker daemon 的 `registry-mirrors`。

## 验证策略

静态契约测试验证默认 mirror、探测函数、用户优先、daemon.json 合并和失败
分支；使用 Bash 语法检查及完整质量门禁。

## 回滚方案

删除 `registry-mirrors` 中的自动 mirror 并恢复原 `daemon.json`，重启 Docker。
