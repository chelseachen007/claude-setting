import json
a=json.load(open('board_k.json')); b=json.load(open('bkhist.json'))
d=dict(a); d.update({k:v for k,v in b.items() if len(v)>len(d.get(k,[]))})
spans=[("基站 2019-07~2020-07","2019-06-01","2020-07-31"),("双碳 2020-09~2021-11","2020-09-01","2021-11-30"),("AI 2023-01~2024-12","2023-01-01","2024-12-31"),("2025","2025-01-02","2025-12-31"),("2026 YTD","2026-01-02","2026-11-11")]
rows=[]
for k,v in d.items():
    out=[]
    for n,s,e in spans:
        seg=[(x,c) for x,c in v if s<=x<=e]
        out.append(f"{(seg[-1][1]/seg[0][1]-1)*100:>+8.1f}%" if len(seg)>1 else "     n/a")
    cur=v[-1][1]; inc=[x for x in v if x[0]>="2025-01-01"]; hi=max(inc,key=lambda t:t[1])
    rows.append((k," ".join(out),f"{(cur/hi[1]-1)*100:+.1f}%"))
print(f"{'板块':<14}{'基站':>10}{'双碳':>10}{'AI23-24':>10}{'2025':>10}{'2026YTD':>10}{'距25-26高':>10}")
for k,o,h in rows: print(f"{k:<14}{o}{h:>10}")
