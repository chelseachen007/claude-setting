---
name: daily-learning-journal
description: 每日学习总结助手。分析今天的Claude Code会话记录，提取学习知识点和未完成事项，自动记录到Obsidian行思录中。当用户说"总结今天的学习"、"写日记"、"记录今天学到了什么"、"今日复盘"、"更新行思录"或运行/daily-journal时触发。
---

# 每日学习总结助手

将Claude Code使用记录自动总结并写入Obsidian行思录。

## 工作流程

### 1. 收集今日会话数据

运行脚本分析今天的会话记录：

```bash
python3 scripts/analyze_sessions.py --date today
```

脚本会从 `~/.claude/projects/` 目录读取所有项目的会话数据。

### 2. 分析并总结

根据会话内容，提取：

- **学习知识点**：技术概念、API用法、工具技巧、最佳实践
- **使用的Skills**：今天调用了哪些skills
- **项目活动**：在哪些项目上工作了什么
- **未完成事项**：被中断的任务、提到但未执行的TODO

### 3. 写入行思录

行思录路径：`~/Obsidian/行思录/年/年-月/年-月-日.md`

例如：`行思录/2026/2026-03/2026-03-13.md`

文件格式遵循Obsidian日记模板：
- YAML frontmatter
- #日记 标签
- ## 事件记录 部分
- ## 今日新闻（可选）
- ## 那年今日 dataview查询

### 4. 文件格式模板

```markdown
---
tags:
title: "YYYY-MM-DD"
date: YYYY-MM-DD
lastmod: YYYY-MM-DD
---

#日记

## 事件记录

### 今日学习

- **技术点1**：描述...
- **技术点2**：描述...

### 使用的Skills

- skill-name: 用途描述

### 项目活动

- 项目名: 完成的工作

### 未完成事项

- [ ] 待办事项1
- [ ] 待办事项2

## 今日新闻

## 那年今日

\`\`\`dataview
List
where file.name= dateformat(date(today)-dur(1 year), "yyyy-MM-dd")
or file.name= dateformat(date(today)-dur(2 year), "yyyy-MM-dd")
or file.name= dateformat(date(today)-dur(3 year), "yyyy-MM-dd")
\`\`\`
```

## 配置

**环境变量**: `OBSIDIAN_VAULT_PATH` - Obsidian库的根路径

**当前配置**: `/Users/chenjie/Documents/study/github/Obsidian`

### 首次使用时的路径发现流程

如果 `OBSIDIAN_VAULT_PATH` 环境变量未设置，按以下步骤操作：

1. **搜索常见Obsidian位置**：
   - `~/Documents/study/github/Obsidian` (当前配置)
   - `~/Obsidian`
   - `~/Documents/Obsidian`
   - `~/Library/Mobile Documents/iCloud~md~obsidian/Documents/` (iCloud)

2. **验证Obsidian库**：检查目录是否包含 `.obsidian` 文件夹

3. **用户确认**：找到后向用户展示路径，确认是否正确

4. **存储配置**：将确认的路径设置到环境变量：
   ```bash
   # 添加到 ~/.zshrc 或 ~/.bashrc
   export OBSIDIAN_VAULT_PATH="/Users/chenjie/Documents/study/github/Obsidian"
   ```

5. **日记文件夹**：在Obsidian库内查找名为 `行思录` 的文件夹，如不存在则创建

### 后续使用

设置好环境变量后，直接使用 `$OBSIDIAN_VAULT_PATH/行思录/` 作为日记目录

## 示例用法

用户说：
- "总结今天的学习"
- "写今天的日记"
- "记录今天学到了什么"
- "/daily-journal"

执行后会在Obsidian行思录中创建或更新当天的日记文件。
