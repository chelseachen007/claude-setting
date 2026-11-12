#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""美股快照 + 两年日线（腾讯，us 前缀，延迟行情）。字段含义未逐一核验，PE 列按美股习惯为广义 PE。"""
from __future__ import annotations
import json, urllib.request
from datetime import date
from pathlib import Path

OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}))
SYMS = ["usSNOW", "usMU", "usSTX", "usSNDK", "usSNPS", "usVRNS", "usNTAP", "usPANW", "usNET", "usSMCI", "usCRWD"]


def snap() -> list[dict]:
    url = "https://qt.gtimg.cn/q=" + ",".join(SYMS)
    raw = OPENER.open(urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=30).read()
    out = []
    for line in raw.decode("gbk", "ignore").split(";"):
        if '="' not in line:
            continue
        f = line.split('="', 1)[1].rstrip('"').split("~")
        if len(f) < 50:
            continue
        def n(i):  # 字段可能为空，空即 0
            try:
                return float(f[i])
            except (ValueError, IndexError):
                return 0.0
        out.append(dict(sym=line.split("=")[0][2:], name=f[1], px=n(3), chg_pct=n(32),
                        pe=n(39), mcap_yi=n(45), pb=n(46),
                        w52_hi=n(48), w52_lo=n(49), time=f[30] if len(f) > 30 else ""))
    return out


def kline(sym: str, n: int = 300) -> list[tuple[str, float]]:
    # 美股要走 usfqkline，且 code 需带交易所后缀（usWDC.OQ）
    code = sym + ".OQ"
    url = f"https://web.ifzq.gtimg.cn/appstock/app/usfqkline/get?param={code},day,,,{n},qfq"
    d = json.loads(OPENER.open(urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=30).read())
    node = d["data"][code]
    rows = node.get("qfqday") or node.get("day")
    return [(r[0], float(r[2])) for r in rows]


if __name__ == "__main__":
    base = Path(__file__).resolve().parent.parent / "数据"
    s = snap()
    for r in s:
        print(f"{r['sym']} {r['name']:<10} {r['px']:>9.2f} PE{r['pe']:>8.2f} 市值{r['mcap_yi']:>8.1f}亿USD 涨跌{r['chg_pct']:>6.2f}% 52w {r['w52_lo']:.1f}-{r['w52_hi']:.1f}")
    (base / f"us_snap_{date.today():%Y%m%d}.json").write_text(json.dumps(s, ensure_ascii=False))
    hist = {}
    for sym in SYMS:
        try:
            hist[sym] = kline(sym)
        except Exception as e:  # noqa: BLE001
            print(sym, "err", e)
    (base / f"us_prices_{date.today():%Y%m%d}.json").write_text(json.dumps(hist, ensure_ascii=False))
    for k, v in hist.items():
        print(k, v[-1], len(v))
