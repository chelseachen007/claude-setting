---
summary: "自动化中台（agent-autoloop）的配置、token 经济学与待办"
read_when:
  - 要加/改自动化的规则、通道、worker
  - 要排查定时任务失败、飞书通道、Chrome/CDP 连接
  - 要评估自动化任务的 token 成本
---

# 自动化中台 agent-autoloop

## 现状（2026-11-11）

- 引擎在 `~/.agent-autoloop/app`（git 仓库，1.0.0），运行态在 `~/.agent-autoloop/`
- hub `127.0.0.1:3350`，worker 名 `macbook-air`，由 LaunchAgent `agent-autoloop` 托管
- 通道：`desktop`（桌面通知）+ `feishu`（飞书，answerer `ou_12400ec40b5912a2fe6c5e2b9cebbaaf`，走 `~/.npm-global/bin/lark-cli`）
- 规则（`~/.agent-autoloop/rules.json`，热加载，改完 hub 自动应用并记 fact）：
  1. 「试一下」— 来源 `try.*`，用于验证通道
  2. 「早报」— cron `0 8 * * *`，skill `morning-brief`，cwd 是 Obsidian 库，`tell: always`
  3. 「雪球日报」— cron `0 9 * * *`，prompt 内嵌完整幂等与抓取耐心规则，`tell: always`
- 不要直接 `cd ~/agent-autoloop`（不存在），正确是 `~/.agent-autoloop`。试跑用的 cwd 是 `~/.agent-autoloop/try`。

## token 经济学（2026-11-11 实测）

单次 run 的 `usage.input_tokens`：
- run 30-1（雪球日报）= 9,872,631，其中 cached 9,680,768
- run 27-1（雪球日报）= 5,548,349，其中 cached 5,417,472
- 其余 run 在 0.18M ~ 0.9M

**根因不是「读了大文件」，而是多轮 tool call 的累积**：27-1 有 83 个 item、30-1 有 46 个。
每轮都把整个上下文重发一遍，所以 input ≈ 轮次 × 上下文长度。

三个放大因素：
1. **Codex 的 MCP 工具一直在**（`notion`、`node_repl`、`computer-use`），每次请求都带这些工具的 schema；定时任务一个都用不上。
2. **大段输出进了上下文**：27-1 单次 `command_execution` 的 `aggregated_output` 有 62,659 字符（打印 scored.json 全量），另有 40,128 / 35,241 各一次。这些是上下文里最贵的部分。
3. **skill 与踩坑文档的反复读取**：`xueqiu-digest/SKILL.md` 读了两次（7088 + 2829），`web-access/SKILL.md` 7936，`投资研究/触发器清单.md` 2034。

## 已做的优化

- 2026-11-11：`agents.codex.model` 设为 `deepseek-v4.1-flash`（原为 config.toml 的 `deepseek-v4-flash`），按用户「Codex 快模式做决策」的偏好。备份 `rules.json.bak-opt-20261111`。hub fact seq 27844 已生效。
- **2026-11-12：上面那条是错的，已改回 `deepseek/deepseek-flash`。** `deepseek-v4.1-flash` 是 magpie 没注册的名字，
  codex 会先打 `Model metadata for \`deepseek-v4.1-flash\` not found`，然后模型名被丢进 fallback 路由 → 落到 xdpool →
  `11128 Illegal API invocation from an unapproved channel`。早报/雪球日报因此**每天静默失败**（card #31 #32 每小时重试一次，全挂）。
  改后 `agent-autoloop try` 连跑两次都通（#69 #70）。**别再用裸模型名**，一律带 `deepseek/` 前缀。
- 顺带修了 `app/plugins/codex/agent.ts` 的 `check()`：原来只跑 `codex login status`，而走第三方 provider（magpie）的配置
  本来就没有 `auth.json`，于是 `doctor` 永远报「Codex 没有登录或用不了」，可 `codex exec` 实际跑得通。
  现在先读 `~/.codex/config.toml` 的 `model_provider`，非 `openai` 且有对应 `[model_providers.X]` 段就直接判可用。
- 规则级 `model` 会覆盖 config.toml，可以按规则分别指定（协议文档：`agents.<id>.model` / `effort` / `access`）。

## 待做（按 ROI）

1. **给定时任务瘦身工具面**：给早报/雪球日报单独建一个 `agent` 条目，用 `command` 适配器起 `codex exec` 时加 `-c` 关掉 MCP，或直接用 `--profile` 指定精简配置。
2. **规则 prompt 里写死「只打印摘要」**：抓取脚本的输出一律重定向到临时文件，只 `wc -l` / `head -20` 回显，禁止一次性 print 全量 JSON。
3. **雪球日报拆两段**：抓取段（纯脚本，可定时无人值守）+ 分析段（读落盘文件，短上下文），避免一个 run 里既抓又写长文。
4. **给 skill 加「先跑脚本再读文档」的入口**：SKILL.md 里的稳定流程沉成 `run.sh`，模型只读输出摘要，不读 10KB 流程文档。

## 已知问题

- `~/.codex/config.toml` 有 3 条无效配置被忽略：`disable_response_storage`、`network_access`、`windows_wsl_setup_acknowledged`。每个 run 开头都会重复报一次（占两行 item），删掉更干净。
- 飞书 websocket 在 `~/.agent-autoloop/logs/up.log` 里 `reconnecting` 出现 154 次，属正常断线重连（04:00:48 disconnected → 04:02:21 connected），不影响投递。
- Chrome 远程调试失效时（如 11-08）雪球日报会失败并派卡片；恢复后选「已恢复，重新派发」会从抓取开始补跑。人机协同链路已验证可用。
