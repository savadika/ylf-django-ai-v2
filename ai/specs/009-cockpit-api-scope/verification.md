# 验证记录

| 验收项 | 状态 | 证据 |
| --- | --- | --- |
| AC-001 | PASS | Chrome 实际点击：`beforeOpen=false`、`immediateOpen=true`、`finalOpen=true`。 |
| AC-002 | PASS | 页面包含用户、角色、菜单、部门四组，共 38 个 method/path；从 `POST /user/gen_token` 到 `GET /department/filter-options`。 |
| AC-003 | PASS | `test_test_runner.py` 通过，运行器结果的 `api_scope` 元数据包含 38 个接口组合。 |
