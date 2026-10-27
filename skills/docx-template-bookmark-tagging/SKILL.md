---
name: docx-template-bookmark-tagging
description: 把已填的 Word 文档（.docx）清理成空白模板、打标签、并产出「打标预处理json + 书签json + 字段分类json」。当用户说「模板清理」「清空数据做空白模板」「对模板进行打标签」「生成书签json」「字段分类json」「打标预处理」「让别的地方取数回填模板」「模板变量化」，或给出一个 docx 模板 + 参考 json 结构要求照做时使用。
agent_created: true
---

# Word 模板：清理 → 打标 → 书签 + 两个 JSON

把一份已填的 Word 文档变成「可被程序按字段回填」的空白模板，产出：

1. **空白模板 docx**：清掉数据、保留骨架
2. **打标预处理 json**：全部待填充点清单（位置 + 建议 code + 类型 + 来源），驱动下一步
3. **模板 docx**：每个填充点插一个以 `code` 命名的**零长度 Word 书签**
4. **书签json文档**：嵌套结构，镜像文档章节（表型 / 叙述型）
5. **字段分类json**：扁平叶子字段清单，带 category / field_type / hint_doc_types

## 铁律

- **书签名 == JSON 里的 code**，一一对应，不允许重复（Word 书签名必须唯一）
- 书签是**零长度**的，不带文字：`<w:bookmarkStart w:id="N" w:name="code"/><w:bookmarkEnd w:id="N"/>`
- 书签放在 `<w:p>` 内 `</w:pPr>` **之后**（`'</w:pPr>'` 长度是 **8**，写 7 会插进标签内部 → XML 非良构）
- **`editor_sdk`（tencent-local-office-edit）没有书签工具**，必须直接改 `word/document.xml`
- 重打包 docx 用「复制原 docx、只替换 `word/document.xml`」，不要重新遍历目录打包（会丢 zip 目录条目）
- 改 `word/document.xml` 必须做**字符串级**操作（重新序列化会改命名空间前缀）

## 第零步：模板清理（把已填文档变成空白模板）

先找一份**同类业务的空白模板**当标准（金鼎项目里是 `担保类尽调报告.docx`），反推它的形态再照做。

实测形态（担保类 / 审查意见类一致）：

| 处理 | 对象 |
|---|---|
| **保留** | 章节标题、表格表头与行标签、引导语（「…如下：」）、表标题与表注、附件清单、落款/签署栏、页眉页脚、无数据的结构图 |
| **清空** | 表格数据单元格 —— 只删 `<w:r>`，保留 `<w:p>`/`<w:pPr>`（保住行与单元格格式） |
| **删除** | 分析性正文段落（担保类模板里标题下直接跟下一个标题，正文全无） |
| **保留选项框** | 勾选类单元格（`□符合 ☑不符合`）→ 复位成 `□符合 □不符合`，删掉具体理由，**不要清空** |
| **占位** | 标题 / 文号 / 日期 / 附件名里的具体值 → `XX` |

> ⚠️ 具体机构名（担保人简称、发行人简称）**不只出现在标题**，还会藏在**表格的标签格 / 依据格**里
> （如「参照**金玉担保**获批的《…》」）。清理时要把这些一并占位成 `XX担保`，
> 否则模板里会残留真实企业名。做法：给 `CELL_TEXT` 也加一条精确改写规则。

实现见 `scripts/clean_template.py`。关键做法：

```python
DELETE / REPLACE 用「文本规则」判定，不要用下标：
  - 标题：re.match(r'^[一二三四五六七八九十]+、', t) 或 r'^（[一二三四五六七八九十]+）'
  - 精确文本映射表 REPLACE_MAP（原文 -> 占位文本）
  - 其余非空段落 -> 删除
```

> ⚠️ **别用元素下标定位段落**。顶层切分时 `<w:bookmarkEnd>` 不属于 `w:p/w:tbl/w:sectPr`，
> 不计入索引，会让 ElementTree 子节点索引和自定义扫描器索引**整体错位 1**（尤其 `bookmarkEnd` 之后）。
> 文本规则稳定且可复核。

> ⚠️ 正则 `<w:t[^>]*>` 会**误匹配** `<w:tcPr>` / `<w:tab/>` / `<w:textAlignment>`，
> 必须写成 `<w:t(?: [^>]*)?>`。

清理时同步记下「被删掉的段落」—— 打标阶段要在这些位置补空段落 + 书签。

## 第零步之二：打标预处理 json

清理完顺手产出，作为打标的输入（实现见 `scripts/build_fields.py`）：

```json
{
  "meta": {"doc_type": "...", "template_file": "...", "based_on": "...", "total_fields": 106},
  "tables": [{"index":1, "code":"applyPlan", "desc":"申报方案", "shape":"keyvalue", "render":"2", "rows":20, "cols":2}],
  "fields": [
    {"seq":1, "section":"一、申报方案", "slot":"cell", "table":1, "row":0, "cell":1,
     "code":"applyUnit", "desc":"申报单位", "field_type":"structured",
     "category":"信用与担保类", "hint_doc_types":["担保文件"], "sample":"…"},
    {"seq":88, "section":"二、…", "slot":"para", "after":"（一）发行人、反担保人股权结构及对外投资",
     "code":"equityHoldingDesc", "desc":"…", "field_type":"narrative", "…":"…"}
  ]
}
```

- `slot=cell`：按 `(table, row, cell)` 定位，`row/cell` 是 **tc 序号**（不是列号，合并单元格会错位）
- `slot=para`：叙述型字段，`after` = 插在该段落之后；跨表的用 `after_table`
- `sample` 存原文档样例值，只作理解参考，**不写入模板**
- 生成后必须校验：code 唯一、每个 cell 位置存在且目标格为空（选项框字段除外）、每个 anchor 文本在模板中存在

## 第一步：先逆向出参考约定

拿到参考产物（书签 json + 对应 docx）时，**不要凭想象**，先解压参考 docx 反查约定：

```bash
unzip -o ref.docx -d /tmp/ref
python3 - <<'PY'
import xml.etree.ElementTree as ET, re
W='{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
root=ET.parse('/tmp/ref/word/document.xml').getroot()
def ptext(p): return ''.join(t.text or '' for t in p.iter(W+'t'))
for tbl in root.iter(W+'tbl'):
    rows=tbl.findall(W+'tr')
    print(f'=== {len(rows)} 行')
    for ri,tr in enumerate(rows[:4]):
        cs=[]
        for tc in tr.findall(W+'tc'):
            b=[x.get(W+'name') for x in tc.iter(W+'bookmarkStart')]
            cs.append(f'[{ptext(tc).strip()}|{",".join(b) or "-"}]')
        print(f'  R{ri}: '+' '.join(cs))
PY
```

要确认的四件事：
1. 书签是不是零长度、放在 `</w:pPr>` 之后
2. **键值表**（json 里 `render:"2"`）：标签格留文字、值格挂书签；表锚点（= 表 code）放哪
3. **网格表**（无 `render`）：表头行 / 锚点行 / 列定义行 / 空数据行的排布
4. 字段分类 json 是否**排除表本身的 code**、表内 desc 是否用 `父级desc-子级desc`

> 实测（金鼎担保类）约定见 `references/conventions.md`。

## 第二步：枚举填充点

按文档顺序过一遍顶层段落与表格，逐个记：

| 类型 | 处理 |
|---|---|
| 标题里的变量（公司名/金额/品种/文号） | 行内零长度书签，原文字删除 |
| 章节标题里的变量（如「发行人{简称}情况分析」） | 行内书签，**保留**"发行人""情况分析"等静态字 |
| 键值表的值格 | 值格挂书签，标签格保留 |
| 网格表 | 见上面铁律的 4 行结构 |
| 叙述段（分析/说明/结论） | 新建空段落 + 书签（原占位文字删掉） |
| 空标题下无正文 | 必须**补一个空段落**放书签，否则无处可填 |

注意：文档里可能有多处**同名段落**（如两个「财务分析」），用出现顺序区分，别用文本做唯一 key。

## 第三步：写脚本生成

参考实现（按流程顺序）：

| 脚本 | 作用 |
|---|---|
| `scripts/clean_template.py` | 模板清理 → 空白模板 docx |
| `scripts/build_fields.py` | → 打标预处理 json |
| `scripts/tag_template.py` | 读预处理 json → 插书签 + 书签json + 字段分类json |
| `scripts/verify_tagged.py` | 强制校验 |

```bash
PY=/Users/chenjie/.workbuddy-ai/binaries/python/versions/3.13.12/bin/python3
$PY scripts/clean_template.py
$PY scripts/build_fields.py
$PY scripts/tag_template.py
$PY scripts/verify_tagged.py
```

`clean_template.py` 的 `REPLACE_MAP` / `CELL_CLEAR`、`build_fields.py` 的 `FIELDS` 是**唯一真源**，
改字段只改这里，别两头手工同步。

### 插书签的定位实现

- **单元格字段**：算绝对偏移 `表起始 + 行起始 + 格起始 + 段内 </w:pPr> 之后`
- **叙述字段**：在锚点段落 `</w:p>` 之后插入 `PARA_TPL`（正文格式空段落 + 书签）
- **表锚点**：**独占一个空行**，挂在该行 C0，位置紧贴字段定义行之前（表头行之后）。
  本套文档的键值表原本没有这一行 → 用 `insert_anchor_row()` 克隆字段行、剥掉内容后插进去。
  ⚠️ **绝不能把锚点塞进表头行** —— 渲染引擎会把含锚点的行当数据行覆盖掉，表头就没了
  （金鼎审查意见类实测踩坑）。行号因此整体 +1，`build_fields.py` 用 `R(t,r)` 换算
- 所有插入操作先收集成 `(offset, text)`，再**按 offset 降序**统一插入，避免偏移漂移
- 书签 id 从现有 `max(w:id)+1` 起递增，保证唯一

### `render` 的运行时语义（决定静态标签会不会被抹掉）

`render` 不是给人看的元数据，它**直接改变引擎回填时对整行的处理方式**：

| json 里的 `render` | 引擎行为 | 结果 |
|---|---|---|
| `"2"` | 只替换**书签所在格**，同行其余格原样保留 | 行标签（发行人 / 编号 / 审查依据 / 合计 / 占比…）**保住** |
| 不写 | 把**写进去的那一行整行清掉**，再按 code 落位 | 行标签被抹掉，只剩值 |

判定规则（**实测推导，不是猜的**）：

- **凡是「字段行里除了书签格还有静态标签格」的表，一律给 `render:"2"`**
- 反查依据：金鼎**担保类**模板 36 张表里，字段行含静态标签格的 **14 张全部带 `render:"2"`**（14/14）；
  另 9 张带 `render:"2"` 但无静态标签格 —— 多给无害，所以判定放宽成「有标签格就给」
- 反面验证：审查意见类 T1 带 `render:"2"` → 20 行标签全保留；
  T2/T5/T6/T7/T8 当时漏了 `render` → 「发行人 / 反担保人」「1…5 + 参照《…》」「合计 / 占比」全被清空
- 注意引擎**只清它写过的行**：某表只喂 1 条数据时，后面没被写的「合计」行看起来还在，
  容易误判成「不加 render 也没事」——所以判据要看**模板结构**，不要看单次渲染结果

`render` 的其它取值见过 `"1"`（地产类 1 张表）和 `"饼图"`（`type:"charts"`），含义未逆清，**别乱套**。

> ⚠️ **修 render 时不要顺手改 `shape`**。`shape`（`keyvalue`/`grid`）是**纯描述性元数据**，
> 没有任何脚本读它；`render` 才是给引擎的功能开关。两个字段容易看着「语义重复」就一起改，
> 但改了会让 json 与之前交付的版本**结构不一致**（金鼎审查意见类被用户退回来过：
> 「数据结构和之前不一样啊，不要改数据结构」）。判定标准：**改完的 json 与上一版
> 应该只差 `render` 那一个字段的值**；可以用「把新 json 的 render 置回 null、重新 dump、
> 比对字节数是否等于上一版」来自证。

### 两个 JSON 的形态

- **书签 json**：数组，按文档顺序。叙述型 `{code, desc, value:""}`；
  表型 `{code, type:"table", [render:"2"], desc, value:[[{code,desc,value}, …]]}`
- **字段分类 json**：扁平数组，`{code, desc, category, field_type, hint_doc_types, narrative_cells}`，
  表内字段 `desc = 表desc-字段desc`，**不含表自身的 code**（故条数 = 书签数 − 表数）
- ⚠️ 拼 `desc` 前缀时，字段自身的 desc 必须是**纯字段名**，否则会拼出
  「合规性审查-合规性审查-1-具体内容」这种重复

## 第四步：强制校验

**每次生成后必须跑**（脚本在 `scripts/verify_tagged.py`）：

- docx 所有 XML part 合法（`ET.parse` 全过）
- zip 完整性 `testzip() is None`；与源 docx 相比**无缺失/新增部件**
- 书签 **id 唯一 + name 唯一**；`bookmarkStart` 与 `bookmarkEnd` 数量配对
- 书签集合（去掉 Word 自带 `_GoBack` / `_Hlk*` / `RANGE!*`）**等于** JSON code 集合；无重复书签
- 字段分类条数 = 书签数 − 表 code 数
- 逐表打印 R0..R3 的 `[文字|书签名]`，肉眼过一遍位置对不对

## 第五步：打包产出

**所有产物统一放一个新建的产出文件夹**，不要跟源文档混在同一个目录里。标准结构：

```
<产出文件夹>/                      # 只放这两份 json（+ txt）+ 两个 docx
  （xx）xxx类模板（空白）.docx
  （xx）xxx类模板（已打标签）.docx
  xxx类模板书签json文档.json
  xxx类模板书签json文档.txt         # 紧凑单行 json
  xxx类模板字段分类.json
  xxx类模板字段分类.txt             # 紧凑单行 json
```

⚠️ **`打标预处理.json` 不进产出文件夹** —— 它是**流水线中间产物**（`tag_template.py` 的输入），
只留在源目录。用户明确说过「不需要预处理这个 json，只要 模板书签json文档 和 模板字段分类」。
`pack_output.py` 里有 `DROP` 清单，重跑时会把误放进产出目录的中间产物清掉。

**交付的 json 都要配 txt** —— 甲方参考产物（`担保类/地产类模板书签json文档.txt`）就是这种
「pretty json + 紧凑 txt」成对交付的形态。

> ⚠️ **`render` 只存在于 `书签json文档.json` 里**（不在字段分类里）。所以「修静态标签被抹掉」
> 改的 `render` 最终要体现在**交付的那份书签json**上；预处理 json 只是链路中间件。
> 改完记得确认交付版里那几张表确实带上了 `render:"2"`。

`txt` 不是纯文本摘要，是**去掉缩进的紧凑 JSON**（可直接被程序读）：

```python
json.dump(d, fp, ensure_ascii=False, separators=(',', ':'))
```

实现见 `scripts/pack_output.py`。生成后必须校验 `json.loads(txt) == json.load(json)`。

⚠️ **产物必须写到用户实际在用的那个目录**。踩过两次的坑：脚本归档目录和用户交付目录是两个路径，
只写了一个，用户上传的仍是另一边的旧版，于是「改了没生效」。`pack_output.py` 现在**强制双写**
（`OUT` 归档 + `MIRROR` 用户目录），加新目录时记得一起挂上。

## 第六步：字段分类 json 的规则

规则来自用户库里的 `字段分类提示词.md`，要点：

- `field_type`：`narrative`（要 LLM 成段分析，desc 含 说明/分析/结论/建议/评价/概述/总结/综述/判断/意见/展望/可行性/研判/评述/阐述）→ `category` 填 `分析说明类`；否则 `structured`（能原样摘取）
- ⚠️ **例外**：勾选类字段（"是否符合…""集团客户判断""审批权限"）字面含"判断"但实为短值 → 仍判 `structured`
- `category` 取值：工商信息类 / 财务信息类 / 银行与税务类 / 经营与合同类 / 资产与权属类 / 资质与荣誉类 / 信用与担保类 / 项目与背景类 / 其他类 / 分析说明类
- `hint_doc_types` 取值：营业执照 / 公司章程 / 财务报表 / 审计报告 / 银行流水 / 购销合同 / 发票 / 完税证明 / 股东会决议 / 董事会决议 / 不动产权证 / 土地使用权证 / 建设工程规划许可证 / 商品房预售许可证 / 招投标文件 / 订单与应收账款清单 / 资质证书 / 征信报告 / 担保文件 / 企业简介与项目说明 / 其他；判断不了给 `[]`
- `narrative_cells` 恒为 `[]`

建议**显式给每个 code 配元数据**（dict 查表），不要靠关键词自动匹配——更可控，且漏配能靠 assert 兜住。

## 交付前

- **清理完必须先把空白模板交用户确认「是否真的空白」**，再往下做打标/打包。
  主动 dump 一遍全部非空文本（含表格坐标），把「结构性文字」和「残留具体值」分开列给用户拍板，
  不要自己判断完就往下走
- 产物**改完不算生效**：`renderTemplate` 这类回填接口用的是**服务端已上传的那份模板 + 预处理 json**，
  本地改了必须让用户重新上传再调。别拿本地文件去解释线上渲染结果
- ⚠️ **`editor_sdk` 打开着的 docx 会被编辑器自动保存覆盖**。如果产出目录里的文件正被编辑器打开，
  重新生成后必须**先让用户关掉编辑器**，或**换新文件名**再交付 —— 否则你新生成的版本会被旧内容盖掉，
  用户上传的还是旧版（金鼎审查意见类踩过这个坑）
- 排查「改了没生效」的顺序：① 比对**本地源文件 vs 服务端产物**的 md5 / 表行数；
  ② 用「把所有值换成唯一标记」实验区分是**服务端缓存**还是**模板没更新**
- 别覆盖用户原始模板文件，另存新文件
- 自己补的表头 / 补的章节，要在回复里**明确列出来**让用户确认，不要默认用户知道
- 文档原有编号跳号（如「三、」跳「五、」）**不要擅自改**，只报告
- 清理阶段拿不准的（表头年份要不要占位、审查依据列要不要清空、选项框留不留），**列出来让用户拍板**，
  不要默默替用户决定
- 清理/打标脚本里的 `REPLACE_MAP`、`CELL_CLEAR`、`FIELDS` 是**唯一真源**，改字段只改这里，别手工同步多个产物
