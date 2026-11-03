---
id: SPEC-016
title: Docker Hub 镜像拉取自动回退
status: done
owner: project-maintainer
created: 2026-11-03
updated: 2026-11-03
---

# Docker Hub 镜像拉取自动回退

## 背景与问题

Rocky Linux 服务器无法连接 Docker Hub，生产构建在加载
`python:3.12-slim`、`mysql:8.0`、`node:22-alpine` 和
`nginx:stable-alpine` 元数据时超时。脚本虽然有 `--mirror` 参数，但未配置时
不会设置任何 registry mirror。

## 目标

- 默认探测多个 Docker Hub mirror，只写入可达的地址。
- 用户显式提供的 `--mirror` 保持最高优先级。
- mirror 都不可达时检查 Docker Hub 直连，并给出明确错误。
- 保留现有 `daemon.json` 配置，只将可达 mirror 放到优先位置。

## 非目标

- 不替换 Dockerfile 中的基础镜像。
- 不修改应用镜像仓库 GHCR。
- 不保证第三方公共 mirror 永久可用。

## 用户故事

- 作为运维人员，我希望未手动传入 `--mirror` 时部署脚本也能应对 Docker Hub
  在服务器网络上不可直达的情况。

## 验收标准

- [x] AC-001 脚本默认探测多个 Docker Registry mirror，并接受 Registry v2 的认证挑战响应。
  验证：`test_registry_mirror_default_fallback_ac_001` 静态契约测试。
- [x] AC-002 用户 `--mirror` 地址优先，多个可达 mirror 写入 `daemon.json` 且保留原有配置。
  验证：同一契约测试与 Bash 语法检查。
- [x] AC-003 没有可达 mirror 且 Docker Hub 直连失败时，脚本在构建前明确终止。
  验证：契约测试锁定失败提示和 `registry-1.docker.io` 探测。
- [x] AC-004 README 和运维文档说明默认 mirror、覆盖方式和失败排查。
  验证：文档关键词契约测试。

## 约束与风险

- 公共 mirror 属于外部依赖，可能随时变化或被限流。
- 当前环境只能验证地址可达和脚本契约，真实拉取需在 Rocky Linux 服务器测试。

## 变更记录

| 日期 | 变更 | 作者 |
| --- | --- | --- |
| 2026-11-03 | 增加 Docker Hub registry mirror 自动回退 | project-maintainer |
