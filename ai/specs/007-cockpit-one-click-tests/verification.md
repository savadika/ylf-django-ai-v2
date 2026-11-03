# 验证记录

| 验收项 | 状态 | 证据 |
| --- | --- | --- |
| AC-001 | PASS | Chrome 实际点击后按钮进入运行态并显示两项结果；按钮文字中心偏移为 0px。 |
| AC-002 | PASS | `test_test_runner.py` 通过 4 项：成功解析 91/56、超时降级、并发拒绝、失败输出限长；真实接口返回 91+56。 |
| AC-003 | PASS | `test_test_server.py` 通过 3 项；真实无请求头 POST 返回 403，带专用请求头返回 200。 |
| AC-004 | PASS | Chrome file 模式检查：按钮 `disabled`，状态为 `unavailable`，提示先执行 `quality.py serve`。 |
| AC-005 | PASS | Chrome 实际点击结果：`passed`、147 项、11.10 秒；后端 91 项、前端 56 项均通过。 |

## 质量门禁

- `python ai/quality/quality.py quick`：PASS，4/4 门禁；工具测试 41 项通过。
- `business\.venv\Scripts\python.exe ai/quality/quality.py full`：FAIL，9/10 门禁。
- 通过：tool-tests、specs、docs、python-syntax、backend-lint、backend-check、migrations、
  backend-tests（91 项，85%）、frontend-tests（56 项）。
- 失败：`frontend-lint`，仍为范围外既有 230 个错误、308 个警告。
