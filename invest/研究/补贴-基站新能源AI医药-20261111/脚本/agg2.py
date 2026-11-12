import json
a=json.load(open("fin_2025-09-30.json")); b=json.load(open("fin_2026-09-30.json"))
A={r["SECURITY_CODE"]:r for r in a}; B={r["SECURITY_CODE"]:r for r in b}
data=[(B[c],A[c]) for c in B if c in A]
def row(name,inds):
    p=[x for x in data if x[0].get("BOARD_NAME") in inds]
    def mid(x,k):
        v=[(y[k] or 0) for y in p if y.get(k) is not None]
        v.sort(); return v[len(v)//2] if v else None
    return p
subs={
"半导体":["半导体"],"光伏设备":["光伏设备"],"电池":["电池"],"通信设备":["通信设备"],"软件+IT":["软件开发","IT服务Ⅱ"],
"创新药(化学制药)":["化学制药"],"中药":["中药Ⅱ"],"医疗器械":["医疗器械"],"医疗服务":["医疗服务"],
"白酒":["白酒Ⅱ"],"白色家电":["白色家电"],"电网设备":["电网设备"],"汽车零部件":["汽车零部件"],"游戏":["游戏Ⅱ"]}
print(f"{'行业':<16}{'样本':>5}{'26Q3毛利率%':>11}{'同比pp':>8}{'毛利率中位数%':>12}")
for k,inds in subs.items():
    p=[x for x in data if x[0].get("BOARD_NAME") in inds and x[0].get("XSMLL") is not None and x[1].get("XSMLL") is not None]
    if len(p)<5: continue
    gm=[x[0]["XSMLL"] for x in p]; g0=[x[1]["XSMLL"] for x in p]
    srt=sorted(gm); med=srt[len(srt)//2]
    print(f"{k:<16}{len(p):>5}{sum(gm)/len(gm):>11.1f}{sum(gm)/len(gm)-sum(g0)/len(g0):>8.2f}{med:>12.1f}")
