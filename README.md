# claude-setting — AI 信息版本档案

这个仓库是 `~/ai/` 的**只读快照**，用来记录个人 AI 资产（规则、记忆、技能）的版本演进。

## 它是什么

`~/ai/` 是本机运行中的 AI 资产单一源——Codex / WorkBuddy / DeepSeek Harness 三个平台都通过软链共享同一份规则、记忆和技能。这个仓库定期把那份目录同步过来，形成可追溯的时间线。

**仓库不是工作副本。** 不要在这里改东西然后往回同步，会跟 `~/ai/` 分叉。要改就改 `~/ai/`，再同步过来。

## 目录

```
rules/global.md     全局规则（唯一源，软链到各平台 AGENTS.md）
memory/             USER.md（用户画像）· SOUL.md（人格）· MEMORY.md（长期记忆）· daily/（日志）
skills/             技能唯一源，每个技能一个真实目录 + SKILL.md
scripts/            build-memory-agents.sh · sync-skill-sources.sh · chrome-cache-gc.sh
sync.sh             软链体检 / 修复
```

## 历史

| 分支 | 内容 | 时间 |
|---|---|---|
| `main` | `~/ai` 快照 | 2026-10-27 起 |
| `legacy/main-20260714` | 旧的 Claude Code 配置（settings.json、agents、commands、hooks、plugins、26 个旧技能） | 至 2026-07-14 |

旧结构是 Claude Code 时代留下的。2026-10-22 Claude Code 停用，资产体系重建为 `~/ai/` 单一源，`main` 分支在 2026-10-27 被接管。

## 同步方式

```bash
# 在 ~/ai 侧执行
rsync -a --delete \
  --exclude '.backup' --exclude 'logs' --exclude '__pycache__' \
  --exclude '*.pyc' --exclude '.venv' --exclude 'node_modules' \
  ~/ai/ /path/to/claude-setting/
```

`--delete` 是必要的——技能删除后要能从档案里看出来。排除项都是运行时产物和本地备份，不属于资产本身。

## 注意

- `memory/MEMORY.md` 里有本机路径、内网 IP、域名等环境信息，仓库是公开的，写入前自己确认过没有密钥。
- 技能目录里若出现 `.venv` / `node_modules` / `__pycache__`，是运行时生成的，已被 `.gitignore` 排除。
