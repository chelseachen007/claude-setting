---
summary: "DSH / 平台配置与记忆体系迁移的全部技术档案（从 MEMORY.md 拆出，2026-11-11）"
read_when:
  - 要改 ~/.dsh 配置、插件或 workspace
  - 要排查 dsh-chat-import / Mnemon / magpie 的问题
  - 要判断某条经验从哪来
---

# PROJECTS: DSH 与平台

> 2026-11-11 从 `MEMORY.md` 拆出。原来这些内容挤在 18.6KB 的 MEMORY.md 里，
> 每天都被注入进每个会话；拆分后 MEMORY.md 只留指针，需要时读本文件。
> 追加规则：只写「什么时候会用到」的技术档案，天气式的进展记到 `daily/`。

## 记忆体系（Mnemon，2026-10-23）

**DSH 的记忆入口换成了 Mnemon 插件**（`dsh-mnemon` 0.5.34 + 系列 provider/source/strategy 包），旧的 `@xiaozhugez/dsh-project-memory` 已卸载，`~/.dsh/profiles/web/cordis.patch.yml` 里那两行 `autoInject` 覆盖也删了。

- Mnemon 运行态：`~/.mnemon/runtime/{memories.json,MEMORY.md,USER.md}`；项目文档索引 `~/.mnemon/documents/index.json`
- **只能通过 `mnemon_runtime_memory` 工具写**，不要手改上面这些文件
- 迁移落点：跨项目通用事实 → `MEMORY.md`；项目私有 → `codex-migrated.md` / `workbuddy-migrated.md` / `projects/`；Codex 原始摘要仍可查 `~/.codex/memories*/`
- 与 `~/ai/memory/*.md` 的关系：`~/ai/memory` 是跨平台唯一源，Mnemon 是 DSH 的运行态缓存。**两边都要写的话，以 `~/ai/memory` 为准**。

## DSH 本机配置

- 应用：`/Applications/DeepSeek Harness.app`，CLI 软链 `~/.npm-global/bin/dsh`；数据目录 `~/.dsh/`
- web 服务：`dsh web --no-open`，监听 `127.0.0.1:3080`，每次启动换新 token，token 打在 `~/.dsh/web.out`
- 由 LaunchAgent `~/Library/LaunchAgents/com.user.dsh-web.plist` 托管（RunAtLoad + KeepAlive）
- 工作区数据：`~/.dsh/storages/workspace.json`（`global.workspaceIds` + `tables.workspaces`，会话 id 挂在各 workspace 下）
- **运行中改这个文件会被内存状态覆盖**，必须先停服务再改
- 没有跨工作区搬会话的 API（只有 create/rename/delete/insertBefore/insertSessionBefore/archive/pin），UI 也没有拖拽合并
- WorkBuddy 的 Bash 工具里 `nohup &` 起的进程会随 shell 退出被回收；要持久化用 Python `start_new_session=True`
- **坑**：`launchctl bootstrap` 对该 plist 返回 `EIO 5` 是假报错 —— 任务其实已加载。判断依据看 `launchctl print gui/501/com.user.dsh-web` 的 `state/pid/runs`，别看返回码

## 模型网关：magpie 取代 CC Switch（2026-10-28）

**CC Switch 已退场**：登录项删除、进程退出、15721 不再监听；其遗留 LaunchAgent `io.ccswitch.deepseek-responses-sanitizer`（15722）已 bootout，plist 移到 `~/.config/magpie/backups/cc-switch-disabled/`。App 本体没删，可回退；迁移前的库备份在 `~/.config/magpie/backups/cc-switch-before-migration-20261028-090931.db`。

- 网关 `http://127.0.0.1:3425`，健康检查 `magpie healthcheck`（退出码 0 = 正常）；CLI 在 `~/.npm-global/bin/magpie` → `~/.local/bin/magpie`。
- **magpie 启动时自动读 `~/.cc-switch/cc-switch.db` 导入 provider**（8 个），所以换代时旧库别急着删。
- 接入一律用 CLI 写，不手改配置：`magpie claude|codex|gemini|dsh <provider/model>`，`magpie dsh effort off`，`magpie ls` 看全局状态。
- **xdpool 只能给 Codex/DSH，不能给 Claude Code**：流式必报 `11128 Illegal API invocation from an unapproved channel`，而 curl 单发 200，`user-agent=agent` 治不好。
  - **2026-11-12 补：中台 Codex 也中招了。** 裸模型名 `deepseek-v4.1-flash` 会被路由到 xdpool，报 11128
    （`displayTips: not sent from an official client`）。早报/雪球日报因此连挂 3 次。
    判断依据：`~/.agent-autoloop/worker/runs/*/stdout-2.log` 里搜 `"provider":"XD Pool"`。
    修法：`magpie codex deepseek/deepseek-flash`（**官方 DeepSeek 那条路由，显示名就是 DeepSeek-V4.1-Flash**；
    `deepseek/deepseek-v4.1-flash` 这个 id 不存在，照抄会报 "model list has no ..."）。
    修完 `config.toml` 应变成 `model_provider = "magpie"` + `base_url = "http://127.0.0.1:3425/v1"`。
    **注意：curl 测不出来**——curl 走的路由和 CLI 不同，三种模型名 curl 全通。要验就真跑一次 `codex exec`。
- **Gemini CLI 必须开 `experimental.dynamicModelConfiguration`**，否则自定义模型名被兜底成 `gemini-3.5-flash` 并报 ModelNotFoundError。
- **magpie library 的 instructions/skills 不用**——会与 `~/ai/rules/global.md`、`~/ai/skills/` 双写；只把 MCP 收口在 library（当前 notion → codex）。
- dsh 侧：`~/.dsh/.credentials.yaml` 的 refs 段需要 `MAGPIE_GATEWAY_KEY: magpie`（值随意，网关不校验）；`cordis.patch.yml` 里同 id 的多个 patch 是**浅覆盖不合并**，`!delete` 自定义 tag 会让整个文件解析失败，删键只能整段重写。
- 实际可用的 provider 目前只有 deepseek 官方 + xdpool；neko（403 余额不足）、xiaomi（401 key 失效）、zhipu（429 余额不足）、minimax（402 余额不足）、nvidia（404 模型不存在）都不可用。

## 平台会话迁移（2026-10-27 核对）

- 技能和记忆继续只维护 `~/ai/skills/`、`~/ai/memory/`，不要为了换平台复制第二份。
- dsh 会话位于 `~/.dsh/sessions/`，Codex 会话位于 `~/.codex/sessions/`，两边格式不同；当前 Codex 的外部会话导入索引只识别 Claude Code，不能直接灌入 dsh 的 `session.v4.jsonl.zstd`。
- dsh 的归档和 workspace 分组属于 dsh 自己的状态，不自动等同于 Codex 的 thread/project 整理；不要按文件名伪造 Codex 会话索引。
- 跨平台续做时，优先从项目文件、Git、`~/ai/memory/` 恢复可验证结果；确需完整对话原文时，保留在来源平台，并按主题提炼成记忆或项目文档。
- **WorkBuddy 会话已全量导入 dsh（2026-11-01）**：国内版 `~/.workbuddy/projects`（10 个）+ 国外版 `~/.workbuddy-ai/projects`（117 个）共 127 个会话，全部在 `~/.dsh/dsh-chat-import/imports.json` 注册、会话落 `~/.dsh/sessions/`。新建 5 个 workspace 分组。以后新会话照常 `/import-all workbuddy` 增量导。
- **⚠️ dsh-chat-import 0.26.2 的 workbuddy 扫描器有 bug（已本地修）**：`lib/discovery/claude.mjs` 的 `scanWorkbuddy` 路径自拒正则写成 `\.workbuddy[\\/]projects`，漏了 `-ai` 后缀（同文件里 `roots()`/`matchFile`/`layoutProject` 三处都放行了），导致 `~/.workbuddy-ai/projects` 下 110 个会话在面板与 `/import-all` 里完全不可见——而 `npx dsh-chat-import scan workbuddy` 另有一份实现能扫到 127 个，两边数字不一致就是这个症状。已就地改成 `\.workbuddy(-ai)?[\\/]projects`。**升级插件后要复查这处是否被覆盖回去。**
- **发现层扫不到 ≠ 导入管线不能用**：`POST /api-import/import` 直接吃 `items:[{source,sourcePath,sessionId}]`，不经过来源扫描器，可作应急通道。token 取 `~/.dsh/web.out` 最后一个 `dsh web: ...?token=`。改 `node_modules` 里的插件代码后要重启 dsh web 才生效（ESM 已缓存）。

## 旧 project-memory 插件的真实情况（避免重复踩）

`@xiaozhugez/dsh-project-memory` 的 `agent/pre-step` 注入**没有写错**：dsh 里 `agent/pre-step` 就是 `(event, next) => Promise<PreStepDecision>` 的 waterfall，`{ prepend: true }` 是分发顺序而非中间件位置，宿主自己的 `modelSwitchNotice` 也用同一套写法。之前判定的「永不 resolve」不成立，那段误诊注释已从 patch 删除。

**同类通用根因**：插件报 `cannot get required service "X" in inactive context`，通常是插件把 service 注册（webServer 路由、commands、skills 等）挂在 apply 的 ctx 上却没绑 `ctx.effect` 生命周期，插件 fiber 重载后旧注册残留、闭包 ctx 已失活 → 请求 500 而工具面照常可用。修法：把注册包进 `ctx.inject` 回调的 `webCtx.effect(() => register(...), label)` 并收集 disposer。2026-10-23 在 dsh-chat-import 面板路由上实测复现并修复（改的是 node_modules 里 `lib/index.mjs` + `lib/panel.mjs`，插件升级会被覆盖）。

## 迁移进来的通用经验（与平台无关，也值得记住）

- **跨页面移植代码前先核对符号表**：两页同名功能可能用不同函数名/存储键。这类 `xxx is not defined` 语法检查和 DOM 桩都抓不到，只有真实浏览器 + `pageerror` 能抓
- **第三方元数据「字段存在」≠「字段有值」**：Commons 的 `Artist` 经常为空，但 CC BY-SA 要求署名——署名缺失是合规问题，不是显示问题
- **检测本机端口别用 curl**：配了 `http_proxy` 时 curl 会把 `127.0.0.1` 也发给代理，代理返回 502 但 **curl 退出码仍是 0**。用 `/dev/tcp/127.0.0.1/$PORT`
- **同一份缓存不要并发跑多个写入进程**
- **迁移数据要顺手删旧键**：只合并不删旧的，用户取消操作后一刷新又被迁移回来，像「删不掉」的 bug
- **沙箱环境不通 ≠ 用户环境不通**
- **CSS 必须写在 `</style>` 之内**：追加到闭合标签之后会静默失效，改完数一下标签计数
- **懒加载图片的测试别急着断言失败**：`naturalWidth===0` 可能只是没加载完
- **`osascript` 移文件到废纸篓会撞 Finder 自动化权限**（-10004），直接 `mv` 到 `~/.Trash/` 更省事
- **本机 shell 的 `grep` 对中文/多字节不可靠**（静默无输出），一律用 Grep 工具
- **`agent-browser click` 是真实鼠标点击**：元素滚出视口或被遮挡时静默失败（返回 ✓ Done 但没生效），用 `eval` 直接 `.click()` 可区分

## Codex 时代的可复用流程

- **可靠的 Notion 同步顺序**：读本地 Markdown → 提取新增段 → `notion_search` → `notion_fetch` 所有候选 → 按日期/正文选一个 → 用 `position: {"type":"end"}` 追加 → 再 `notion_fetch` 回读验证
- **Notion MCP OAuth 重复 resource**：Notion 插件默认同时有 `url` 和 `oauth_resource`，会在授权请求里产生两个 `resource` 参数 → `invalid_target` / `Only one resource parameter is supported`。在 `/Users/chenjie/.codex/config.toml` 里只保留 `[mcp_servers.notion] url = "https://mcp.notion.com/mcp"` 即可
- **本地有 MCP 配置 ≠ 当前会话已挂载工具**，没挂载就不要声称写过
- **发布脚本的 `clean` 必须单独执行**：Gradle 的 `clean assembleDebug` 放在同一调用里可能因上游产物已删而报 "Unable to make progress running work"；先跑 `clean`，再跑 `assembleDebug`。
- **本机 GitHub CLI 凭据与 Git 传输分离**：`git push` 可走 SSH，而 `gh release` 依赖 `gh auth status` 显示的 keyring token；不要用 push 成功推断 Release 权限正常。
- 「每个青少年都应该读的中国历史故事」共八册：上古夏商西周、春秋战国、秦汉、三国两晋南北朝、隋唐、五代十国宋、元朝、明朝
- 中国历史 GIS：服务器 `47.80.76.56`，部署目录 `/var/www/history-map`，Nginx 配置 `/etc/nginx/sites-available/history-map`，域名 `https://history.trotter.top/`

## 已知噪音（不用追）

- **`dsh: [dsh-xdpool] patch: entry "billion-context-xdpool" not found`**（2026-11-12 查清）
  - 来源：`~/.dsh/profiles/web/node_modules/dsh-xdpool/cordis.patch.yml` 末尾硬编码一条
    `- id: billion-context-xdpool` + `disabled: true`。
  - 为什么留着：插件 2.0.0 曾自动挂载 billion-context，但对**已装过**的用户会造成
    `service "…" has been registered at <…>` 的永久 failed 条目。作者改为保留一条 disabled 记录
    （可寻址 + 记录决策 + 保证 `bili-native` 是唯一挂载点）。
  - 代价：该 id 在当前 profile 不存在 → 启动时 stderr 一行 `not found`。**exit=0，不影响功能。**
  - **不要动它**：改 node_modules 会被升级覆盖；在 profile 里加同名 disabled 条目虽然能消警告，
    但那条目会出现在插件列表里，正是作者想避免的局面。
