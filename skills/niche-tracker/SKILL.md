---
name: niche-tracker
description: >
  低粉爆款赛道分析 Skill。基于"七步开钱眼"方法论，自动在 YouTube/小红书搜索关键词、
  采集频道数据、按阈值筛选低粉高互动赛道，生成结构化报告到 Obsidian。
  触发词：赛道分析、低粉爆款、niche tracker、找赛道。
---

# Niche Tracker — 低粉爆款赛道分析

## 触发条件

当用户说以下类似话术时触发：
- "赛道分析"、"低粉爆款分析"、"找赛道"
- "niche tracker"、"niche 分析"
- "帮我分析 XX 平台的赛道"
- "七步开钱眼"（配合平台/关键词）

## 依赖

- **web-access** Skill：CDP 浏览器自动化（必须先加载）
- Obsidian 知识库路径：`~/Documents/study/github/Obsidian/`
- 报告输出目录：`~/Documents/study/github/Obsidian/AI探索报告/`

## 输入参数

| 参数 | 必填 | 默认值 | 说明 |
|------|------|--------|------|
| 平台 | 是 | — | `youtube` 或 `xiaohongshu` |
| 关键词 | 是 | — | 要分析的核心关键词（空格分隔多个） |
| 最低粉丝 | 否 | 0 | 筛选下限 |
| 最高粉丝 | 否 | 30000 | 筛选上限，超过此数的排除 |

## 执行流程（七步开钱眼）

### Step 1：搜索目标领域

使用 web-access CDP 打开目标平台：

**YouTube**：
1. `curl -s "http://localhost:3456/new?url=https://www.youtube.com/results?search_query={关键词}"`
2. 用 `/eval` 收集搜索结果中的视频卡片数据

**小红书**：
1. `curl -s "http://localhost:3456/new?url=https://www.xiaohongshu.com/search_result?keyword={关键词}"`
2. 用 `/scroll` 触发懒加载，`/eval` 提取笔记数据

**采集数据**：标题、链接、频道/账号名、播放量/点赞数

### Step 2：收集关键词

从搜索结果中提取高频关键词：

```javascript
// eval 提取标题文本后，用正则分词统计频率
const words = titles.match(/[\u4e00-\u9fa5]{2,4}|[a-zA-Z]+/gi);
```

输出 Top 15 关键词及出现频率。

### Step 3：深挖细分关键词

取 Top 5 关键词，逐个在平台搜索，扩大覆盖面。每个关键词搜索后收集新的视频/笔记数据。

**限流注意**：每个搜索间隔 3-5 秒，避免触发 429。

### Step 4：采集频道/账号数据

从收集的视频/笔记中提取去重的频道/账号列表，逐个访问：

**YouTube 频道页提取**：
- 订阅数：`#subscriber-count`
- 视频数：`yt-tab-shape` 中含"视频"的 tab
- 热门视频：`ytd-rich-item-renderer` 前 10 条

**小红书账号页提取**：
- 粉丝数、获赞数
- 近期笔记列表及互动数据

### Step 5：筛选候选

按阈值筛选：

| 条件 | 权重 | 说明 |
|------|------|------|
| 粉丝 < 最高粉丝阈值 | 30 分 | 低粉 = 机会窗口 |
| 竞争者 < 5 | 25 分 | 搜索同类内容的账号数量 |
| 播放/粉丝比 > 2x | 25 分 | 异常值 = 内容质量远超账号影响力 |
| 视频数 < 50 | 20 分 | 内容少但效果好 = 可复制模式 |

### Step 6：验证竞争

对 TOP 候选用其爆款标题的关键词搜索，统计同类内容创作者数量。

### Step 7：生成报告

写入 Obsidian `AI探索报告/` 目录。

**Frontmatter**：
```yaml
---
date: YYYY-MM-DD
tags: [learning, daily-journal, {平台}, 低粉爆款, {赛道关键词}]
publish: false
---
```

**报告结构**（参考已有报告格式）：
1. 研究方法说明
2. 关键词 Top 15 表格
3. 全部频道/账号数据表格（名称、链接、粉丝、内容数、互动数据、互动比）
4. TOP 3 候选详情（评分、数据、爆款分析、风险）
5. 爆款标题公式提炼
6. 行动建议（具体到选题方向、发布频率）

## 并行策略

当用户给出多个关键词时，可分治给子 Agent 并行分析：

- 每个子 Agent 负责 1 个关键词的完整 7 步流程
- 子 Agent 必须加载 web-access skill
- 共享 Chrome Proxy，通过不同 targetId 操作不同 tab
- 主 Agent 汇总结果生成最终报告

## 错误处理

| 错误 | 处理 |
|------|------|
| CDP 未启动 | 运行 `bash ~/.claude/skills/web-access/scripts/check-deps.sh` |
| 429 限流 | 等待 10 秒后重试，最多 3 次 |
| 页面加载超时 | 跳过当前项，继续下一项 |
| 数据提取失败 | 用 `/screenshot` 截图后视觉识别 |

## 与 youtube-gold-miner 的关系

`~/study/claude/youtube-gold-miner/miner.mjs` 是独立的 Playwright 脚本，可在纯 YouTube 场景下作为替代方案运行。本 Skill 主要依赖 web-access CDP，支持多平台。
