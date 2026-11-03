# 任务

- [x] T001 新增禁止内联脚本的回归测试。
- [x] T002 移除生产构建 runtime 内联配置。
- [x] T003 重建前端并运行质量门禁。

## 完成定义

- [x] 所有验收项有自动化或可重复证据。
- [x] `business\.venv\Scripts\python.exe ai/quality/quality.py release` 通过。
- [x] 构建产物检查确认所有 `<script>` 都有 `src`。
