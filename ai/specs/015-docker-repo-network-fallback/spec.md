---
id: SPEC-015
title: Docker CE 仓库网络重试与镜像回退
status: done
owner: project-maintainer
created: 2026-11-03
updated: 2026-11-03
---

# Docker CE 仓库网络重试与镜像回退

## 背景与问题

Rocky Linux 一键部署从 Docker 官方源下载 RPM 后，还会在线读取 GPG key。
服务器网络出现 `Curl error (35)` 时，安装事务失败；当前脚本没有重试、本地
GPG key 保存或镜像源回退，重复执行仍可能命中同一故障。

## 目标

- 下载 Docker CE 仓库定义和 GPG key 时带连接超时与重试。
- GPG key 先保存到本地，再让 YUM/DNF 从本地文件完成签名校验。
- 国内镜像不可用时回退 Docker 官方源，仍不可用时明确失败。
- 不使用 `--nogpgcheck`，不降低软件包校验要求。

## 非目标

- 不替代 Docker registry mirror。
- 不处理 Rocky Linux 基础仓库的网络故障。
- 不改变应用部署、镜像构建或回滚逻辑。

## 用户故事

- 作为运维人员，我希望 Docker 官方源短暂重置时，一键部署能自动换源继续。

## 验收标准

- [x] AC-001 脚本使用带重试的 curl 下载仓库文件和 GPG key，并保存到本地文件供 DNF 校验。
  验证：`test_docker_repo_network_fallback_ac_001` 静态契约测试。
- [x] AC-002 默认国内镜像失败时回退 Docker 官方源，并通过环境变量覆盖仓库地址；全程禁止 `--nogpgcheck`。
  验证：同一契约测试和 Bash 语法检查。
- [x] AC-003 README 和运维文档说明镜像源回退、覆盖变量及失败后的排查命令。
  验证：文档关键词契约测试。

## 约束与风险

- 镜像源仍必须使用 Docker 官方签名包，导入的 key 与镜像源中的包必须匹配。
- 当前 Windows 工作区只能做静态测试，真实 Rocky Linux 网络故障需在服务器复验。

## 变更记录

| 日期 | 变更 | 作者 |
| --- | --- | --- |
| 2026-11-03 | 增加 Docker CE 仓库重试与镜像回退 | project-maintainer |
