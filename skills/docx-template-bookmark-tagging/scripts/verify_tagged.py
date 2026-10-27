# -*- coding: utf-8 -*-
import glob, xml.etree.ElementTree as ET, zipfile, re, json, os, sys
B = '/Users/chenjie/Documents/work/AI/智能模板/template 2'
DST = B + '/新模板相关/（金鼎集团）审查意见类模板（已打标签）.docx'
SRC = B + '/新模板相关/（金鼎集团）审查意见类模板（空白）.docx'
WORK = '/tmp/tag_v'

os.system('rm -rf %s && mkdir -p %s' % (WORK, WORK))
zipfile.ZipFile(DST).extractall(WORK)

z = zipfile.ZipFile(DST)
s = zipfile.ZipFile(SRC)
print('zip 完整性:', z.testzip() or 'OK')
print('部件 缺失:', sorted(set(s.namelist()) - set(z.namelist())), '| 新增:', sorted(set(z.namelist()) - set(s.namelist())))
print('仅 document.xml 变化:', all(z.read(n) == s.read(n) for n in s.namelist() if n != 'word/document.xml'))

bad = []
for f in glob.glob(WORK + '/**/*.xml', recursive=True) + glob.glob(WORK + '/**/*.rels', recursive=True):
    try:
        ET.parse(f)
    except Exception as e:
        bad.append((f, str(e)))
print('XML 合法性:', '全部通过' if not bad else bad)

doc = z.read('word/document.xml').decode('utf-8')
names = re.findall(r'<w:bookmarkStart[^>]*w:name="([^"]*)"', doc)
ids = re.findall(r'<w:bookmarkStart[^>]*w:id="(\d+)"', doc)
print('书签数:', len(names), '| id 唯一:', len(ids) == len(set(ids)), '| 名唯一:', len(names) == len(set(names)))
print('start/end 配对:', len(re.findall(r'<w:bookmarkStart', doc)) == len(re.findall(r'<w:bookmarkEnd', doc)))

bk = json.load(open(B + '/审查意见类模板书签json文档.json', encoding='utf-8'))
codes = []
for it in bk:
    codes.append(it['code'])
    if it.get('type') == 'table':
        codes += [c['code'] for c in it['value'][0]]
dset = set(names) - {'_GoBack', '_Hlk109676603', 'RANGE!D14'}
cset = set(codes)
print('书签数 vs JSON code 数:', len(dset), len(cset))
print('docx 有 / JSON 无:', sorted(dset - cset))
print('JSON 有 / docx 无:', sorted(cset - dset))

fc = json.load(open(B + '/审查意见类模板字段分类.json', encoding='utf-8'))
# 约定：字段分类不含「表自身的 code」，只含叶子字段
table_codes = {it['code'] for it in bk if it.get('type') == 'table'}
leaf_codes = cset - table_codes
print('字段分类条数:', len(fc), '| 表 code 数:', len(table_codes), '| 叶子 code 数:', len(leaf_codes))
print('字段分类 == 叶子集合:', {x['code'] for x in fc} == leaf_codes)
print('字段分类误含表 code:', sorted({x['code'] for x in fc} & table_codes))

print()
print('=== 逐表书签位置 ===')
W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
root = ET.parse(WORK + '/word/document.xml').getroot()
body = root.find(W + 'body')


def ptext(p):
    return ''.join(t.text or '' for t in p.iter(W + 't'))


ti = 0
for ch in body:
    if ch.tag == W + 'tbl':
        ti += 1
        rows = ch.findall(W + 'tr')
        names_all = [b.get(W + 'name') for b in ch.iter(W + 'bookmarkStart')]
        print('T%d (%d行): %s' % (ti, len(rows), names_all))
        for ri, tr in enumerate(rows[:4]):
            cs = []
            for tc in tr.findall(W + 'tc'):
                b = [x.get(W + 'name') for x in tc.iter(W + 'bookmarkStart')]
                cs.append('[%s|%s]' % (ptext(tc).strip()[:16], ','.join(b) or '-'))
            print('   R%d: %s' % (ri, ' '.join(cs)))

print()
print('=== 段落书签 ===')
for ch in body:
    if ch.tag != W + 'p':
        continue
    b = [x.get(W + 'name') for x in ch.iter(W + 'bookmarkStart')]
    t = ptext(ch).strip()
    if b or t:
        print('P: %-52r %s' % (t[:50], b if b else ''))
