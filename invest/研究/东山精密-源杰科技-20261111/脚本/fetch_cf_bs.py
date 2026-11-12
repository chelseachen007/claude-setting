# 现金流 / 资产负债表 字段探测 + 抓取
import sys, json, urllib.parse
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT/'工具/抓数'))
import fetch_eastmoney as F
OUT = Path(__file__).resolve().parents[1]/'数据'

def raw(name, code, date):
    q = dict(reportName=name, columns="ALL", pageSize=5, sortColumns="REPORT_DATE", sortTypes="-1",
             source="WEB", client="WEB", pageNumber=1,
             filter=f'(SECURITY_CODE="{code}")(REPORT_DATE=\'{date} 00:00:00\')')
    j = F._get("https://datacenter-web.eastmoney.com/api/data/v1/get?" + urllib.parse.urlencode(q))
    r = j.get('result')
    return (r['data'][0] if r and r['data'] else {k: j.get(k) for k in ('code','message')})

for nm in ("RPT_DMSK_FN_CASHFLOW","RPT_DMSK_FN_BALANCE"):
    x = raw(nm, "002384", "2026-09-30")
    print(nm, list(x.keys()))
