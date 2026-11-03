---
id: SPEC-014
title: 发布镜像仅构建 x86_64
status: done
owner: project-maintainer
created: 2026-11-03
updated: 2026-11-03
---

# 发布镜像仅构建 x86_64

## 背景与问题

生产服务器固定为 x86_64。release workflow 当前同时构建 `linux/amd64` 和
`linux/arm64`，ARM64 依赖 QEMU 模拟，导致前端镜像构建时间显著增加。

## 目标

- GitHub Actions 只构建 X86_64 Docker 镜像。
- 回归测试锁定单一 `linux/amd64` 平台，避免重新引入 ARM64 构建。
- 发布文档明确说明当前生产镜像只支持 x86_64。

## 非目标

- 不移除部署脚本中的架构检测。
- 不支持 ARM64 生产服务器。
- 不改变应用代码、镜像内容或回滚流程。

## 用户故事

- 作为维护者，我希望发布流水线与实际 X86_64 服务器匹配，减少等待时间。

## 验收标准

- [x] AC-001 release workflow 的前后端镜像都只构建 `linux/amd64`，不再包含 `linux/arm64`。
  验证：`test_tag_pipeline_publishes_after_release_gate_ac_001` 与 workflow 内容检查。
- [x] AC-002 发布文档明确当前 CI 产物仅支持 x86_64，`quick`、`full`、`release` 继续通过。
  验证：文档关键词契约测试和 quality release。

## 约束与风险

- 若未来切换 ARM64 服务器，必须重新增加并验证 arm64 镜像构建。
- 已经开始的旧 workflow run 不会读取新提交，必须等它完成或取消后重新打标签。

## 变更记录

| 日期 | 变更 | 作者 |
| --- | --- | --- |
| 2026-11-03 | 将发布镜像限定为 x86_64 | project-maintainer |
