# 验证记录

| 验收项 | 状态 | 证据 |
| --- | --- | --- |
| AC-001 | PASS | `test_production_build_avoids_inline_runtime_scripts_ac_001` 在修复前失败、修复后通过；`ScriptExtHtmlWebpackPlugin` 和内联规则已移除，`runtimeChunk('single')` 保留。 |
| AC-002 | PASS | 生产构建生成 `runtime.229b109d.js`；`dist/index.html` 的 4 个 `<script>` 全部带 `src`，内联数量为 0；release 最终复验。 |

## 质量门禁

- `business\.venv\Scripts\python.exe ai/quality/quality.py quick`：PASS，4/4。
- `business\.venv\Scripts\python.exe ai/quality/quality.py full`：PASS，10/10。
- `npm run build:prod`：PASS。
- `business\.venv\Scripts\python.exe ai/quality/quality.py release`：最终复验。
