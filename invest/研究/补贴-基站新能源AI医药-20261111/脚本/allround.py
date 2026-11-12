import json, urllib.request, urllib.parse, time
UA={"User-Agent":"Mozilla/5.0"}
op=urllib.request.build_opener(urllib.request.ProxyHandler({}))
def get(u): return op.open(urllib.request.Request(u,headers=UA),timeout=60).read().decode("utf-8","ignore")
def period(p):
    out=[]; pg=1
    while True:
        q=dict(reportName="RPT_LICO_FN_CPD",columns="SECURITY_CODE,SECURITY_NAME_ABBR,TOTAL_OPERATE_INCOME,YSTZ,PARENT_NETPROFIT,SJLTZ,XSMLL,BOARD_NAME,REPORTDATE",
               pageSize=500,sortColumns="SECURITY_CODE",sortTypes="1",source="WEB",client="WEB",pageNumber=pg,
               filter=f"(REPORTDATE='{p}')")
        d=json.loads(get("https://datacenter-web.eastmoney.com/api/data/v1/get?"+urllib.parse.urlencode(q)))
        r=d.get("result")
        if not r: break
        out+=r["data"]
        if pg>=r["pages"]: break
        pg+=1; time.sleep(0.15)
    return out
d=period("2026-06-30"); print(len(d)); json.dump(d,open("fin_2026-06-30.json","w"),ensure_ascii=False)
