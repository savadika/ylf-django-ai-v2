# 验证记录

| 验收项 | 状态 | 证据 |
| --- | --- | --- |
| AC-001 | PASS | `CockpitDashboard.spec.js` 验证鉴权快照写入 `sandbox=""` 的 `srcdoc` iframe，旧随机指标未渲染；`npm run build:prod` 通过；无头 Chrome 在 `default-src 'self'` CSP 下实测 `srcdoc` 正常显示。默认菜单顺序为 0，登录根路由仍进入 `/dashboard`。 |
| AC-002 | PASS | `python ai/quality/quality.py full`：新增 API 测试覆盖 200、401、403、404；Django 105 项通过，`cockpit/views.py` 覆盖率 100%。 |
| AC-003 | PASS | `python -m unittest ai.quality.tests.test_cockpit -v`：8 项通过；验证嵌入式快照存在、无 `<script`、隐藏一键测试区，并继续生成 `ai/cockpit/index.html`。 |
| AC-004 | PASS | 菜单迁移测试验证名称为“驾驶舱”且路径/组件不变；独立驾驶舱一键测试与 API 范围测试通过；`python ai/quality/quality.py quick` 通过（72 项工具测试，规格、文档、语法门禁均通过）。 |

## 质量门禁

- `python ai/quality/quality.py quick`：PASS，4/4。
- `python ai/quality/quality.py full`：PASS，10/10；Django 105 项、Jest 75 项通过。
- `npm run lint`：PASS。
- `npm run build:prod`：PASS；仅有既有的大包体积告警。
- `python ai/quality/quality.py release`：未执行；本次不是发布或部署配置变更。
