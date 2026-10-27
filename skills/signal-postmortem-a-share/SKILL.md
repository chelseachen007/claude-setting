---
name: signal-postmortem-a-share
description: A 股交易信号的事后复盘与归因。给每个已做或想做过的信号记结局，算 5 日/20 日实际收益，分类成真阳性 / 假阳性 / 错失机会 / 正确回避 / 环境不匹配，并按信号来源汇总胜率，判断哪类信号值得继续用。触发词：信号复盘、交易复盘、这个信号准不准、复盘一下这笔、看看我最近的胜率、postmortem、归因分析。
---

# A 股信号复盘

## 这个技能解决什么问题

大多数人复盘只会说「这单亏了/赚了」，于是永远不知道自己**错在哪一环**。

亏损有三种完全不同的原因，处理方式也完全不同：

| 原因 | 表现 | 该怎么办 |
|---|---|---|
| 信号本身不行 | 同来源的信号反复亏 | 停用这个来源，或改造筛选条件 |
| 大盘环境变了 | 单个信号没问题，但整体转熊 | 需要的是仓位和择时规则，不是换信号 |
| 执行跑偏 | 有信号但没做，或做早了做晚了 | 修的是纪律，不是信号 |

这个技能把每个信号按 5 日 / 20 日的**实际收益**分类归因，跑多了就能看出系统性偏差在哪。

## 什么时候用

- 一笔交易平仓后，想记下结局
- 周末/月末做例行复盘，一批信号到了观察期
- 发现「最近老亏」，想确认是运气差还是某类信号真的不行
- 想给某个技能或选股方法做质量审计

## 五类结局

| 分类 | 含义 |
|---|---|
| `TRUE_POSITIVE` | 做了，方向对了 |
| `FALSE_POSITIVE` | 做了，方向错了，且不是环境导致 |
| `MISSED_OPPORTUNITY` | 没做，但事后证明该做 |
| `GOOD_SKIP` | 没做，事后证明避开是对的 |
| `REGIME_MISMATCH` | 做了但亏了，期间大盘环境发生反转——不是信号本身的问题 |

判定用 **20 日收益**做主判据（A 股 5 日噪声太大），5 日只作参考。方向为 `SHORT` 时收益取反算。

`REGIME_MISMATCH` 需要你填入 `regime_at_signal` 和 `regime_at_exit`，两者不同且单笔亏损 > 3% 才判定。没有环境信息就会归到 `FALSE_POSITIVE`——**归因不准的代价是错误地废掉一个还能用的方法**，所以尽量填。

## 怎么用

### 第 1 步：写信号清单

```json
{
  "signals": [
    {
      "code": "600519",
      "name": "贵州茅台",
      "signal_date": "2026-09-01",
      "predicted_direction": "LONG",
      "source_skill": "stock-investment-report",
      "taken": true,
      "regime_at_signal": "RISK_ON",
      "regime_at_exit": "RISK_OFF",
      "notes": "突破后买入，止损设在缺口下沿"
    }
  ]
}
```

| 字段 | 必填 | 说明 |
|---|---|---|
| `code` | ✅ | 6 位代码 |
| `signal_date` | ✅ | 信号产生日（`YYYY-MM-DD`），入场价取该日或之后第一个交易日收盘 |
| `predicted_direction` | — | `LONG`（默认）或 `SHORT`。A 股融券做空才填 `SHORT` |
| `source_skill` | — | 信号来自哪个技能/方法，默认 `manual`。汇总按这个字段分组 |
| `taken` | — | 是否真的做了这笔，默认 `true`。填 `false` 用来统计错失机会 |
| `regime_at_signal` / `regime_at_exit` | — | 信号时和观察期末的大盘状态，用来区分环境不匹配 |
| `notes` | — | 当时的判断理由，复盘最值钱的东西 |

### 第 2 步：跑复盘

```bash
python3 scripts/postmortem.py \
  --signals state/signals/trades.json \
  --output-dir reports/postmortem
```

参数：

| 参数 | 作用 |
|---|---|
| `--signals` | 信号清单 JSON |
| `--output-dir` | 输出目录，默认 `reports/postmortem` |
| `--min-sample` | 按来源下结论所需最小样本，默认 `10` |
| `--json-only` | 只输出 JSON |

### 第 3 步：读汇总

输出两份文件：

- `reports/postmortem/postmortem_<时间>.json` —— 逐条明细 + 汇总
- `reports/postmortem/postmortem_summary_<时间>.md` —— 给人看的报告

汇总表按 `source_skill` 分组，给出样本量、真阳性数、假阳性数、环境不匹配数、胜率、5 日均收益和结论：

| 结论 | 触发条件 | 含义 |
|---|---|---|
| `KEEP` | 样本 ≥ 门槛 且 胜率 ≥ 60% 且 均值为正 | 继续用 |
| `WATCH` | 样本 ≥ 门槛 但胜率在 40-60% | 优势不明显，继续观察 |
| `REVIEW` | 样本 ≥ 门槛 但 胜率 ≤ 40% | 该改造或停用 |
| `INSUFFICIENT` | 样本 < 门槛 | 不下结论 |

## 数据来源

行情走腾讯财经公开日线接口（前复权），**无需 API Key**。

已知坑：本机配了 `http_proxy`，脚本已显式绕过代理（`urllib.request.ProxyHandler({})`）。如果你在别的环境复用它，别删这行，否则会 502。

## 和别的技能怎么配

| 场景 | 用哪个 |
|---|---|
| 下单前过关卡、留痕 | `a-share-pre-trade-gate` |
| 选股和估值 | `stock-investment-report` |
| 多空观点对打 | `stock-debate-analysis` |
| 拉行情、财务、北向资金 | `cn-finance-toolkit` |
| **事后归因、判断方法好坏** | **本技能** |

完整闭环：**选股 → 辩论 → 下单前关卡 → 执行 → 复盘归因**。关卡日志在 `state/journal/trade-gate/`，复盘时把 `realized_pnl` 回填进去，冷静期检测才有效。

## 几条原则

1. **每条结局都要归到来源**。不写 `source_skill`，复盘就变成一堆散落的对错，学不到东西。
2. **样本不够就别下结论**。连亏三次不代表方法废了，连赚三次也不代表有效。门槛默认 10，别为了「看出结论」把它调低。
3. **环境不匹配不算信号失败**。把它和假阳性混在一起统计，会让你在熊市里误杀所有正常方法。
4. **诚实记录没做的信号**。`taken: false` 的错失机会同样值钱——它说明你可能过于保守。
5. **复盘的目的不是让心情好过**，是找出「我到底在哪一步系统性地错」。表格不好看才是它的价值。
