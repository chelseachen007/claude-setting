import sys, json, urllib.parse
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT/'工具/抓数'))
import fetch_eastmoney as F
PEERS={'300308':'中际旭创','300502':'新易盛','300394':'天孚通信','688048':'长光华芯','688313':'仕佳光子',
       '002463':'沪电股份','600183':'生益科技','300476':'胜宏科技','002938':'鹏鼎控股','300433':'蓝思科技','603228':'景旺电子'}
out={}
for c,n in PEERS.items():
    try:
        q=F.quote(c); q['name']=n; out[c]=q
        print(f"{c} {n:<6} 价{q['px']:>8.2f} 市值{q['mcap']/1e8:>7.0f}亿 PE25A{q['pe_static']:>7.1f} PB{q['pb']:>6.2f}")
    except Exception as e:
        print(c,n,'ERR',e)
Path(__file__).resolve().parents[1].joinpath('数据/peers.json').write_text(json.dumps(out,ensure_ascii=False,indent=1),encoding='utf-8')
