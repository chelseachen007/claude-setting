import json, urllib.request, urllib.parse
UA={"User-Agent":"Mozilla/5.0"}
op=urllib.request.build_opener(urllib.request.ProxyHandler({}))
ids={"通信设备":"BK0448","CPO概念":"BK1128","光通信模块":"BK1136","半导体":"BK1036","半导体设备":"BK1326","创新药":"BK1106","医疗器械":"BK1041","中药概念":"BK0615","锂矿":"BK1173","医疗服务":"BK0727","电池":"BK1033","沪深A股":"BK0740"}
for n,s in ids.items():
    u=f"https://push2.eastmoney.com/api/qt/stock/get?secid=90.{s}&fields=f43,f58,f162,f167,f116,f173,f92,f9"
    d=json.loads(op.open(urllib.request.Request(u,headers=UA),timeout=30).read())["data"]
    print(n, {k:v for k,v in d.items() if k in("f162","f167","f173","f92")})
