---
name: daily-learning-journal
description: 每日学习总结助手。分析今天的Claude Code会话记录，提取学习知识点和未完成事项，自动记录到Obsidian行思录中。当用户说"总结今天的学习"、"写日记"、"记录今天学到了什么"、"今日复盘"、"更新行思录"或运行/daily-journal时触发。
---

# 每日学习总结助手（并行 Agent 版）

将 Claude Code 使用记录自动总结并写入 Obsidian 行思录。

## 核心架构

```
┌─────────────────────────────────────────────────────────────┐
│                      主协调器                                │
│  1. 发现今日会话文件                                         │
│  2. 并行启动 Agent 分析每个会话                              │
│  3. 汇总所有 Agent 结果                                     │
│  4. 生成并写入日记                                          │
└─────────────────────────────────────────────────────────────┘
         │              │              │              │
         ▼              ▼              ▼              ▼
    ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐
    │ Agent 1 │   │ Agent 2 │   │ Agent 3 │   │ Agent N │
    │ 会话A   │   │ 会话B   │   │ 会话C   │   │ 会话N   │
    └─────────┘   └─────────┘   └─────────┘   └─────────┘
```

## 执行流程

### Step 1: 发现今日会话文件

**⚠️ 重要：必须按日期精确筛选，不能用 `-mtime 0`（那是过去24小时）**

```bash
# 正确方法：获取今天日期，精确匹配修改日期
TODAY=$(date +%Y-%m-%d)
find ~/.claude/projects -name "*.jsonl" -not -path "*/subagents/*" 2>/dev/null | while read f; do
  mod_date=$(stat -f "%Sm" -t "%Y-%m-%d" "$f" 2>/dev/null)
  if [ "$mod_date" = "$TODAY" ]; then
    echo "$f"
  fi
done
```

获取所有今天修改的会话文件列表。

### Step 2: 分批并行启动 Agent 分析（最多4个并发）

**为每个会话文件启动一个独立的 Agent**，使用 `run_in_background: true` 并行执行。

**⚠️ 并发限制：最多同时启动 4 个 Agent**，超过则分批处理：
- 第1批：会话 1-4
- 第2批：会话 5-8
- 依此类推...

每批 Agent 全部完成后，再启动下一批。

**Agent Prompt 模板：**

```
分析以下 Claude Code 会话文件，提取关键信息并返回 JSON 格式摘要。

会话文件: {session_file_path}

请执行以下分析：

1. **用户主要意图** - 从前几条用户消息中提取
2. **使用的 Skills** - 搜索 `<command-name>/` 和 `<command-message>` 标签
3. **MCP 工具调用** - 搜索 `mcp__` 开头的工具调用，统计调用次数
4. **创建/更新的文件** - 搜索 `Write`, `Edit` 工具的 `file_path` 参数
5. **技术主题** - 识别 React, Vue, TypeScript, Python, Go, Docker, MCP, Agent, Hook 等关键词
6. **未完成事项** - 搜索 `[ ]`, `TODO`, `待办`, `未完成` 标记
7. **关键洞察** - 从对话中提取有价值的知识点
8. **项目路径** - 从 `cwd` 字段提取

返回格式：
```json
{
  "session_id": "从文件名提取",
  "project": "项目名称",
  "user_intent": "用户主要意图的一句话总结",
  "skills_used": [{"name": "skill名", "count": 1}],
  "mcp_tools": [{"name": "工具名", "count": 2}],
  "files_created": ["文件路径1"],
  "files_updated": ["文件路径2"],
  "tech_topics": ["主题1", "主题2"],
  "todos": ["待办事项1"],
  "insights": ["关键洞察1"],
  "message_count": 10
}
```

只返回 JSON，不要其他内容。
```

**启动方式：**

使用 Agent 工具，为每个会话文件启动一个 general-purpose agent，设置 `run_in_background: true`。

### Step 3: 等待所有 Agent 完成

使用 TaskOutput 收集每个 Agent 的结果。所有 Agent 并行运行，等待全部完成后汇总。

### Step 4: 汇总并生成日记

**汇总逻辑：**

1. **合并 Skills 使用** - 相同 skill 的 count 相加
2. **合并 MCP 工具** - 相同工具的 count 相加
3. **合并技术主题** - 去重
4. **合并文件操作** - 按笔记目录筛选
5. **合并未完成事项** - 去重
6. **提取关键洞察** - 选择最有价值的 3-5 条
7. **统计项目活动** - 按项目分组统计消息数

### Step 5: 写入行思录

**日记路径**: `$OBSIDIAN_VAULT_PATH/行思录/YYYY/YYYY-MM/YYYY-MM-DD.md`

**路径发现顺序**：
1. 环境变量 `OBSIDIAN_VAULT_PATH`
2. 常见位置：
   - `~/Documents/study/github/Obsidian`
   - `~/Obsidian`
   - `~/Documents/Obsidian`
   - `~/Library/Mobile Documents/iCloud~md~obsidian/Documents/`
3. 验证：目录包含 `.obsidian` 文件夹

## 日记模板

```markdown
---
tags:
title: "YYYY-MM-DD"
date: YYYY-MM-DD
lastmod: YYYY-MM-DD
---

#日记

## 事件记录

### 今日完成

1. **[主要活动1]**
   - 具体内容...
2. **[主要活动2]**
   - 具体内容...

### 技术学习

- **Claude Code**: 今日共 N 次会话，M 次交互
- **技术主题**: 主题1, 主题2, ...

### 使用的 Skills/MCP

- `/skill-name`: N 次 - 用途描述
- MCP `tool-name`: N 次

### 项目活动

- **项目名**: N 条消息

### 未完成事项

- [ ] 待办事项1
- [ ] 待办事项2

### 今日创建/更新的笔记

| 笔记 | 类型 | 主题 |
|------|------|------|
| 笔记名 | 新建/更新 | 主题 |

### 关键洞察

1. 洞察1
2. 洞察2

## 间隔复习

## 今日新闻

## 那年今日

\`\`\`dataview
List
where file.name= dateformat(date(today)-dur(1 year), "yyyy-MM-dd")
or file.name= dateformat(date(today)-dur(2 year), "yyyy-MM-dd")
or file.name= dateformat(date(today)-dur(3 year), "yyyy-MM-dd")
\`\`\`
```

## 单会话 Agent 分析指令

当需要分析单个会话时，启动一个 Agent 执行以下任务：

### 分析脚本

```bash
# 读取会话文件的前 50 行获取基本信息
head -50 {session_file}

# 搜索关键模式
grep -c "command-name\|command-message" {session_file}  # Skills 使用
grep -o "mcp__[a-z_]*" {session_file} | sort | uniq -c  # MCP 工具
grep -o '"file_path":"[^"]*\.md"' {session_file} | head -20  # 笔记文件
grep -c '"role":"user"' {session_file}  # 消息数量
```

### 提取规则

| 信息类型 | 搜索模式 | 提取方法 |
|----------|----------|----------|
| 用户意图 | `role: user, content` | 取前 3 条用户消息 |
| Skills | `<command-name>` | 统计出现次数 |
| MCP 工具 | `mcp__` 前缀 | 提取工具名并计数 |
| 文件操作 | `Write`, `Edit` + `file_path` | 提取文件路径 |
| 技术主题 | 关键词匹配 | React, Vue, Python 等 |
| 未完成 | `[ ]`, `TODO` | 提取整行 |
| 项目路径 | `cwd` 字段 | 提取目录名 |

## 性能优化

1. **分批并行执行** - 每批最多 4 个 Agent 并行，分批处理
2. **限制数量** - 如果会话超过 20 个，只分析最近 20 个
3. **超时控制** - 每个 Agent 设置 60 秒超时
4. **增量分析** - 可选只分析新增内容

## 示例用法

用户说：
- "总结今天的学习"
- "写今天的日记"
- "记录今天学到了什么"
- "/daily-journal"

## 执行示例

```
主协调器:
1. 发现 5 个今日会话文件
2. 启动 5 个并行 Agent...
3. 等待 Agent 完成... (3.2s)
4. 汇总结果:
   - Skills: 3 个，共 5 次调用
   - MCP: 4 个工具，共 12 次调用
   - 笔记: 新建 8 篇，更新 3 篇
   - 洞察: 4 条
5. 写入日记: 行思录/2026/2026-03/2026-03-18.md
```
