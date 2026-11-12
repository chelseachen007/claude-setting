import sys, json, urllib.parse
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT/'工具/抓数'))
import fetch_eastmoney as F
OUT = Path(__file__).resolve().parents[1]/'数据'
CODES={'002384':'东山精密','688498':'源杰科技'}
res={}
for c in CODES:
    url=(f"https://push2his.eastmoney.com/api/qt/stock/kline/get?secid={F._secid(c)}"
         "&fields1=f1,f2,f3&fields2=f51,f53,f57&klt=101&fqt=1&end=20500101&lmt=700")
    k=F._get(url)['data']['klines']
    rows=[(x.split(',')[0], float(x.split(',')[1]), float(x.split(',')[2])) for x in k]
    res[c]=rows
    cur=rows[-1][1]; hi=max(rows,key=lambda r:r[1])
    for n in (20,60,120,250):
        if len(rows)>=n:
            print(f"{CODES[c]} 近{n}日 {(cur/rows[-n][1]-1)*100:+.1f}%")
    print(f"{CODES[c]} 最新{rows[-1][0]} {cur:.2f} 700日高{hi[1]:.2f}({hi[0]}) 距高{(cur/hi[1]-1)*100:+.1f}%")
    # 2025年初以来
    for r in rows:
        if r[0]=='2025-01-02': print(f"  2025-01-02收{r[1]:.2f} -> 至今{(cur/r[1]-1)*100:+.0f}%")
    # 2026年内
    y=[r for r in rows if r[0]>='2026-01-01']
    if y: print(f"  2026年初{y[0][1]:.2f} -> 至今{(cur/y[0][1]-1)*100:+.0f}%")
    # 成交量
(OUT/'kline.json').write_text(json.dumps(res,ensure_ascii=False),encoding='utf-8')
