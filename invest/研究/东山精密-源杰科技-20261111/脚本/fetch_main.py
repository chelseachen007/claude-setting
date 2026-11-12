# 拉 2021Q3~2026Q3 各季报 + 年报主指标，落盘
import sys, json, urllib.parse
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT/'工具/抓数'))
import fetch_eastmoney as F

OUT = Path(__file__).resolve().parents[1]/'数据'
CODES = {'002384':'东山精密','688498':'源杰科技'}
DATES = ['2021-12-31','2022-06-30','2022-12-31','2023-06-30','2023-12-31',
         '2024-06-30','2024-12-31','2025-06-30','2025-12-31','2026-06-30','2026-09-30']
res = {}
for code in CODES:
    rows = []
    for d in DATES:
        q = dict(reportName="RPT_LICO_FN_CPD", columns="ALL", pageSize=10,
                 sortColumns="REPORTDATE", sortTypes="-1", source="WEB", client="WEB", pageNumber=1,
                 filter=f'(SECURITY_CODE="{code}")(REPORTDATE=\'{d}\')')
        j = F._get("https://datacenter-web.eastmoney.com/api/data/v1/get?" + urllib.parse.urlencode(q))
        r = j.get('result')
        if r and r['data']:
            x = r['data'][0]
            rows.append({k: x.get(k) for k in
                         ['REPORTDATE','TOTAL_OPERATE_INCOME','PARENT_NETPROFIT','YSTZ','SJLTZ','YSHZ','SJLHZ','XSMLL','WEIGHTAVG_ROE','BASIC_EPS','BPS','MGJYXJJE','BOARD_NAME']})
        else:
            rows.append({'REPORTDATE': d, 'err': j.get('message')})
    res[code] = rows
    print(code, CODES[code], len(rows))
(OUT/'fin_main.json').write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding='utf-8')

for code, rows in res.items():
    print('\n==', CODES[code], code)
    for x in rows:
        if 'err' in x: print(x); continue
        rev = (x['TOTAL_OPERATE_INCOME'] or 0)/1e8
        np_ = (x['PARENT_NETPROFIT'] or 0)/1e8
        f = lambda v: f"{v:>9.2f}" if v is not None else '     None'
        print(f"{x['REPORTDATE'][:10]} 营收{f(rev)}亿 YoY{f(x['YSTZ'])} 净利{f(np_)}亿 YoY{f(x['SJLTZ'])} "
              f"毛利率{f(x['XSMLL'])} ROE{f(x['WEIGHTAVG_ROE'])} EPS{f(x['BASIC_EPS'])} BPS{f(x['BPS'])} 现金流EPS{f(x['MGJYXJJE'])}")
