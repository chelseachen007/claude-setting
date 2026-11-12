#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""盯盘：按 watchlist.json 机械检查「今天有没有值得出手/需要我拍板的事」。

定位（别把它当另一个日报）：
  * 雪球日报回答「今天大家在想什么」，本脚本回答「今天我的票和触发器有没有真的动」。
  * 默认**沉默**：没有状态翻转就不输出。只有 `state_changed` 或 `actionable` 才会被打印并推到手机上。
  * 不做加仓建议、不给目标价，只做三件事：报价、跟状态比、说清楚「变了什么」。

为什么不用东财：
  push2/push2his 在本机整天整天地限流（`Remote end closed connection`），
  行情走腾讯（qt.gtimg.cn 快照 + web.ifzq.gtimg.cn 日K），商品走新浪（hq.sinajs.cn 带 Referer），
  宏观走 datacenter-web（东财财报口，不受 push2 限流影响）。
  2026-11-12 实测三个源都通。

用法：
    python3 工具/盯盘/盯盘.py                # 跑一遍，只有值得说的才打印
    python3 工具/盯盘/盯盘.py --force        # 全部打印（人工排查用）
    python3 工具/盯盘/盯盘.py --json         # 机器可读，给中台/子代理吃
    python3 工具/盯盘/盯盘.py --mark-alert   # 有 actionable 时弹 macOS 通知
    python3 工具/盯盘/盯盘.py --advance      # 检查通过后推进状态文件（先看输出再推进）

退出码：0 正常（无论有无信号）；1 抓取失败；2 状态文件损坏
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import urllib.request
from datetime import date, datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
INVEST = HERE.parent.parent  # ~/WorkBuddy AI/投资

WATCH_FILE = HERE / "watchlist.json"
STATE_FILE = HERE / "watch_state.json"

UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"}
_NO_PROXY = urllib.request.build_opener(urllib.request.ProxyHandler({}))


# ── HTTP ──────────────────────────────────────────────────────────
def _get(url: str, referer: str = "") -> str:
    h = dict(UA)
    if referer:
        h["Referer"] = referer
    req = urllib.request.Request(url, headers=h)
    return _NO_PROXY.open(req, timeout=20).read().decode("utf-8", "ignore")


def _get_gbk(url: str, referer: str = "") -> str:
    h = dict(UA)
    if referer:
        h["Referer"] = referer
    req = urllib.request.Request(url, headers=h)
    return _NO_PROXY.open(req, timeout=20).read().decode("gbk", "ignore")


# ── 行情源 ────────────────────────────────────────────────────────
def tencent_quote(symbols: list[str]) -> dict[str, dict]:
    """腾讯快照。symbol 形如 sh600690 / sz002460。返回 {symbol: {name, px, pct, pe, pb}}"""
    out: dict[str, dict] = {}
    for i in range(0, len(symbols), 20):
        chunk = symbols[i:i + 20]
        raw = _get_gbk("https://qt.gtimg.cn/q=" + ",".join(chunk))
        for line in raw.splitlines():
            if "=" not in line or "~" not in line:
                continue
            body = line.split('="', 1)[-1].rstrip('";')
            f = body.split("~")
            if len(f) < 50:
                continue
            sym = line.split("=")[0].replace("v_", "").strip()
            try:
                out[sym] = {
                    "name": f[1],
                    "px": float(f[3] or 0),
                    "pct": float(f[32] or 0),      # 涨跌幅 %
                    "pe": float(f[39] or 0),       # 动态 PE
                    "pb": float(f[46] or 0),
                    "mcap": float(f[45] or 0),     # 总市值(亿)
                }
            except (ValueError, IndexError):
                continue
    return out


def tencent_kline(symbol: str, days: int = 70) -> list[tuple[str, float, float]]:
    """腾讯日K，返回 [(date, close, volume)]，升序。"""
    url = f"https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param={symbol},day,,,{days},qfq"
    d = json.loads(_get(url))
    node = (d.get("data") or {}).get(symbol) or {}
    key = "qfqday" if "qfqday" in node else "day"
    rows = node.get(key) or []
    return [(r[0], float(r[2]), float(r[5])) for r in rows if len(r) >= 6]


def sina_commodity(code: str) -> dict | None:
    """新浪商品连续合约。code 形如 LC0（碳酸锂）。返回 {name, last, prev, date}"""
    raw = _get_gbk(f"https://hq.sinajs.cn/list=nf_{code}", "https://finance.sina.com.cn")
    if '"' not in raw:
        return None
    body = raw.split('="', 1)[-1].rstrip('";')
    f = body.split(",")
    if len(f) < 18 or not f[0]:
        return None
    try:
        return {"name": f[0], "last": float(f[8]), "open": float(f[2]),
                "high": float(f[4]), "low": float(f[5]), "prev": float(f[10]),
                "date": f[17]}
    except (ValueError, IndexError):
        return None


# ── 宏观（东财 datacenter，避开 push2 限流） ───────────────────────
ECON = {
    # key: (reportName, 时间列, 数值列, 口径说明)
    "cpi_yoy": ("RPT_ECONOMY_CPI", "TIME", "NATIONAL_SAME", "CPI 同比%"),
    "ppi_yoy": ("RPT_ECONOMY_PPI", "TIME", "BASE_SAME", "PPI 同比%"),
    "retail_yoy": ("RPT_ECONOMY_TOTAL_RETAIL", "TIME", "RETAIL_TOTAL_SAME", "社零同比%"),
    "m1_yoy": ("RPT_ECONOMY_CURRENCY_SUPPLY", "TIME", "CURRENCY_SAME", "M1 同比%"),
    "m2_yoy": ("RPT_ECONOMY_CURRENCY_SUPPLY", "TIME", "BASIC_CURRENCY_SAME", "M2 同比%"),
}


def econ_series(key: str, n: int = 6) -> list[dict]:
    rep, tcol, vcol, _ = ECON[key]
    url = ("https://datacenter-web.eastmoney.com/api/data/v1/get?"
           f"reportName={rep}&columns={tcol},{vcol}&pageSize={n}&pageNumber=1"
           "&sortColumns=REPORT_DATE&sortTypes=-1")
    d = json.loads(_get(url))
    rows = ((d.get("result") or {}).get("data")) or []
    return [{"period": r.get(tcol), "value": r.get(vcol)} for r in rows if r.get(vcol) is not None]


# ── 状态 ──────────────────────────────────────────────────────────
def load_json(p: Path, default):
    if not p.exists():
        return default
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"[状态文件损坏] {p}: {e}", file=sys.stderr)
        sys.exit(2)


def save_json(p: Path, obj) -> None:
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


# ── 检查逻辑（纯函数，方便单独测） ─────────────────────────────────
def check_stock(rules: list[dict], kline: list[tuple[str, float, float]],
                quote: dict) -> tuple[list[dict], dict]:
    """对一只票跑全部规则。返回 (触发列表, 本次快照状态)。

    状态只记「跨日才会变的东西」：价格、PE、距 N 日高点的回撤、均线位置。
    条件真值由状态现算，所以规则改阈值不需要重算历史。
    """
    fired: list[dict] = []
    closes = [c for _, c, _ in kline]
    if len(closes) < 2:
        return [{"id": "KLINE_EMPTY", "text": "日K不足，跳过"}], {}

    cur = closes[-1]
    high252 = max(closes[-252:])
    ma20 = sum(closes[-20:]) / min(20, len(closes))
    snap = {
        "date": kline[-1][0],
        "close": round(cur, 2),
        "pct": round(quote.get("pct", 0.0), 2),
        "pe": round(quote.get("pe", 0.0), 2),
        "dd_from_high": round((cur / high252 - 1) * 100, 2) if high252 else 0.0,
        "above_ma20": cur >= ma20,
    }

    for r in rules:
        rid, typ = r.get("id", "?"), r.get("type")
        if typ == "price_below" and cur <= r["value"]:
            fired.append({"id": rid, "kind": "actionable",
                          "text": f"现价 {cur:.2f} ≤ 阈值 {r['value']}，回到你写的买入区间"})
        elif typ == "price_above" and cur >= r["value"]:
            fired.append({"id": rid, "kind": "actionable",
                          "text": f"现价 {cur:.2f} ≥ 阈值 {r['value']}"})
        elif typ == "pe_below" and snap["pe"] and snap["pe"] <= r["value"]:
            fired.append({"id": rid, "kind": "actionable",
                          "text": f"动态 PE {snap['pe']:.1f} ≤ {r['value']}"})
        elif typ == "dd_from_high" and snap["dd_from_high"] <= -abs(r["value"]):
            fired.append({"id": rid, "kind": "actionable",
                          "text": f"距一年高点回撤 {snap['dd_from_high']:.1f}%，达到 {r['value']}% 档"})
        elif typ == "cross_ma20":
            prev_above = closes[-2] >= (sum(closes[-21:-1]) / min(20, len(closes) - 1))
            if snap["above_ma20"] != prev_above:
                fired.append({"id": rid, "kind": "state_change",
                              "text": f"今日{'上穿' if snap['above_ma20'] else '下穿'} 20 日均线"})
    return fired, snap


def check_commodity(code: str, rule: dict, snap_old: dict | None) -> tuple[list[dict], dict]:
    q = sina_commodity(code)
    if not q:
        return [{"id": f"{code}_FAIL", "kind": "actionable", "text": f"{code} 行情抓取失败"}], {}
    snap = {"date": q["date"], "last": q["last"], "prev": q["prev"]}
    fired = []
    if rule.get("type") == "price_above" and q["last"] >= rule["value"]:
        fired.append({"id": "T7_price", "kind": "actionable",
                      "text": f"{q['name']} {q['last']:.0f} ≥ {rule['value']:g}"})
    return fired, snap


def check_macro(conds: list[dict], hist: dict[str, list[dict]]) -> list[dict]:
    """宏观触发器：conds 每项 {id, expr, text}，expr 是形如 'cpi_yoy>=1.0' 或 'm1_yoy>m2_yoy' 的偏最小表达式。"""
    fired = []
    ctx = {}
    for k, series in hist.items():
        ctx[k] = [r["value"] for r in series]  # 最新在前
    for c in conds:
        expr = c["expr"]
        try:
            ok = _eval_expr(expr, ctx)
        except Exception as e:  # 表达式写错要让用户看见，不要静默当 False
            fired.append({"id": c["id"], "kind": "error", "text": f"表达式错误 {expr}: {e}"})
            continue
        if ok:
            fired.append({"id": c["id"], "kind": "actionable", "text": c.get("text", expr),
                          "group": "触发器"})
    return fired


def _eval_expr(expr: str, ctx: dict[str, list[float]]) -> bool:
    """支持 A>=数 / A>=B / 连续n月(A>=数)。空数据一律 False。"""
    import re
    m = re.fullmatch(r"连续(\d+)月\((\w+)\s*(>=|<=|>|<)\s*([\d.]+)\)", expr)
    if m:
        n, key, op, val = int(m.group(1)), m.group(2), m.group(3), float(m.group(4))
        vals = ctx.get(key) or []
        if len(vals) < n:
            return False
        return all(_cmp(v, op, val) for v in vals[:n])
    # 差值式：A-B<op>数（T4 剪刀差就是这种），只支持两个指标相减
    m = re.fullmatch(r"(\w+)\s*-\s*(\w+)\s*(>=|<=|>|<)\s*([\d.]+)", expr)
    if m:
        a, b, op, val = m.group(1), m.group(2), m.group(3), float(m.group(4))
        av = (ctx.get(a) or [None])[0]
        bv = (ctx.get(b) or [None])[0]
        if av is None or bv is None:
            return False
        return _cmp(av - bv, op, val)
    # A<op>B，A/B 可以是 ctx 里的指标名，也可以是数字（支持 10.0 / 0.5 / 2 这类写法）
    m = re.fullmatch(r"([\w.]+)\s*(>=|<=|>|<)\s*([\w.]+)", expr)
    if m:
        a, op, b = m.group(1), m.group(2), m.group(3)
        av = (ctx.get(a) or [None])[0]
        bv = float(b) if re.fullmatch(r"\d+(\.\d+)?", b) else (ctx.get(b) or [None])[0]
        if av is None or bv is None:
            return False
        return _cmp(av, op, bv)
    raise ValueError("不认识的表达式格式")


def _cmp(a: float, op: str, b: float) -> bool:
    return {">=": a >= b, "<=": a <= b, ">": a > b, "<": a < b}[op]


# ── 主流程 ────────────────────────────────────────────────────────
def run(force: bool = False, advance: bool = False, as_json: bool = False,
        notify: bool = False) -> int:
    cfg = load_json(WATCH_FILE, None)
    if cfg is None:
        print(f"缺配置文件：{WATCH_FILE}", file=sys.stderr)
        return 1
    state = load_json(STATE_FILE, {"stocks": {}, "commodities": {}, "fired": {}})
    today = date.today().isoformat()

    report: dict = {"date": today, "stocks": {}, "commodities": {}, "macro": {}, "fired": []}
    errors: list[str] = []

    # 1) 股票
    stocks = cfg.get("stocks", [])
    symbols = [s["symbol"] for s in stocks]
    try:
        quotes = tencent_quote(symbols) if symbols else {}
    except Exception as e:
        quotes = {}
        errors.append(f"腾讯快照失败：{e}")

    for s in stocks:
        sym, name = s["symbol"], s.get("name", s["symbol"])
        try:
            kl = tencent_kline(sym)
        except Exception as e:
            errors.append(f"{name} 日K失败：{e}")
            continue
        q = quotes.get(sym, {})
        fired, snap = check_stock(s.get("rules", []), kl, q)
        for f in fired:
            f.update(stock=name, symbol=sym, kind=f.get("kind", "actionable"), group="关注池")
        report["stocks"][sym] = {"name": name, "snapshot": snap, "fired": fired}
        report["fired"].extend(fired)
        if advance and snap:
            state.setdefault("stocks", {})[sym] = snap
        elif snap:
            # 状态变化（跨日）单独标出来，方便「今天变了什么」一眼看懂
            old = (state.get("stocks") or {}).get(sym) or {}
            if old.get("close") and snap.get("close"):
                if old.get("above_ma20") != snap.get("above_ma20"):
                    report["fired"].append({
                        "id": "STATE_MA20", "kind": "state_change", "stock": name, "symbol": sym,
                        "text": f"站上/跌破 20 日线切换：{old.get('above_ma20')} → {snap.get('above_ma20')}"})
                if abs((snap.get("dd_from_high") or 0) - (old.get("dd_from_high") or 0)) >= 10:
                    report["fired"].append({
                        "id": "STATE_DD", "kind": "state_change", "stock": name, "symbol": sym,
                        "text": f"回撤带移动：{old.get('dd_from_high')}% → {snap.get('dd_from_high')}%（跨过 10pct 档）"})

    # 2) 商品
    for c in cfg.get("commodities", []):
        try:
            fired, snap = check_commodity(c["code"], c.get("rule", {}), None)
        except Exception as e:
            errors.append(f"{c.get('code')} 抓取失败：{e}")
            continue
        for f in fired:
            f.update(stock=c.get("name", c["code"]), kind=f.get("kind", "actionable"), group="商品")
        report["commodities"][c["code"]] = {"name": c.get("name"), "snapshot": snap, "fired": fired}
        report["fired"].extend(fired)
        if advance and snap:
            state.setdefault("commodities", {})[c["code"]] = snap

    # 3) 宏观触发器
    macro_conds = (cfg.get("macro_triggers") or {}).get("conditions", [])
    if macro_conds:
        hist: dict[str, list[dict]] = {}
        for key in ECON:
            try:
                hist[key] = econ_series(key)
            except Exception as e:
                errors.append(f"宏观 {key} 失败：{e}")
        report["macro"]["series"] = {k: v[:3] for k, v in hist.items()}
        fired = check_macro(macro_conds, hist)
        for f in fired:
            f["kind"] = f.get("kind", "actionable")
        report["fired"].extend(fired)

    if errors:
        report["errors"] = errors

    # 4) 标注「今天是否已经报过」，但**不隐藏**
    #
    # 2026-11-12 踩的坑：第一版在这里直接把已报过的信号从 report 里删掉，
    # 结果 16:45 定时任务消费掉 T2 之后，次日 8:00 的早报拿到空的 fired，
    # 会得出「今天什么都不用做」的结论——而 T2 明明已经过线。
    # 去重属于「推送」这一层，不属于「检查」这一层：检查必须永远说真话。
    fired_today = state.get("fired", {})
    for f in report["fired"]:
        key = f"{f.get('id')}:{f.get('symbol', f.get('stock', ''))}"
        f["already_reported"] = fired_today.get(key) == today
    report["fired_today_count"] = len([f for f in report["fired"] if not f["already_reported"]])

    # 只在真正推送时（--mark-alert）才记「已报」，冷检查不消费信号
    if notify:
        for f in report["fired"]:
            key = f"{f.get('id')}:{f.get('symbol', f.get('stock', ''))}"
            fired_today[key] = today

    if advance:
        state["fired"] = fired_today
        state["checked_on"] = today
        save_json(STATE_FILE, state)

    actionable = [f for f in report["fired"] if f["kind"] == "actionable"]

    # 5) 输出：默认沉默
    if as_json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    elif force or report["fired"] or errors:
        _print_human(report)
    else:
        print(f"{today} 无信号：关注池和触发器都没动，不用看。")

    fresh_alerts = [f for f in actionable if not f.get("already_reported")]
    if notify and fresh_alerts:
        _macos_notify(f"盯盘：{len(fresh_alerts)} 条要你拍板", fresh_alerts[0]["text"])

    return 0 if not errors else 1


def _print_human(report: dict) -> None:
    print(f"# 盯盘 {report['date']}")
    fired = report["fired"]
    if not fired:
        print("\n今天没有信号。")
    else:
        act = [f for f in fired if f["kind"] == "actionable"]
        chg = [f for f in fired if f["kind"] == "state_change"]
        err = [f for f in fired if f["kind"] == "error"]
        if act:
            fresh = [f for f in act if not f.get("already_reported")]
            print(f"\n## 关注池 / 触发器触发了（{len(act)}）")
            for f in act:
                # 宏观触发器没有个股名，用 group（触发器/商品）兜底，别打出 "[T2]：..." 这种空主体
                who = f.get("stock") or f.get("symbol") or f.get("group") or ""
                head = f"[{f['id']}] {who}" if who else f"[{f['id']}]"
                mark = "" if not f.get("already_reported") else "（今天已报过）"
                print(f"- {head}：{f['text']}{mark}")
        if chg:
            print(f"\n## 状态变化（{len(chg)}，不一定动手，但要知道）")
            for f in chg:
                print(f"- {f.get('stock','')}：{f['text']}")
        if err:
            print(f"\n## 出错（{len(err)}）")
            for f in err:
                print(f"- {f['id']}：{f['text']}")

    stocks = report.get("stocks") or {}
    if stocks:
        print("\n## 关注池")
        for sym, v in stocks.items():
            s = v.get("snapshot") or {}
            if not s:
                continue
            print(f"- {v['name']}({sym}) {s.get('close')} ({s.get('pct')}%)  "
                  f"PE {s.get('pe')}  回撤 {s.get('dd_from_high')}%  "
                  f"{'在' if s.get('above_ma20') else '破'}20日线")

    if report.get("errors"):
        print("\n## 抓取失败")
        for e in report["errors"]:
            print(f"- {e}")


def _macos_notify(title: str, body: str) -> None:
    script = f'display notification {json.dumps(body, ensure_ascii=False)} with title {json.dumps(title, ensure_ascii=False)}'
    try:
        subprocess.run(["osascript", "-e", script], timeout=10, check=False)
    except Exception:
        pass


def main() -> int:
    ap = argparse.ArgumentParser(description="关注池 + 触发器机械检查")
    ap.add_argument("--force", action="store_true", help="无条件打印全部")
    ap.add_argument("--json", action="store_true", help="机器可读输出")
    ap.add_argument("--advance", action="store_true", help="推进状态文件（确认输出无误后再用）")
    ap.add_argument("--mark-alert", dest="notify", action="store_true", help="有 actionable 时弹通知")
    a = ap.parse_args()
    return run(force=a.force, advance=a.advance, as_json=a.json, notify=a.notify)


if __name__ == "__main__":
    sys.exit(main())
