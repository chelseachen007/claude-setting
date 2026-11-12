import json, html
from pathlib import Path
HERE = Path(__file__).resolve().parent
rows=[]; bs=[0.5,1,1.5,2,3,4]; ps=[0.30,0.35,0.40,0.45,0.50,0.55,0.60,0.65,0.70,0.80]
for p in ps:
    r=[]
    for b in bs:
        f=(p*(b+1)-1)/b
        r.append(f)
    rows.append((p,r))

def cell(f):
    if f<=0: return '<td class="neg">停手</td>'
    v=f*100
    cls="w3" if v>50 else ("w2" if v>30 else ("w1" if v>10 else "w0"))
    return f'<td class="{cls}">{v:.1f}%</td>'

grid=""
for p,r in rows:
    grid+=f'<tr><th>{p*100:.0f}%</th>'+"".join(cell(x) for x in r)+"</tr>"

fin=json.load(open(HERE/"final.json"))
def win_table(label, rowspec):
    h=f'<table class="t2"><thead><tr><th>窗口</th><th>区间</th><th>年化μ</th><th>年化σ</th><th>几何年化</th><th>MDD</th><th>超额(μ−1.8%)</th><th>凯利 f*</th><th>半凯利</th></tr></thead><tbody>'
    for k in rowspec:
        v=fin[label][k]
        fpos = "pos" if v['f']>0 else "neg"
        half = v['f']/2
        h+=f'<tr><td>{k}</td><td class="mono small">{v["start"]} → {v["end"]}</td><td>{v["mu"]:.1f}%</td><td>{v["sd"]:.1f}%</td><td>{v["geo"]:.1f}%</td><td class="neg">{v["mdd"]:.0f}%</td><td class="{fpos}">{v["ex"]:+.1f}%</td><td class="{fpos} big">{v["f"]:.0f}%</td><td class="mono">{half:.0f}%</td></tr>'
    return h+"</tbody></table>"

spec1=["近1年(日)","近3年(日)","近3年(周)","近10年(周)","全样本(周)"]
spec2=["近1年(日)","近3年(日)","全样本(日)","近3年(周)","近10年(周)","全样本(周)"]

HTML=f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>凯利公式速查表 · 海尔智家 / 中证500</title>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:-apple-system,"PingFang SC","Helvetica Neue",sans-serif;background:#0d1117;color:#c9d1d9;padding:40px 24px;line-height:1.6}}
.wrap{{max-width:1120px;margin:0 auto}}
h1{{font-size:30px;color:#f0f6fc;font-weight:700;letter-spacing:-.5px}}
h2{{font-size:20px;color:#58a6ff;margin:44px 0 8px;font-weight:600;border-left:3px solid #58a6ff;padding-left:12px}}
h3{{font-size:15px;color:#8b949e;margin:20px 0 10px;font-weight:500}}
.sub{{color:#8b949e;font-size:14px;margin-top:8px}}
.formula{{background:#161b22;border:1px solid #30363d;border-radius:10px;padding:20px 24px;margin:20px 0;font-family:"SF Mono",Menlo,monospace;font-size:14px}}
.formula .k{{color:#f0883e}} .formula .v{{color:#3fb950}}
.f1{{color:#8b949e;font-size:12px;margin-top:14px;line-height:1.8}}
table{{width:100%;border-collapse:separate;border-spacing:0;margin:12px 0;font-size:14px}}
th,td{{padding:10px 8px;text-align:center;border-bottom:1px solid #21262d}}
thead th{{background:#161b22;color:#8b949e;font-weight:500;font-size:12px;text-transform:uppercase;letter-spacing:.5px;border-bottom:1px solid #30363d}}
tbody th{{background:#0d1117;color:#e6edf3;font-weight:600}}
tbody tr:hover td{{background:#161b22}}
.t2 td:first-child{{text-align:left;color:#e6edf3;font-weight:500}}
.t2 td:nth-child(2){{text-align:left}}
.mono{{font-family:"SF Mono",Menlo,monospace;font-size:12px;color:#8b949e}}
.small{{font-size:11px}}
.w0{{background:rgba(63,185,80,.10);color:#7ee787}}
.w1{{background:rgba(63,185,80,.20);color:#56d364;font-weight:600}}
.w2{{background:rgba(240,136,62,.20);color:#ffa657;font-weight:600}}
.w3{{background:rgba(248,81,73,.22);color:#ff7b72;font-weight:700}}
.neg{{color:#8b949e}}
.pos{{color:#3fb950}} .big{{font-weight:700;font-size:15px}}
.card{{background:#161b22;border:1px solid #30363d;border-radius:12px;padding:24px;margin:16px 0}}
.tag{{display:inline-block;padding:2px 9px;border-radius:20px;font-size:12px;margin-right:6px;font-weight:600}}
.t-red{{background:rgba(248,81,73,.15);color:#ff7b72}}
.t-green{{background:rgba(63,185,80,.15);color:#3fb950}}
.t-gray{{background:rgba(139,148,158,.15);color:#8b949e}}
.t-yellow{{background:rgba(210,153,34,.15);color:#e3b341}}
ul{{margin:10px 0 0 20px}} li{{margin:7px 0}}
.kv{{display:grid;grid-template-columns:130px 1fr;gap:8px 16px;font-size:14px;margin-top:14px}}
.kv dt{{color:#8b949e}} .kv dd{{color:#e6edf3}}
.warn{{background:rgba(248,81,73,.07);border-left:3px solid #f85149;padding:14px 18px;border-radius:6px;margin:16px 0;font-size:14px}}
.note{{background:rgba(88,166,255,.07);border-left:3px solid #58a6ff;padding:14px 18px;border-radius:6px;margin:16px 0;font-size:14px}}
.legend{{display:flex;gap:18px;font-size:12px;color:#8b949e;margin-top:10px;flex-wrap:wrap}}
.legend span::before{{content:"";display:inline-block;width:10px;height:10px;border-radius:3px;margin-right:6px;vertical-align:middle}}
.l0::before{{background:rgba(63,185,80,.10)}} .l1::before{{background:rgba(63,185,80,.20)}}
.l2::before{{background:rgba(240,136,62,.20)}} .l3::before{{background:rgba(248,81,73,.22)}}
footer{{margin-top:56px;padding-top:20px;border-top:1px solid #21262d;color:#6e7681;font-size:12px;line-height:1.9}}
@media print{{body{{background:#fff;color:#111}} h1,h2,h3{{color:#111}} table th{{background:#f3f4f6;color:#333}} .card{{border-color:#ddd}}}}
</style></head><body><div class="wrap">

<h1>凯利公式速查表</h1>
<p class="sub">海尔智家 600690（现价 21.47）· 中证500 000905（现价 6643.68）<br>数据：腾讯前复权日线/周线 · 拉取 2026-11-10 11:28</p>

<h2>一、静态速查表</h2>
<div class="formula">
<span class="k">f*</span> = <span class="v">(p × (b+1) − 1) / b</span>　　=　<span class="v">(p × W − q × L) / (W × L)</span><br>
<span class="f1">p = 胜率 · b = 盈亏比（每赚1元承担的风险，b=2 表示赚2亏1）· q = 1−p</span>
</div>

<h3>凯利满仓比例 f*（看表，不看信心）</h3>
<table><thead><tr><th>胜率 p ↓ / 盈亏比 b →</th><th>0.5 : 1</th><th>1 : 1</th><th>1.5 : 1</th><th>2 : 1</th><th>3 : 1</th><th>4 : 1</th></tr></thead>
<tbody>{grid}</tbody></table>
<div class="legend"><span class="l0">0–10%</span><span class="l1">10–30%</span><span class="l2">30–50% 偏高</span><span class="l3">&gt;50% 大概率算错</span></div>

<div class="note">
<b>怎么读这张表：</b>先找你的胜率行，再找你的盈亏比列，交叉格就是凯利满仓线。<b>实战取它的 1/4 到 1/2。</b><br>
例：胜率 55%、盈亏比 2:1 → f*=32.5%，半凯利 = <b>16%</b>。
</div>

<div class="warn">
<b>三个反直觉的地方：</b><br>
① 胜率不到 50%、赔率 1:1 时，凯利是<b>负数</b>——意思是这一局根本不该碰，而不是"小赌一把"。<br>
② p=0.40、b=1.5 时 f*=0，刚好卡在盈亏平衡点，一分钱的"优势"都没有。<br>
③ <b>表里超过 50% 的格子基本都是假信号。</b>真实世界的可验证优势通常只有 2–10 个百分点，凯利只让你押个位数百分比。
</div>

<h3>分数凯利的代价曲线</h3>
<table><thead><tr><th>下注倍数</th><th>长期对数增长率</th><th>年化波动</th><th>最大回撤量级</th><th>参数估错 30% 的后果</th></tr></thead><tbody>
<tr><td>0.25 × f*</td><td>~55%</td><td>25%</td><td>25%</td><td class="pos">仍正增长</td></tr>
<tr><td>0.50 × f*</td><td>~75%</td><td>50%</td><td>50%</td><td class="pos">仍正增长</td></tr>
<tr><td>1.00 × f*</td><td>100%</td><td>100%</td><td>100%</td><td class="neg">可能变负</td></tr>
<tr><td>1.50 × f*</td><td>~75%</td><td>150%</td><td>150%</td><td class="neg">大概率为负</td></tr>
<tr><td>2.00 × f*</td><td class="neg">0（归零）</td><td>200%</td><td>200%</td><td class="neg">必然亏光</td></tr>
</tbody></table>
<p class="sub">这是连续近似下的理论形状。关键：<b>倍数 ≤1 时几乎不损失增长率，&gt;1 后收益换风险还倒贴。</b></p>

<h2>二、海尔智家 600690</h2>
<div class="card">
<span class="tag t-green">存在正优势（近 3 年口径）</span><span class="tag t-yellow">近 1 年为负</span><span class="tag t-gray">波动高、回撤深</span>
<ul>
<li><b>近 3 年：f* ≈ 44%（半凯利 22%）</b>，超额年化 3.6%。但 σ=28.8%、最大回撤 −40%，这 44% 是"高波动换来的名义仓位"。</li>
<li><b>近 1 年：f* 为负（−249%）。</b>价格从 24.76 跌到 21.47，超额 −13.4%。按凯利口径<b>现在不该加仓</b>。</li>
<li>近 10 年周线 f*≈134%，但同期最大回撤 −52%——<b>超过 100% 的 f* 意味着要上杠杆</b>，实际不可行。</li>
<li>现价 21.47 落在近 52 周区间（18.47–27.06）的 <b>35% 分位</b>，属于中低位。</li>
</ul>
</div>
{win_table("海尔智家", spec1)}
<div class="note">
<b>结论：</b>如果一定要给一个仓位上限，用近 3 年口径的<b>半凯利 = 22%</b>，再叠加"近 1 年优势为负"这个负面信号，<b>实操建议 10–15%</b>。理由不是"我看好它"，而是"即使我的 3 年统计有偏差，这个仓位也不会让我出局"。
</div>

<h2>三、中证500 000905</h2>
<div class="card">
<span class="tag t-green">近 3 年有优势</span><span class="tag t-red">全样本无优势</span><span class="tag t-yellow">窗口依赖极强</span>
<ul>
<li><b>近 3 年：f* ≈ 106%（半凯利 53%）</b>，超额 6.8%。超过 100% 说明要杠杆，实际不可行。</li>
<li><b>全样本 5 年：f* 为负（−18%）。</b>同一指数，换个窗口结论就反转。</li>
<li><b>近 10 年周线：f*≈16%（半凯利 8%）。</b>这是最接近"长期真实优势"的数字——年化超额只有 0.7%。</li>
<li>近 1 年 f* 也是负（−116%），现价 6643.68 在近 52 周区间 <b>14% 分位</b>。</li>
</ul>
</div>
{win_table("中证500", spec2)}
<div class="note">
<b>结论：</b>凯利口径给中证500 的合理答案是<b>8–15%</b>——用的是 10 年周线的半凯利（8%）到近 3 年的 1/4 凯利（26%）之间的低端。它现在的价格分位很低（14%），但<b>"便宜"不等于"有正优势"</b>，凯利要的是 μ，不是估值折价。
</div>

<h2>四、两者对比与组合</h2>
<table class="t2"><thead><tr><th>维度</th><th>海尔智家</th><th>中证500</th></tr></thead><tbody>
<tr><td>近 1 年超额</td><td class="neg">−13.4%</td><td class="neg">−8.6%</td></tr>
<tr><td>近 3 年超额</td><td class="pos">+3.6%</td><td class="pos">+6.8%</td></tr>
<tr><td>10 年周线超额</td><td class="pos">+21.2%（区间起点特殊）</td><td>+0.7%</td></tr>
<tr><td>年化波动 σ</td><td>28.8%</td><td>23.0%</td></tr>
<tr><td>最大回撤</td><td>−40%</td><td>−40%</td></tr>
<tr><td>52 周分位</td><td>35%</td><td>14%</td></tr>
<tr><td>凯利结论</td><td>10–15%</td><td>8–15%</td></tr>
</tbody></table>

<div class="warn">
<b>⚠️ 相关性的坑：两个都别简单相加。</b>海尔是沪深300成分，中证500是它的"下一档"，两者相关度很高。如果各押 15%，等效于押一个 30% 的"中国权益"大单——<b>实际风险远大于两个独立 15% 的仓位</b>。多品种必须用协方差矩阵，不能一注一注加凯利。
</div>

<h2>五、这套算法的前提与局限</h2>
<div class="card">
<h3>能信的</h3>
<ul><li>μ、σ 用真实历史日线数据算出，不是拍脑袋；</li><li>凯利 f* = μ/σ² 对<b>股票和指数是可计算、可复现的</b>。</li></ul>
<h3>不能信的</h3>
<ul>
<li><b>μ 的估计极不稳定。</b>中证500 近 3 年正、全样本负——换窗口就翻脸。μ 的样本误差远大于 σ。</li>
<li><b>正态假设。</b>凯利公式假设收益正态，A 股是肥尾的（跌停、政策突变），这会系统性低估极端亏损。</li>
<li><b>f* 经常 &gt; 100%</b>，但 A 股 T+1、无杠杆、不能做空，实际有效 f 天花板是 100%，超出部分作废。</li>
<li><b>凯利不管"对不对"。</b>它只回答"给定 μ、σ 该押多少"，不回答"μ 该怎么估"——后者才是投资的核心工作。</li>
</ul>
</div>

<div class="note">
<b>一句话：</b>凯利公式的真正用处不是算出一个精确的百分比，而是<b>逼你说出"我凭什么觉得这里有优势"</b>。说不出来，f* 就是负的，答案就是不下注——这正好是"安全边际"在仓位维度上的等价物。
</div>

<footer>
数据源：腾讯财经 web.ifzq.gtimg.cn（前复权日线/周线，复权口径已统一）<br>
无风险利率取 1.8%（10Y 国债近似）· 凯利公式采用连续形式 f* = (μ−rf)/σ²（Kelly 1956）<br>
本表为机械计算，不构成投资建议。α 无法从价格序列直接测出，表中"超额"是长期均值口径的近似。
</footer>
</div></body></html>"""
open(HERE/"凯利公式速查表.html","w").write(HTML)
print("written", len(HTML))
