# 任务

- [x] T001 新增发布清单生成与校验工具及单元测试。
- [x] T002 将生产 Compose 改为固定镜像注入，并增加数据库健康检查。
- [x] T003 实现清单驱动的部署、数据库备份、健康检查和自动回滚脚本。
- [x] T004 实现人工回滚脚本和历史版本记录。
- [x] T005 扩展 GitHub Actions，在 release 门禁后构建推送发布镜像、发布清单并受控部署。
- [x] T006 更新环境模板、README、运维文档和静态契约测试。
- [x] T007 运行 quick、full、release 并记录验证证据和未执行项。

## 完成定义

- [x] 所有验收项有自动化或可重复证据。
- [x] `business\.venv\Scripts\python.exe ai/quality/quality.py full` 通过。
- [x] `business\.venv\Scripts\python.exe ai/quality/quality.py release` 通过。
- [x] 变更说明包含未执行项和残余风险。
