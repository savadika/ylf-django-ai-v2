# 验证记录

| 验收项 | 状态 | 证据 |
| --- | --- | --- |
| AC-001 | PASS | `test_project_structure.py` 校验 business 下业务代码、部署、文档、脚本和配置全部存在。 |
| AC-002 | PASS | 结构测试校验根目录旧业务路径全部不存在，固定协议入口保留。 |
| AC-003 | PASS | 质量命令输出显示 Ruff、Django 和前端均使用 `business/` 路径；CI、Dev Container 和文档已同步。 |
| AC-004 | PASS | quick 通过 29 个测试；full 已从新路径执行并保留依赖缺失的真实失败报告。 |
