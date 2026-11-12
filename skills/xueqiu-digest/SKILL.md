---
name: xueqiu-digest
description: 雪球每日精选日报。通过浏览器 CDP 抓取、脚本评分、Claude 智能分析，写入投资工作区 素材/雪球日报/ 的每日笔记。触发词：雪球日报、雪球精选、xueqiu digest、每日雪球。
---

# 雪球每日精选日报

## 触发条件

当用户说"雪球日报"、"雪球精选"、"看看雪球"、"今日雪球"、"xueqiu digest" 时触发。

## 用户画像

用户是混合风格投资者，关注科技/AI/新能源和医药健康板块。目的：指导投资操作。偏好有数据有观点的长文，不要情绪帖。

## 架构

抓取通过浏览器 CDP 完成（雪球 HttpOnly cookies + WAF 导致 Python 直连不可用），评分用 Python 脚本，分析由 Claude 完成。

```
CDP 浏览器抓取（热门帖 + 自选股数据 + 个股讨论 + 关注的人原创帖） → JSON → Python 评分（含自选股/日记加分） → Claude 智能分析 → Obsidian 笔记
```

**自选股关联**：抓取脚本自动获取用户雪球自选股列表，并将自选股个股的帖子一并纳入评分。
**投资日记关联**：评分脚本读取 `private/投资日记.md` 中的观察个股，相关帖子获得加分并标记 `journal_focus`，在日报中单独标注。
**关注的人动态**：通过 `/statuses/home_timeline.json` API 抓取关注用户的原创帖+转发评论（过滤纯转发无评论的帖子），在日报中生成"👥 关注的人动态汇总"板块，**排在「今日三问」和「今日亮点」之后**，按作者分组展示。

## 日期确定规则

**日期必须从抓取结果 JSON 的 `date` 字段获取**，该字段是脚本运行时的 `new Date().toISOString().split("T")[0]`（UTC 日期）。不要使用系统提示中的 `currentDate`——它可能是会话开始时的快照，跨午夜 UTC 边界时会过期。

所有后续步骤中的 `YYYY-MM-DD` 占位符均指这个值。在第一步提取 JSON 后立即确定日期，贯穿整个流程。

## 工作流程

### 第一步：浏览器抓取（CDP）

加载 `web-access` skill。

1. 检查 CDP 可用性：
```bash
node ~/.agents/skills/web-access/scripts/check-deps.mjs
```

2. 用 `/new` 打开雪球：
```bash
curl -s "http://localhost:3456/new?url=https://xueqiu.com"
```
记下返回的 targetId。

3. 检查登录状态：用 `/eval` 执行以下检查。注意不要用 `[class*=login]` 选择器——雪球的隐藏登录弹窗 `.modal__login` 会误匹配。
```bash
curl -s -X POST "http://localhost:3456/eval?target=ID" --data-binary 'document.cookie.includes("u=") && document.title.includes("首页") ? "LOGGED_IN" : "NOT_LOGGED_IN"'
```
如果返回 `NOT_LOGGED_IN`，提示用户在 Chrome 中登录雪球后继续（CDP 使用用户日常 Chrome）。

4. 执行浏览器端抓取脚本。读取 `~/.agents/skills/xueqiu-digest/xueqiu_browser_fetch.js` 的全部内容，脚本路径可写成 `SKILL_DIR/xueqiu_browser_fetch.js`，用 `$(dirname)` 推导，通过 `/eval` 在页面上下文中执行。脚本路径是 `SKILL_DIR/xueqiu_browser_fetch.js`。脚本是 async IIFE，CDP eval 不会 await，所以立即返回 `"RUNNING"`。**不要依赖返回值判断完成**。

5. 等待脚本完成。脚本用 `window.__xueqiu_done` 信号通知完成（非空即完成）。

**必须耐心等，别提前放弃。** 雪球会间歇限流，正常一轮 3-5 分钟，被限流时脚本会自适应降速，最长可达 20 分钟（脚本内的 `MAX_TOTAL_MS`）。脚本自己有超时、限流冷却和「到点带着已有数据收尾」的保护，**不会永久挂住**，调用方只需要等它。

```bash
# 轮询等待完成：每 10 秒一次，最多 30 分钟（180 次）
# 注意必须用 --data-binary，不能用 -d：-d 会把内容按表单编码，长 JS 会触发 proxy 500
for i in $(seq 1 180); do
  result=$(curl -s -X POST "http://localhost:3456/eval?target=ID" --data-binary 'window.__xueqiu_done || "WAITING"' 2>/dev/null)
  echo "$result" | grep -q "WAITING" || { echo "$result"; break; }
  sleep 10
done
```
`window.__xueqiu_done` 值为 JSON 字符串（含 ok/total 等摘要），或 `{"ok":false,"error":"..."}` 表示失败。

判读摘要时必须看 `partial` / `throttled` / `warnings` 三个字段——它们会明确告诉你哪个环节被限流截断了（例如「关注动态：到时间预算，已翻 0 页」）。**如果 `partial=true`，日报里要如实标注"本轮部分环节因雪球限流未采全"，不要假装数据完整。**

另外：`curl -d` 传输长脚本会触发 proxy 500（实际是 URL 编码失败），执行脚本和读结果时**一律用 `--data-binary`**。

6. 提取结果。脚本将数据存入 `window.__xueqiu_result`。由于数据较大（通常 20-40KB），分块提取：
```bash
# 先获取长度
curl -s -X POST "http://localhost:3456/eval?target=ID" --data-binary 'window.__xueqiu_result.length'

# 分块提取（每次 8000 字符）
curl -s -X POST "http://localhost:3456/eval?target=ID" --data-binary 'window.__xueqiu_result.substring(0, 8000)'
curl -s -X POST "http://localhost:3456/eval?target=ID" --data-binary 'window.__xueqiu_result.substring(8000, 16000)'
# ... 直到取完
```

7. 拼接完整 JSON，保存到 `/tmp/xueqiu_digest/posts_YYYY-MM-DD.json`：
```bash
mkdir -p /tmp/xueqiu_digest
# 将拼接的 JSON 写入文件
```
**⚠️ 从拼接好的 JSON 中读取 `date` 字段作为日期**，后续所有步骤使用此日期。

8. 关闭 tab：
```bash
curl -s "http://localhost:3456/close?target=ID"
```

### 第二步：确定性评分（Python）

```bash
cd ~/ai/skills/xueqiu-digest && python3 xueqiu_score.py --date YYYY-MM-DD
```

如果用户指定了日期：
```bash
python3 xueqiu_score.py --date 2026-04-16
```

脚本读取 JSON，对每个帖子进行多维度评分（长度、数据密度、结构、估值、产业深度、观点、宏观、情绪惩罚、自选股加分），按总分排序，保留 Top 50。

**自选股加分**：帖子涉及用户雪球自选股中的个股，额外加 0-10 分（每只股票 +5，上限 10）。

**投资日记关注**：传入 `--journal` 参数指定投资日记路径，脚本提取其中的股票代码和名称（通过映射表），相关帖子标记 `journal_focus: true`。

完整命令：
```bash
python3 xueqiu_score.py --date YYYY-MM-DD --journal "/Users/chenjie/Documents/study/github/Obsidian/private/投资日记.md"
```

**三问输出**：脚本会在末尾打印「今日三问」——关注池每只股的命中篇数（含连续 0 命中天数）、触发器 T1–T7 命中情况。这段输出是日报首屏的直接来源，原样搬进笔记即可，不要二次加工。

- `--daily-dir`：历史日报目录，用于计算关注池连续 0 命中天数（默认 `/Users/chenjie/ai/invest/素材/雪球日报`，2026-11-12 起日报在投资工作区，不再在 Obsidian）
- 评分结果默认写入 `posts_YYYY-MM-DD_scored.json`，**不再覆盖原始抓取文件**——原始文件保留全量帖子，三问才能扫到被 Top 50 筛掉的提及
- 触发器关键词定义在 `xueqiu_score.py` 的 `TRIGGER_KW`，与 `投资/素材/触发器清单.md` 的 T1–T7 对应；改清单时同步改这里

**关注 ETF**（2026-11-05 新增）：恒生科技ETF华夏 `SH513180`（港股科技）、中证500增强ETF华泰柏瑞 `SH561550`。

- 抓取侧：`xueqiu_browser_fetch.js` 的 `FOCUS_ETFS` 负责。除自己的 symbol，还会搜一组**邻居标的**（港股科技取恒指/中概/腾讯阿里类宽基，500增强取中证500/1000/300 宽基）和名称关键词——ETF 自己的 symbol 时间线基本没帖，只盯它必然抓空。
- 评分侧：`xueqiu_score.py` 的 `FOCUS_ETFS` 给出 `etf_hits` 标记，并在 `three_questions.etf_focus` 里统计讨论篇数。
- 讨论帖**不进 Top N 竞争**，单独存在 JSON 的 `etf_posts`（正文 ≥200 字，最多 12 篇）；行情在 `etf_quotes`（一次 `quotec.json` 批量请求）。
- 要加/换 ETF：两边 `FOCUS_ETFS` 同步改（symbol、name、label、kw、symbols），否则日报里行情有、讨论没有，或者反过来。
- 成本：新增约 15 次请求（1 行情 + 14 搜索），按 600ms 间隔约 10 秒。限流时优先放弃 ETF 搜索，而不影响热门和关注动态。

### 第三步：Claude 智能分析

读取评分后的 JSON 文件（`/tmp/xueqiu_digest/posts_YYYY-MM-DD_scored.json`）。

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

### 第四步：生成日报笔记

输出到：`/Users/chenjie/ai/invest/素材/雪球日报/YYYY-MM-DD.md`

> 2026-11-12 起投资人肉内容统一放在投资工作区，**不要再往 Obsidian 写**。历史 141 篇日报已一并迁入该目录，三问的连续性依赖它。

**`YYYY-MM-DD` 必须使用第一步 JSON 中的 `date` 字段**，不要用其他来源的日期。

#### 笔记模板

```markdown
---
tags:
title: 雪球日报 {{date}}
date: {{date}}
lastmod: {{date}}
---

# 雪球日报 {{date}}

> 昨日雪球新帖精选。共抓取 {{total_fetched}} 篇，筛选 {{total_filtered}} 篇。自选股 {{watchlist_count}} 只。关注动态 {{following_count}} 条。

## 今日三问

> [!question] 先回答这三个问题，再往下看。答完这两问第 3 问自然有答案。

**1. 关注池有异动吗？**

{{从脚本输出的「今日三问」原样搬：每只关注股命中篇数；0 命中的标注连续多少天}}

**2. 触发器命中几个？**

{{脚本输出的 T1–T7 命中情况 + 每条的示例标题。没有命中就写「无」——这不是坏消息，说明今天不用动}}

**3. 今天要动作吗？**

{{基于上面两问给结论：无命中 → 「不动，继续观察」；有命中 → 指向 [[触发器清单]] 里对应的判定标准}}

---

## 今日亮点

> [!abstract] 一句话总结今天最值得关注的 2-3 个观点

---

## 👥 关注的人动态汇总

> [!info] 你关注的雪球用户近两日动态（原创帖+转发评论），共 {{following_count}} 条，按信息价值筛选。

### {{author_name}}（{{post_count}} 条：{{original_count}} 原创 + {{retweet_comment_count}} 转发评论）

- **{{key_point}}**：{{detail}}
- ...

---

## 📓 投资日记关注

> [!important] 以下帖子涉及你投资日记中观察的个股（{{journal_stocks}}），需要着重关注

### 1. {{title}}

**作者**：{{author}} | **分类**：{{category}} | **脚本评分**：{{script_score}} | **Claude 评分**：{{claude_score}}

**核心观点**：2-3 句话概括

**涉及股票**：`{{stock_codes}}`

> [原文链接]({{url}})

---

## 关注 ETF

> [!info] 恒生科技ETF华夏（港股科技）· 中证500增强ETF华泰柏瑞 —— 数据来自 `etf_quotes`

| ETF | 代码 | 现价 | 涨跌幅 | 讨论篇数 |
|-----|------|------|--------|---------|
| {{name}} | {{symbol}} | {{current}} | {{percent}}% | {{etf_talk_count}} |

> [!tip] 今日讨论要点
> 1-3 条从 `etf_posts` 里提炼：谁在看多/看空、给了什么理由、有没有涉及溢价/折价、份额变化、指增超额表现

---

## 自选股概览

> [!info] 你的雪球自选股今日行情

| 股票 | 代码 | 现价 | 涨跌幅 | 日记关注 |
|------|------|------|--------|---------|
| {{name}} | {{symbol}} | {{current}} | {{percent}}% | {{journal_mark}} |

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

| # | 标题 | 作者 | 评分 | 日记 | 一句话总结 | 链接 |
|---|------|------|------|------|-----------|------|
| 1 | ... | ... | ... | 📓 | ... | [原文]({{url}}) |

---

## 涉及股票汇总

| 股票/板块 | 出现次数 | 多空倾向 | 日记关注 | 值得关注 |
|----------|---------|---------|---------|---------|
| 光模块（中际/新易盛） | 2 | 偏多（结构性） | ✓ | 关键变化 |

---

## 涉及股票汇总

| 股票/板块 | 出现次数 | 多空倾向 | 日记关注 | 值得关注 |
|----------|---------|---------|---------|---------|
| 光模块（中际/新易盛） | 2 | 偏多（结构性） | ✓ | 关键变化 |

---

> [!tip] 使用说明
> - 👥 关注动态含转发评论：博主转发时的评论也是原创观点，已纳入分析
> - 📓 投资日记关注：涉及你正在观察的个股，优先阅读
> - ⭐ 必读：数据扎实、观点独到，值得仔细研究
> - 📖 推荐：有参考价值，快速浏览
> - 🔍 快速浏览：看标题即可
> - 共筛选 {{total}} 篇帖子 + {{following_count}} 条关注动态，有 {{必读数}} 篇真正值得深读
```

### 第五步：输出总结

最后向用户输出：
1. 今日共筛选了多少帖子
2. 必读/推荐/浏览分别几篇
3. 最值得关注的 1-2 个观点的简短总结
4. 笔记文件路径

## 技术要点

- **为什么用 CDP 而不是 Python 直连**：雪球的 `xq_a_token` 是 HttpOnly cookie，`document.cookie` 无法获取；同时雪球有 WAF 反爬，Python requests 会被拦截返回验证页面。浏览器内的 `fetch()` 自动携带所有 cookies（含 HttpOnly），是唯一可行的方式。
- **登录检查不能用 `[class*=login]`**：雪球页面有隐藏的 `.modal__login` 弹窗元素，即使已登录也会被 `[class*=login]` 匹配到，导致误判为未登录。正确方式是检查 `document.cookie.includes("u=")` + 页面标题包含"首页"。
- **CDP eval 不会 await async IIFE**：脚本是 async IIFE，CDP eval 返回的是 Promise 对象（显示为 `{"type":"undefined"}`），不会等待异步完成。脚本通过 `window.__xueqiu_done` 信号通知完成，调用方必须轮询此信号而非依赖 eval 返回值。
- **数据提取要分块**：抓取结果通常 20-40KB（含自选股数据后可能更大），超过 CDP eval 的单次返回限制。用 `substring()` 分 8000 字符一块提取后拼接。
- **两个 API 响应结构不同**：热门帖子 API 返回 `original_status` 包装，个股时间线 API 返回扁平结构。浏览器脚本已处理。
- **关注的人动态 API**：`/statuses/home_timeline.json?page=N&count=50`，返回数组格式。API 每页实际返回约 16 条（不是 50），所以**分页终止条件必须用 `items.length === 0`，不能用 `items.length < PAGE_SIZE`**（否则第 1 页就 break）。翻页直到遇到昨天之前的帖子为止（通常需 5-8 页）。保留原创帖和转发评论（`description` 非空的转发帖），过滤纯转发无评论的帖子。最终通常 60-80 条。
- **自选股 API**：`/v4/stock_portfolio/stocks.json?pid=-1&size=1000`，返回用户的默认自选股列表（名称、价格、涨跌幅等）。自选股中不在硬编码列表里的个股也会被抓取帖子，上限 20 只避免耗时过长。
- **投资日记关联**：通过 `STOCK_NAME_MAP` 映射表将中文股票名称转为代码，同时支持正则提取 `SH/SZ` 代码和 `[[...]]` 链接。映射表需要随投资日记内容更新。

## 注意事项

- 不要编造帖子内容，严格基于 JSON 数据
- 如果 CDP 连接失败或 Chrome 未开启 remote debugging，引导用户设置
- 如果雪球未登录，提示用户在 Chrome 中登录后继续（CDP 使用用户日常 Chrome）
- 评分要客观，不要因为帖子看多就给高分
- "真理掌握在少数人手里"——非主流但数据扎实的观点应该得高分
- 涉及股票汇总可以帮助用户快速发现当日热点
- 关注的人动态以短言论为主，重点提取有数据、有观点的内容，跳过纯感悟/生活类发言
- 关注的人动态**含转发评论**：博主转发时的评论（`description` 字段非空）也算原创发言，需要纳入分析和日报
- 投资日记关注的帖子用 📓 标记，放在日报最前面，便于优先阅读
- 自选股概览表格直接展示当日行情数据，无需额外查询
- 旧文件 `xueqiu_fetch.py` 已弃用（Python 直连不可用），保留仅供参考

## 文件清单

| 文件 | 用途 |
|------|------|
| `xueqiu_browser_fetch.js` | 浏览器端抓取脚本，通过 CDP eval 执行 |
| `xueqiu_score.py` | Python 确定性评分脚本 |
| `config.json` | 板块配置（cookies 字段已不需要，CDP 自动携带） |
| `config.example.json` | 配置模板 |
| `xueqiu_fetch.py` | [已弃用] 旧的 Python 抓取+评分脚本 |
