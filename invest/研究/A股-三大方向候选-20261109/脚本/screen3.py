import json, datetime, collections
rows = json.load(open('scratch/universe_raw.json'))
div = json.load(open('scratch/div_all.json'))
bvps = json.load(open('scratch/bvps.json'))
today = datetime.date(2026,11,9)
def num(v):
    try: return float(v)
    except: return None
def board(c):
    if c.startswith(('60','00')): return 'main'
    if c.startswith('30'): return 'gem'
    if c.startswith('68'): return 'star'
    return 'bj'
GAOXI=['煤炭','银行','电力','燃气','公路','铁路','港口','水务','保险','石油','炼化','航运','钢铁','水泥','建筑','房地产','采掘','公用']
XIAOFEI=['白酒','啤酒','饮料','食品','乳品','调味','休闲','酒店','餐饮','旅游','景区','商业','零售','百货','超市','服装','家纺','化妆品','美容','珠宝','饰品','家居','家电','汽车','摩托','教育','出版','传媒','游戏','纺织']
YILIAO=['化学制药','中药','生物制品','医疗器械','医疗服务','医药商业','原料药']
AI=['半导体','通信设备','光学光电子','元件','消费电子','计算机设备','IT服务','软件开发','电池','光伏','电子化学','自动化设备']
def cats(ind):
    if not ind: return []
    c=[]
    if any(k in ind for k in GAOXI): c.append('高股息')
    if any(k in ind for k in XIAOFEI): c.append('消费')
    if any(k in ind for k in YILIAO): c.append('医疗')
    if any(k in ind for k in AI): c.append('AI')
    return c
out=[]
for r in rows:
    c=r['f12']; price=num(r['f2']); mcap=num(r['f20'])
    if not price or not mcap: continue
    recs = div.get(c) or []
    # 按除息年份归集
    byyear=collections.defaultdict(float); cnt=collections.defaultdict(int)
    last=None
    for x in recs:
        ex=x.get('ex'); b=num(x.get('bonus'))
        if not ex or b is None: continue
        try: d=datetime.date.fromisoformat(ex[:10])
        except: continue
        if d>today: continue
        if last is None: last=d
        byyear[d.year]+=b; cnt[d.year]+=1
    # 采用最近一个完整分红年度（优先2025，其次2026）
    dy=None; base_year=None; n_div=0
    for y in (2025,2026,2024):
        if byyear.get(y):
            dy=round(byyear[y]/10.0/price*100,2); base_year=y; n_div=cnt[y]; break
    # 稳定性：连续3年有分红 + 单次占比
    years_div = sorted(byyear.keys())[-3:]
    stable = len([y for y in (2024,2025,2026) if byyear.get(y)]) >= 2
    oneshot = stable and byyear.get(2025,0)>0 and byyear.get(2024,0)==0
    b=num(bvps.get(c)); pb=round(price/b,2) if b and b>0 else None
    out.append(dict(code=c,name=r['f14'],board=board(c),ind=r.get('f100'),price=price,
      mcap_yi=round(mcap/1e8,1),pe=num(r['f115']),pb=pb,dy=dy,dy_year=base_year,n_div=n_div,
      stable=stable, lastdiv=str(last) if last else None, cats=cats(r.get('f100'))))
json.dump(out,open('scratch/base3.json','w'),ensure_ascii=False)
print('stocks',len(out),'有股息率',sum(1 for x in out if x['dy']))
for n in ['贵州茅台','海澜之家','达仁堂','中国神华','招商银行','长江电力','周大生']:
    m=[x for x in out if x['name']==n]
    if m:
        x=m[0]; print(f"{n:6s} 价{x['price']:8.2f} 股息{x['dy'] or 0:6.2f}% (年度{x['dy_year']}) 分红次数{x['n_div']}")
