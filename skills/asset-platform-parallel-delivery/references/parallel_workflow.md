# 多 Agent 并行工作流

## 文件所有权矩阵

每个 agent 启动前写清楚“允许修改”和“禁止修改”。示例：

| Agent | 允许修改 | 禁止修改 |
|---|---|---|
| `account-ui` | `src/views/management/payment/account/**` | `router/**`、`api/**`、其他模块 |
| `balance-ui` | `src/views/management/payment/balance/**` | `router/**`、`api/**`、其他模块 |
| `transaction-ui` | `src/views/management/payment/transaction/**` | `router/**`、`api/**`、其他模块 |
| `payment-api` | `src/api/payment/**`、共享类型文件 | 所有页面和路由 |
| `payment-router` | `src/router/index.*`、`src/router/menu.*` | 业务页面、API 文件 |
| `verification` | 只读整个工作区 | 任何源文件 |

如果多个页面必须共用一个数据文件，先由 API/架构 agent 定义该文件，再把它视为只读契约；不要让页面 agent 同时编辑。

## 子 agent 提示词模板

```text
你不是单独工作的 agent，其他 agent 会同时修改同一项目。

任务：<一个明确模块>
仓库：<绝对路径>
分支/工作区：<分支或 worktree>
允许修改：<明确文件/目录>
禁止修改：<共享文件和其他模块>
业务约束：<文档字段、风格、权限、mock、状态流转>
接口约束：<现有 request wrapper、endpoint、请求/响应假设>
完成标准：<页面可渲染、核心交互可操作、接口优先、错误态明确>
验证：运行 <最小命令>，不要修复无关问题

完成后只回报：
1. 修改的文件
2. 验证命令和结果
3. 未解决问题/假设
4. 需要集成 agent 处理的共享改动
不要 commit、push，不要回滚其他 agent 的修改。
```

## 推荐调度顺序

### 首模块验收模式

1. `research`：只读梳理项目和文档。
2. `contract`：确定 API、状态和路由契约。
3. `module-ui`：完成一个完整模块。
4. `integration`：接路由、菜单映射和权限。
5. `verification` + `code-reviewer`：启动、构建、浏览器和代码审查。
6. 用户验收通过后，才启动其他模块并行。

### 已有基线后的并行模式

1. `research` 与各模块需求拆分并行。
2. 各模块 UI agent 按目录并行。
3. API agent 与 UI agent 并行，但通过固定类型/接口契约对接。
4. 集成 agent 最后统一处理 router/menu/shared styles。
5. verification 和 code review 在集成后运行。

## 回报格式

协调者最终报告应包含：

```text
分支：<repo>:<branch>
已完成：<模块列表>
并行 agent：<角色 -> 交付物>
菜单：<menuCode、URL、回查结果>
验证：<build/type-check/browser/API>
已知问题：<基线问题与新增问题分开>
下一步：<用户需要验收或确认的动作>
```
