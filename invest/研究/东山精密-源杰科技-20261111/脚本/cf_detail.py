import sys, json, urllib.parse
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT/'工具/抓数'))
import fetch_eastmoney as F
# 全字段现金流量表最新两期，用于判断是否含并购/受限资金
for c in ('002384','688498'):
    q = dict(reportName="RPT_DMSK_FN_CASHFLOW", columns="ALL", pageSize=5, sortColumns="REPORT_DATE", sortTypes="-1",
             source="WEB", client="WEB", pageNumber=1,
             filter=f'(SECURITY_CODE="{c}")(REPORT_DATE=\'2026-09-30 00:00:00\')')
    j=F._get("https://datacenter-web.eastmoney.com/api/data/v1/get?"+urllib.parse.urlencode(q))
    x=j['result']['data'][0]
    print(c, {k:x[k] for k in ('NETCASH_OPERATE','CONSTRUCT_LONG_ASSET','NETCASH_INVEST','NETCASH_FINANCE','BEGIN_CCE','END_CCE')})
