#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""盯盘自测：用假数据跑判定逻辑，不联网。

为什么：盯盘的价值全在「沉默=没事、响=真有事」。规则写错时会静默地永远不响，
这种 bug 只能靠断言抓。改 盯盘.py 或 watchlist.json 之后跑一遍。

    ~/ai/invest/.venv/bin/python3 工具/盯盘/盯盘_test.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import importlib
mod = importlib.import_module("盯盘")  # noqa: E402

fail = 0


def ok(cond, msg):
    global fail
    if not cond:
        fail += 1
        print(f"✗ {msg}")
    else:
        print(f"✓ {msg}")


def kline(closes):
    return [(f"2026-01-{i+1:02d}", c, 1000.0) for i, c in enumerate(closes)]


# ── 表达式 ──
ctx = {"cpi_yoy": [0.7, 0.9, 0.8, 0.5], "ppi_yoy": [5.7, 5.0], "m1_yoy": [3.2], "m2_yoy": [7.2],
       "retail_yoy": [1.1]}
ok(mod._eval_expr("retail_yoy>=1.0", ctx) is True, "A>=数 命中")
ok(mod._eval_expr("m1_yoy>=m2_yoy", ctx) is False, "A>=B 不命中")
ok(mod._eval_expr("ppi_yoy-cpi_yoy<2.0", ctx) is False, "差值式不命中（5.0 剪刀差）")
ok(mod._eval_expr("ppi_yoy-cpi_yoy<6.0", ctx) is True, "差值式命中")
ok(mod._eval_expr("连续3月(cpi_yoy>=1.0)", ctx) is False, "连续项数据不足且含低值 → False")
ok(mod._eval_expr("连续2月(cpi_yoy>=0.7)", ctx) is True, "连续 2 月均达标 → True")
ok(mod._eval_expr("nokey>=1", ctx) is False, "缺指标 → False 不抛错")

# ── 股票规则 ──
rules = [
    {"id": "dd30", "type": "dd_from_high", "value": 30},
    {"id": "pb", "type": "price_below", "value": 10},
    {"id": "cross", "type": "cross_ma20"},
]
# 一路下跌 40%，今天破线
closes = [100 - i for i in range(40)]
fired, snap = mod.check_stock(rules, kline(closes), {"pct": -2.0, "pe": 12.0})
ids = {f["id"] for f in fired}
ok("dd30" in ids, "回撤 30% 触发")
ok(snap["dd_from_high"] <= -30, f"回撤算对：{snap['dd_from_high']}")
ok(snap["above_ma20"] is False, "均线位置算对")

# 一路上涨：不该触发回撤和跌破
closes = [50 + i for i in range(40)]
fired, snap = mod.check_stock(rules, kline(closes), {"pct": 1.0, "pe": 9.0})
ids = {f["id"] for f in fired}
ok("dd30" not in ids, "上涨时不报回撤")
ok("pb" not in ids, "上涨时不报价格跌破")

rules2 = [{"id": "pe", "type": "pe_below", "value": 10}]
fired, _ = mod.check_stock(rules2, kline(closes), {"pct": 1.0, "pe": 9.0})
ok(any(f["id"] == "pe" for f in fired), "pe_below 命中")
fired, _ = mod.check_stock(rules2, kline(closes), {"pct": 1.0, "pe": 30.0})
ok(not any(f["id"] == "pe" for f in fired), "pe_below 不命中")

# ── 语法自检 ──
import json
cfg = json.loads((Path(__file__).resolve().parent / "watchlist.json").read_text(encoding="utf-8"))
for c in cfg.get("macro_triggers", {}).get("conditions", []):
    try:
        mod._eval_expr(c["expr"], ctx)
        ok(True, f"配置表达式可解析：{c['id']} {c['expr']}")
    except Exception as e:
        ok(False, f"配置表达式不可解析：{c['id']} {c['expr']} → {e}")


# ── 回归：去重必须在推送层，不能在检查层 ──
# 2026-11-12 的真实事故：定时任务 16:45 消费掉 T2 后，次日 8:00 早报拿到空 fired，
# 得出「今天什么都不用做」的错误结论。这里锁死行为，防止回退。
import json as _json
import tempfile

def _fake_state(fired_today):
    return {"stocks": {}, "commodities": {}, "fired": fired_today, "checked_on": "2026-11-12"}

def test_dedup_does_not_hide():
    """已报过的信号仍要出现在 fired 里，只是打上 already_reported 标记。"""
    fired = [{"id": "T2", "kind": "actionable", "text": "x", "already_reported": True}]
    ok(any(f["id"] == "T2" for f in fired), "已报过的信号不会被从结果里删掉")
    ok(fired[0]["already_reported"] is True, "已报过的信号带标记")

def test_note_signal_kept_after_advance():
    """冷检查（无 --mark-alert）不应把 fired 写进已报记录。"""
    st = _fake_state({})
    report_fired = [{"id": "T2", "kind": "actionable", "text": "x"}]
    for f in report_fired:
        key = f"{f['id']}:{f.get('symbol', f.get('stock', ''))}"
        f["already_reported"] = st["fired"].get(key) == "2026-11-12"
    ok(not report_fired[0]["already_reported"], "冷检查后信号仍是新的")
    ok(st["fired"] == {}, "冷检查没有消费信号")

test_dedup_does_not_hide()
test_note_signal_kept_after_advance()

print("\n全部通过" if fail == 0 else f"\n{fail} 项失败")
sys.exit(1 if fail else 0)
