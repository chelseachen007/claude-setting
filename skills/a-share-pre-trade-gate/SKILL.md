---
name: a-share-pre-trade-gate
description: A 股下单前的纪律关卡。手动买入/加仓前跑一遍，检查有没有写下来的计划、止损定了没、仓位和风险金额超没超、亏钱后是不是在报复窗口中、大盘状态允不允许开新仓，输出 GO / REVIEW_REQUIRED / NO_GO。触发词：下单前检查、纪律关卡、能不能买、这笔单能不能下、帮我过一遍checklist、pre-trade gate、交易纪律检查。
---

# A 股下单前纪律关卡

## 这个技能解决什么问题

大多数亏钱不是选错股，是**没按计划执行**：临时加仓、亏了急着回本、没定止损就买、大盘已经转弱还在开新仓。

这个技能把「下单前该问自己的几个问题」固化成一个强制检查，跑完给你明确的 `GO` / `NO_GO`，并把当时怎么想的记下来。

它是**离线顾问，不连接券商、不下单、不撤回订单**。`GO` 只代表「符合你自己定的纪律」，不代表「这票会涨」。

## 什么时候用

- 准备手动买入或加仓之前（每次都要跑，不是跑一次就完）
- 刚割肉/止损完，想马上再买一单时——重点检查报复交易
- 大盘急跌、情绪不稳时，想知道现在到底该不该开新仓
- 想量化「我到底多守纪律」，给复盘提供数据

## 四类决策

| 决策 | 含义 | 怎么办 |
|---|---|---|
| `GO` | 全部规则通过 | 可以下单，但仓位按计划来 |
| `NO_GO` | 触发了纪律规则 | **不要下单**，先解决列出的每一条 |
| `REVIEW_REQUIRED` | 信息不全（缺止损、缺风险金额、大盘状态未知） | 补齐信息重跑 |
| `NO_ACTIONABLE` | 清单里没有可下单的标的 | 只是记录，什么都没该下 |

优先级：`NO_GO` > `REVIEW_REQUIRED` > `NO_ACTIONABLE` > `GO`。只要有任一条明确违反，就是 `NO_GO`，不会因为别的票不明确就放过。

## 怎么用

### 第 1 步：写候选清单

格式是 JSON，一个文件可以放多只票：

```json
{
  "candidates": [
    {
      "code": "600519",
      "name": "贵州茅台",
      "order_intent": "ENTRY_READY",
      "entry_in_written_plan": true,
      "stop_predefined": true,
      "size_within_plan": true,
      "planned_risk_yuan": 2000,
      "actual_risk_yuan": 2000,
      "notes": "突破缺口回踩不破 5 日线买入"
    }
  ]
}
```

字段说明：

| 字段 | 必填 | 说明 |
|---|---|---|
| `code` | ✅ | 6 位 A 股代码，如 `600519`、`000001`、`300750` |
| `order_intent` | ✅ | 见下方「意图取值」 |
| `entry_in_written_plan` | ✅ | 这笔买入写进计划了吗（必须是布尔 `true`） |
| `stop_predefined` | ✅ | 止损价定了吗（必须是 `true`，不是「打算定」） |
| `size_within_plan` | ✅ | 仓位在计划范围内吗 |
| `planned_risk_yuan` | ✅ | 计划亏多少钱就止损（元，有限非负数） |
| `actual_risk_yuan` | ✅ | 按当前价位算实际会亏多少 |
| `notes` | — | 一句话记下当时理由，复盘时很有用 |

**意图取值**

- 会触发检查：`ENTRY_READY`、`ACTIONABLE`、`ACTIONABLE_DAY1`、`MANUAL_ORDER`、`ADD_POSITION`
- 只记录不检查：`WATCHLIST`、`DELAYED_WATCH`、`IGNORE`、`REJECTED`

风险金额怎么算：`(买入价 - 止损价) × 股数`。算不出来说明止损没定，这本身就是问题。

### 第 2 步：跑关卡

```bash
python3 scripts/check_trade_gate.py \
  --answers state/manual-entry-checklist.json \
  --capital 100000 \
  --index 000300 \
  --journal-dir state/journal/trade-gate \
  --output-dir reports/trade-gate
```

常用参数：

| 参数 | 作用 |
|---|---|
| `--capital` | 账户总本金（元），用来算单笔风险占比 |
| `--max-risk-pct` | 单笔风险占本金上限，默认 `2.0`（%） |
| `--index` | 自动拉指数判大盘状态，默认 `000300`（沪深300），可换 `000001` 上证、`399006` 创业板 |
| `--market-state` | 手动指定大盘状态，指定后不联网 |
| `--halted` | 标记系统级暂停（比如你决定这个月不交易了） |
| `--cooldown-days` | 亏损后冷静期天数，默认 `3` |
| `--fail-on-non-go` | 非 `GO` 时退出码返回 2，方便挂到脚本里 |
| `--json-only` | 只输出 JSON，不打印 Markdown |

### 第 3 步：读结论

终端会打印一份 Markdown 报告，同时写入：

- `reports/trade-gate/gate_decision_<时间>.json` —— 完整决策，含当时填的每一项
- `reports/trade-gate/gate_report_<时间>.md` —— 给人看的报告
- `state/journal/trade-gate/gate_<时间>.json` —— 日志行，供冷静期检测和复盘回查

## 八条阻断规则

任何一条触发都是 `NO_GO`：

1. **没有写下来的计划** —— `entry_in_written_plan` 不是 `true`
2. **没有预设止损** —— `stop_predefined` 不是 `true`
3. **仓位超出计划** —— `size_within_plan` 不是 `true`
4. **实际风险超过计划风险** —— `actual_risk_yuan > planned_risk_yuan`
5. **单笔风险占比超标** —— `actual_risk_yuan / capital` 超过 `--max-risk-pct`
6. **报复交易窗口** —— 最近 `--cooldown-days` 天内有亏损离场记录
7. **大盘不允许开新仓** —— 状态为 `REDUCE_ONLY` / `CASH_PRIORITY` / `COOLDOWN` / `HALTED` / `TRADING_HALTED`
8. **系统级暂停** —— 传了 `--halted`

触发 `REVIEW_REQUIRED` 的情况：

- 风险金额缺失、布尔值、非数字、`NaN`、无穷、负数
- 大盘状态未知，或拿到一个不在放行/阻断列表里的值

## 大盘状态怎么判定

`--index` 会自动用腾讯财经日线算，规则很粗，**只做「现在该不该开新仓」的粗筛，不是择时信号**：

| 条件 | 状态 |
|---|---|
| 近 20 日跌幅 ≤ -8% | `CASH_PRIORITY`（现金优先） |
| 收盘 < MA60 | `REDUCE_ONLY`（只减不加） |
| 收盘 ≥ MA60 且 ≥ 20 日最高 | `NEW_ENTRY_ALLOWED` |
| 其余 | `ALLOW` |

要按自己的体系判断，直接用 `--market-state` 手动传，脚本就不联网了。

## 和别的技能怎么配

| 场景 | 用哪个 |
|---|---|
| 选出标的、算估值、看基本面 | `stock-investment-report` |
| 多空双方观点对打 | `stock-debate-analysis` |
| 拉 A 股行情、财务、北向资金 | `cn-finance-toolkit` |
| **下单前最后一道闸** | **本技能** |
| 交易做完复盘、找系统性错误 | `signal-postmortem-a-share` |

## 几条原则

1. **只做手动执行的把关**，不是订单路由器。它不会替你下单，也不会替你取消。
2. **先有书面计划，才有下单资格**。计划、止损、仓位三个字没写下来，就是没有。
3. **不确定就是不过**。信息缺失一律 `REVIEW_REQUIRED`，绝不给「先下了再说」的口子。
4. **日志只记不改账**。关卡日志不会自动改写你的持仓记录，复盘时人工核对。
5. **关卡的结论要服气**。规则是你自己定的，跑出来 `NO_GO` 就别绕过去——绕过去的那一单，正是以后复盘里最贵的教训。
