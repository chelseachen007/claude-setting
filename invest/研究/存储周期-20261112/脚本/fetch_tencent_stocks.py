#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""腾讯行情快照：东财 push2 对部分沪市代码（688362/688126/688981 等）会掐连接，
这里做降级补充。字段位置以 sh688981 实测为准。

用法: python3 fetch_tencent_stocks.py sh688981 sz301308 sh000688
"""
from __future__ import annotations
import sys, urllib.request

OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}))


def q(codes: list[str]) -> list[dict]:
    url = "https://qt.gtimg.cn/q=" + ",".join(codes)
    raw = OPENER.open(urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=30).read()
    out = []
    for line in raw.decode("gbk", "ignore").split(";"):
        if "=" not in line:
            continue
        f = line.split('="', 1)[1].rstrip('"').split("~")
        if len(f) < 50:
            continue
        out.append(dict(code=f[2], name=f[1], px=float(f[3] or 0), mcap_yi=float(f[45] or 0),
                        pe_ttm=float(f[39] or 0), pb=float(f[46] or 0), chg_pct=float(f[32] or 0),
                        time=f[30], w52_hi=float(f[47] or 0), w52_lo=float(f[48] or 0)))
    return out


if __name__ == "__main__":
    for r in q(sys.argv[1:]):
        print(f"{r['code']} {r['name']:<6} {r['px']:>8.2f}  市值{r['mcap_yi']:>9.0f}亿  PE(TTM){r['pe_ttm']:>8.2f}  PB{r['pb']:>6.2f}  涨跌{r['chg_pct']:>6.2f}%  {r['time']}")
