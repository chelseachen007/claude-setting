---
title: Codex 记忆迁移归档
date: 2026-10-23
source: ~/.codex/memories/ (v1) + ~/.codex/memories_v2/ 的 memory_summary.md 与 rollout_summaries/
---

# Codex 记忆迁移归档

> 2026-10-23 从 Codex 的 `memories` / `memories_v2` 目录汇总迁入。跨会话有复用价值的条目已提炼进 `MEMORY.md`；这里保留 Codex 原始摘要与对应会话文件位置，供回溯。

## 来源文件

| 来源 | 路径 | 内容 |
|---|---|---|
| v2 摘要 | `~/.codex/memories_v2/memory_summary.md` | 用户画像、偏好、通用提示、时间线 |
| v1 摘要 | `~/.codex/memories/memory_summary.md` | 上一代摘要（含 Obsidian 删除策略） |
| v1 原始 | `~/.codex/memories/raw_memories.md` | 分线程的原始记录 |
| 线程详情 | `~/.codex/memories*/rollout_summaries/` | 5 份会话级摘要 |

另有 SQLite 形式的历史库：`~/.codex/memories_1.sqlite`、`~/.codex/memories_v2_1.sqlite`（未展开，需要时再查）。

## 会话级摘要（5 份）

### `2026-10-15T02-47-55-4z5G-notion_mcp_oauth_fix_and_obsidian_book_sync.md`
- thread: `01a13d75-887a-7751-9888-9ca9c559a8cc`，cwd: Obsidian 库
- 修复 Notion MCP 重复 OAuth resource 配置，并把 Obsidian 历史读书笔记增量同步到正确的 Notion 书籍页面。
- 修正后 `codex mcp login notion` 成功输出 `Successfully logged in to MCP server 'notion'.`

### `2026-10-15T03-28-05-Ii5W-persist_obsidian_deletion_safety_policy.md`
- 把 Obsidian 的删除与清理策略写进 `AGENTS.md`，并在修改后用 `git diff --check` 校验。

### `2026-10-14T08-42-23-heQo-weread_history_series_obsidian_notion_sync.md`
- thread: `01a13993-b4f5-74e0-966c-ceea80d52a80`
- 八册历史系列导入、第一册「上古夏商西周」带问题阅读复盘、博物馆线索。

### `2026-10-15T02-44-41-oWN0-reading_loop_skill_creation_and_notion_sync_blocker.md`
- thread: `01a13d72-934e-7f41-8f77-89b3a8934df6`
- 创建 `reading-loop` Skill；Notion MCP 当时未挂载导致同步受阻。

### `2026-10-15T03-28-05-Ii5W-obsidian_agents_delete_cleanup_policy.md`
- thread: `01a13d9a-5105-7993-9b37-df2e6b32d1e8`
- `AGENTS.md` 增加「删除与清理策略」一节，`lastmod` 改为 `2026-10-15`。

## 历史系列（通用事实）

「每个青少年都应该读的中国历史故事」共八册：上古夏商西周、春秋战国、秦汉、三国两晋南北朝、隋唐、五代十国宋、元朝、明朝。

## 待确认

- Notion MCP 是否仍可用：v2 摘要记录某次会话「没有可用的 Notion 资源/工具」，之后再试前需重新确认挂载状态。
- `reading-loop` Skill 的源码与打包产物已创建，但摘要中没有证据表明用户安装、提交或完成过一次真实同步。
- v2 摘要提到「可能同步到 Notion」，属于推测，未证实。
