#!/usr/bin/env python3
"""
policydiff.py — 政策文件的滤波器（不是写报告器）

设计原则来自四路实测：90% 的政策文件不值得出点评，
模型会把它们都写成有结论的样子。所以这个工具只做判定，不产出解读。

用法：
  1) 找上一期同类文件
     python3 policydiff.py prev "修改和废止部分行政法规的决定"
  2) 抓正文（gov.cn 专用，用 UCAP-CONTENT 定向提取 + 关键词计数校验）
     python3 policydiff.py fetch <url> [-o out.md]
  3) 抽改动条文并分类（修改/删去/废止 + 减力词/加力词）
     python3 policydiff.py diff <本地md路径>
  4) 一键判定这份文件值不值得读
     python3 policydiff.py triage <url>

只依赖标准库。仅支持 gov.cn 域名。
"""
import sys, re, html, json, os, urllib.parse, urllib.request

UA = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
                  'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36',
    'Referer': 'https://sousuo.www.gov.cn/',
}

# ---------------------------------------------------------------- 抓取

def fetch_text(url, timeout=40):
    """抓 gov.cn 页面正文。用正文容器定向提取，不用宽泛剥标签。
    教训：<[^>]+> 会把嵌套 div 里的文号、署名、「删去」条款一起吃掉。"""
    req = urllib.request.Request(url, headers=UA)
    raw = urllib.request.urlopen(req, timeout=timeout).read().decode('utf-8', 'ignore')

    m = re.search(r'id="UCAP-CONTENT".*?>(.*?)</div>\s*</div>', raw, re.S)
    seg = m.group(1) if m else raw
    seg = re.sub(r'<script.*?</script>|<style.*?</style>', '', seg, flags=re.S)
    seg = re.sub(r'<br\s*/?>|</p>|</div>|</h\d>', '\n', seg)
    seg = re.sub(r'<[^>]+>', '', seg)
    seg = html.unescape(seg)
    lines = [l.strip() for l in seg.split('\n') if l.strip()]
    txt = '\n'.join(lines)
    # 去页脚
    for cut in ('扫一扫在手机打开当前页', '主办单位：国务院办公厅'):
        i = txt.find(cut)
        if i > 0:
            txt = txt[:i]
    return txt


def sanity_check(txt):
    """关键词计数校验。抓取失败最常见的表现不是报错，是静默缺内容。"""
    return {
        'chars': len(txt),
        '删去': txt.count('删去'),
        '修改为': txt.count('修改为'),
        '废止': txt.count('废止'),
        '有文号': bool(re.search(r'第\s*\d+\s*号', txt)),
        '有署名': ('总理' in txt) or ('主席令' in txt) or ('国务院办公厅' in txt),
    }

# ---------------------------------------------------------------- 找上一期

def search(title_keyword, n=20):
    q = urllib.parse.quote(title_keyword)
    url = ('https://sousuo.www.gov.cn/search-gov/data'
           f'?t=zhengcelibrary_gw&q={q}&timetype=timeqb&sort=pubtime&sortType=1'
           f'&searchfield=title&p=1&n={n}&type=gwyzcwjk')
    req = urllib.request.Request(url, headers=UA)
    d = json.loads(urllib.request.urlopen(req, timeout=30).read().decode('utf-8', 'ignore'))
    sv = d.get('searchVO') or {}
    out = []
    for it in sv.get('listVO') or []:
        out.append({
            '文号': it.get('pcode') or '',
            '标题': re.sub(r'<[^>]+>', '', html.unescape(it.get('title') or '')),
            '发布': it.get('pubtimeStr') or it.get('pubtime') or '',
            '链接': it.get('url') or '',
        })
    return {'total': sv.get('totalCount'), 'items': out}

# ---------------------------------------------------------------- 抽改动

# 动作类型
ACT_PATTERNS = [
    ('废止', re.compile(r'予以?废止|^废止《')),
    ('删去', re.compile(r'删去')),
    ('修改', re.compile(r'修改为|改为')),
    ('新增', re.compile(r'增加一款|增加一项|增写')),
]

# 减力词 / 加力词。两套都要有——只看加力词会把「减法式治理」误判为无信息。
UNESCALATE = ['精简', '优化', '撤', '废止', '删', '取消', '免除', '简化',
              '压减', '下放', '不再', '无需', '减轻', '规范', '清理', '整治']
ESCALATE = ['加大', '强化', '加快', '坚决', '严格', '从严', '严厉', '全面',
            '切实', '着力', '确保', '坚决', '一律', '不得', '禁止', '查处']

# 真金白银的抓手词——决定这份文件是不是「政策工具」
TOOL_TERMS = {
    '规模': ['亿元', '万元', '资金', '基金', '规模以上', '专项债', '财政'],
    '试点': ['试点', '示范', '先导区', '试验区', '中试基地'],
    '时限': ['到20\\d\\d年', '时限', '节点', '底前', '之前完成'],
    '清单': ['清单', '目录', '名单', '标准体系'],
    '准入': ['准入', '许可', '资质', '审批', '备案'],
    '罚则': ['罚款', '处罚', '追究', '处分', '吊销', '责令'],
}


def split_articles(txt):
    """按「一、二、……」「（一）（二）」切分条文块。"""
    txt = re.sub(r'[ \t\u3000]+', ' ', txt)
    blocks, cur, head = [], [], ''
    for line in txt.split('\n'):
        if re.match(r'^[一二三四五六七八九十百]+、', line) or \
           re.match(r'^\(?[一二三四五六七八九十]+\)?.{0,30}(条例|规定|办法|法)', line):
            if head or cur:
                blocks.append((head, '\n'.join(cur)))
            head, cur = line, []
        else:
            cur.append(line)
    if head or cur:
        blocks.append((head, '\n'.join(cur)))
    return [(h, b) for h, b in blocks if b.strip()]


def count_repealed(txt):
    """附件2「废止的行政法规」清单条目数。
    坑1：附件2 里每部法规只写标题（如「危险化学品安全管理条例」），
    不带「废止」二字，按「废止」关键词计数会严重低估。
    坑2：正文前言开头就有「附件：1.国务院决定修改的生政法规 2.国务院决定废止的行政法规」
    清单，正则若从第一次出现处切，会把附件1 的条目全数进去。
    所以取最后一次出现的位置。"""
    marker = '国务院决定废止的行政法规'
    idx = txt.rfind(marker)
    if idx < 0:
        return 0
    body = txt[idx + len(marker):]
    nxt = body.find('附件1')
    if nxt >= 0:
        body = body[:nxt]
    return len(re.findall(r'^[一二三四五六七八九十百]+、', body, re.M))


def analyse(txt):
    acts = {}
    for name, pat in ACT_PATTERNS:
        acts[name] = len(pat.findall(txt))
    acts['废止清单条目'] = count_repealed(txt)

    unesc = {w: txt.count(w) for w in UNESCALATE if txt.count(w)}
    esc = {w: txt.count(w) for w in ESCALATE if txt.count(w)}

    tools = {}
    for cat, words in TOOL_TERMS.items():
        hits = 0
        for w in words:
            hits += len(re.findall(w, txt))
        if hits:
            tools[cat] = hits

    return {
        'sanity': sanity_check(txt),
        '动作': acts,
        '减力词': unesc,
        '加力词': esc,
        '抓手词': tools,
    }


def triage(txt):
    """核心判定。只回答「值不值得读」，不产出解读。"""
    a = analyse(txt)
    acts, tools = a['动作'], a['抓手词']
    unesc_n = sum(a['减力词'].values())
    esc_n = sum(a['加力词'].values())
    tool_n = sum(tools.values())

    # 判定文件性质
    cleanup_signal = acts['删去'] + acts['废止清单条目']
    if cleanup_signal >= 5 and tool_n < 8:
        kind = '法规清理'
        story = '减法型：删义务、废旧规，不产生新增合规动作'
    elif tool_n >= 8:
        kind = '政策工具'
        story = '加法型：有规模/试点/时限/清单等可落地抓手'
    elif esc_n >= 5:
        kind = '方向性表态'
        story = '定调型：有强度词但缺抓手，看方向不看价格'
    else:
        kind = '低信息量'
        story = '常规性：既无抓手也无明显强度变化'

    verdict = '无需精读' if kind in ('法规清理', '低信息量') else '值得精读'
    return {'性质': kind, '说明': story, '判定': verdict, '明细': a}

# ---------------------------------------------------------------- CLI

def _print_triage(txt):
    r = triage(txt)
    d = r['明细']
    print(f"文件性质：{r['性质']}  |  {r['判定']}")
    print(f"理由：{r['说明']}")
    print()
    s = d['sanity']
    print(f"字数 {s['chars']}  文号{'✓' if s['有文号'] else '✗'}  "
          f"署名{'✓' if s['有署名'] else '✗'}")
    print(f"动作：修改 {d['动作']['修改']} / 删去 {d['动作']['删去']} / "
          f"废止清单 {d['动作']['废止清单条目']} 条 / 新增 {d['动作']['新增']}")
    print(f"减力词 {sum(d['减力词'].values())} 个 {d['减力词'] or ''}")
    print(f"加力词 {sum(d['加力词'].values())} 个 {d['加力词'] or ''}")
    print(f"抓手词 {sum(d['抓手词'].values())} 个 {d['抓手词'] or ''}")


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 1
    cmd = argv[1]

    if cmd == 'prev':
        kw = argv[2]
        r = search(kw)
        print(f"gov.cn 政策库 标题含「{kw}」共 {r['total']} 条\n")
        for i, it in enumerate(r['items']):
            mark = '  ← 上一期' if i == 1 else ('  ← 本期' if i == 0 else '')
            print(f"{it['文号']:<16} {it['发布']}  {it['标题']}{mark}")
            if i <= 1:
                print(f"{'':16} {it['链接']}")
        return 0

    if cmd == 'fetch':
        txt = fetch_text(argv[2])
        out = None
        if '-o' in argv:
            out = argv[argv.index('-o') + 1]
        if out:
            open(out, 'w', encoding='utf-8').write(txt + '\n')
            print(f"已写入 {out}")
        print(json.dumps(sanity_check(txt), ensure_ascii=False, indent=2))
        return 0

    if cmd == 'diff':
        txt = open(argv[2], encoding='utf-8').read()
        _print_triage(txt)
        return 0

    if cmd == 'triage':
        txt = fetch_text(argv[2])
        _print_triage(txt)
        return 0

    print(__doc__)
    return 1


if __name__ == '__main__':
    sys.exit(main(sys.argv))
