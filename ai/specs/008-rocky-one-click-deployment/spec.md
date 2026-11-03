---
id: SPEC-008
title: Rocky Linux 一键安装与部署
status: blocked
owner: project-maintainer
created: 2026-11-02
updated: 2026-11-02
---

# Rocky Linux 一键安装与部署

## 背景与问题

当前 Rocky Linux 部署分散在基础环境安装、环境变量初始化、生产启动、镜像源切换和 Makefile
命令中。多个脚本职责重叠，且旧脚本给 MySQL、Redis 和管理员复用同一个密码。新服务器需要一种
可重复执行、失败可诊断、默认安全的单入口部署方式。

## 目标

- 提供单个 Rocky Linux 8/9/10 部署脚本，自动安装 Docker Engine、Compose 插件和必要工具。
- 自动检测访问地址、生成独立随机密钥/密码、创建受限权限的配置文件并启动生产 Compose。
- 等待服务可用、初始化管理员、输出访问地址和后续管理命令。
- 重复执行时不覆盖已有数据库密码，不无故重置管理员密码。
- 删除被新入口取代的旧部署脚本、Makefile 生产目标和旧文档说明。

## 非目标

- 不自动申请域名或安装 TLS 证书；HTTPS 仍由外部反向代理或负载均衡负责。
- 不删除开发用 `docker-compose-dev.yml`、`scripts/dev.sh`、Dockerfile、Nginx 或 Compose 运行资产。
- 不在当前 Windows 工作机实际安装 Rocky Linux 系统包；通过静态检查和在 Rocky 主机上的手工验收。

## 用户故事

- 作为运维人员，我希望在全新 Rocky Linux 上执行一条命令就完成 Docker 安装和应用启动。
- 作为维护者，我希望重复部署不会替换已有数据库密码或管理员凭证。
- 作为安全负责人，我希望 Django、JWT、MySQL、Redis 使用不同的随机密钥，且配置文件权限受限。

## 验收标准

- [ ] AC-001 仅保留一个 Rocky Linux 一键部署入口，旧部署脚本和 Makefile 生产目标被删除。
  验证：`python -m unittest ai.quality.tests.test_rocky_deployment`。
- [ ] AC-002 脚本自动安装 Docker/Compose、生成独立密钥、配置端口和防火墙并启动生产服务。
  验证：脚本静态断言与 Rocky Linux 主机实际运行记录。
- [ ] AC-003 重复运行不会覆盖原数据库密码；管理员凭证仅在首次部署或显式重置时生成。
  验证：脚本逻辑检查和 Rocky Linux 主机重复执行记录。
- [ ] AC-004 启动后等待后端和前端就绪，失败时返回非零并输出定位命令。
  验证：脚本健康检查逻辑与主机实际运行。
- [ ] AC-005 README、操作文档和工程结构测试只引用新部署入口。
  验证：`python ai/quality/quality.py quick` 与 `rg` 检查。

## 约束与风险

- 脚本需要 root 权限执行；可通过 `sudo bash ...` 启动并自动完成 Docker 安装。
- Docker Hub 在部分网络不可达；提供 `--mirror` 可选项，不默认使用第三方镜像。
- 现有旧版数据目录若已用旧密码初始化，不允许脚本自动轮换密码，以免锁死数据库。
- 不包含域名证书签发，生产公网必须另配 TLS。
- 当前 Windows 工作区没有 Bash、Docker 和 Rocky Linux 目标主机，系统安装与真实启动无法在本机执行；
  恢复条件是在 Rocky Linux 8/9/10 测试机运行 `sudo bash business/scripts/deploy-rocky.sh`。

## 变更记录

| 日期 | 变更 | 作者 |
| --- | --- | --- |
| 2026-11-02 | 创建 Rocky Linux 一键部署规格 | project-maintainer |
