#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""东财 push2his 中断时的降级：腾讯日线，存张成 JSON。

用法: python3 fetch_prices.py sh688981 sz301308 ...
输出: ../数据/prices_<YYYYMMDD>.json
"""
from __future__ import annotations
import json, sys, urllib.request
from datetime import date
from pathlib import Path

OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}))


def kline(code: str, n: int = 400) -> list[tuple[str, float]]:
    url = (f"https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param={code},day,,,{n},qfq")
    d = json.loads(OPENER.open(urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=30).read())
    rows = d["data"][code].get("qfqday") or d["data"][code]["day"]
    return [(r[0], float(r[2])) for r in rows]  # date, close


if __name__ == "__main__":
    out = Path(__file__).resolve().parent.parent / "数据" / f"prices_{date.today():%Y%m%d}.json"
    res = {}
    for c in sys.argv[1:]:
        res[c] = kline(c)
        print(c, res[c][-1], len(res[c]))
    out.write_text(json.dumps(res, ensure_ascii=False), encoding="utf-8")
    print("->", out)
