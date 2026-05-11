# 已注册 Agent 能力描述

总管根据此文件判断每个任务应该分派给哪个 Agent。

---

## 写作助手 (writer)

- **workspace**：`~/.claude/agents/writer/`
- **定位**：长文写作、风格复刻、去 AI 味、多平台发布
- **触发场景**：写文章、内容创作、润色文案、翻译写作、整理笔记为文章
- **核心工具**：web-search, web-reader, multi-publish, baoyu-translate, obsidian-markdown
- **输出位置**：`产出文章/` 或用户指定目录
- **工作流**：需求理解 → 调研 → 大纲 → 逐节撰写 → 补充 → 润色 → 去 AI 味 → 交付

---

## 投资助手 (investment)

- **workspace**：`~/.claude/agents/investment/`
- **定位**：A股/美股分析、个股研究、投资评分、行业对比
- **触发场景**：分析股票、投资建议、行业对比、板块扫描、宏观分析
- **核心工具**：cn-finance-toolkit, stock-debate-analysis
- **输出位置**：`投资研究/` 或用户指定
- **工作流**：识别对象 → 获取数据 → 基本面 → 估值 → 资金面 → 技术面 → 风险评估 → 输出报告

---

## 开发助手 (dev)

- **workspace**：`~/.claude/agents/dev/`
- **定位**：全栈开发、Issue 处理、PR 审查、代码分析
- **触发场景**：写代码、修 bug、审查 PR、处理 Issue、重构、跑测试
- **核心工具**：/multi-* 命令族, project-analyzer, GitHub MCP
- **输出位置**：项目仓库
- **工作流**：理解任务 → 环境准备 → 代码分析 → 实施改动 → 验证 → 提交

---

## 资讯助手 (news)

- **workspace**：`~/.claude/agents/news/`
- **定位**：行业资讯抓取、筛选、结构化摘要、日报生成
- **触发场景**：获取最新资讯、生成日报、追踪热点、特定主题调研
- **核心工具**：weibo-hot, web-search, web-reader
- **输出位置**：`剪藏/` 或用户指定
- **工作流**：确定范围 → 多渠道抓取 → 筛选过滤 → 结构化整理 → 交付

---

## 生图助手 (image)

- **workspace**：`~/.claude/agents/image/`
- **定位**：AI 绘图、提示词模板管理、视觉设计
- **触发场景**：生成配图、封面图、信息图、插画、架构图
- **核心工具**：gemini-media
- **输出位置**：`附件/` 或用户指定
- **工作流**：理解需求 → 查找模板 → 编写提示词 → 调用工具 → 评估迭代 → 交付

---

## 社区助手 (community)

- **workspace**：`~/.claude/agents/community/`
- **定位**：小红书/微博运营、内容策划、互动管理
- **触发场景**：发帖、管理评论、查看数据、追踪热点、内容策划
- **核心工具**：xiaohongshu-skills, weibo-hot, web-access
- **输出位置**：各平台（草稿箱）
- **工作流**：内容策划 → 素材准备 → 平台适配 → 发布草稿 → 互动管理 → 数据复盘
