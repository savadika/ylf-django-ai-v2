# AI 工程工作区

本目录集中存放 AI 辅助开发所需的规格、质量工具、测试、文档和可视化产物。产品运行时代码不放在这里。

## 边界

```text
ai/
├── specs/       规格驱动开发目录与模板
├── quality/     质量策略、CLI、内部模块和验证器测试
├── docs/        AI 协作、编码约定、质量门禁和驾驶舱说明
├── reports/     最近一次验证报告和后端覆盖率 JSON
└── cockpit/     静态开发驾驶舱
```

业务代码位于 `business/UniDjango/` 和 `business/frontend/`；部署配置、文档、脚本和 Compose
也全部位于 `business/`。

根目录的 `AGENTS.md`、`.agents/`、`.claude/`、`.pre-commit-config.yaml` 和
`.github/workflows/quality.yml` 是工具协议要求的适配入口。它们负责发现和转发，不承载业务逻辑。

## 常用命令

从仓库根目录执行：

```bash
python ai/quality/quality.py quick
python ai/quality/quality.py full
python ai/quality/quality.py release
python ai/quality/quality.py serve
```

也可以在 `ai/` 目录使用：

```bash
make quality-quick
make quality-full
make serve
```

规格、证据、失败详情和覆盖率分别写入 `ai/specs`、`ai/reports` 和 `ai/cockpit`。
