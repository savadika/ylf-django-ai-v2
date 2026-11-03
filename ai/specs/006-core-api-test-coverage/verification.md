# 验证记录

| 验收项 | 状态 | 证据 |
| --- | --- | --- |
| AC-001 | PASS | `manage.py test user role menu department log`：91 项通过；四个应用覆盖匿名、越权、CRUD、分页筛选、详情及关键失败路径。 |
| AC-002 | PASS | 用户登录/JWT/注销、角色菜单授权、菜单树、用户角色与角色菜单删除清理均有 HTTP 行为测试。 |
| AC-003 | PASS | `core_test_support.py` 创建独立测试用户/角色/权限，使用内存 SQLite 与 locmem cache；连续执行 91 项业务测试均通过。 |
| AC-004 | PASS | `python -m unittest ai.quality.tests.test_cli`：5 项通过；full 报告命令与 `business/Makefile` 默认值均包含 `user role menu department log`，后端工具测试共 33 项通过。 |
| AC-005 | PASS | full 的 `backend-tests` 通过：91 项测试、合计行覆盖率 85%；department 100%、role 100%、menu views 100%、user views 99%。 |
| AC-006 | PASS | Jest：8 个套件、56 项测试通过；新增 28 个核心 API 契约测试，前端行覆盖率 33.74%，高于 20% 阈值。 |

## 质量门禁

- `python ai/quality/quality.py quick`：PASS，4/4 门禁。
- `business\.venv\Scripts\python.exe ai/quality/quality.py full`：PASS，10/10 门禁。
- backend-tests：91 项测试、行覆盖率 85%；frontend-tests：56 项测试、行覆盖率 33.74%；
  frontend-lint：0 错误、0 警告。
