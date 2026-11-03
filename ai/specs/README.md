# 规格驱动开发

规格把“要解决的问题”和“如何证明已经解决”放在代码之前。一个活动规格使用一个目录：

```text
ai/specs/
  001-example/
    spec.md
    plan.md
    tasks.md
    verification.md
```

目录名必须是 `NNN-kebab-case`，`NNN` 连续递增。模板位于 `ai/specs/templates/`，复制后按实际内容填写。

## 生命周期

1. `draft`：问题和范围仍在澄清，可以修改验收项。
2. `approved`：目标和验收项已明确，可以开始实现。
3. `in-progress`：任务正在执行；未完成项保持 `- [ ]`。
4. `blocked`：外部依赖或决策阻塞，在规格中写明恢复条件。
5. `done`：全部验收项和任务完成，`verification.md` 记录通过证据。
6. `superseded`：被新规格替代，在标题或变更记录中指向新规格。

## 硬规则

- `spec.md` 必须包含 `## 目标`、`## 非目标`、`## 验收标准`。
- 每个验收项使用唯一编号 `AC-001`，并写明 `验证：` 方法。
- `tasks.md` 使用唯一编号 `T001`，每项是可独立交付和验证的动作。
- `verification.md` 必须为每个验收项提供证据行；`done` 状态的证据必须标记为 `PASS`。
- 规格是行为的权威来源；计划可以调整，验收标准变化必须显式修改并重新验证。
- 实现过程中发现范围变化时，先更新规格，再改代码。

## 推荐写法

验收标准描述可观察结果，不描述实现细节。例如：

```markdown
- [x] AC-001 未认证用户访问受保护接口时返回 401 和统一响应信封。
  验证：`python -m unittest user.tests.JwtMiddlewareTests` 与 `verification.md` 证据。
```

任务描述动作和完成边界。例如：

```markdown
- [x] T003 为登录锁定增加成功、失败和 Redis 不可用分支测试。
```
