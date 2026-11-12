import json, urllib.request
UA={"User-Agent":"Mozilla/5.0"}
op=urllib.request.build_opener(urllib.request.ProxyHandler({}))
def k(s,n=800):
    u=f"https://push2his.eastmoney.com/api/qt/stock/kline/get?secid={s}&fields1=f1,f2,f3&fields2=f51,f53&klt=101&fqt=1&end=20500101&lmt={n}"
    d=json.loads(op.open(urllib.request.Request(u,headers=UA),timeout=30).read())["data"]
    return [(x.split(",")[0],float(x.split(",")[1])) for x in d["klines"]]
for n,s in {"药明康德":"1.603259","恒瑞医药":"1.600276","迈瑞医疗":"0.300760","工业富联":"1.601138","兆易创新":"1.603986","中际旭创":"0.300308","亨通光电":"1.600487","长飞光纤":"1.601869","天齐锂业":"0.002466"}.items():
    ks=k(s); q=[c for x,c in ks]; cur=q[-1]
    out=[]
    for m in [20,60,120,250]:
        if len(q)>m: out.append(f'MA{m} {(cur/(sum(q[-m:])/m)-1)*100:+.1f}%')
    inc=[x for x in ks if x[0]>="2025-01-01"]; hi=max(inc,key=lambda t:t[1]); lo=min(inc,key=lambda t:t[1])
    print(f'{n:<6}{cur:>8.2f} 距25-26高{(cur/hi[1]-1)*100:+.1f}%({hi[0]}) 现/低{(cur/lo[1]-1)*100:+.0f}%  |', ' '.join(out))
