"""凯利公式计算：海尔智家 & 中证500
口径：日收益 → 年化 μ、σ → 连续形式 f* = (μ-rf)/σ²
数据：腾讯前复权日线（海尔 641 根自 2024-03，中证500 1201 根自 2021-11）
"""
import json, math, statistics as st
from pathlib import Path
HERE = Path(__file__).resolve().parent

d = json.load(open(HERE/"raw.json"))
RF = 0.018  # 10Y 国债近似

def series(rows):
    out = [(r[0], float(r[2])) for r in rows]
    # 过滤非正价格（部分标的早期前复权为负/接近 0，无意义）
    return [x for x in out if x[1] > 0.01]

def stats(px, label):
    closes = [p for _, p in px]
    rets = [closes[i]/closes[i-1]-1 for i in range(1, len(closes))]
    T = len(rets)
    mu_a = st.mean(rets) * 252
    sd_a = st.stdev(rets) * math.sqrt(252)
    geo_a = (closes[-1]/closes[0])**(252/T) - 1
    peak, mdd = closes[0], 0
    for c in closes:
        peak = max(peak, c); mdd = min(mdd, c/peak-1)
    return dict(label=label, start=px[0][0], end=px[-1][0], n=T,
                first=round(closes[0],3), last=round(closes[-1],3),
                mu_a=mu_a, sd_a=sd_a, geo_a=geo_a, mdd=mdd,
                win=sum(1 for r in rets if r>0)/T, rets=rets)

def kelly(s, k=1.5):
    ex = s["mu_a"] - RF
    return dict(ex=ex, f=ex/s["sd_a"]**2, f_risk=ex/(k*s["sd_a"]**2))

res = {}
for label, v in d.items():
    day = series(v["day"])
    res[label] = dict(
        full=stats(day, "全样本"), 
        y3=stats(day[-757:], "近3年"),
        y1=stats(day[-253:], "近1年"),
        wk=stats(series(v["week"]), "周线全样本"),
        spot=v["spot"])
    for kk in ["full","y3","y1","wk"]:
        s = res[label][kk]
        if kk == "wk":
            T = s["n"]; s["mu_a"] = st.mean(s["rets"])*52; s["sd_a"] = st.stdev(s["rets"])*math.sqrt(52)
            s["geo_a"] = (s["last"]/s["first"])**(52/T)-1
        res[label]["k_"+kk] = kelly(s)

def clean(v):
    if isinstance(v, dict): return {k: clean(x) for k,x in v.items() if k!="rets"}
    if isinstance(v, list): return [clean(x) for x in v]
    if isinstance(v, float): return v
    return v
json.dump(clean(res), open(HERE/"results.json","w"), ensure_ascii=False, indent=1)

for label, v in res.items():
    print("="*72); print(label)
    for kk,nm in [("full","全样本"),("y3","近3年"),("y1","近1年"),("wk","周线全")]:
        s=v[kk]; k=v["k_"+kk]
        print(f"  [{nm}] {s['start']}→{s['end']} n={s['n']:5d}  {s['first']}→{s['last']}")
        print(f"      年化μ={s['mu_a']*100:7.2f}%  年化σ={s['sd_a']*100:6.2f}%  几何年化={s['geo_a']*100:7.2f}%  MDD={s['mdd']*100:6.1f}%  日胜率={s['win']*100:4.1f}%")
        print(f"      ★超额={k['ex']*100:7.2f}%   f*={k['f']*100:8.2f}%   风险约束f={k['f_risk']*100:6.1f}%")
