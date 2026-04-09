---
name: clip-and-process
description: >
  一站式剪藏工作流：自动提取网页内容 → 保存到剪藏 → 深度处理。
  整合 cn-content-extractor 和 clip-process，一次完成从抓取到深度笔记的全流程。
  触发词：剪藏并处理、智能剪藏、clip、完整剪藏。
  当用户提供 URL 并要求剪藏+处理时触发。
---

# Clip and Process — 智能剪藏工作流

## 触发条件

当用户说以下类似话术时触发：
- "剪藏并处理"、"智能剪藏"、"完整剪藏"
- "clip" + URL
- "剪藏这篇文章并整理"
- 用户提供 URL 且上下文暗示需要完整的剪藏→处理流程

**不触发**：用户只说"剪藏"（此时只用 cn-content-extractor 保存即可）

## 工作流程

本技能编排 3 个步骤：

1. **内容提取**：调用 `cn-content-extractor` 从网页提取内容
2. **保存剪藏**：将内容保存到 Obsidian `剪藏/` 目录，标记为 `状态/未整理`
3. **深度处理**：调用 `clip-process` 补充常青笔记、连接和行动

## 执行步骤

### Step 1：调用内容提取

加载 `cn-content-extractor` skill，传入用户提供的 URL。

按照 cn-content-extractor 的三层降级策略执行（直接抓取 → CDP → 缓存搜索）。

**成功标志**：提取到实质性正文内容。

**失败处理**：直接告知用户失败原因，不继续后续步骤。

### Step 2：保存剪藏文件

将提取的内容保存到 Obsidian vault：

**文件路径**：`/Users/chenjie/Documents/study/github/Obsidian/剪藏/{文件名}.md`

**Frontmatter 格式**：

```yaml
---
title: 文章标题
date: YYYY-MM-DD
tags: [剪藏, 状态/未整理]
lastmod: YYYY-MM-DD
source: 来源平台
url: 原始链接
author: 作者（如果可获取）
---

## 总结

（由用户在浏览器中手动填充）

## 金句摘抄

（由用户在浏览器中手动填充）

## 原文

[提取的正文内容]
```

### Step 3：触发深度处理

剪藏文件保存成功后，立即执行 `clip-process` 流程：

1. 搜索 `剪藏/` 目录下刚创建的 `状态/未整理` 文件
2. 读取文章内容，搜索关联卡片
3. 生成常青笔记、连接、行动
4. 将标签从 `状态/未整理` 改为 `状态/已整理`
5. 更新 `lastmod` 日期

**关键**：如果 clip-process 失败，剪藏本身已完成，告知用户稍后手动运行 `/clip-process`。

### Step 4：返回结果

向用户报告完整结果：

```
✅ 智能剪藏完成

📄 文章：[文章标题]
🔗 来源：[平台名]
💾 保存：剪藏/[文件名].md

深度处理完成：
   📝 常青笔记：X 条
   🔗 已有卡片连接：X 个
   ✨ 建议新卡片：X 个
   ⚡ 行动项：X 个
```

## 错误处理

| 阶段 | 失败处理 |
|------|---------|
| 内容提取失败 | 告知用户原因，建议手动粘贴 |
| 剪藏保存失败 | 告知错误信息，检查 vault 路径 |
| 深度处理失败 | 剪藏已保存，提示用户稍后手动 `/clip-process` |

## 配置

- **Obsidian Vault**：`~/Documents/study/github/Obsidian/`
- **剪藏目录**：`剪藏/`
- **卡片目录**：`卡片/`

## 与其他技能的关系

- **cn-content-extractor**：提供内容提取能力（三层降级）
- **web-access**：当 cn-content-extractor 需要 CDP 时调用
- **clip-process**：提供深度处理能力（常青笔记、连接、行动）

本技能作为编排器，协调这些技能完成完整工作流。
