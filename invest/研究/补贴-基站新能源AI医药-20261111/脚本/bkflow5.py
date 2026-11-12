import json, urllib.request, urllib.parse, time
UA={"User-Agent":"Mozilla/5.0"}
op=urllib.request.build_opener(urllib.request.ProxyHandler({}))
ids={"通信设备":"BK0448","CPO概念":"BK1128","光通信模块":"BK1136","半导体":"BK1036","半导体设备":"BK1326","创新药":"BK1106","医疗器械":"BK1041","中药概念":"BK0615","光伏主材":"BK1318","锂矿":"BK1173","风电设备":"BK1032","医疗服务":"BK0727","化学制药":"BK0465","电池":"BK1033"}
u="https://push2.eastmoney.com/api/qt/ulist.np/get?fltt=2&invt=2&fields=f12,f14,f3,f62,f184,f66,f69,f267,f127&secids="+",".join(f"90.{v}" for v in ids.values())
d=json.loads(op.open(urllib.request.Request(u,headers=UA),timeout=30).read())
for r in d["data"]["diff"]:
    print(r)
