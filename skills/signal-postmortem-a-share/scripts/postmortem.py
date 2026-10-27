#!/usr/bin/env python3
"""
A 股信号复盘 / Signal postmortem (A-share)

用途：给每个「当时想买/已经买了」的信号记结局，算它的实际收益，分类成
真阳性 / 假阳性 / 错失机会 / 环境不匹配，再汇总成「哪类信号靠谱、哪类
总骗你」的统计。

核心价值不在记录，在**归因**：把亏损分清是「信号本身不行」还是
「大盘环境变了」，这两件事的处理方式完全不同。

依赖：Python 3.9+，仅标准库。
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

CST = timezone(timedelta(hours=8))

HOLDING_PERIODS = (5, 20)   # A 股常用观察周期：1 周 / 1 月


def now_cst() -> datetime:
    return datetime.now(CST)


def tencent_symbol(code: str) -> str:
    """6 位代码 → 腾讯前缀。6/9 开头沪市，其余深市。"""
    return f"sh{code}" if code[0] in "69" else f"sz{code}"


def fetch_closes(code: str, days: int = 60) -> list[tuple[str, float]]:
    """拉前复权日线，返回 [(日期, 收盘)]，按时间升序。

    必须绕过系统代理：本机 http_proxy 会把外网请求一并转走导致失败。
    """
    symbol = tencent_symbol(code)
    url = (
        "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get"
        f"?param={symbol},day,,,{days},qfq"
    )
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    raw = opener.open(url, timeout=15).read()
    node = json.loads(raw)["data"][symbol]
    rows = node.get("qfqday") or node.get("day") or []
    return [(r[0], float(r[2])) for r in rows]


def close_on_or_after(series: list[tuple[str, float]], date_str: str) -> tuple[str, float] | None:
    """取目标日（或其后第一个交易日）的收盘价。"""
    for d, c in series:
        if d >= date_str:
            return d, c
    return None


def close_on_or_before(series: list[tuple[str, float]], date_str: str) -> tuple[str, float] | None:
    hit = None
    for d, c in series:
        if d <= date_str:
            hit = (d, c)
        else:
            break
    return hit


def classify(direction: str, ret: float | None, taken: bool, regime_changed: bool) -> str:
    """四分类：真阳性 / 假阳性 / 错失机会 / 环境不匹配。"""
    if ret is None:
        return "NO_DATA"
    if not taken:
        # 没做的信号：涨了是错失，跌了是躲过
        if direction == "LONG":
            return "MISSED_OPPORTUNITY" if ret > 0.02 else "GOOD_SKIP"
        return "MISSED_OPPORTUNITY" if ret < -0.02 else "GOOD_SKIP"

    hit = (ret > 0) if direction == "LONG" else (ret < 0)
    if hit:
        return "TRUE_POSITIVE"
    # 判断是否由环境变化导致
    if regime_changed and abs(ret) > 0.03:
        return "REGIME_MISMATCH"
    return "FALSE_POSITIVE"


CATEGORY_LABEL = {
    "TRUE_POSITIVE": "✔ 真阳性（方向对了）",
    "FALSE_POSITIVE": "✘ 假阳性（信号骗人）",
    "MISSED_OPPORTUNITY": "○ 错失（没做但该做）",
    "GOOD_SKIP": "– 正确回避（没做是对的）",
    "REGIME_MISMATCH": "⚠ 环境不匹配（信号对，市场变脸）",
    "NO_DATA": "? 数据不足",
}


def record_signal(sig: dict) -> dict:
    code = str(sig["code"])
    signal_date = sig["signal_date"]
    direction = str(sig.get("predicted_direction", "LONG")).upper()
    source = sig.get("source_skill", "manual")
    taken = bool(sig.get("taken", True))

    try:
        series = fetch_closes(code, days=90)
    except Exception as e:  # noqa: BLE001
        return {**sig, "error": f"取价失败 {type(e).__name__}: {e}"}

    entry = close_on_or_after(series, signal_date)
    if entry is None:
        return {**sig, "error": "信号日之后没有交易日数据"}
    entry_date, entry_price = entry

    returns = {}
    for p in HOLDING_PERIODS:
        target = (datetime.fromisoformat(entry_date) + timedelta(days=p)).date().isoformat()
        got = close_on_or_after(series, target)
        if got and entry_price:
            returns[f"{p}d"] = round((got[1] / entry_price - 1) * 100, 2)

    regime_at_signal = str(sig.get("regime_at_signal", "")).upper()
    regime_at_exit = str(sig.get("regime_at_exit", "")).upper()
    regime_changed = bool(regime_at_signal and regime_at_exit and regime_at_signal != regime_at_exit)

    # 主判据用最长持有期（A 股 5 日噪声大，20 日更能反映信号成色）；缺失则退回 5 日
    primary = returns.get(f"{HOLDING_PERIODS[-1]}d")
    if primary is None:
        primary = returns.get(f"{HOLDING_PERIODS[0]}d")
    if primary is not None:
        primary /= 100
    category = classify(direction, primary, taken, regime_changed)

    return {
        "code": code,
        "name": sig.get("name", ""),
        "signal_date": signal_date,
        "entry_date": entry_date,
        "entry_price": round(entry_price, 3),
        "predicted_direction": direction,
        "source_skill": source,
        "taken": taken,
        "returns": returns,
        "outcome_category": category,
        "regime_at_signal": regime_at_signal or None,
        "regime_at_exit": regime_at_exit or None,
        "notes": sig.get("notes", ""),
        "reviewed_at": now_cst().isoformat(timespec="seconds"),
    }


def summarize(records: list[dict], min_sample: int) -> dict:
    """按来源技能分组统计，判断哪类信号值得信。"""
    buckets: dict[str, list[dict]] = {}
    for r in records:
        if r.get("error") or r.get("outcome_category") == "NO_DATA":
            continue
        buckets.setdefault(r["source_skill"], []).append(r)

    stats = []
    for source, rows in buckets.items():
        taken_rows = [r for r in rows if r.get("taken")]
        n = len(taken_rows)
        tp = sum(1 for r in taken_rows if r["outcome_category"] == "TRUE_POSITIVE")
        rets = [r["returns"].get("5d") for r in taken_rows if r["returns"].get("5d") is not None]
        win_rate = (tp / n * 100) if n else None
        avg_ret = (sum(rets) / len(rets)) if rets else None

        if n >= min_sample and win_rate is not None:
            if win_rate >= 60 and (avg_ret or 0) > 0:
                verdict = "KEEP"           # 继续用
            elif win_rate <= 40:
                verdict = "REVIEW"         # 该停用或改造
            else:
                verdict = "WATCH"          # 样本够了但优势不明显，继续观察
        else:
            verdict = "INSUFFICIENT"       # 样本不足，不下结论

        stats.append({
            "source_skill": source,
            "sample_size": n,
            "true_positive": tp,
            "false_positive": sum(1 for r in taken_rows if r["outcome_category"] == "FALSE_POSITIVE"),
            "regime_mismatch": sum(1 for r in taken_rows if r["outcome_category"] == "REGIME_MISMATCH"),
            "win_rate_pct": round(win_rate, 1) if win_rate is not None else None,
            "avg_return_5d_pct": round(avg_ret, 2) if avg_ret is not None else None,
            "verdict": verdict,
        })
    stats.sort(key=lambda x: (x["sample_size"], x["win_rate_pct"] or 0), reverse=True)
    return {"min_sample_threshold": min_sample, "by_source_skill": stats, "total": len(records)}


def render_md(records: list[dict], summary: dict) -> str:
    lines = [f"# 信号复盘 · {now_cst():%Y-%m-%d %H:%M}", ""]

    errs = [r for r in records if r.get("error")]
    ok = [r for r in records if not r.get("error")]

    if ok:
        lines += ["## 逐条结果", "", "| 代码 | 信号日 | 方向 | 来源 | 5日 | 20日 | 分类 |",
                  "|---|---|---|---|---|---|---|"]
        for r in ok:
            r5 = f"{r['returns']['5d']:+.2f}%" if r["returns"].get("5d") is not None else "—"
            r20 = f"{r['returns']['20d']:+.2f}%" if r["returns"].get("20d") is not None else "—"
            nm = r["name"] or "—"
            lines.append(
                f"| {r['code']} {nm} | {r['signal_date']} | {r['predicted_direction']} | "
                f"{r['source_skill']} | {r5} | {r20} | {CATEGORY_LABEL.get(r['outcome_category'], r['outcome_category'])} |"
            )
        lines.append("")

    if summary["by_source_skill"]:
        lines += ["## 按信号来源汇总", "",
                  "| 来源 | 样本 | 真阳性 | 假阳性 | 环境不匹配 | 胜率 | 5日均值 | 结论 |",
                  "|---|---|---|---|---|---|---|---|"]
        verdict_cn = {"KEEP": "✅ 可继续用", "REVIEW": "⚠️ 该改造或停用",
                      "WATCH": "👀 观察中", "INSUFFICIENT": "— 样本不足"}
        for s in summary["by_source_skill"]:
            wr = f"{s['win_rate_pct']}%" if s["win_rate_pct"] is not None else "—"
            ar = f"{s['avg_return_5d_pct']:+.2f}%" if s["avg_return_5d_pct"] is not None else "—"
            lines.append(
                f"| {s['source_skill']} | {s['sample_size']} | {s['true_positive']} | "
                f"{s['false_positive']} | {s['regime_mismatch']} | {wr} | {ar} | "
                f"{verdict_cn.get(s['verdict'], s['verdict'])} |"
            )
        lines += ["",
                  f"> 判定门槛：样本 ≥ {summary['min_sample_threshold']} 才下结论。"
                  "样本不足时不要因为「最近三次都亏」就废掉一个来源。", ""]

    if errs:
        lines += ["## 取价失败", ""]
        for r in errs:
            lines.append(f"- `{r['code']}` {r.get('name', '')}：{r['error']}")
        lines.append("")

    return "\n".join(lines)


def main() -> int:
    p = argparse.ArgumentParser(description="A 股信号复盘")
    p.add_argument("--signals", required=True, help="信号清单 JSON")
    p.add_argument("--output-dir", default="reports/postmortem", help="输出目录")
    p.add_argument("--min-sample", type=int, default=10, help="下结论所需最小样本，默认 10")
    p.add_argument("--json-only", action="store_true", help="只输出 JSON")
    args = p.parse_args()

    path = Path(args.signals).expanduser()
    if not path.exists():
        print(json.dumps({"error": f"找不到 {path}"}, ensure_ascii=False), file=sys.stderr)
        return 1
    payload = json.loads(path.read_text(encoding="utf-8"))
    signals = payload.get("signals", payload if isinstance(payload, list) else [])

    records = [record_signal(s) for s in signals]
    summary = summarize(records, args.min_sample)

    out_dir = Path(args.output_dir).expanduser()
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = now_cst().strftime("%Y-%m-%d_%H%M%S")

    full = {"schema": "signal-postmortem-a-share/1.0",
            "reviewed_at": now_cst().isoformat(timespec="seconds"),
            "records": records, "summary": summary}
    (out_dir / f"postmortem_{stamp}.json").write_text(
        json.dumps(full, ensure_ascii=False, indent=2), encoding="utf-8")

    if args.json_only:
        print(json.dumps(full, ensure_ascii=False, indent=2))
    else:
        md = render_md(records, summary)
        (out_dir / f"postmortem_summary_{stamp}.md").write_text(md, encoding="utf-8")
        print(md)

    return 0


if __name__ == "__main__":
    sys.exit(main())
