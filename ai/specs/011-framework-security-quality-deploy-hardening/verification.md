# 验证记录

| 验收项 | 状态 | 证据 |
| --- | --- | --- |
| AC-001 | PASS | `UserProfileApiTests` 覆盖普通用户更新头像、改密后旧令牌失效、弱密码不撤销令牌和只更新当前用户；`full` 后端 100 项测试通过。 |
| AC-002 | PASS | `JwtAuthTests` 覆盖版本写入和 8 小时默认/可配置有效期；`JwtMiddlewareTests` 覆盖版本不匹配返回 401；改密后新登录可用。 |
| AC-003 | PASS | `auth.spec.js` 证明令牌只写 `sessionStorage`；`test_security_headers.py` 校验 CSP、frame、MIME、referrer、HSTS 和镜像复制；`release` 生产构建通过。 |
| AC-004 | PASS | Jest 14 个套件、72 项测试通过；全 `src` 收集范围内行覆盖率 43.56%，高于 20% 阈值。 |
| AC-005 | PASS | `test_rocky_deployment.py` 锁定“已有凭证 + 管理员参数 + 未显式重置”的失败分支；质量工具 54 项测试通过。 |
| AC-006 | PASS | Django 健康接口成功/缓存失败分支通过；部署脚本静态测试要求 `/healthz/`、数据库迁移检查和前端 HTTP 同时成功；`full` 10/10 通过。 |

## 质量门禁

- `business\.venv\Scripts\python.exe ai/quality/quality.py quick`：PASS，4/4。
- `business\.venv\Scripts\python.exe ai/quality/quality.py full`：PASS，10/10；后端 100 项测试、覆盖率 86%；前端 72 项测试、行覆盖率 43.56%。
- `business\.venv\Scripts\python.exe ai/quality/quality.py release`：PASS，12/12；生产构建完成。
- `release` 仍报告既有 `security.W009` 测试密钥告警；该问题属于后续质量门禁加固，不在本规格范围内。
- 当前 Windows 工作区没有 Bash、Docker 和 Nginx，未执行 `bash -n`、`docker build`、`nginx -t` 或 Rocky Linux 实机部署；SPEC-008 的真实主机证据仍未闭环。
