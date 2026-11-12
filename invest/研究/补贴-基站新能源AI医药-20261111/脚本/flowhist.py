import json, urllib.request, time
UA={"User-Agent":"Mozilla/5.0"}
op=urllib.request.build_opener(urllib.request.ProxyHandler({}))
ids={"通信设备":"BK0448","CPO":"BK1128","半导体":"BK1036","半导体设备":"BK1326","创新药":"BK1106","医疗器械":"BK1041","中药":"BK0615","锂矿":"BK1173","医疗服务":"BK0727","电池":"BK1033","光伏主材":"BK1318"}
for n,s in ids.items():
    u=f"https://push2his.eastmoney.com/api/qt/stock/fflow/daykline/get?lmt=0&klt=101&secid=90.{s}&fields1=f1,f2,f3,f7&fields2=f51,f52"
    d=json.loads(op.open(urllib.request.Request(u,headers=UA),timeout=30).read())["data"]
    ks=[(x.split(",")[0],float(x.split(",")[1])) for x in d["klines"]]
    s5=sum(x[1] for x in ks[-5:])/1e8; s20=sum(x[1] for x in ks[-20:])/1e8; s60=sum(x[1] for x in ks[-60:])/1e8
    print(f"{n:<8} 5日{s5:>+9.1f}亿 20日{s20:>+9.1f}亿 60日{s60:>+9.1f}亿  最新{ks[-1][0]}")
    time.sleep(0.1)
