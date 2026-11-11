---
summary: "长期记忆：只放每次都需要知道的事（偏好、习惯、在线资产位置）。技术档案在 projects/。"
read_when:
  - 每次启动都会注入，不需要主动读
---

# MEMORY.md — 核心层

> **写入规则（重要）**
>
> - 这里只放**每个会话都要知道**的事：用户偏好、沟通习惯、在线资产在哪。
> - 技术细节、踩坑记录、平台配置 → `projects/<主题>.md`，这里只留一行指针。
> - 当天做了什么 → `daily/YYYY-MM-DD.md`。
> - 写完跑 `~/ai/scripts/build-memory-agents.sh`（或 `~/ai/sync.sh`）。
> - Mnemon 那边的运行态由 `mnemon_runtime_memory` 工具写，别手改 `~/.mnemon/`。
>
> **拆分记录**：2026-11-11 从 18.6KB 拆为「核心层 + projects/」，原文件备份在
> `~/ai/.backup/memory-split-20261111/MEMORY.md`。

## 项目档案索引（projects/）

| 文件 | 什么时候读 |
|---|---|
| `projects/dsh-platform.md` | 改 `~/.dsh` 配置、插件、workspace；排查 dsh-chat-import / Mnemon / magpie；查平台迁移经验 |
| `projects/agent-autoloop.md` | 改自动化中台的规则、通道、worker；查「单次任务百万 token」的优化结论 |
| `projects/invest-workspace.md` | 投资数据抓取的接口坑、口径纪律、复盘机制 |

## 跨平台 AI 资产架构

唯一源 `~/ai/`，通过软链分发到各平台。**Claude Code 已于 2026-10-22 完全停用并卸载。**

- 规则：`~/ai/rules/global.md` → `~/.codex/AGENTS.md`、`~/.dsh/AGENTS.md`
- 记忆：`~/ai/memory/{IDENTITY,USER,SOUL,MEMORY}.md` → `~/ai/memory/AGENTS.md`（生成物）→ `~/.agents/AGENTS.md`
- 技能：`~/ai/skills/<name>/SKILL.md`，索引在 `~/ai/skills/README.md`。三个入口软链：`~/.agents/skills`、`~/.dsh/skills`、`~/.codex/skills`
- MCP：**没有跨平台唯一源**，各平台格式本来就不同，能统一的是「同一个 server 的参数」
- 项目级（Obsidian 库）：`AGENTS.md` 唯一规则源；**库内技能已清空**（2026-11-11），`.agents/skills/` 只剩指向全局的 `sigma` 软链，新技能一律放 `~/ai/skills/`
- 体检：`~/ai/sync.sh`（`--fix` 修软链）；技能源 `~/ai/scripts/sync-skill-sources.sh`
- 档案仓库 `chelseachen007/claude-setting`：`~/ai` 的只读快照，同步用 `bash ~/ai/scripts/archive-ai.sh`（`--commit` 自动推送）。排除 `.backup/`、`logs/`、`__pycache__`、`.venv`、`.system`。**脚本会 `git checkout HEAD -- README.md`：仓库 README 描述档案，`~/ai/README.md` 描述运行目录，两者不同，别合并。**

## 系统维护脚本

- `~/ai/scripts/chrome-cache-gc.sh`：清理 Chrome 长期未访问的 Service Worker 缓存。
  - 起因：飞书多维表格（`bitableHtml`）的 SW 缓存泄漏，曾累积 39GB / 70+ 个 feishu.cn 租户站点
  - 默认 dry-run，`--force` 移废纸篓，`--purge` 永久删除，`--days=N` 改阈值（默认 30 天）
  - 判断依据是 origin 目录 mtime，Chrome 运行中执行也安全

## 用户偏好

- 名称：奔跑的小胖；城市：杭州；助手名：小胖助手 🐻
- 关注领域：Coding、理财
- 沟通风格：随意直接，不喜欢弯弯绕
- 核心要求：不说谎，不知道就说不知道，信息不全先追问
- 在玩《燕云十六声》（网易武侠开放世界），关注剧情与叙事

## 职业背景

- 前端开发，2026-09 起正转型全栈 + AI 应用方向（受 AI 冲击驱动）
- 已给过的方向建议：不补「写后端代码」的课，重点升到系统设计 + AI 应用层 + AI 协作层（上下文工程／任务分解／验证体系／代码审查）
- 技术栈倾向建议：后端走 Node 最短路，不啃 Java 生态（除非公司即 Java）

## 沟通方式

- 默认中文；代码、命令、变量名用英文
- 结论先行，再给理由，不要先铺垫背景
- 不谄媚：不夸想法好、不说「好问题」、不说「当然可以」
- 不主动问「你确定吗」——除非有真实风险
- 遇到模糊需求，先给最合理的方案，再问要不要调整

## 思维方式

- 第一性原理：从问题本质出发，不因「惯例如此」照搬。发现更好的做法直接说，不用等问
- 约束先行：新项目先建规则文档再动手；已有规范严格遵守；要改规范先改文档、再改实践
- 用户体验是产品最高准则，优先级高于技术偏好、代码整洁度、架构优雅度：
  - 为目标设计，不为功能设计
  - 不让用户思考——需要说明书才能用，设计就是失败的
  - 系统承担复杂性：能自动化的不手动，能推断的不让用户填
  - 渐进式展示；反馈要引导行动，不只报告问题

## 开发习惯

- 改完主动跑验证（test / lint / build），不要只改不验
- 不为了让代码跑起来而注释掉报错，找根本原因
- 密钥、token、密码不进代码
- 把任务转化为可验证的目标，循环直到验证通过
- 匹配现有代码风格，即使不喜欢
- 发现死代码提一句，但别删

## 每日间隔复习（微信推送）

复习内容每晚 23:00 通过微信助理推送。**推送时不标记，只有用户作答后才标记。**

当用户在微信或对话里回复了复习答案（或说「答完了」「标记一下」）时：

1. 读 `/Users/chenjie/Documents/study/github/Obsidian/行思录/review-pending.md`
   —— 里面有本次待标记的卡片路径 + 参考答案
2. 逐题给反馈：对照参考答案，指出漏了什么、错在哪，不要只说「对了」
3. 反馈完成后，对清单里每张卡片执行标记：
   ```bash
   cd /Users/chenjie/Documents/study/github/Obsidian
   /Users/chenjie/.workbuddy-ai/binaries/python/versions/3.13.12/bin/python3 .claude/scripts/review.py mark "<卡片相对路径>"
   ```
4. 把 `review-pending.md` 的 frontmatter `status` 改成 `done`

若 `review-pending.md` 不存在或 `status` 已是 `done`，说明没有待处理的复习，直接说明即可。

## Claude 清理记录

`~/.claude`(439M)、`~/.local/share/claude`(636M)、`~/.claude.json` 已移入废纸篓（`claude-20261022-1511`、`claude-share-20261022`、`claude.json-20261022`）；`.zshrc` 中 5 个 claude 别名/函数已删。仅剩 `/usr/local/bin/claude`（npm 全局包，需 `sudo npm uninstall -g @anthropic-ai/claude-code`）。
