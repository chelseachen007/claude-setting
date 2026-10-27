# -*- coding: utf-8 -*-
"""
给「（金鼎集团）审查意见类模板（空白）.docx」插书签，产出：
  1. （金鼎集团）审查意见类模板（已打标签）.docx
  2. 审查意见类模板书签json文档.json
  3. 审查意见类模板字段分类.json

书签约定（逆向自 担保类尽调报告.docx）：
  <w:bookmarkStart w:id="N" w:name="code"/><w:bookmarkEnd w:id="N"/>
  零长度，紧跟 </w:pPr> 之后
  表锚点 -> 表头行之后、字段定义行之前的那个**独立空行**的 C0
            （该空行由 clean_template.py 按 ANCHOR_BEFORE 插入）
  单元格字段 -> 值格；叙述字段 -> 独立空段落（插在锚点段落之后）
"""
import re, os, zipfile, json, shutil

# 表锚点所在的「空行」行号（= clean_template.py 的 ANCHOR_BEFORE，即插入前字段行的行号）
ANCHOR_BEFORE = {1: 0, 2: 1, 3: 2, 4: 2, 5: 1, 6: 1, 7: 1, 8: 2}

BASE = '/Users/chenjie/Documents/work/AI/智能模板/template 2'
SRC = os.path.join(BASE, '新模板相关/（金鼎集团）审查意见类模板（空白）.docx')
DST = os.path.join(BASE, '新模板相关/（金鼎集团）审查意见类模板（已打标签）.docx')
FJ = os.path.join(BASE, '审查意见类模板打标预处理.json')
OUT_BK = os.path.join(BASE, '审查意见类模板书签json文档.json')
OUT_FC = os.path.join(BASE, '审查意见类模板字段分类.json')
WORK = '/tmp/build_tag'

PARA_TPL = ('<w:p><w:pPr><w:spacing w:after="156" w:afterLines="50" w:line="400" w:lineRule="exact"/>'
            '<w:ind w:firstLine="560" w:firstLineChars="200"/><w:contextualSpacing/>'
            '<w:rPr><w:rFonts w:hint="eastAsia" w:ascii="仿宋" w:hAnsi="仿宋" w:eastAsia="仿宋" w:cs="仿宋"/>'
            '<w:bCs/><w:color w:val="000000" w:themeColor="text1"/><w:sz w:val="28"/><w:szCs w:val="24"/>'
            '<w:lang w:val="en-US" w:eastAsia="zh-CN"/></w:rPr></w:pPr>%s</w:p>')


def bmk(bid, name):
    return '<w:bookmarkStart w:id="%d" w:name="%s"/><w:bookmarkEnd w:id="%d"/>' % (bid, name, bid)


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


def split_tagged(x, tag):
    res, i, n = [], 0, len(x)
    while i < n:
        if x.startswith('<%s>' % tag, i) or x.startswith('<%s ' % tag, i):
            j = x.find('</%s>' % tag, i) + len(tag) + 3
            res.append((i, j)); i = j
        else:
            i += 1
    return res


def para_text(p):
    raw = ''.join(m.group(1) for m in re.finditer(r'<w:t(?: [^>]*)?>(.*?)</w:t>', p, re.S))
    return (raw.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
               .replace('&quot;', '"').replace('&apos;', "'")).strip()


def ppr_end(seg):
    """段落内 </w:pPr> 之后的位置；没有 pPr 则返回 <w:p> 之后"""
    m = re.search(r'</w:pPr>', seg)
    if m:
        return m.end()
    m = re.search(r'<w:p(?: [^>]*)?>', seg)
    return m.end() if m else 0


def main():
    doc = json.load(open(FJ, encoding='utf-8'))
    fields, tables = doc['fields'], doc['tables']

    if os.path.exists(WORK):
        shutil.rmtree(WORK)
    os.makedirs(WORK)
    with zipfile.ZipFile(SRC) as z:
        z.extractall(WORK)
    docp = os.path.join(WORK, 'word', 'document.xml')
    s = open(docp, encoding='utf-8').read()

    # 书签 id 起点
    ids = [int(x) for x in re.findall(r'<w:bookmarkStart[^>]*w:id="(\d+)"', s)]
    next_id = (max(ids) + 1) if ids else 1
    print('现有书签 id 最大值:', max(ids) if ids else None, '-> 新 id 从', next_id, '开始')

    m = re.search(r'(<w:body>)(.*)(</w:body>)', s, re.S)
    head, body, tail = s[:m.start(2)], m.group(2), s[m.end(2):]

    els = split_top_level(body)
    tbl_spans = [(st, en) for st, en, k in els if k == 'tbl']
    para_spans = [(st, en) for st, en, k in els if k == 'p']
    print('表格 %d 个 / 段落 %d 个' % (len(tbl_spans), len(para_spans)))

    def cell_ppr_end(tno, row, cell):
        """返回 (绝对偏移, 是否找到)"""
        ts, te = tbl_spans[tno - 1]
        tbl = body[ts:te]
        rows = split_tagged(tbl, 'w:tr')
        if row >= len(rows):
            return None
        rs, rend = rows[row]
        cells = split_tagged(tbl[rs:rend], 'w:tc')
        if cell >= len(cells):
            return None
        cs, ce = cells[cell]
        tcs = tbl[rs + cs: rs + ce]
        ps = split_tagged(tcs, 'w:p')
        if not ps:
            return None
        off = ts + rs + cs + ps[0][0] + ppr_end(tcs[ps[0][0]:ps[0][1]])
        return off

    def para_anchor_end(text):
        hits = [en for st, en in para_spans if para_text(body[st:en]) == text]
        if len(hits) != 1:
            return None, len(hits)
        return hits[0], 1

    ops = []          # (offset, insert_text)
    order = []        # (offset, entry)  用于书签 json 排序
    id_map = {}       # code -> bookmark id

    # ---------- 1) 表锚点 + 单元格字段 ----------
    by_tbl = {}
    for f in fields:
        if f['slot'] == 'cell':
            by_tbl.setdefault(f['table'], []).append(f)

    for t in tables:
        tno = t['index']
        bid = next_id; next_id += 1
        id_map[t['code']] = bid
        off = cell_ppr_end(tno, ANCHOR_BEFORE[tno], 0)
        assert off is not None, '表%d 锚点空行定位失败' % tno
        ops.append((off, bmk(bid, t['code'])))
        cells_json = []
        for f in by_tbl.get(tno, []):
            b2 = next_id; next_id += 1
            id_map[f['code']] = b2
            o2 = cell_ppr_end(tno, f['row'], f['cell'])
            assert o2 is not None, '%s 定位失败' % f['code']
            ops.append((o2, bmk(b2, f['code'])))
            cells_json.append({'code': f['code'], 'desc': f['desc'], 'value': ''})
        entry = {'code': t['code'], 'type': 'table'}
        if t.get('render'):
            entry['render'] = t['render']
        entry['desc'] = t['desc']
        entry['value'] = [cells_json]
        order.append((off, entry))

    # ---------- 2) 叙述字段 ----------
    for f in fields:
        if f['slot'] != 'para':
            continue
        if 'after' in f:
            off, cnt = para_anchor_end(f['after'])
            assert off is not None, '锚点「%s」命中 %d 次' % (f['after'], cnt)
        else:
            tno = f['after_table']
            ts, te = tbl_spans[tno - 1]
            off = te
        bid = next_id; next_id += 1
        id_map[f['code']] = bid
        ops.append((off, PARA_TPL % bmk(bid, f['code'])))
        order.append((off, {'code': f['code'], 'desc': f['desc'], 'value': ''}))

    # ---------- 3) 逆序插入 ----------
    for off, txt in sorted(ops, key=lambda x: -x[0]):
        body = body[:off] + txt + body[off:]

    newdoc = head + body + tail
    open(docp, 'w', encoding='utf-8').write(newdoc)

    if os.path.exists(DST):
        os.remove(DST)
    with zipfile.ZipFile(SRC) as zin, zipfile.ZipFile(DST, 'w', zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = newdoc.encode('utf-8') if item.filename == 'word/document.xml' else zin.read(item.filename)
            zout.writestr(item, data)

    # ---------- 4) 书签 json ----------
    order.sort(key=lambda x: x[0])
    bk_json = [e for _, e in order]
    with open(OUT_BK, 'w', encoding='utf-8') as fp:
        json.dump(bk_json, fp, ensure_ascii=False, indent=2)

    # ---------- 5) 字段分类 json ----------
    tbl_desc = {t['index']: t['desc'] for t in tables}
    fc = []
    for f in fields:
        desc = f['desc'] if f['slot'] == 'para' else '%s-%s' % (tbl_desc[f['table']], f['desc'])
        fc.append({'code': f['code'], 'desc': desc, 'category': f['category'],
                   'field_type': f['field_type'], 'hint_doc_types': f['hint_doc_types'],
                   'narrative_cells': []})
    with open(OUT_FC, 'w', encoding='utf-8') as fp:
        json.dump(fc, fp, ensure_ascii=False, indent=2)

    print('书签总数:', len(id_map), '| 书签json条目:', len(bk_json), '| 字段分类条目:', len(fc))
    print('written:', DST)
    print('written:', OUT_BK)
    print('written:', OUT_FC)


if __name__ == '__main__':
    main()
