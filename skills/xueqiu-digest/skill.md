---
name: xueqiu-digest
description: 雪球每日精选日报。通过浏览器 CDP 抓取、脚本评分、Claude 智能分析，生成 Obsidian 每日笔记。触发词：雪球日报、雪球精选、xueqiu digest、每日雪球。
---

# 雪球每日精选日报

## 触发条件

当用户说"雪球日报"、"雪球精选"、"看看雪球"、"今日雪球"、"xueqiu digest" 时触发。

## 用户画像

用户是混合风格投资者，关注科技/AI/新能源和医药健康板块。目的：指导投资操作。偏好有数据有观点的长文，不要情绪帖。

## 架构

抓取通过浏览器 CDP 完成（雪球 HttpOnly cookies + WAF 导致 Python 直连不可用），评分用 Python 脚本，分析由 Claude 完成。

```
CDP 浏览器抓取 → JSON → Python 评分 → Claude 智能分析 → Obsidian 笔记
```

## 工作流程

### 第一步：浏览器抓取（CDP）

加载 `web-access` skill。

1. 检查 CDP 可用性：
```bash
bash ~/.claude/skills/web-access/scripts/check-deps.sh
```

2. 用 `/new` 打开雪球：
```bash
curl -s "http://localhost:3456/new?url=https://xueqiu.com"
```
记下返回的 targetId。

3. 检查登录状态：用 `/eval` 检查页面是否显示已登录。如果未登录，提示用户在 Chrome 中登录雪球后继续。

4. 执行浏览器端抓取脚本。读取 `~/.claude/skills/xueqiu-digest/xueqiu_browser_fetch.js` 的全部内容，通过 `/eval` 在页面上下文中执行。

5. 提取结果。脚本将数据存入 `window.__xueqiu_result`。由于数据较大（通常 20-40KB），分块提取：
```bash
# 先获取长度
curl -s -X POST "http://localhost:3456/eval?target=ID" -d 'window.__xueqiu_result.length'

# 分块提取（每次 8000 字符）
curl -s -X POST "http://localhost:3456/eval?target=ID" -d 'window.__xueqiu_result.substring(0, 8000)'
curl -s -X POST "http://localhost:3456/eval?target=ID" -d 'window.__xueqiu_result.substring(8000, 16000)'
# ... 直到取完
```

6. 拼接完整 JSON，保存到 `/tmp/xueqiu_digest/posts_YYYY-MM-DD.json`：
```bash
mkdir -p /tmp/xueqiu_digest
# 将拼接的 JSON 写入文件
```

7. 关闭 tab：
```bash
curl -s "http://localhost:3456/close?target=ID"
```

### 第二步：确定性评分（Python）

```bash
cd ~/.claude/skills/xueqiu-digest && python3 xueqiu_score.py --date YYYY-MM-DD
```

如果用户指定了日期：
```bash
python3 xueqiu_score.py --date 2026-04-16
```

脚本读取 JSON，对每个帖子进行多维度评分（长度、数据密度、结构、估值、产业深度、观点、宏观、情绪惩罚），按总分排序，保留 Top 50。

### 第三步：Claude 智能分析

读取评分后的 JSON 文件（`/tmp/xueqiu_digest/posts_YYYY-MM-DD.json`）。

对每个帖子进行**智能评分**（这是脚本确定性评分的补充）：

#### Claude 智能评分维度（每项 1-5 分）

| 维度 | 评分标准 |
|------|---------|
| **推理质量** | 假设→证据→结论的逻辑链条是否完整 |
| **数据可信度** | 引用的数据是否具体、可验证、来源合理 |
| **独特洞察** | 是否有市场共识之外的观点，非人云亦云 |
| **可操作性** | 是否能直接指导买入/卖出/持有决策 |
| **风险意识** | 是否讨论了风险因素和假设失败的场景 |

#### Claude 综合建议

对每个帖子给出：**必读** / **推荐** / **浏览** / **跳过**

### 第四步：生成 Obsidian 笔记

输出到：`/Users/chenjie/Documents/study/github/Obsidian/投资研究/雪球日报/YYYY-MM-DD.md`

#### 笔记模板

```markdown
---
tags:
  - 投资研究
  - 雪球日报
title: 雪球日报 {{date}}
date: {{date}}
lastmod: {{date}}
---

# 雪球日报 {{date}}

> 昨日雪球新帖精选。共抓取 {{total_fetched}} 篇，筛选 {{total_filtered}} 篇。

## 今日亮点

> [!abstract] 一句话总结今天最值得关注的 2-3 个观点

---

## ⭐ 必读（Claude 评分 20+）

### 1. {{title}}

**作者**：{{author}} | **分类**：{{category}} | **脚本评分**：{{script_score}} | **Claude 评分**：{{claude_score}}

**核心观点**：2-3 句话概括帖子的核心判断和预测

**关键数据**：
- 数据点 1
- 数据点 2
- 数据点 3

**逻辑链条**：简述假设 → 推理 → 结论

**涉及股票**：`{{stock_codes}}`

**风险提示**：帖子可能存在的问题或评论区争议

> [原文链接]({{url}})

---

## 📖 推荐（Claude 评分 15-19）

（同上格式，可略微简化）

---

## 🔍 快速浏览（脚本评分 30+，Claude 评分 < 15）

用表格形式：

| # | 标题 | 作者 | 评分 | 一句话总结 | 链接 |
|---|------|------|------|-----------|------|
| 1 | ... | ... | ... | ... | [原文]({{url}}) |

---

## 涉及股票汇总

| 股票/板块 | 出现次数 | 多空倾向 | 值得关注 |
|----------|---------|---------|---------|
| 光模块（中际/新易盛） | 2 | 偏多（结构性） | 关键变化 |

---

> [!tip] 使用说明
> - ⭐ 必读：数据扎实、观点独到，值得仔细研究
> - 📖 推荐：有参考价值，快速浏览
> - 🔍 快速浏览：看标题即可
> - 共筛选 {{total}} 篇，有 {{必读数}} 篇真正值得深读
```

### 第五步：输出总结

最后向用户输出：
1. 今日共筛选了多少帖子
2. 必读/推荐/浏览分别几篇
3. 最值得关注的 1-2 个观点的简短总结
4. 笔记文件路径

## 技术要点

- **为什么用 CDP 而不是 Python 直连**：雪球的 `xq_a_token` 是 HttpOnly cookie，`document.cookie` 无法获取；同时雪球有 WAF 反爬，Python requests 会被拦截返回验证页面。浏览器内的 `fetch()` 自动携带所有 cookies（含 HttpOnly），是唯一可行的方式。
- **数据提取要分块**：抓取结果通常 20-40KB，超过 CDP eval 的单次返回限制。用 `substring()` 分 8000 字符一块提取后拼接。
- **两个 API 响应结构不同**：热门帖子 API 返回 `original_status` 包装，个股时间线 API 返回扁平结构。浏览器脚本已处理。

## 注意事项

- 不要编造帖子内容，严格基于 JSON 数据
- 如果 CDP 连接失败或 Chrome 未开启 remote debugging，引导用户设置
- 如果雪球未登录，提示用户在 Chrome 中登录后继续（CDP 使用用户日常 Chrome）
- 评分要客观，不要因为帖子看多就给高分
- "真理掌握在少数人手里"——非主流但数据扎实的观点应该得高分
- 涉及股票汇总可以帮助用户快速发现当日热点
- 旧文件 `xueqiu_fetch.py` 已弃用（Python 直连不可用），保留仅供参考

## 文件清单

| 文件 | 用途 |
|------|------|
| `xueqiu_browser_fetch.js` | 浏览器端抓取脚本，通过 CDP eval 执行 |
| `xueqiu_score.py` | Python 确定性评分脚本 |
| `config.json` | 板块配置（cookies 字段已不需要，CDP 自动携带） |
| `config.example.json` | 配置模板 |
| `xueqiu_fetch.py` | [已弃用] 旧的 Python 抓取+评分脚本 |
