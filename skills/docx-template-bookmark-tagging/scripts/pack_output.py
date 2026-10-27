# -*- coding: utf-8 -*-
"""把产物汇总到产出文件夹，并把交付的 json 各压一份紧凑单行 txt。

交付物（只这两份 json，用户明确要求）：
  （xx）xxx类模板（空白）.docx
  （xx）xxx类模板（已打标签）.docx
  xxx类模板书签json文档.json + .txt
  xxx类模板字段分类.json     + .txt

`审查意见类模板打标预处理.json` 是**流水线中间产物**（tag_template.py 的输入），
只留在源目录 `template 2/`，**不进产出文件夹**。

两个产出目录都要写：
  OUT    = template 2/审查意见类模板      （脚本自己的归档目录）
  MIRROR = 智能模板/审查意见类模板        （用户实际在用的目录，编辑器也开在这里）
历史上踩过「产物只写了一个目录、用户上传的是另一个目录的旧版」的坑，所以这里强制双写。
"""
import json, os, shutil

BASE = '/Users/chenjie/Documents/work/AI/智能模板/template 2'
SRC_DIR = os.path.join(BASE, '新模板相关')
OUT = os.path.join(BASE, '审查意见类模板')
MIRROR = '/Users/chenjie/Documents/work/AI/智能模板/审查意见类模板'

DOCX = ['（金鼎集团）审查意见类模板（空白）.docx',
        '（金鼎集团）审查意见类模板（已打标签）.docx']
JSON = ['审查意见类模板书签json文档.json',
        '审查意见类模板字段分类.json']
TXT = ['审查意见类模板书签json文档',
       '审查意见类模板字段分类']
# 不交付：曾经误放进产出目录，重跑时清掉
DROP = ['审查意见类模板打标预处理.json',
        '审查意见类模板打标预处理.txt']

os.makedirs(OUT, exist_ok=True)
DIRS = [OUT] + ([MIRROR] if os.path.isdir(MIRROR) else [])
print('写入目录:', DIRS)

# 0) 清掉不该出现在产出目录里的中间产物
for d in DIRS:
    for f in DROP:
        p = os.path.join(d, f)
        if os.path.exists(p):
            os.remove(p)
            print('drop ->', f)

# 1) 复制 docx
for d in DIRS:
    for f in DOCX:
        shutil.copy2(os.path.join(SRC_DIR, f), os.path.join(d, f))
print('copy -> docx x%d  (%d 个目录)' % (len(DOCX), len(DIRS)))

# 2) 复制 json
for d in DIRS:
    for f in JSON:
        shutil.copy2(os.path.join(BASE, f), os.path.join(d, f))
print('copy -> json x%d' % len(JSON))

# 3) json -> 紧凑单行 txt，并校验 txt 能原样读回
for name in TXT:
    d = json.load(open(os.path.join(BASE, name + '.json'), encoding='utf-8'))
    body = json.dumps(d, ensure_ascii=False, separators=(',', ':'))
    assert json.loads(body) == d, '%s txt 回读不一致' % name
    for dd in DIRS:
        p = os.path.join(dd, name + '.txt')
        with open(p, 'w', encoding='utf-8') as fp:
            fp.write(body)
    print('txt  -> %-30s %8d B  (回读校验 OK)' % (name + '.txt', len(body.encode('utf-8'))))

print()
for d in DIRS:
    print('=== %s ===' % d)
    for f in sorted(os.listdir(d)):
        print('  %-48s %8d B' % (f, os.path.getsize(os.path.join(d, f))))
