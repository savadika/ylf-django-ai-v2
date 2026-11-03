# 项目结构

本文件是仓库的结构地图。仓库分为 `business/` 业务区和 `ai/` AI 工程区两个明确边界。

## 顶层目录

```text
.
├── business/        全部业务运行时、部署和运维资产
│   ├── UniDjango/   Django 后端、后端测试、迁移和后端容器
│   ├── frontend/    Vue 2 管理端、前端测试、Nginx 和前端容器
│   ├── scripts/     一键部署和开发启动脚本
│   ├── docs/        业务运维与需求文档
│   ├── docker/      MySQL 等基础设施镜像
│   ├── docker-compose.yml
│   ├── docker-compose-dev.yml
│   ├── Makefile
│   └── .env.example
├── ai/              AI 规格、质量工具、测试、文档、报告和驾驶舱
├── .github/         GitHub Actions
├── .devcontainer/   VS Code 开发容器定义
├── .agents/         Codex 使用的共享技能库
├── .claude/         Claude Code 的技能入口
├── skills-lock.json AI 技能来源和版本锁定
├── AGENTS.md        AI 和开发者的仓库操作契约
└── README.md        项目入口
```

## 后端

`business/UniDjango/UniDjango/` 是 Django 项目配置；其余一级包按领域划分：

| 目录 | 职责 |
| --- | --- |
| `user/` | 用户、JWT、认证中间件和管理员初始化 |
| `role/` | 角色及用户角色关系 |
| `menu/` | 菜单、角色菜单关系和动态前端组件路径 |
| `department/` | 部门 |
| `log/` | 请求日志、异常日志和请求中间件 |
| `utils/` | 响应信封、ViewSet 基类、过滤、分页、上传、媒体 URL 等横切能力 |
| `media/` | 运行时上传媒体；仅默认头像作为种子资源保留 |

每个领域的 `tests.py` 或 `tests/` 是回归测试，`migrations/` 是数据结构的权威演进记录，均不得按“目录整洁”
理由删除。

## 前端

`business/frontend/` 采用 Vue 2 + Element UI。固定路由只包含登录、404 和根布局；业务页面由后端菜单的 `component`
字段动态加载。当前初始化命令使用的页面是：

```text
src/views/dashboard/index.vue
src/views/user/index.vue
src/views/role/index.vue
src/views/menu/index.vue
src/views/department/index.vue
src/views/log/index.vue
src/views/login/index.vue
src/views/404.vue
```

| 目录 | 职责 |
| --- | --- |
| `src/api/` | 业务 API 封装 |
| `src/components/` | 可复用组件 |
| `src/directive/` | 权限指令 |
| `src/layout/` | 侧边栏、顶栏和主布局 |
| `src/router/` | 固定路由 |
| `src/store/` | Vuex 用户、权限和应用状态 |
| `src/styles/` | 全局样式和共享 SCSS |
| `src/utils/` | 请求、认证、导出和格式化工具 |
| `tests/unit/` | Jest 单元测试 |
| `nginx/` | 生产环境静态资源和反向代理配置 |

新增业务页面时，应同时更新后端初始化菜单或数据库菜单、前端页面和 API，并在规格中覆盖两者之间的约定。

## 工程与验证

- `ai/README.md`：AI 工作区入口。
- `ai/quality/quality.py`：统一质量入口和驾驶舱静态服务。
- `ai/quality/qualitylib/`：规格解析、文档校验、门禁执行和驾驶舱渲染。
- `ai/quality/tests/`：验证工具和业务/AI 边界回归测试。
- `ai/specs/<NNN-slug>/`：每次行为改动的事实来源。
- `ai/reports/report.json`：最近一次质量报告，被驾驶舱读取。
- `ai/cockpit/index.html`：可提交、可直接浏览的静态驾驶舱。

根目录只保留工具协议强制要求的 AI 适配入口：`AGENTS.md`、`.agents/`、`.claude/`、
`.pre-commit-config.yaml` 和 `.github/workflows/quality.yml`。它们不得承载业务逻辑。

## 生成物和本地环境

以下内容不属于源码，不手工维护：

- `.venv/`、`__pycache__/`、`*.pyc`
- `business/frontend/node_modules/`、`business/frontend/dist/`
- `business/frontend/tests/unit/coverage/`
- `ai/reports/` 中的运行报告
- 数据库、上传文件和密钥环境变量

驾驶舱和 `ai/reports/report.json` 由 `ai/quality/quality.py` 生成。需要改变结论时重新运行门禁，
不能直接编辑结果。
