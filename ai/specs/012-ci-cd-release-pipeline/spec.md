---
id: SPEC-012
title: CI/CD 发布、部署与回滚流水线
status: done
owner: project-maintainer
created: 2026-11-03
updated: 2026-11-03
---

# CI/CD 发布、部署与回滚流水线

## 背景与问题

仓库已有提交和 Pull Request 的质量检查，也会在版本标签上运行 release
门禁，但尚未构建和推送固定版本镜像、生成发布清单，也没有服务器部署和自动
回滚入口。服务器当前仍使用 `latest` 镜像并现场构建，因此无法可靠证明某个
线上版本对应哪份代码，也无法快速恢复上一个可用版本。

## 目标

- 版本标签通过 release 门禁后，自动构建并推送前后端固定版本镜像。
- 每次发布生成一份可机器读取、可存档的发布清单。
- 服务器根据发布清单拉取固定镜像，部署前备份数据库并执行健康检查。
- 健康检查失败时自动切回上一个成功版本，也提供人工回滚命令。
- 自动上线必须显式开启并绑定受保护的 GitHub production 环境。

## 非目标

- 本次不升级 Vue、Axios 或其他业务依赖。
- 本次不改造 MySQL 应用账号，也不实现数据库结构自动降级。
- 本次不提供 Kubernetes、蓝绿双写或零停机发布。
- 本次不保存真实服务器地址、SSH 私钥或镜像仓库令牌。

## 用户故事

- 作为维护者，我希望推送版本标签后自动得到可追溯的镜像和发布清单。
- 作为运维人员，我希望一条命令部署指定版本，失败时能自动恢复上一版。
- 作为发布负责人，我希望没有生产环境凭证或未显式开启自动上线时，流水线
  不会误改生产服务器。

## 验收标准

- [x] AC-001 只有 tag 上的 release 门禁通过后才构建并推送 GHCR 前后端镜像，镜像标签包含发布版本和提交 SHA，不把 `latest` 作为发布产物。
  验证：`ReleasePipelineContractTests` 与 GitHub Actions workflow 静态契约测试。
- [x] AC-002 CI 生成发布清单，记录 release id、commit SHA、两个镜像 digest、创建时间和来源标签，并作为 artifact 保留。
  验证：`test_release_manifest_round_trip_ac_002` 与 workflow artifact 契约测试。
- [x] AC-003 部署脚本只消费发布清单，先备份已有 MySQL，拉取固定 digest 镜像，禁止现场构建，并在前后端健康后记录当前和上一版本。
  验证：`ReleasePipelineContractTests` 与 Bash 语法检查（环境有 Bash 时执行）。
- [x] AC-004 新版本健康检查失败时自动使用上一份成功发布清单恢复；人工回滚可以显式指定历史 release，失败时返回非零。
  验证：`ReleasePipelineContractTests` 覆盖失败分支和回滚入口。
- [x] AC-005 自动上线仅在仓库变量 `ENABLE_AUTO_DEPLOY=true` 且受保护 `production` 环境提供必要 secrets 时执行；未开启时只发布镜像和清单，不连接服务器。
  验证：GitHub Actions workflow 静态契约测试和部署文档。
- [x] AC-006 README 和运维文档说明首次启用、正常发布、人工回滚、数据库备份与恢复边界及必需 secrets。
  验证：文档链接检查和关键词契约测试。
- [x] AC-007 release 门禁在生产安全检查出现 warning 时失败，测试配置使用足够长度的随机特征密钥，不再存在 W009 假通过。
  验证：`test_release_check_fails_warnings_ac_007` 和 release 门禁输出。

## 约束与风险

- 生产服务器需要一次性配置 GHCR 只读凭证、部署用户 SSH 权限和项目路径。
- 初始版本构建 `linux/amd64` 与 `linux/arm64`；后续由 SPEC-014 根据实际
  x86_64 服务器收敛为单架构构建。
- 自动回滚只恢复应用镜像，不自动回滚数据库。破坏性迁移必须先备份，并按
  “先兼容、后删除”的方式分开发布。
- 当前 Windows 工作区缺少 Bash、Docker 和真实生产主机，Shell 语法与真实
  SSH 部署需要在 CI 或 Rocky Linux 主机完成最终验证。

## 变更记录

| 日期 | 变更 | 作者 |
| --- | --- | --- |
| 2026-11-03 | 创建 CI/CD 发布与回滚规格 | project-maintainer |
