import sys, json, urllib.parse
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT/'工具/抓数'))
import fetch_eastmoney as F
OUT = Path(__file__).resolve().parents[1]/'数据'
CODES={'002384':'东山精密','688498':'源杰科技'}
DATES=['2023-12-31','2024-12-31','2025-12-31','2026-09-30']
def raw(name, code, date):
    q = dict(reportName=name, columns="ALL", pageSize=5, sortColumns="REPORT_DATE", sortTypes="-1",
             source="WEB", client="WEB", pageNumber=1,
             filter=f'(SECURITY_CODE="{code}")(REPORT_DATE=\'{date} 00:00:00\')')
    j = F._get("https://datacenter-web.eastmoney.com/api/data/v1/get?" + urllib.parse.urlencode(q))
    r=j.get('result'); return r['data'][0] if r and r['data'] else {}
CF=['NETCASH_OPERATE','NETCASH_INVEST','CONSTRUCT_LONG_ASSET','NETCASH_FINANCE','SALES_SERVICES','END_CCE']
BS=['TOTAL_ASSETS','TOTAL_LIABILITIES','MONETARYFUNDS','ACCOUNTS_RECE','INVENTORY','TOTAL_EQUITY','CURRENT_RATIO','DEBT_ASSET_RATIO','FIXED_ASSET','SHORT_LOAN','ACCOUNTS_PAYABLE']
res={}
for c in CODES:
    res[c]={}
    for d in DATES:
        cf=raw("RPT_DMSK_FN_CASHFLOW",c,d); bs=raw("RPT_DMSK_FN_BALANCE",c,d)
        res[c][d]={'cf':{k:cf.get(k) for k in CF},'bs':{k:bs.get(k) for k in BS}}
(OUT/'cf_bs.json').write_text(json.dumps(res,ensure_ascii=False,indent=1),encoding='utf-8')
for c,v in res.items():
    print('\n==',CODES[c])
    for d,x in v.items():
        g=lambda k: (x['cf'].get(k) or 0)/1e8
        b=lambda k: (x['bs'].get(k) or 0)/1e8
        print(f"{d} OCF{g('NETCASH_OPERATE'):.2f}亿 投资CF{g('NETCASH_INVEST'):.2f} 购建{g('CONSTRUCT_LONG_ASSET'):.2f} 筹资CF{g('NETCASH_FINANCE'):.2f} 期末现金{g('END_CCE'):.2f} | "
              f"总资产{b('TOTAL_ASSETS'):.1f} 负债率{x['bs'].get('DEBT_ASSET_RATIO')} 货币{b('MONETARYFUNDS'):.1f} 应收{b('ACCOUNTS_RECE'):.1f} 存货{b('INVENTORY'):.1f} 权益{b('TOTAL_EQUITY'):.1f}")
