# 仓库操作契约

本文件是 AI 和开发者进入仓库后的入口。开始任何会改变行为、接口、数据结构或部署方式的
改动前，按下面的顺序完成三个闸门。

1. **规格闸门**：在 `ai/specs/<NNN-slug>/` 创建或更新 `spec.md`、`plan.md`、`tasks.md`、
   `verification.md`。流程见 [ai/specs/README.md](ai/specs/README.md)。纯错别字和无语义格式修复可跳过。
2. **实现闸门**：先读 [ai/docs/CODING_STANDARDS.md](ai/docs/CODING_STANDARDS.md)，按规格和任务实施。
   Bug 修复先补能稳定复现问题的测试；接口、模型或权限变更必须有回归测试。
3. **验证闸门**：从仓库根目录运行 `python ai/quality/quality.py quick`。交付行为改动前运行
   `python ai/quality/quality.py full`；发布相关改动还要运行 `python ai/quality/quality.py release`。
   未执行的验证必须在交付说明中写明原因，不能把“没跑”写成“通过”。

规格中的每个 `AC-xxx` 必须在 `verification.md` 里有证据行，代码中的测试尽量在名称或注释里
引用对应的 `AC-xxx`。生成物 `ai/reports/report.json` 和 `ai/cockpit/index.html` 由验证器维护，
直接改这两个文件不会改变质量结论。

AI 工程工作区入口见 [ai/README.md](ai/README.md)。质量门禁、运行模式和故障处理见
[ai/docs/QUALITY_GATES.md](ai/docs/QUALITY_GATES.md)。需要查看项目现状、规格进度和最近一次验证结果时，
运行 `python ai/quality/quality.py serve` 打开开发驾驶舱，使用说明见
[ai/docs/COCKPIT.md](ai/docs/COCKPIT.md)。
    