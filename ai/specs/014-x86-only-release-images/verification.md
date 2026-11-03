# 验证记录

| 验收项 | 状态 | 证据 |
| --- | --- | --- |
| AC-001 | PASS | `test_tag_pipeline_publishes_after_release_gate_ac_001` 在修改前因 `linux/arm64` 失败，修改后通过；前后端均为 `platforms: linux/amd64`，QEMU 已移除。 |
| AC-002 | PASS | RELEASE 文档已注明仅支持 x86_64；`quick` 4/4、`full` 10/10 通过，release 最终复验。 |

## 残余风险

- 当前发布镜像不再支持 ARM64；未来切换服务器架构时必须重新启用并验证。
