---
name: daily-learning-journal
description: 每日学习总结助手。分析今天的Claude Code会话记录，提取学习知识点和未完成事项，自动记录到Obsidian行思录中。当用户说"总结今天的学习"、"写日记"、"记录今天学到了什么"、"今日复盘"、"更新行思录"或运行/daily-journal时触发。
---

# 每日学习总结助手

将Claude Code使用记录自动总结并写入Obsidian行思录。

## 工作流程

### 1. 发现今日会话文件

使用 Glob 工具查找今天修改的会话文件：

```
~/.claude/projects/**/*.jsonl
```

筛选条件：文件修改日期为今天，排除 subagents 目录。

### 2. 读取并分析会话内容

使用 Read 工具读取会话文件，提取：

**关键活动识别：**
- 安装的新工具/MCP（搜索 "install", "pipx", "npm install", "brew install"）
- 使用的 Skills（搜索 `<command-name>/`, `<command-message>`）
- MCP 工具调用（搜索 `mcp__`, 工具名如 `webReader`, `github`）
- 创建/更新的文件（搜索 `Write`, `Edit`, `file_path`）
- 后台任务（搜索 `run_in_background`, `task-notification`）

**项目活动：**
- 从 `cwd` 字段提取工作目录
- 统计各项目的消息数量

**技术主题：**
- 关键词匹配：React, Vue, TypeScript, Python, Go, Docker, MCP, Agent, Hook, Skill 等

**未完成事项：**
- 搜索 `[ ]`, `TODO`, `待办`, `未完成` 等标记

### 3. 生成日记内容

根据分析结果，按以下模板生成日记：

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

- **Claude Code**: 今日共 N 次交互
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

### 4. 写入行思录

**日记路径**: `$OBSIDIAN_VAULT_PATH/行思录/YYYY/YYYY-MM/YYYY-MM-DD.md`

**路径发现顺序**：
1. 环境变量 `OBSIDIAN_VAULT_PATH`
2. 常见位置：
   - `~/Documents/study/github/Obsidian`
   - `~/Obsidian`
   - `~/Documents/Obsidian`
   - `~/Library/Mobile Documents/iCloud~md~obsidian/Documents/`

3. 验证：目录包含 `.obsidian` 文件夹

## 分析要点

### 重点捕获

1. **新安装的工具** - 特别关注 MCP 工具、npm/pip 包
2. **Skills 使用** - `/command` 形式的技能调用
3. **笔记创建** - 卡片/目录下的 .md 文件
4. **后台任务** - 长时间运行的任务
5. **未完成事项** - 被中断的工作

### 避免遗漏

- 同时检查用户消息和助手消息
- 注意 MCP 工具调用（可能没有 `/` 前缀）
- 检查文件操作（Write/Edit）了解实际产出
- 关注安装日志中的包名

## 示例用法

用户说：
- "总结今天的学习"
- "写今天的日记"
- "记录今天学到了什么"
- "/daily-journal"
