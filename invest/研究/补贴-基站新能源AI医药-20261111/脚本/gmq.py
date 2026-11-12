import json
def load(p): return {x["SECURITY_CODE"]:x for x in json.load(open(p))}
h1=load("fin_2026-06-30.json"); q3=load("fin_2026-09-30.json")
r=json.load(open("rank2.json"))
# Q3单季毛利率 = (Q3累计收入*累计毛利 - H1) / (Q3累计收入-H1)
import math
def qgm(c):
    a=q3.get(c); b=h1.get(c)
    if not a or not b: return None
    try:
        r1,r0=a["TOTAL_OPERATE_INCOME"],b["TOTAL_OPERATE_INCOME"]
        if not r1 or not r0 or r1<=r0: return None
        g1=a.get("XSMLL"); g0=b.get("XSMLL")
        if g1 is None or g0 is None: return None
        gp1=r1*g1/100; gp0=r0*g0/100
        return (gp1-gp0)/(r1-r0)*100
    except: return None
for n in ["兆易创新","长鑫科技","江波龙","佰维存储","德明利","中际旭创","长飞光纤","亨通光电","天齐锂业","赣锋锂业","药明康德"]:
    c=[k["code"] for k in r if k["name"]==n]
    if c: print(n, c[0], "累计口径", q3[c[0]].get("XSMLL"), "→单季", round(qgm(c[0]) or 0,1))
