# -*- coding: utf-8 -*-
"""
把「（金鼎集团）XX城投集团有限公司审查意见.docx」清理成空白模板。

清理规则（参照 担保类尽调报告.docx 的空白模板形态）：
  保留：章节标题 / 表格表头与行标签 / 引导语 / 表标题 / 附件清单 / 落款 / 页眉页脚 / 结构图
  清空：表格数据单元格（保留行与单元格格式）
  删除：分析性正文段落
  占位：标题、文号、日期、附件3 中的具体值 -> XX

段落判定用「文本规则」，不用下标，避免 bookmarkEnd 造成的索引漂移。
"""
import re, os, zipfile, shutil
import xml.etree.ElementTree as ET

SRC = '/Users/chenjie/Documents/work/AI/智能模板/template 2/新模板相关/1.（金鼎集团）XX城投集团有限公司审查意见.docx'
DST = '/Users/chenjie/Documents/work/AI/智能模板/template 2/新模板相关/（金鼎集团）审查意见类模板（空白）.docx'
WORK = '/tmp/build_blank'

WNS = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
DRAW = '{http://schemas.openxmlformats.org/drawingml/2006/main}'

# ---------- 段落改写表（精确文本 -> 新文本）----------
REPLACE_MAP = {
    '关于金玉担保申报的XX城投集团有限公司不超过5亿元人民币境外债项目的审查意见':
        '关于XX担保申报的XX集团有限公司不超过XX亿元人民币XX项目的审查意见',
    '（2024）前审字第008号':
        '（XXXX）前审字第XXX号',
    '发行人“XX城投”作为XX县重要的城市基础设施建设投融资和土地开发整理主体，业务涵盖XX县城市基础建设、土地开发整理、水务、公交运营、导线光缆销售、显示屏销售等业务，收入结构较为多元，具体收入结构如下：':
        '发行人主营业务收入结构如下：',
    '近年来收入的主要来源以委托代建业务、贸易销售业务、房地产销售业务为主，合计占比在70%以上，供水业务、沙石业务等对收入形成有益补充，具体收入结构如下：':
        '反担保人主营业务收入结构如下：',
    '（一）主承销商：东海国际金融控股有限公司':
        '（一）主承销商：',
    '（二）备证开立行：上海银行股份有限公司':
        '（二）备证开立行：',
    '我们基本同意金玉担保在审查意见中反映的本项目风险以及对应风险分析意见，针对该项目的风险分析结论，强调与补充以下风险点：':
        '针对该项目的风险分析结论，强调与补充以下风险点：',
    '根据申报单位提供的发改委批文（详见附件2），其募集资金总额不超过20亿人民币，其中16亿人民币拟用于项目建设，4亿人民币用于补充流动性资金，具体项目如下：':
        '募集资金拟投向项目如下：',
    '鉴于该笔债券通过了发改委的审核登记和外管局的同意，根据现行政策在募集资金用途方面，要求新增企业借用外债不得新增地方政府隐性债务的要求，明确了外债用途的负面禁止清单。针对上述风险我部提出以下风控措施：':
        '针对上述风险，提出以下风控措施：',
    '附件3：眉山市各区县2022年财政数据':
        '附件3：XX市各区县20XX年财政数据',
    '2024年1月30日':
        '20XX年X月X日',
}

KEEP_EXACT = {'1.从经营方面来看', '2.从财务方面来看'}
KEEP_PREFIX = ('还本付息计划测算', '附件1：', '附件2：',
               '以上建议仅供', '四川能投金鼎产融控股集团有限公司风险管理部')


def classify(txt, has_img):
    t = txt.strip()
    if has_img or t == '':
        return 'keep'
    if t in REPLACE_MAP:
        return 'replace'
    if t in KEEP_EXACT:
        return 'keep'
    if t.startswith(KEEP_PREFIX):
        return 'keep'
    if '主审人员' in t:
        return 'keep'
    if re.match(r'^[一二三四五六七八九十]+、', t):
        return 'keep'
    if re.match(r'^（[一二三四五六七八九十]+）', t):
        return 'keep'
    return 'delete'


# ---------- 表格清空规则（表序号, 行tc索引, 列tc索引）----------
def cell_spec():
    s = set()
    for r in range(20):                       # TABLE 1 键值表：清值列
        s.add((1, r, 1))
    for r in (1, 2):                          # TABLE 2 股权表：留行标签
        for c in range(1, 6):
            s.add((2, r, c))
    for r in range(2, 7):                     # TABLE 3 业务板块收入
        for c in range(0, 10):
            s.add((3, r, c))
    for r in range(2, 7):                     # TABLE 4 反担保人收入
        for c in range(0, 10):
            s.add((4, r, c))
    for r in range(1, 6):                     # TABLE 5 合规性审查：留编号+审查依据
        for c in (2, 3):
            s.add((5, r, c))
    for r in range(1, 5):                     # TABLE 6 募投项目
        for c in range(0, 3):
            s.add((6, r, c))
    s.add((6, 5, 1)); s.add((6, 5, 2))        # 合计行留标签
    for r in (1, 2):                          # TABLE 7 还本付息
        for c in range(1, 6):
            s.add((7, r, c))
    for r in range(2, 6):                     # TABLE 8 区域平台对比
        for c in range(0, 9):
            s.add((8, r, c))
    for c in range(1, 6):                     # 合计行留标签
        s.add((8, 6, c))
    return s


CELL_CLEAR = cell_spec()
CELL_TEXT = {
    (3, 0, 1): '2022年',
    (4, 0, 1): '2022年度',
    # 标签/依据里含具体担保机构名 -> 占位
    (1, 18, 0): '是否符合《关于XX担保申请XX担保地方投融资平台公司债券增信业务产品（2023年版）的风险提示意见》（金鼎业审委〔2023〕88号）',
    (5, 1, 1): '参照XX担保获批的《地方投融资平台公司债券增信业务产品（2023年版）的风险提示意见》（金鼎业审委〔2023〕88号）',
}

# 勾选项：保留选项框结构，只把勾选状态复位、去掉具体理由
CELL_KEEP_TEXT = {
    (1, 18, 1): '□符合                □不符合',
    (1, 10, 1): '□是                  □否',
}

# ---------- 表锚点空行插入位置 ----------
# 约定（对齐 担保类尽调报告.docx）：表头行之后、字段定义行之前，单独插一个空行放表锚点。
# 值是「插入前」的行号（0-based）：新空行插到该行之前，该行及其后所有行号 +1。
ANCHOR_BEFORE = {
    1: 0,   # 申报方案（键值表）：整行空锚点行放最前，R1 起才是键值对
    2: 1,   # 股权结构：R0 表头 -> 插 -> 发行人行
    3: 2,   # 发行人收入：R0 表头 / R1 子表头 -> 插 -> 字段行
    4: 2,   # 反担保人收入：同上
    5: 1,   # 合规性审查：R0 表头 -> 插 -> 第 1 条
    6: 1,   # 募投项目：R0 表头 -> 插 -> 字段行
    7: 1,   # 还本付息：R0 表头 -> 插 -> 合计行
    8: 2,   # 区域平台：R0 表头 / R1 子表头 -> 插 -> 字段行
}


# ---------- 工具 ----------
def split_top_level(body):
    i, n, els = 0, len(body), []
    while i < n:
        if body.startswith('<w:tbl>', i):
            d, j = 0, i
            while j < n:
                if body.startswith('<w:tbl>', j):
                    d += 1; j += 6; continue
                if body.startswith('</w:tbl>', j):
                    d -= 1; j += 8
                    if d == 0: break
                    continue
                j += 1
            els.append((i, j, 'tbl')); i = j
        elif body.startswith('<w:p ', i) or body.startswith('<w:p>', i):
            j = body.find('</w:p>', i) + 6
            els.append((i, j, 'p')); i = j
        elif body.startswith('<w:sectPr', i):
            j = body.find('</w:sectPr>', i) + 10
            els.append((i, j, 'sectPr')); i = j
        else:
            i += 1
    return els


def set_para_text(p, newtext):
    out, idx, first = [], 0, True
    while True:
        m = re.search(r'(<w:t(?: [^>]*)?>)(.*?)(</w:t>)', p[idx:], re.S)
        if not m:
            break
        s, e = idx + m.start(), idx + m.end()
        out.append(p[idx:s])
        out.append(m.group(1) + (newtext if first else '') + m.group(3))
        idx, first = e, False
    out.append(p[idx:])
    return ''.join(out)


def clear_cell(tc):
    return re.sub(r'<w:r(?: [^>]*)?>.*?</w:r>', '', tc, flags=re.S)


def set_cell_text(tc, newtext):
    """单元格只保留第一个段落并设为 newtext，其余段落删除"""
    ps = split_tagged(tc, 'w:p')
    if not ps:
        return tc
    first = set_para_text(tc[ps[0][0]:ps[0][1]], newtext)
    return tc[:ps[0][0]] + first + tc[ps[-1][1]:]


def split_tagged(x, tag):
    res, i, n = [], 0, len(x)
    while i < n:
        if x.startswith('<%s>' % tag, i) or x.startswith('<%s ' % tag, i):
            j = x.find('</%s>' % tag, i) + len(tag) + 3
            res.append((i, j)); i = j
        else:
            i += 1
    return res


def process_table(tbl, tno):
    rows = split_tagged(tbl, 'w:tr')
    pieces, last = [], 0
    for ri, (rs, rend) in enumerate(rows):
        row = tbl[rs:rend]
        cells = split_tagged(row, 'w:tc')
        cpieces, clast = [], 0
        for ci, (cs, ce) in enumerate(cells):
            cell = row[cs:ce]
            if (tno, ri, ci) in CELL_KEEP_TEXT:
                cell = set_cell_text(cell, CELL_KEEP_TEXT[(tno, ri, ci)])
            elif (tno, ri, ci) in CELL_CLEAR:
                cell = clear_cell(cell)
            elif (tno, ri, ci) in CELL_TEXT:
                cell = set_para_text(cell, CELL_TEXT[(tno, ri, ci)])
            cpieces.append(row[clast:cs]); cpieces.append(cell); clast = ce
        cpieces.append(row[clast:])
        pieces.append(tbl[last:rs]); pieces.append(''.join(cpieces)); last = rend
    pieces.append(tbl[last:])
    return ''.join(pieces)


def insert_anchor_row(tbl, before):
    """在 tbl 的第 before 行之前插入一个空行（克隆该行的列结构，清掉全部内容与书签）。

    锚点行本身是空行，书签由打标阶段写入 C0。
    """
    rows = split_tagged(tbl, 'w:tr')
    rs, rend = rows[before]
    row = tbl[rs:rend]
    row = re.sub(r'<w:r(?: [^>]*)?>.*?</w:r>', '', row, flags=re.S)
    row = re.sub(r'<w:proofErr[^>]*/>', '', row)
    row = re.sub(r'<w:bookmarkStart[^>]*/>', '', row)
    row = re.sub(r'<w:bookmarkEnd[^>]*/>', '', row)
    return tbl[:rs] + row + tbl[rs:]


def para_text(p):
    """从段落 XML 片段取纯文本（避免 <w:tcPr>/<w:tab/> 被误当 <w:t>）"""
    raw = ''.join(m.group(1) for m in
                  re.finditer(r'<w:t(?: [^>]*)?>(.*?)</w:t>', p, re.S))
    return (raw.replace('&amp;', '&').replace('&lt;', '<')
               .replace('&gt;', '>').replace('&quot;', '"').replace('&apos;', "'"))


# ---------- 主流程 ----------
def main():
    if os.path.exists(WORK):
        shutil.rmtree(WORK)
    os.makedirs(WORK)
    with zipfile.ZipFile(SRC) as z:
        z.extractall(WORK)

    docp = os.path.join(WORK, 'word', 'document.xml')
    s = open(docp, encoding='utf-8').read()
    m = re.search(r'(<w:body>)(.*)(</w:body>)', s, re.S)
    head, body, tail = s[:m.start(2)], m.group(2), s[m.end(2):]

    # 1) 表格：逆序改写
    els = split_top_level(body)
    tbl_spans = [(st, en) for st, en, k in els if k == 'tbl']
    print('表格数:', len(tbl_spans))
    for tno in range(len(tbl_spans), 0, -1):
        st, en = tbl_spans[tno - 1]
        body = body[:st] + process_table(body[st:en], tno) + body[en:]

    # 1.5) 表锚点空行：在「字段定义行」之前插一个空行（逆序，避免偏移漂移）
    els = split_top_level(body)
    tbl_spans = [(st, en) for st, en, k in els if k == 'tbl']
    for tno in range(len(tbl_spans), 0, -1):
        st, en = tbl_spans[tno - 1]
        body = body[:st] + insert_anchor_row(body[st:en], ANCHOR_BEFORE[tno]) + body[en:]
    print('已插入表锚点空行:', len(tbl_spans), '个')

    # 2) 段落：按文本规则分类，逆序处理
    els = split_top_level(body)
    plan = []   # (start, end, action, newtext)
    for st, en, k in els:
        if k != 'p':
            continue
        seg = body[st:en]
        has_img = ('<w:drawing>' in seg) or (DRAW + 'blip' in seg)
        txt = para_text(seg)
        act = classify(txt, has_img)
        plan.append((st, en, act, REPLACE_MAP.get(txt.strip(), ''), txt.strip()[:30]))

    stat = {}
    for st, en, act, newt, preview in plan:
        stat[act] = stat.get(act, 0) + 1
    print('段落动作统计:', stat)

    for st, en, act, newt, preview in reversed(plan):
        if act == 'delete':
            body = body[:st] + body[en:]
        elif act == 'replace':
            body = body[:st] + set_para_text(body[st:en], newt) + body[en:]

    newdoc = head + body + tail
    open(docp, 'w', encoding='utf-8').write(newdoc)

    if os.path.exists(DST):
        os.remove(DST)
    with zipfile.ZipFile(SRC) as zin, zipfile.ZipFile(DST, 'w', zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = newdoc.encode('utf-8') if item.filename == 'word/document.xml' else zin.read(item.filename)
            zout.writestr(item, data)
    print('written:', DST)

    # 回显保留下来的段落，便于核对
    print('\n--- 保留/改写后的段落 ---')
    for st, en, act, newt, preview in plan:
        if act != 'delete':
            print(f'[{act}] {preview}')


if __name__ == '__main__':
    main()
