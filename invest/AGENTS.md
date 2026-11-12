# AGENTS.md — 投资工作区规则

> 这是本目录的唯一规则源。新来的 agent 先读这个文件，再动手。
> 修改规则时：先改这个文件，再改实践。不要反过来。

## 这是什么

一个「研究 → 结论 → 复用」的工作区，不是笔记仓库，也不是自动交易系统。

产出只有一个衡量标准：**半年后回看，能不能一眼说清「当时凭什么这么判断、后来对不对」**。

## 目录结构

```
投资/
├── AGENTS.md              ← 本文件
├── 研究/                   ← 所有研究，一个专题一个目录
│   └── <主题>-<YYYYMMDD>/
│       ├── 研究.md         ← 正文（结论先行）
│       ├── 方法.md         ← 数据口径、做了什么、哪几条没核实
│       ├── 数据/           ← 原始快照 JSON（抓取日状态，不覆盖）
│       └── 脚本/           ← 只用一次的脚本放这，跟数据一起归档
├── 工具/                   ← 跨研究复用，进这里要过「用过两次」的门槛
│   ├── 抓数/               ← fetch_eastmoney.py：东财行情/财报/资金流
│   ├── 数据湖/             ← lake.py、fact_card.py：本地 duckdb 数据湖查询
│   ├── 策略/               ← kelly/：仓位算法与速查表
│   └── 盯盘/               ← 盯盘.py：关注池 + 触发器每日机械检查（默认沉默）
├── 素材/                   ← 2026-11-12 从 Obsidian 投资研究/ 迁入的历史笔记与原始数据
│   ├── 个股分析/            ← 多空辩论、个股研究（66 篇）
│   ├── 选股分析/            ← 六线选股
│   ├── 雪球大佬图鉴/         ← 雪球大 V 拆解
│   ├── 雪球日报/            ← 每日日报，由 xueqiu-digest 技能每晚写入
│   ├── 航天航空/ 半导体/     ← 板块研究
│   ├── youdata/            ← 有数 BI 指标映射脚本与 CSV
│   └── *.md *.csv *.json    ← 散篇研究、国家队持仓原始数据
├── 知识库/                 ← 跨研究复用的方法论（政策解读法、估值口径等）
├── 配置/                   ← cnequity.toml 等工具配置
├── scripts/                ← 运维脚本：lake-watchdog.sh、cne-wb（cnequity 包装器）
├── logs/                   ← 运行日志（看门狗、拉取记录）
├── .tmp/                   ← 临时文件，超过 7 天自动清理
├── .archive/               ← 2 个月没动过的东西，按日期归档
└── .venv/                  ← Python 环境（cnequity 0.18.0，Python 3.13.12）
```

**根目录只放 AGENTS.md 和上面这些目录，不放任何散文件。**

## 数据湖在别处（2026-11-12 迁出）

行情数据湖 **不在本目录**，在 `~/Data/cnequity/`（2.6G，87000+ 文件）：

```
~/Data/cnequity/
├── cnequity/          ← 主数据湖（curated/derived/duckdb/meta），cnequity.toml 的 root 指这里
└── cnequity-demo/     ← 演示库
```

**这是刻意的分离**：代码和规则进 `~/ai/invest/`（可 Git、体积小），数据湖留在外面（可重建、体积大）。
数据湖只通过 `cnequity` CLI 操作，不手改 parquet。绑定的路径有四处，改任一处要同步改其余三处：

| 位置 | 字段 |
|---|---|
| `配置/cnequity.toml` | `root = "/Users/chenjie/Data/cnequity/cnequity"` |
| `~/Data/cnequity/cnequity/meta/state/web_scheduler/settings.json` | `config_path` / `working_directory` / `backup_root` |
| `~/Library/LaunchAgents/com.cnequity.web.706c3d40b7beb570.plist` | `--scheduler-lock-dir`、日志路径 |
| `~/Library/LaunchAgents/com.cnequity.lake-serve.plist` | `StandardOut/ErrorPath` |

## 三条硬规则

### 1. 一个研究 = 一个目录，不按 md 文件搜

新研究开目录 `研究/<主题>-<YYYYMMDD>/`。同一个专题第二次做，在同目录加 `研究-v2.md` 或新开目录，**不要覆盖旧文件**——旧结论本身就是复盘素材。

### 2. 脚本进 `工具/` 要过门槛：用过两次

- 第一次用 → 放 `研究/<专题>/脚本/`
- 第二次还要用 → 提到 `工具/` 并改造成可复用（带 argparse、路径无关）

**脚本必须路径无关。** 用 `Path(__file__).resolve().parent` 定位自己的目录，不要依赖当前工作目录，也不要把绝对路径写死。2026-11-11 迁移时 kelly 的 5 个脚本就是因为依赖 cwd 全部失效。

### 3. 数据快照不覆盖

`数据/` 里的 JSON 是「某一天抓到的市场状态」。同一天重抓可以覆盖，跨天抓的一律新文件，文件名带日期。

### 4. 素材/ 只进不改结构

`素材/` 是历史沉淀区（2026-11-12 从 Obsidian 迁入），不是新研究的落脚点：

- 老的个股/板块笔记 **原样保留**，不按新规范重排目录，不复原 `方法.md`
- `雪球日报/` 由技能每日写入，日报文件名固定 `YYYY-MM-DD.md`，**同一天重跑覆盖，跨天新增**
- 需要基于老笔记做新研究 → 新建 `研究/<主题>-<YYYYMMDD>/`，老笔记只引用不改写
- 触发器清单 `素材/触发器清单.md` 是日报「今日三问」的数据源，改它要同步改 `xueqiu_score.py` 的 `TRIGGER_KW`

## 数据抓取约定

**统一走 `工具/抓数/fetch_eastmoney.py`，不要再写一次性抓取脚本。**

```bash
PY=.venv/bin/python3
$PY 工具/抓数/fetch_eastmoney.py quote 603986 300308      # 个股快照
$PY 工具/抓数/fetch_eastmoney.py board CPO --days 500     # 板块日线
$PY 工具/抓数/fetch_eastmoney.py flow 半导体设备           # 主力资金 今日/5/20/60 日
$PY 工具/抓数/fetch_eastmoney.py fin 2026-09-30 --out 研究/x-20261112/数据/fin.json
```

作为库：`sys.path.insert(0, '工具/抓数')` 后 `import fetch_eastmoney as F`。

### 接口踩坑清单（都在 fetch_eastmoney.py 里处理了，绕过它就会重新踩）

| 坑 | 症状 | 做法 |
|---|---|---|
| 本机代理 | 所有东财接口超时或 502 | `ProxyHandler({})` 绕过 |
| f43/f162/f167 精度 | 价格变成 24445 | 一律 /100 |
| `RPT_LICO_FN_CPD` 列名 | code 9501「返回字段参数不存在」 | 不要写 NOTICE_DATE / DEDUCT_PARENT_NETPROFIT / OPERATE_INCOME |
| 现金流/资产负债 filter | 「REPORTDATE 列不存在」 | 用 `REPORT_DATE='xxx 00:00:00'` |
| 大模型网关指纹 | 11128 Illegal API invocation | 见 `~/ai/memory/MEMORY.md`，与本目录无关但会咬人 |

### 口径纪律

**PE 一律标清楚是哪个口径。** 静态 PE（去年年报）写 `PE25A`，TTM 写 `PE(TTM)`。2026 年很多公司利润爆发，两者能差 3 倍。

**板块涨跌用东财板块指数自算，必须注明「自算口径」。** 和申万、同花顺会差 10%~30%。

## 盯盘（工具/盯盘/）

**分工**：雪球日报回答「今天大家在聊什么」；盯盘回答「我的票和触发器今天有没有真的动」。

```bash
PY=.venv/bin/python3
$PY 工具/盯盘/盯盘.py            # 默认沉默：没信号就一句话
$PY 工具/盯盘/盯盘.py --force    # 全量打印（人工排查）
$PY 工具/盯盘/盯盘.py --json     # 机器可读，给中台/子代理
$PY 工具/盯盘/盯盘_test.py       # 改规则后必跑，离线断言
```

- **规则只写机械可判定的条件**（`watchlist.json`）。「值不值得买」这类判断留在 `素材/触发器清单.md` 和 `投资日记`，不塞进脚本。
- **沉默是特性，不是故障。** 只有 `actionable`（阈值真到了）和 `state_change`（站上/跌破 20 日线、回撤带移动 10pct）才会打印；同一 id 当天只报一次。
- **`--advance` 会推进状态文件**，只在人工确认输出无误后手动加，定时任务（`com.user.dingpan`，工作日 16:45）里才自动带。
- **去重在推送层，不在检查层。** 已报过的信号**永远留在 report 里**，只加 `already_reported: true` 标记；
  只有 `--mark-alert`（notify=True）才写 `fired_today`。**否则次日早报会拿到空 fired，误报「今天什么都不用做」——而 T 线可能早已过线。**（2026-11-12 踩过）
- **信号正文必须有主体。** 宏观触发器没有个股名，打印时用 `group`（触发器/商品）兜底，不能打出 `[T2]：...` 这种空主体。
- 行情源不用 push2（本机常年限流），走腾讯快照/日K + 新浪商品 + 东财 datacenter 宏观。脚本里已写死，别换回 push2。
- 宏观指标目前**没有核心 CPI**（东财无此字段），T1 用整体 CPI 同比代偿；要精确判定得补统计局口径。

## 研究怎么写

`研究.md` 的 frontmatter：

```yaml
---
title: 主题
date: YYYY-MM-DD
type: 政策研究 | 候选筛选 | 个股分析 | 复盘
tags: []
status: 初稿 | 定稿 | 已复盘 | 已废弃
---
```

正文结构（按需裁剪，但顺序不要乱）：

1. **结论** — 第一段就要能单独看懂，不铺垫背景
2. **数据/证据** — 表格优先，每个数字标来源和口径
3. **可执行判断** — 分「可以做 / 不要做 / 触发条件」三类
4. **不确定项** — 哪些没核实、哪些是自媒体口径、哪些是简化计算

### 没核实的东西必须标出来

用户明确要求「不说谎，不知道就说不知道」。政策文号、补贴金额、产能数字这类，**没用原始政府网站核对过就不能写「已确认」**，要写来源性质（官方原文 / 二手转载 / 估算）。

第七节「不确定项」不是免责声明，是给人看的行动清单。

## 复盘机制

研究完成后 1~3 个月，回来补一段：

```markdown
## 复盘（YYYY-MM-DD）
- 当时的判断：...
- 实际结果：...
- 错在哪：数据错 / 逻辑错 / 环境变了
```

用 `signal-postmortem-a-share` 技能算 5/20 日收益归因。**不复盘的研究等于没做。**

## 与外部系统的关系

- **Obsidian 知识库**：`/Users/chenjie/Documents/study/github/Obsidian/`（投资内容已迁出，原 `投资研究/` 只剩指路索引页）
- **雪球日报**：由 `~/.agents/skills/xueqiu-digest` 技能每晚写入本目录 `素材/雪球日报/`，历史日报目录同此。**不要再往 Obsidian 写**
- **交易纪律**：下单前跑 `a-share-pre-trade-gate` 技能，本目录的结论不能替代它
- **全局规则**：`~/ai/rules/global.md`（本文件是它的子集，冲突时以全局为准）

## 清理约定

- `.tmp/` 里超过 7 天的直接删
- `.archive/` 里超过半年、体积大的（>100MB）问一句再删
- 数据湖 `~/Data/cnequity/` 只通过 `cnequity` CLI 操作，不手改 parquet
