"""分数凯利在 A 股（T+1、无杠杆、无做空）下的真实约束"""
import json, math, statistics as st
from pathlib import Path
HERE = Path(__file__).resolve().parent
d=json.load(open(HERE/"raw.json"))
RF=0.018

def series(rows):
    return [(r[0],float(r[2])) for r in rows if float(r[2])>0.01]

def rets(px): 
    c=[p for _,p in px]; return [c[i]/c[i-1]-1 for i in range(1,len(c))]

def sim(rets, frac, kelly_f, years=10):
    """全仓 frac 比例，其余吃无风险。日度再平衡，无杠杆、无做空 → f∈[0,1]"""
    f = max(0.0, min(1.0, frac*kelly_f))
    rf_d = RF/252
    nav=1.0; peak=1.0; mdd=0
    for r in rets:
        nav *= (1 + f*r + (1-f)*rf_d)
        peak=max(peak,nav); mdd=min(mdd,nav/peak-1)
    mu=st.mean(rets); sd=st.stdev(rets)
    mu_a=mu*252; sd_a=sd*math.sqrt(252)
    g = f*(mu_a-RF) + RF - 0.5*f**2*sd_a**2      # 连续近似下的对数增长
    return dict(f=f, mdd=mdd, geo_ann=(nav**(252/len(rets))-1), log_growth=g)

cases = {}
for label in ["海尔智家","中证500"]:
    day=series(d[label]["day"]); r=rets(day)
    mu_a=st.mean(r)*252; sd_a=st.stdev(r)*math.sqrt(252)
    fstar=(mu_a-RF)/sd_a**2
    wk=series(d[label]["week"]); rw=rets(wk)
    mu_w=st.mean(rw)*52; sd_w=st.stdev(rw)*math.sqrt(52)
    fstar_w=(mu_w-RF)/sd_w**2
    cases[label]=dict(fstar=fstar, fstar_w=fstar_w, mu_a=mu_a, sd_a=sd_a,
                      table={f: sim(r, f, fstar) for f in [0.25,0.5,1.0,1.5,2.0]},
                      table_w={f: sim(rw, f, fstar_w) for f in [0.25,0.5,1.0,1.5,2.0]})

for label,v in cases.items():
    print("="*70); print(label, f" 日线 f*={v['fstar']*100:.1f}%  周线 f*={v['fstar_w']*100:.1f}%")
    print(f"{'倍数':>6} {'日线f':>8} {'日线对数增长':>13} {'日线MDD':>9} | {'周线f':>8} {'周线对数增长':>13} {'周线MDD':>9}")
    for f in [0.25,0.5,1.0,1.5,2.0]:
        a=v["table"][f]; b=v["table_w"][f]
        print(f"{f:>6.2f} {a['f']*100:>7.1f}% {a['log_growth']*100:>12.2f}% {a['mdd']*100:>8.1f}% | {b['f']*100:>7.1f}% {b['log_growth']*100:>12.2f}% {b['mdd']*100:>8.1f}%")
json.dump(cases, open(HERE/"fvar.json","w"), ensure_ascii=False, indent=1)
