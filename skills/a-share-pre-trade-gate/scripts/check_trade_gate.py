#!/usr/bin/env python3
"""
A 股下单前纪律关卡 / Pre-trade discipline gate (A-share)

用途：手动下单前跑一遍，检查「有没有写计划 / 止损定了没 / 仓位超没超 /
亏钱后有没有在报复窗口里又下单 / 大盘状态允不允许开新仓 / 系统是否暂停」。

设计原则：
  - 纯离线。不连接券商、不下单、不取实时行情（大盘行情由外部传入或用 --index 拉）
  - 规则失败一律给 NO_GO，不要为了「让单子过」去改规则
  - 输出决策 JSON + Markdown 报告，写进日志目录，供复盘技能回查

依赖：Python 3.9+，仅标准库（网络取行情用 --index 时可走 urllib）
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

CST = timezone(timedelta(hours=8))

# ── 可下单的意图 ────────────────────────────────────────────────
ACTIONABLE_INTENTS = {
    "ENTRY_READY",      # 已看完图表和仓位，准备买
    "ACTIONABLE",       # 计划内可执行
    "ACTIONABLE_DAY1",  # 首日建仓
    "MANUAL_ORDER",     # 手动指定要下的单
    "ADD_POSITION",     # 加仓（同样要过关卡）
}

# ── 只要记录、不产生下单许可的意图 ──────────────────────────────
NON_ACTIONABLE_INTENTS = {
    "WATCHLIST",        # 只看
    "DELAYED_WATCH",    # 推迟观察
    "IGNORE",           # 不关注
    "REJECTED",         # 已否决
}

# ── 大盘状态 → 是否允许开新仓 ──────────────────────────────────
ALLOWED_MARKET_STATES = {"NEW_ENTRY_ALLOWED", "ALLOW"}
BLOCKED_MARKET_STATES = {
    "REDUCE_ONLY",       # 只减不加
    "CASH_PRIORITY",     # 现金优先
    "COOLDOWN",          # 冷却期
    "HALTED",            # 暂停交易
    "TRADING_HALTED",    # 交易停止
}

DECISION_ORDER = {"GO": 0, "NO_ACTIONABLE": 1, "REVIEW_REQUIRED": 2, "NO_GO": 3}


def now_cst() -> datetime:
    return datetime.now(CST)


def parse_num(v):
    """把计划/实际风险金额解析成有限非负数；非法返回 None。"""
    if isinstance(v, bool) or v is None:
        return None
    if isinstance(v, (int, float)):
        f = float(v)
    elif isinstance(v, str):
        try:
            f = float(v.strip())
        except ValueError:
            return None
    else:
        return None
    if f != f or f in (float("inf"), float("-inf")) or f < 0:
        return None
    return f


def fetch_index_state(index_code: str = "000300", days: int = 120) -> dict:
    """用腾讯财经公开接口拉指数日线，粗判大盘状态。

    只做「粗略状态判定」，不是择时信号：
      - 指数收盘 < MA60            → REDUCE_ONLY
      - 指数 20 日跌幅 ≤ -8%        → CASH_PRIORITY
      - 指数收盘 ≥ MA60 且创 20 日新高 → NEW_ENTRY_ALLOWED
      - 其他                        → ALLOW
    注意：必须绕过系统代理（本机 http_proxy 会把外网请求也转走导致 502）。
    """
    # 腾讯财经接口（日线，qfq）。指数代码需要带市场前缀：sh000300 / sz399006
    prefix = "sh" if index_code.startswith(("0", "6")) else "sz"
    symbol = f"{prefix}{index_code}"
    url = (
        "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get"
        f"?param={symbol},day,,,{max(days, 60)},qfq"
    )
    try:
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        raw = opener.open(url, timeout=15).read()
        node = json.loads(raw)["data"][symbol]
        rows = node.get("qfqday") or node.get("day") or []
        # 行格式：[日期, 开, 收, 高, 低, 成交量]
        closes = [float(r[2]) for r in rows]
        last_date = rows[-1][0]
    except Exception as e:  # noqa: BLE001
        return {"index": index_code, "error": f"{type(e).__name__}: {e}"}

    if len(closes) < 60:
        return {"index": index_code, "error": f"数据点不足（{len(closes)} < 60）"}

    ma60 = sum(closes[-60:]) / 60
    last = closes[-1]
    ret20 = (last / closes[-21] - 1) if len(closes) >= 21 else 0.0
    high20 = max(closes[-20:])

    if ret20 <= -0.08:
        state = "CASH_PRIORITY"
    elif last < ma60:
        state = "REDUCE_ONLY"
    elif last >= high20:
        state = "NEW_ENTRY_ALLOWED"
    else:
        state = "ALLOW"

    return {
        "index": index_code,
        "close": round(last, 2),
        "ma60": round(ma60, 2),
        "return_20d": round(ret20 * 100, 2),
        "state": state,
        "as_of": last_date,
    }


def load_json(path: Path | None) -> dict | None:
    if path is None or not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return None


def recent_losing_exits(journal_dir: Path | None, window_days: int) -> list[dict]:
    """扫描历史关卡日志，找出冷却窗口内的亏损离场记录（报复交易风险）。"""
    if journal_dir is None or not journal_dir.exists():
        return []
    cutoff = now_cst() - timedelta(days=window_days)
    hits = []
    for f in sorted(journal_dir.glob("*.json")):
        rec = load_json(f)
        if not rec:
            continue
        pnl = rec.get("realized_pnl")
        if pnl is None or parse_num(str(abs(pnl))) is None or pnl >= 0:
            continue
        try:
            ts = datetime.fromisoformat(rec.get("recorded_at", ""))
        except ValueError:
            continue
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=CST)
        if ts >= cutoff:
            hits.append({"file": f.name, "realized_pnl": pnl, "recorded_at": rec.get("recorded_at")})
    return hits


def evaluate_candidate(c: dict, ctx: dict) -> dict:
    """对单个候选股跑全部规则。"""
    reasons: list[str] = []
    review: list[str] = []
    intent = str(c.get("order_intent", "")).upper()

    if intent not in ACTIONABLE_INTENTS:
        return {
            "code": c.get("code", "?"),
            "name": c.get("name", ""),
            "order_intent": intent,
            "decision": "NO_ACTIONABLE",
            "reasons": [f"意图 {intent or '空'} 不属于可下单类型，仅记录"],
            "review": [],
        }

    # 规则 1-3：必须有书面计划 / 止损 / 仓位
    for field, label in (
        ("entry_in_written_plan", "建仓必须在写下来的计划里"),
        ("stop_predefined", "必须先定好止损价"),
        ("size_within_plan", "仓位必须在计划范围内"),
    ):
        if c.get(field) is not True:
            reasons.append(label)

    # 规则 4：计划风险 vs 实际风险
    planned = parse_num(c.get("planned_risk_yuan"))
    actual = parse_num(c.get("actual_risk_yuan"))
    if planned is None:
        review.append("planned_risk_yuan 缺失或非法（需有限非负数）")
    if actual is None:
        review.append("actual_risk_yuan 缺失或非法（需有限非负数）")
    if planned is not None and actual is not None and actual > planned:
        reasons.append(f"实际风险 ¥{actual:.0f} 超过计划风险 ¥{planned:.0f}")

    # 规则 5：单笔风险占本金比例上限
    capital = parse_num(ctx.get("capital"))
    max_pct = parse_num(ctx.get("max_risk_pct")) or 2.0
    if capital and actual is not None:
        pct = actual / capital * 100
        if pct > max_pct:
            reasons.append(f"单笔风险 {pct:.2f}% 超过上限 {max_pct:.2f}%")

    # 规则 6：报复交易窗口
    if ctx.get("losing_exits"):
        hits = ctx["losing_exits"][:3]
        detail = "、".join(f"{h['realized_pnl']:+.0f}" for h in hits)
        reasons.append(
            f"近 {ctx.get('cooldown_days', 3)} 天内有亏损离场（{detail} 元），报复交易冷却中"
        )

    # 规则 7：大盘状态
    market_state = str(ctx.get("market_state", "")).upper()
    if not market_state:
        review.append("大盘状态未知：需传入 --market-state 或用 --index 自动拉取")
    elif market_state in BLOCKED_MARKET_STATES:
        reasons.append(f"大盘状态 {market_state} 不允许开新仓")
    elif market_state not in ALLOWED_MARKET_STATES:
        review.append(f"大盘状态 {market_state} 不是明确的放行值")

    # 规则 8：系统级暂停
    if ctx.get("trading_halted"):
        reasons.append("交易系统处于暂停状态")

    if reasons:
        decision = "NO_GO"
    elif review:
        decision = "REVIEW_REQUIRED"
    else:
        decision = "GO"

    return {
        "code": c.get("code", "?"),
        "name": c.get("name", ""),
        "order_intent": intent,
        "decision": decision,
        "reasons": reasons,
        "review": review,
        "checklist_answers": {
            "entry_in_written_plan": c.get("entry_in_written_plan"),
            "stop_predefined": c.get("stop_predefined"),
            "size_within_plan": c.get("size_within_plan"),
            "planned_risk_yuan": planned,
            "actual_risk_yuan": actual,
            "notes": c.get("notes", ""),
        },
    }


def overall(results: list[dict]) -> str:
    if not results:
        return "NO_ACTIONABLE"
    worst = max(DECISION_ORDER.get(r["decision"], 2) for r in results)
    if worst == 0:
        return "GO"
    if all(r["decision"] == "NO_ACTIONABLE" for r in results):
        return "NO_ACTIONABLE"
    return [k for k, v in DECISION_ORDER.items() if v == worst][0]


ICON = {"GO": "✅", "NO_ACTIONABLE": "⏸️", "REVIEW_REQUIRED": "❓", "NO_GO": "⛔"}


def render_md(decision: dict) -> str:
    lines = [
        f"# 下单前纪律关卡 · {decision['recorded_at']}",
        "",
        f"**总决策：{ICON.get(decision['decision'], '')} {decision['decision']}**",
        "",
    ]
    ctx = decision["context"]
    lines += [
        "## 环境",
        "",
        f"- 大盘状态：`{ctx.get('market_state') or '未知'}`"
        + (f"（{ctx['index_snapshot']['index']} 收 {ctx['index_snapshot'].get('close')}，"
           f"MA60 {ctx['index_snapshot'].get('ma60')}，20日 {ctx['index_snapshot'].get('return_20d')}%）"
           if ctx.get("index_snapshot", {}).get("close") else ""),
        f"- 本金：{ctx.get('capital') or '未提供'}　单笔风险上限：{ctx.get('max_risk_pct')}%",
        f"- 冷却窗口：{ctx.get('cooldown_days')} 天　窗口内亏损离场：{len(ctx.get('losing_exits', []))} 笔",
        "",
        "## 逐票结论",
        "",
        "| 代码 | 名称 | 意图 | 结论 |",
        "|---|---|---|---|",
    ]
    for r in decision["results"]:
        nm = r["name"] or "—"
        lines.append(f"| {r['code']} | {nm} | {r['order_intent'] or '—'} | {ICON.get(r['decision'], '')} {r['decision']} |")

    blocking = [r for r in decision["results"] if r["decision"] == "NO_GO"]
    if blocking:
        lines += ["", "## 阻断原因", ""]
        for r in blocking:
            lines.append(f"**{r['code']} {r['name']}**")
            lines += [f"- ⛔ {x}" for x in r["reasons"]]
            lines.append("")

    review = [r for r in decision["results"] if r["decision"] == "REVIEW_REQUIRED"]
    if review:
        lines += ["## 待补齐信息", ""]
        for r in review:
            lines.append(f"**{r['code']} {r['name']}**")
            lines += [f"- ❓ {x}" for x in r["review"]]
            lines.append("")

    if decision["decision"] == "GO":
        lines += ["> 全部规则通过。这是「符合纪律」的确认，不是「该涨」的预测。", ""]
    elif decision["decision"] == "NO_GO":
        lines += ["> **不要下单。** 先把上面每一条阻断原因解决掉，再重跑一次。", ""]

    return "\n".join(lines)


def main() -> int:
    p = argparse.ArgumentParser(description="A 股下单前纪律关卡")
    p.add_argument("--answers", required=True, help="候选清单 JSON（见 SKILL.md 示例）")
    p.add_argument("--capital", type=float, default=None, help="账户总本金（元）")
    p.add_argument("--max-risk-pct", type=float, default=2.0, help="单笔风险占本金上限（%%），默认 2")
    p.add_argument("--market-state", default="", help="大盘状态（手动指定）")
    p.add_argument("--index", default="000300", help="用指数自动判大盘状态，默认沪深300")
    p.add_argument("--halted", action="store_true", help="系统级暂停交易")
    p.add_argument("--cooldown-days", type=int, default=3, help="亏损后冷静期天数，默认 3")
    p.add_argument("--journal-dir", default="state/journal/trade-gate", help="历史关卡日志目录")
    p.add_argument("--output-dir", default="reports/trade-gate", help="输出目录")
    p.add_argument("--json-only", action="store_true", help="只输出 JSON")
    p.add_argument("--fail-on-non-go", action="store_true", help="非 GO 时退出码 2")
    args = p.parse_args()

    answers_path = Path(args.answers).expanduser()
    if not answers_path.exists():
        print(json.dumps({"error": f"找不到 {answers_path}"}, ensure_ascii=False), file=sys.stderr)
        return 1
    payload = load_json(answers_path) or {}
    candidates = payload.get("candidates", [])

    market_state = args.market_state.upper().strip()
    index_snapshot = {}
    if not market_state:
        index_snapshot = fetch_index_state(args.index)
        market_state = index_snapshot.get("state", "")

    journal_dir = Path(args.journal_dir).expanduser() if args.journal_dir else None
    ctx = {
        "capital": args.capital,
        "max_risk_pct": args.max_risk_pct,
        "market_state": market_state,
        "index_snapshot": index_snapshot,
        "trading_halted": args.halted,
        "cooldown_days": args.cooldown_days,
        "losing_exits": recent_losing_exits(journal_dir, args.cooldown_days),
    }

    results = [evaluate_candidate(c, ctx) for c in candidates]
    now = now_cst()
    decision = {
        "schema": "a-share-pre-trade-gate/1.0",
        "recorded_at": now.isoformat(timespec="seconds"),
        "decision": overall(results),
        "context": ctx,
        "results": results,
    }

    out_dir = Path(args.output_dir).expanduser()
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = now.strftime("%Y-%m-%d_%H%M%S")
    json_path = out_dir / f"gate_decision_{stamp}.json"
    json_path.write_text(json.dumps(decision, ensure_ascii=False, indent=2), encoding="utf-8")

    if journal_dir:
        journal_dir.mkdir(parents=True, exist_ok=True)
        (journal_dir / f"gate_{stamp}.json").write_text(
            json.dumps(
                {"recorded_at": decision["recorded_at"], "decision": decision["decision"],
                 "codes": [r["code"] for r in results]},
                ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    if not args.json_only:
        md_path = out_dir / f"gate_report_{stamp}.md"
        md_path.write_text(render_md(decision), encoding="utf-8")
        print(render_md(decision))
    else:
        print(json.dumps(decision, ensure_ascii=False, indent=2))

    print(f"\n已写入：{json_path}", file=sys.stderr)
    if args.fail_on_non_go and decision["decision"] != "GO":
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
