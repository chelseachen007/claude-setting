import json, statistics as st
from pathlib import Path
HERE = Path(__file__).resolve().parent
d=json.load(open(HERE/"raw.json")); RF=0.018
def ser(rows): return [(r[0],float(r[2])) for r in rows if float(r[2])>0.01]
def R(px):
    c=[p for _,p in px]; return [c[i]/c[i-1]-1 for i in range(1,len(c))]
def blk(rets, per, px):
    mu=st.mean(rets)*per; sd=st.stdev(rets)*(per**0.5)
    c=1.0; peak=1.0; mdd=0
    for r in rets:
        c*=1+r; peak=max(peak,c); mdd=min(mdd,c/peak-1)
    geo=(c**(per/len(rets))-1)
    return dict(mu=mu*100, sd=sd*100, geo=geo*100, mdd=mdd*100, ex=(mu-RF)*100,
                f=(mu-RF)/(sd**2)*100, start=px[0][0], end=px[-1][0], n=len(rets))

OUT={}
for lab in ["海尔智家","中证500"]:
    day=ser(d[lab]["day"]); wk=ser(d[lab]["week"])
    c={
      "近1年(日)": blk(R(day[-253:]),252, day[-253:]),
      "近3年(日)": blk(R(day[-757:]),252, day[-757:]),
      "全样本(日)": blk(R(day),252, day),
      "近3年(周)": blk(R(wk[-157:]),52, wk[-157:]),
      "近10年(周)": blk(R(wk[-521:]),52, wk[-521:]),
      "全样本(周)": blk(R(wk),52, wk),
    }
    OUT[lab]=c
    print("="*80); print(lab)
    print(f"{'窗口':<11}{'区间':<25}{'年化μ':>8}{'年化σ':>8}{'几何':>8}{'MDD':>8}{'超额':>8}{'f*':>9}{'半凯利':>9}")
    for k,v in c.items():
        print(f"{k:<11}{v['start']}→{v['end']:<12}{v['mu']:>7.1f}%{v['sd']:>7.1f}%{v['geo']:>7.1f}%{v['mdd']:>7.0f}%{v['ex']:>7.1f}%{v['f']:>8.0f}%{v['f']/2:>8.0f}%")
json.dump(OUT, open(HERE/"final.json","w"), ensure_ascii=False, indent=1)
# 52周高地位
for lab in ["海尔智家","中证500"]:
    day=ser(d[lab]["day"])[-243:]
    hi=max(p for _,p in day); lo=min(p for _,p in day); last=day[-1][1]
    print(f"\n{lab} 近52周区间 {lo:.2f} ~ {hi:.2f}，现价 {last:.2f}，分位 {(last-lo)/(hi-lo)*100:.0f}%")
