import json, urllib.request, time
UA={"User-Agent":"Mozilla/5.0"}
op=urllib.request.build_opener(urllib.request.ProxyHandler({}))
ids={"通信设备":"BK0448","CPO":"BK1128","光通信模块":"BK1136","半导体":"BK1036","半导体设备":"BK1326","创新药":"BK1106","医疗器械":"BK1041","中药":"BK0615","锂矿":"BK1173","医疗服务":"BK0727","电池":"BK1033","沪深A股":"BK0740"}
res={}
for n,s in ids.items():
    u=f"https://push2his.eastmoney.com/api/qt/stock/kline/get?secid=90.{s}&fields1=f1,f2,f3&fields2=f51,f53&klt=101&fqt=1&end=20500101&lmt=1500"
    d=json.loads(op.open(urllib.request.Request(u,headers=UA),timeout=30).read())
    ks=[(x.split(",")[0],float(x.split(",")[1])) for x in d["data"]["klines"]]
    res[n]=ks
    cur=ks[-1][1]
    # 找历史最高（2021年后）
    for y in (2021,2022,2023,2024,2025,2026):
        yy=[x for x in ks if x[0].startswith(str(y))]
        if yy:
            hi=max(yy,key=lambda x:x[1]); lo=min(yy,key=lambda x:x[1])
            print(f"{n:<8}{y} 高{hi[1]:>9.1f}({hi[0]}) 低{lo[1]:>9.1f} 收{yy[-1][1]:>9.1f} 现/年内高 {(cur/hi[1]-1)*100:>6.1f}%")
    print("---")
    time.sleep(0.1)
json.dump(res,open("bkhist.json","w"))
