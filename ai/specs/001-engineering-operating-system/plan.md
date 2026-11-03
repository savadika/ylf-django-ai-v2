# 实现计划

## 方案

以 `ai/quality/quality.py` 作为统一命令行入口，内部模块负责规格解析、文档检查、命令编排、报告与
驾驶舱渲染。质量策略集中放在 `ai/quality/policy.json`，验证器只消费这份策略。后端增加独立测试
设置，使用 SQLite 和 LocMemCache 消除外部服务依赖。

## 影响面

- 后端：新增测试设置；现有应用测试保持原位；补充部门模块和验证工具测试。
- 前端：复用现有 ESLint、Jest 和 Vue CLI 命令，生产构建只在 release 档执行。
- 数据与迁移：不改变业务模型；迁移漂移检查纳入 full 档。
- 部署与配置：新增 GitHub Actions、pre-commit 和质量产物目录忽略规则。

## 验证策略

- 规格和文档由 Python 解析器检查必需结构、编号和仓库内链接。
- 工具自身使用标准库 `unittest` 测试关键解析和渲染行为。
- 后端测试由 Django test runner 执行，覆盖率由 coverage.py 汇总。
- 前端测试由 Jest 执行，构建由 Vue CLI 生产配置验证。
- 所有结果写入 `ai/reports/report.json`，驾驶舱只读取这份报告。

## 回滚方案

质量工具和文档是增量文件，可整体移除。若新测试设置造成阻塞，可恢复使用已有 `make verify`
的容器测试入口；业务运行时代码不受本规格影响。
