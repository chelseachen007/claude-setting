import json, urllib.request
UA={"User-Agent":"Mozilla/5.0"}
op=urllib.request.build_opener(urllib.request.ProxyHandler({}))
codes={"603986":"1.603986","688008":"1.688008","600487":"1.600487","601869":"1.601869","300308":"0.300308","300502":"0.300502","603259":"1.603259","688825":"1.688825","688525":"1.688525","301308":"0.301308","001309":"0.001309","002466":"0.002466","002460":"0.002460","002812":"0.002812","002709":"0.002709","300750":"0.300750","600276":"1.600276"}
for c,s in codes.items():
    u=f"https://push2.eastmoney.com/api/qt/stock/get?secid={s}&fields=f43,f57,f58,f116,f162,f167"
    d=json.loads(op.open(urllib.request.Request(u,headers=UA),timeout=30).read())["data"]
    # f43 价格为 *100 整数
    print(f"{c} {d['f58']} 现价{d['f43']/100:.2f} 市值{d['f116']/1e8:.0f}亿 PE25A {d['f162']/100:.1f} PB {d['f167']/100:.2f}")
