import json,urllib.request,urllib.parse,time
UA={"User-Agent":"Mozilla/5.0"}
op=urllib.request.build_opener(urllib.request.ProxyHandler({}))
def get(u): return json.loads(op.open(urllib.request.Request(u,headers=UA),timeout=60).read())
def page(pr,p,cols):
    out=[];pg=1
    while True:
        q=dict(reportName=pr,columns=cols,pageSize=500,sortColumns="SECURITY_CODE",sortTypes="1",source="WEB",client="WEB",pageNumber=pg,filter=f"(REPORT_DATE='{p}')")
        d=get("https://datacenter-web.eastmoney.com/api/data/v1/get?"+urllib.parse.urlencode(q))
        r=d.get("result")
        if not r: print(pr,d.get("code"),d.get("message")); break
        out+=r["data"]
        if pg>=r["pages"]: break
        pg+=1; time.sleep(0.1)
    return out
import sys
cf25=page("RPT_DMSK_FN_CASHFLOW","2025-09-30 00:00:00","SECURITY_CODE,NETCASH_OPERATE,SALES_SERVICES")
print("cf25",len(cf25)); json.dump(cf25,open("cf_2025Q3.json","w"),ensure_ascii=False)
bs=page("RPT_DMSK_FN_BALANCE","2026-09-30 00:00:00","SECURITY_CODE,ACCOUNTS_RECE,INVENTORY,TOTAL_ASSETS,TOTAL_LIABILITIES,TOTAL_EQUITY")
print("bs",len(bs)); json.dump(bs,open("bs_2026Q3.json","w"),ensure_ascii=False)
